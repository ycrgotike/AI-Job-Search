#!/usr/bin/env python3
"""Autonomous Application Document Generator for AI Job Search.

Tailors, compiles, and verifies ATS-optimized LaTeX CV and Cover Letter
for any target job posting, enforcing all workspace and candidate rules:
- Candidate Name: Yashwanth Gotike
- Reverse chronological experience (SolTech -> G.S.R -> ITC Infotech)
- SolTech location: Hyderabad, India
- Section name: Technical Skills (never Core Competencies)
- Education: 10/2024--Present (no expected graduation text)
- Strict page counts: CV = 2 pages (LuaLaTeX), Cover Letter = 1 page (XeLaTeX)
- Explicit English C1 and German B2 proficiency in Cover Letter
- Document naming: YashwanthGotike_<CompanyName>_CV and YashwanthGotike_<CompanyName>_CoverLetter
- Tracker update: job_search_tracker.csv
- Archival: documents/applications/<CompanyName>_<Role>/
"""

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

# The dashboard reloads this generator per request; refresh its planning dependency too.
for dependency in ('tools.responsibility_plan', 'tools.job_description', 'tools.technology_evidence', 'tools.gemini_tailoring'):
    if dependency in sys.modules:
        import importlib
        importlib.reload(sys.modules[dependency])

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TINYTEX_BIN = Path.home() / "Library" / "TinyTeX" / "bin" / "universal-darwin"
TRACKER_FILE = ROOT / "job_search_tracker.csv"
SEEN_JOBS_FILE = ROOT / "job_scraper" / "seen_jobs.json"
CV_DIR = ROOT / "cv"
COVER_DIR = ROOT / "cover_letters"
DOCUMENTS_DIR = ROOT / "documents" / "applications"


def clean_title(t: str) -> str:
    """Remove parenthetical/bracketed and delimited gender markers, diversity tags, and clean role title."""
    if not t:
        return ""
    s = t.strip()
    # 1. Strip parenthetical / bracketed gender & diversity markers
    s = re.sub(
        r"[\(\[\{]\s*(?:all\s+genders?(?:\s+welcome)?|alle\s+geschlechter(?:\s+willkommen)?|"
        r"m/w/d(?:\*|/x)?|w/m/d(?:\*|/x)?|f/m/d(?:\*|/x)?|m/f/d(?:\*|/x)?|d/f/m(?:\*|/x)?|"
        r"m/f/d/x|w/m/x|m/f/x|m/w/x|m/w/div(?:\.|ers)?|m\|w\|d|w\|m\|d|d\|m\|w|"
        r"m\s*,\s*w\s*,\s*d|m\s*/\s*w\s*/\s*d|w\s*/\s*m\s*/\s*d|"
        r"mwd|gn|g\.n\.|mensch\*?)\s*[\)\]\}]",
        "",
        s,
        flags=re.IGNORECASE,
    )
    # 2. Strip delimiter-separated gender & diversity markers (e.g., " - all genders welcome", " | m/w/d")
    s = re.sub(
        r"[\s,\-\|/]+\s*(?:all\s+genders?(?:\s+welcome)?|alle\s+geschlechter(?:\s+willkommen)?|"
        r"m/w/d(?:\*|/x)?|w/m/d(?:\*|/x)?|f/m/d(?:\*|/x)?|m/f/d(?:\*|/x)?|d/f/m(?:\*|/x)?|"
        r"m/f/d/x|w/m/x|m/f/x|m/w/x|m/w/div(?:\.|ers)?|m\|w\|d|w\|m\|d|d\|m\|w|"
        r"mwd|gn|g\.n\.|mensch\*?)(?=[\s,\-\|/]|$)",
        "",
        s,
        flags=re.IGNORECASE,
    )
    # 3. Strip standalone gender markers if still remaining
    s = re.sub(
        r"\b(?:all\s+genders?(?:\s+welcome)?|alle\s+geschlechter(?:\s+willkommen)?)\b",
        "",
        s,
        flags=re.IGNORECASE,
    )
    # 4. Collapse consecutive whitespace and clean dangling boundary delimiters
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[\s,\-\|/]+$", "", s)
    s = re.sub(r"^[\s,\-\|/]+", "", s)
    return s.strip()


def sanitize_company_name(comp: str) -> str:
    """Extract clean PascalCase company name without legal suffixes."""
    c = comp or "Company"
    c = re.sub(r"\b(?:GmbH & Co\.? KG|GmbH & Co|GmbH|AG|SE|KGaA|KG|Ltd|Limited|LLC|Inc|Corp|e\.V\.)\b", "", c, flags=re.IGNORECASE)
    c = re.sub(r"[^\w\s]", "", c)
    words = c.strip().split()
    if not words:
        words = ["Company"]
    pascal = "".join(w.capitalize() for w in words if w.isalnum())
    return pascal or "Company"


def get_pdf_page_count(pdf_path: Path) -> int:
    """Get exact page count of a PDF using pdfinfo or macOS mdls."""
    if not pdf_path.is_file():
        return 0
    for cmd in ["/opt/homebrew/bin/pdfinfo", "pdfinfo"]:
        try:
            out = subprocess.check_output([cmd, str(pdf_path)], text=True, stderr=subprocess.DEVNULL)
            m = re.search(r"^Pages:\s+(\d+)", out, re.MULTILINE)
            if m:
                return int(m.group(1))
        except Exception:
            pass
    try:
        out = subprocess.check_output(["mdls", "-name", "kMDItemNumberOfPages", str(pdf_path)], text=True, stderr=subprocess.DEVNULL)
        m = re.search(r"=\s*(\d+)", out)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return 0


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters safely."""
    if not text:
        return ""
    chars = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(chars.get(c,c) for c in text)


# ---------------------------------------------------------------------------
#   ON-THE-FLY DESCRIPTION FETCHING (when seen_jobs.json has no description)
# ---------------------------------------------------------------------------

def _run_detail_payload(cli_rel: str, id_or_url: str) -> dict:
    """Run a portal detail CLI and return the description text."""
    cli_path = ROOT / ".agents" / "skills" / cli_rel / "cli" / "src" / "cli.ts"
    if not cli_path.is_file():
        return {}
    cmd = ["bun", "run", str(cli_path), "detail", id_or_url, "--format", "json"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def _run_detail_cli(cli_rel: str, id_or_url: str) -> str:
    return (_run_detail_payload(cli_rel, id_or_url).get('description') or '').strip()


def fetch_description_for_job(job: dict) -> str:
    """Resolve missing/referral descriptions, preserving discovery and freshness data."""
    from tools.job_description import resolve_description
    portal = (job.get('portal') or '').lower()
    url = job.get('url', '')
    job_id = job.get('id', '')
    adapter = next((p for p in ('linkedin', 'stepstone', 'arbeitsagentur', 'xing', 'freehire')
                    if p in portal or p in url), None)
    detail = _run_detail_payload(adapter + '-search', job_id or url) if adapter else {}
    result = resolve_description(job, detail)
    job.update(result)
    persist_description(job.get('key', ''), result.get('description', ''), result)
    return result.get('description', '') if result['description_status'] == 'ready' else ''


def persist_description(job_key: str, description: str, metadata=None):
    """Save a fetched description back into seen_jobs.json so future calls are faster."""
    if not SEEN_JOBS_FILE.is_file() or not job_key:
        return
    try:
        with SEEN_JOBS_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
        seen = data.get("seen", {})
        if job_key in seen:
            if description:
                seen[job_key]["description"] = description
            for field in ('description_source_url', 'discovery_url', 'description_status', 'description_fetch_errors'):
                if metadata and field in metadata:
                    seen[job_key][field] = metadata[field]
            with SEEN_JOBS_FILE.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ---------------------------------------------------------------------------
#   DEEP KEYWORD EXTRACTION FROM JOB DESCRIPTIONS
# ---------------------------------------------------------------------------

# Comprehensive tech/skill keyword registry grouped by domain.
# Each entry: (regex_pattern, canonical_label, domain)
KEYWORD_REGISTRY = [
    # Data Engineering & Lakehouse
    (r"\bdatabricks\b", "Databricks", "data_eng"),
    (r"\bapache\s*spark\b|\bpyspark\b", "Apache Spark / PySpark", "data_eng"),
    (r"\bdelta\s*lake\b", "Delta Lake", "data_eng"),
    (r"\bmedallion\b|bronze.silver.gold", "Medallion Architecture", "data_eng"),
    (r"\blakeflow\b", "Lakeflow", "data_eng"),
    (r"\blakehouse\b", "Lakehouse", "data_eng"),
    (r"\bdata\s*factory\b|\badf\b", "Azure Data Factory", "data_eng"),
    (r"\betl\b|\belt\b", "ETL/ELT", "data_eng"),
    (r"\bdata\s*pipeline", "Data Pipelines", "data_eng"),
    (r"\bdata\s*warehouse\b|\bdwh\b", "Data Warehousing", "data_eng"),
    (r"\bdata\s*model(?:ing|l?)\b|\bdimensional\b|\bstar\s*schema\b|\bsnowflake\s*schema\b", "Data Modeling", "data_eng"),
    (r"\bfabric\b", "Microsoft Fabric", "data_eng"),
    (r"\bdbt\b", "dbt", "data_eng"),
    (r"\bkafka\b", "Apache Kafka", "data_eng"),
    (r"\bstreaming\b", "Streaming Ingestion", "data_eng"),
    (r"\bdata\s*governance\b|\bdata\s*quality\b|\bquality\s*assurance\b|\bdatenqualität\b|\bdatenqualitaet\b|\bdaten-governance\b|\bqa\b|\bdata\s*lineage\b|\bdata\s*profiling\b", "Data Governance & Quality Assurance", "data_eng"),
    (r"\bschema\s*enforc", "Schema Enforcement", "data_eng"),
    # Orchestration
    (r"\bairflow\b", "Apache Airflow", "orchestration"),
    (r"\borchestrat", "Pipeline Orchestration", "orchestration"),
    (r"\bprefect\b", "Prefect", "orchestration"),
    (r"\bdagster\b", "Dagster", "orchestration"),
    # Cloud & Infrastructure
    (r"\bazure\b", "Azure", "cloud"),
    (r"\baws\b|\bamazon\s*web\b", "AWS", "cloud"),
    (r"\bgcp\b|\bgoogle\s*cloud\b", "GCP", "cloud"),
    (r"\bdocker\b", "Docker", "cloud"),
    (r"\bkubernetes\b|\bk8s\b", "Kubernetes", "cloud"),
    (r"\bterraform\b|\biac\b", "Terraform / IaC", "cloud"),
    (r"\bci/?cd\b|\bcontinuous\s*integrat", "CI/CD", "cloud"),
    (r"\bgithub\s*actions\b", "GitHub Actions", "cloud"),
    (r"\bdevops\b", "DevOps", "cloud"),
    (r"\bgit\b", "Git", "cloud"),
    # Programming
    (r"\bpython\b", "Python", "programming"),
    (r"\bsql\b|\bt-sql\b|\bpostgresql\b|\bpostgres\b|\bmysql\b", "SQL", "programming"),
    (r"\bscala\b", "Scala", "programming"),
    (r"\bjava\b(?!script)", "Java", "programming"),
    (r"\br\b(?:\s+programming|\s+language|\s+studio)", "R", "programming"),
    # Analytics & BI
    (r"\bpower\s*bi\b|\bdax\b", "Power BI (DAX)", "analytics"),
    (r"\btableau\b", "Tableau", "analytics"),
    (r"\blooker\b", "Looker", "analytics"),
    (r"\ba/?b\s*test", "A/B Testing", "analytics"),
    (r"\bcohort\b", "Cohort Analysis", "analytics"),
    (r"\bkpi\b|\bdashboard", "KPI Dashboards", "analytics"),
    (r"\beda\b|\bexploratory\s*data\s*analysis\b", "EDA", "analytics"),
    # AI / ML / GenAI
    (r"\brag\b|\bretrieval.augmented", "RAG", "ai_ml"),
    (r"\bllm\b|\blarge\s*language\s*model", "LLMs", "ai_ml"),
    (r"\bgenai\b|\bgenerative\s*ai\b", "GenAI", "ai_ml"),
    (r"\blangchain\b", "LangChain", "ai_ml"),
    (r"\bvector\s*(?:database|db|store|search|embedding)", "Vector Databases", "ai_ml"),
    (r"\bagent(?:ic|s)?\b", "Agentic AI", "ai_ml"),
    (r"\bmcp\b|\bmodel\s*context\s*protocol", "MCP", "ai_ml"),
    (r"\bmachine\s*learning\b|\bml\b", "Machine Learning", "ai_ml"),
    (r"\bdeep\s*learning\b", "Deep Learning", "ai_ml"),
    (r"\bnlp\b|\bnatural\s*language\b", "NLP", "ai_ml"),
    (r"\bpytorch\b|\btensorflow\b", "PyTorch / TensorFlow", "ai_ml"),
    (r"\bmlops\b|\bml\s*pipeline", "MLOps", "ai_ml"),
    # Data Science
    (r"\bstatistic(?:al|s)\b", "Statistical Analysis", "data_science"),
    (r"\btime[\s-]series\b", "Time-Series Analysis", "data_science"),
    (r"\bforecasting\b|\bpredictive\b", "Forecasting / Predictive", "data_science"),
    (r"\bpandas\b|\bnumpy\b", "Pandas / NumPy", "data_science"),
]


def extract_job_keywords(description: str, title: str = "") -> dict:
    """Extract matched tech keywords from job description, grouped by domain.
    
    Returns:
        {
          "data_eng": ["Databricks", "Apache Spark / PySpark", ...],
          "cloud": ["Azure", "Docker", ...],
          "ai_ml": ["RAG", "LLMs", ...],
          ...
          "all_labels": ["Databricks", "Azure", ...],  # flat list for quick lookups
          "top_5": ["Databricks", "Apache Spark / PySpark", "Azure", "ETL/ELT", "Python"],  # top matched
        }
    """
    combined = f"{title} {description}".lower()
    grouped = {}
    all_labels = []

    for pattern, label, domain in KEYWORD_REGISTRY:
        if re.search(pattern, combined, re.IGNORECASE):
            grouped.setdefault(domain, [])
            if label not in grouped[domain]:
                grouped[domain].append(label)
            if label not in all_labels:
                all_labels.append(label)

    # Top 5: prioritize data_eng > cloud > ai_ml > analytics > programming > orchestration
    priority_order = ["data_eng", "cloud", "ai_ml", "analytics", "orchestration", "programming", "data_science"]
    top_5 = []
    for dom in priority_order:
        for lbl in grouped.get(dom, []):
            if lbl not in top_5 and len(top_5) < 5:
                top_5.append(lbl)

    grouped["all_labels"] = all_labels
    grouped["top_5"] = top_5
    return grouped


INVALID_NAME_WORDS = {
    # German stopwords & ad/marketing words
    "wenn", "sie", "wir", "uns", "ihr", "ihre", "ihren", "ihrem", "ihrer", "ihnen",
    "du", "dir", "dich", "dein", "deine", "deinen", "deinem", "deiner",
    "diese", "dieser", "dieses", "diesem", "diesen",
    "fragen", "bitte", "gerne", "unsere", "unserer", "unser", "unseren",
    "interesse", "kontakt", "ansprechpartner", "ansprechpartnerin", "hinweise", "ueber", "über",
    "fuer", "für", "oder", "und", "mit", "bei", "nach", "von", "vom", "zum", "zur",
    "auf", "aus", "im", "in", "dem", "der", "die", "das", "den", "des", "ein", "eine",
    "einen", "einem", "einer", "eines", "vor", "personalwesen", "karriere",
    "bewerbung", "bewerbungen", "bewerben", "willkommen", "vorteile", "angebot", "profil", "aufgaben",
    "standort", "standorte", "einstieg", "chancen", "zukunft", "perspektiven", "erfolg", "begeisterung",
    "team", "talent", "recruiting", "recruiter", "manager", "lead", "head", "bereich", "abteilung",
    "unternehmens", "unternehmen", "gesellschaft", "holding", "gruppe", "group", "partner",
    # English stopwords & ad/marketing/slogan words
    "sounds", "exciting", "join", "joining", "career", "careers", "hiring", "apply", "applying",
    "ready", "about", "your", "overview", "future", "people", "global", "welcome", "lets", "let's",
    "start", "date", "flexible", "benefits", "what", "culture", "opportunities", "diversity",
    "inclusion", "growth", "challenge", "mission", "values", "work", "life", "integration",
    "balance", "good", "great", "world", "sports", "digital", "technology", "technologies",
    "solutions", "success", "potential", "passion", "fast", "forward", "click", "here",
    "learn", "more", "find", "out", "looking", "getting", "know", "contact", "contacts",
    "position", "role", "connect", "together", "have", "with", "this", "that", "from",
    "into", "their", "there", "then", "will", "shall", "should", "could", "would",
    "must", "need", "want", "like", "meet", "who", "which", "where", "when",
    "introduction", "description", "requirements", "qualifications", "responsibilities"
}

TRAILING_TRIM = [
    r"\s+(?:Startdatum|Eintrittsdatum|Eintritt|Bewerbung|Referenz|Job-ID|Kennziffer).*$",
    r"\s+(?:Personalreferent(?:in)?|Recruiter(?:in)?|Recruiting|Personalmanagement|HR|Talent\s+Acquisition).*$",
    r"\s+(?:People\s*&\s*Culture|Team\s*Lead|Manager|Director|Head\s+of|Consultant|Fachbereich).*$",
    r"\s+(?:Tel|E-Mail|Email|Fax|www|Mail|Telefonnummer|Telefon|Phone).*$"
]


def clean_contact_name(raw: str, company: str = "") -> str:
    s = raw.strip(" ,.:;\n\t*#-_()[]{}")
    for tr in TRAILING_TRIM:
        s = re.sub(tr, "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s).strip(" ,.:;-")
    return s


def is_valid_contact_name(candidate: str, company: str = "") -> bool:
    if not candidate:
        return False
    # Reject strings with punctuation that indicates a phrase, sentence, or URL
    if any(ch in candidate for ch in "?!:;()[]{}*#@$%^+=/\\_\""):
        return False
    clean = clean_contact_name(candidate, company)
    if not clean:
        return False
    if company and company.lower() in clean.lower():
        return False
    comp_words = [w.lower() for w in re.split(r"\W+", company) if len(w) >= 4]
    if any(cw in clean.lower() for cw in comp_words if cw not in ["group", "gmbh", "technologies", "consulting", "holding"]):
        return False
    core = re.sub(r"^(?:Frau|Herr|Herrn|Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+", "", clean, flags=re.IGNORECASE).strip()
    words = core.split()
    if len(words) < 2 or len(words) > 3:
        return False
    for w in words:
        # Proper noun check: Starts with capital, followed by lowercase (optional hyphenated part)
        if not re.match(r"^[A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?$", w):
            return False
        # Stopword / marketing buzzword blacklist check
        if w.lower() in INVALID_NAME_WORDS:
            return False
    return True


def extract_contact_person(desc: str, company: str = "", title: str = "") -> str:
    """Extract individual recruiter / contact person from job description."""
    if not desc:
        return ""
    text = desc.replace("\r", "")
    pats = [
        # 1. High confidence: "<Name> is your recruiting contact / recruiter / contact person"
        r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,2})\s+is\s+(?:your\s+)?(?:recruiting\s+contact|recruiter|contact\s+person|talent\s+acquisition)',
        # 2. High confidence: "<Name> ist dein(e)/Ihr(e) Ansprechpartner(in) / Kontakt"
        r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,2})\s+ist\s+(?:dein[e]?|ihr[e]?)\s+(?:ansprechpartner(?:in)?|kontakt|recruiter)',
        # 3. High confidence: "<Name> freut sich auf deine/Ihre Bewerbung"
        r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,2})\s+freut\s+sich\s+(?:auf\s+deine|auf\s+ihre|auf\s+die\s+zusendung)',
        # 4. Ansprechpartner(in) ... (ist) (Frau/Herr) Name
        r'(?:ihr[e]?\s+)?ansprechpartner(?:in)?(?:\s+für\s+[^:\n\.\,]+)?(?:\s+(?:ist|wäre|lautet))?\s*[:\s]+\s*((?:(?:Frau|Herr|Herrn|Dr\.|Prof\.)\s+){0,2}[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,3})',
        # 5. deine Ansprechpartnerin für diese Position, Frau Jenny Brandemann
        r'ansprechpartner(?:in)?(?:\s+für\s+[^,\n]+)?,\s*((?:(?:Frau|Herr|Herrn|Dr\.|Prof\.)\s+){0,2}[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,3})',
        # 6. Kontakt \n Name \n Email
        r'(?:^|\n)\s*Kontakt\s*[:\n]\s*\n?\s*((?:(?:Frau|Herr|Herrn|Dr\.|Prof\.)\s+){0,2}[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,2})(?:\s*\n\s*(?:Email|E-Mail|Tel|Telefon):)',
        # 7. Dein Kontakt bei Rückfragen: Name
        r'(?:dein\s+)?kontakt(?:\s+bei\s+rückfragen)?\s*[:\s]+\s*\n?\s*((?:(?:Frau|Herr|Herrn|Dr\.|Prof\.)\s+){0,2}[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,2})',
        # 8. Für Fragen steht Dir Name zur
        r'(?:bei\s+fragen|für\s+fragen).*?(?:wenden\s+sie\s+sich\s+an|beantwortet\s+dir\s+gerne|beantwortet\s+ihnen|steht\s+ihnen|steht\s+dir)\s+((?:(?:Frau|Herr|Herrn|Dr\.|Prof\.)\s+){0,2}[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,2})',
        # 9. Recruiter: Name
        r'(?:recruiter|talent\s+acquisition\s+partner|talent\s+acquisition\s+manager|recruiting\s+contact|hiring\s+manager)\s*[:\s]+\s*((?:(?:Frau|Herr|Herrn|Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+){0,2}[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,2})',
        # 10. Contact person: Name
        r'contact\s*(?:person)?\s*[:\s]+\s*((?:(?:Mr\.|Ms\.|Mrs\.|Dr\.)\s+){0,2}[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,2})',
    ]
    for pat in pats:
        for m in re.finditer(pat, text, re.IGNORECASE):
            raw = m.group(1)
            if is_valid_contact_name(raw, company):
                return clean_contact_name(raw, company)
    return ""


def format_salutation(contact_person: str) -> tuple[str, str]:
    """Return (salutation_latex, recipient_address_latex) tailored to contact."""
    if not contact_person:
        return "Dear Hiring Team,", "Hiring Team -- Talent Acquisition\\\\Germany"
    
    cp = contact_person.strip()
    words = cp.split()
    
    if words[0].lower() in ["frau", "ms.", "mrs."]:
        lastname = words[-1]
        salutation = f"Dear Ms. {lastname},"
        recipient = f"{escape_latex(cp)} -- Talent Acquisition\\\\Germany"
    elif words[0].lower() in ["herr", "herrn", "mr."]:
        lastname = words[-1]
        salutation = f"Dear Mr. {lastname},"
        recipient = f"{escape_latex(cp)} -- Talent Acquisition\\\\Germany"
    elif words[0].lower() == "dr.":
        lastname = words[-1]
        salutation = f"Dear Dr. {lastname},"
        recipient = f"{escape_latex(cp)} -- Talent Acquisition\\\\Germany"
    elif len(words) >= 2:
        salutation = f"Dear {escape_latex(cp)},"
        recipient = f"{escape_latex(cp)} -- Talent Acquisition\\\\Germany"
    else:
        salutation = "Dear Hiring Team,"
        recipient = "Hiring Team -- Talent Acquisition\\\\Germany"
        
    return salutation, recipient


CV_TEMPLATE = r"""%% Tailored CV for __COMPANY__ - __CLEAN_ROLE__
%% Candidate: Yashwanth Gotike
%% Compile with: lualatex YashwanthGotike___COMPANY_PASCAL___CV.tex

\documentclass[11pt,a4paper,sans]{moderncv}
\moderncvstyle{banking}
\moderncvcolor{blue}

\renewcommand*{\namefont}{\fontsize{30}{32}\bfseries\upshape}
\colorlet{firstnamecolor}{color1}
\colorlet{lastnamecolor}{color1}
\colorlet{namecolor}{color1}
\renewcommand*{\sectionstyle}[1]{{\sectionfont\color{color1}#1}}

\usepackage[utf8]{inputenc}
\AtEndPreamble{\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,
    urlcolor=blue,
    pdftitle={Yashwanth Gotike - CV (__COMPANY_PASCAL__)},
    pdfauthor={Yashwanth Gotike},
    pdfsubject={__CLEAN_ROLE__},
    pdfkeywords={__PDF_KEYWORDS__},
    pdfpagemode=UseNone,
}}
\usepackage[scale=0.82]{geometry}
\usepackage{import}
\usepackage{needspace}
\usepackage{etoolbox}

% Micro-typography: prevent awkward automatic word breaks (e.g. techni-cal, environ-ments)
% while preserving legitimate compound words (exhyphenpenalty)
\hyphenpenalty=10000
\exhyphenpenalty=50

% Left-aligned, ragged-right text inside itemize to remove stretched word spacing
\AtBeginEnvironment{itemize}{\raggedright\renewcommand{\labelitemi}{\textbullet}}

% ATS Optimization: Clean text labels for contact info instead of font glyph ligatures
\renewcommand*{\addresssymbol}{}
\renewcommand*{\mobilephonesymbol}{Phone:~}
\renewcommand*{\emailsymbol}{Email:~}

% Personal data
\name{Yashwanth}{Gotike}
\address{Koblenz, Germany \,|\, __HEADER_TITLE__}{}{}
\phone[mobile]{(+49)~17674755646}
\email{gycrgotike@gmail.com}
\extrainfo{\href{https://linkedin.com/in/ycrgotike}{LinkedIn: in/ycrgotike} \,|\, \href{https://github.com/ycrgotike}{GitHub: ycrgotike}}

\begin{document}

\makecvtitle
\vspace{-12pt}

% ============================================================
%     PROFILE STATEMENT
% ============================================================
\newcount\summarylines
{\raggedright\small __PROFILE__\par\global\summarylines=\prevgraf}
\typeout{CV-SUMMARY-LINES: \the\summarylines}
\ifnum\summarylines<4 \PackageError{application}{CV summary must have exactly 4 rendered lines}{Revise the summary content and recompile.}\fi
\ifnum\summarylines>4 \PackageError{application}{CV summary must have exactly 4 rendered lines}{Revise the summary content and recompile.}\fi

% ============================================================
%     TECHNICAL SKILLS
% ============================================================
\section{Technical Skills}
\vspace{1pt}
\begin{itemize}
__SKILLS_B1__
__SKILLS_B2__
__SKILLS_B3__
__SKILLS_B4__
__SKILLS_B5__
\end{itemize}

% ============================================================
%     PROFESSIONAL EXPERIENCE
% ============================================================
\section{Professional Experience}
\vspace{2pt}

\cventry{09/2022--09/2024}{Data Analyst}{SolTech InfoLabs Pvt Ltd}{Hyderabad, India}{}{\vspace{1pt}
\begin{itemize}
__SOLTECH_BULLETS__
\end{itemize}}

\vspace{3pt}

\cventry{04/2019--09/2022}{Data Engineer}{G.S.R Educational Institutions}{Koilkuntla, India}{}{\vspace{1pt}
\begin{itemize}
__GSR_BULLETS__
\end{itemize}}

\vspace{3pt}

\needspace{5\baselineskip}
\cventry{08/2018--04/2019}{Associate IT Consultant}{ITC Infotech Ltd}{Bengaluru, India}{}{\vspace{1pt}
\begin{itemize}
    \item {Engineered enterprise cloud applications using OutSystems and .NET, integrating RESTful APIs to modernize legacy infrastructure and automate departmental request routing.}
    \item {Delivered 40\% faster system response times and maintained zero unplanned downtime post-deployment across mission-critical inspection operations.}
\end{itemize}}

% ============================================================
%     KEY TECHNICAL PROJECTS
% ============================================================
\newpage
\section{Key Technical Projects}
\vspace{1pt}
__PROJECT_BULLETS__

% ============================================================
%     EDUCATION
% ============================================================
\needspace{5\baselineskip}
\section{Education}
\vspace{1pt}

\cventry{10/2024--Present}{Master of Science (M.Sc.) -- Web and Data Science}{University of Koblenz}{Koblenz, Germany}{}{\vspace{1pt}
__KOBLENZ_COURSEWORK__
}

\vspace{2pt}

\cventry{07/2014--05/2018}{Bachelor of Technology (B.Tech.) -- Computer Engineering}{Sardar Vallabhbhai National Institute of Technology}{Surat, India}{}{\vspace{1pt}
Coursework: Artificial Intelligence, Data Structures and Algorithms, Database Management Systems.
}

% ============================================================
%     LANGUAGES & HONORS
% ============================================================
\section{Languages \& Honors}
\vspace{1pt}
\begin{itemize}
\item \textbf{Languages}: English (Fluent / C1), German (Intermediate / B2).
\item \textbf{Honors \& Awards}: Chairman's Award for Process Improvements -- ITC Infotech Ltd.
\end{itemize}

\end{document}
"""


COVER_TEMPLATE = r"""%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Cover Letter - __COMPANY__, __CLEAN_ROLE__
%% Candidate: Yashwanth Gotike
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\documentclass[]{cover}
\geometry{hmargin=2.0cm, top=1.6cm, bottom=1.6cm}
\usepackage{fancyhdr}

% Micro-typography: prevent awkward automatic word breaks (e.g. techni-cal, environ-ments)
% while preserving legitimate compound words (exhyphenpenalty)
\hyphenpenalty=10000
\exhyphenpenalty=50

\hypersetup{
    pdftitle={Yashwanth Gotike - Cover Letter (__COMPANY_PASCAL__)},
    pdfauthor={Yashwanth Gotike},
    pdfsubject={Cover Letter - __CLEAN_ROLE__},
    pdfkeywords={__COMPANY__, __CLEAN_ROLE__, Yashwanth Gotike, Python, SQL, Data Engineering, Germany},
}

\pagestyle{fancy}
\fancyhf{}
\rfoot{Page \thepage \hspace{0pt}}
\thispagestyle{empty}
\renewcommand{\headrulewidth}{0pt}

% Shared Latin Modern Sans typography across the document pair.
\setmainfont[BoldFont=lmsans10-bold.otf,ItalicFont=lmsans10-oblique.otf]{lmsans10-regular.otf}
\setsansfont[BoldFont=lmsans10-bold.otf,ItalicFont=lmsans10-oblique.otf]{lmsans10-regular.otf}
\newfontfamily\applicationfont[BoldFont=lmsans10-bold.otf,ItalicFont=lmsans10-oblique.otf]{lmsans10-regular.otf}
\definecolor{applicationblue}{rgb}{0.22,0.45,0.70}
\renewcommand{\namesection}[3]{{\raggedright\applicationfont\fontsize{19pt}{23pt}\selectfont\bfseries\color{applicationblue}#2\par}\vspace{4pt}{\raggedright\applicationfont\fontsize{9.5pt}{12pt}\selectfont #3\par}\vspace{5pt}{\color{applicationblue}\hrule height 0.4pt}\vspace{12pt}}
\renewcommand{\companyname}[1]{{\raggedright\applicationfont\bfseries #1\par}}
\renewcommand{\companyaddress}[1]{{\raggedright\applicationfont#1\par}\vspace{3pt}}
\renewcommand{\currentdate}[1]{{\raggedleft\applicationfont#1\par}\vspace{7pt}}
\renewcommand{\lettercontent}[1]{{\leftskip=0pt\rightskip=0pt\parfillskip=0pt plus 1fil\parindent=0pt\applicationfont\fontsize{11pt}{14pt}\selectfont #1\par}\vspace{9pt}}
\renewcommand{\closing}[1]{{\raggedright\applicationfont#1\par}\vspace{9pt}}
\renewcommand{\signature}[1]{{\raggedright\applicationfont#1\par}}

\begin{document}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%     TITLE NAME
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\namesection{}{Yashwanth Gotike}{{\fontsize{9.5pt}{12pt}\selectfont Koblenz, Germany \,|\, Phone: (+49)~17674755646 \,|\, Email: \href{mailto:gycrgotike@gmail.com}{gycrgotike@gmail.com} \,|\, \href{https://linkedin.com/in/ycrgotike}{LinkedIn: in/ycrgotike}}}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%     MAIN COVER LETTER CONTENT
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\companyname{__COMPANY__}
\companyaddress{__RECIPIENT_ADDRESS__}

\currentdate{\today}
\lettercontent{\textbf{Re: __SUBJECT__}}
\lettercontent{__SALUTATION__}

\lettercontent{__OPENING__}

__BODY__

__INTEREST__

\lettercontent{I hold full work authorization in Germany with no visa sponsorship required and communicate fluently in English (C1) with an intermediate proficiency in German (B2). __AVAILABILITY__}

\lettercontent{I would welcome the opportunity to discuss how my technical background can support __COMPANY__'s initiatives. Thank you for your consideration.}

\begin{flushright}
\closing{Sincerely,}

\signature{Yashwanth Gotike}
\end{flushright}
\end{document}
"""


def is_student_role(role_title: str, description: str = "") -> bool:
    """Accurately identify student/intern positions using word boundaries, avoiding false matches on 'internal', 'international', etc."""
    if not role_title:
        return False
    # Senior / lead / principal / staff / director / head of roles are strictly professional full-time roles
    if re.search(r'\b(?:senior|lead|principal|staff|director|head\s+of)\b', role_title, re.I):
        return False
    student_pat = r'\b(?:werkstudent\w*|working\s*student|praktik\w*|intern|internship|interns|duales?\s*studium|thesis|masterarbeit|bachelorarbeit|abschlussarbeit|studentische\s*hilfskraft|hiwi)\b'
    return bool(re.search(student_pat, role_title, re.I))


def is_senior_role(role_title: str, description: str = "") -> bool:
    """Accurately identify senior, lead, principal, or staff full-time roles."""
    if not role_title:
        return False
    if re.search(r'\b(?:senior|lead|principal|staff|director|head\s+of|expert|specialist)\b', role_title, re.I):
        return True
    if description and re.search(r'\b(?:5\+|\b5\s*(?:-\s*\d+)?\s*years?|five\s*years?)\b.*?(?:experience|erfahrung)', description, re.I):
        return True
    return False


def determine_header_title(role_title: str, description: str = "") -> str:
    """Determine dynamic, clean professional headline beside 'Koblenz, Germany' in ModernCV.
    
    Rules:
    1. NEVER include seniority ('Senior', 'Junior', 'Lead', 'Principal', 'Associate', 'Staff', 'Sr.', 'Jr.').
    2. NEVER include student/intern words ('Werkstudent', 'Working Student', 'Praktikant', 'Intern', 'Praktikum', etc.).
    3. If the role mentions both 'AI' and 'Data' (e.g. 'Werkstudent AI & Data'), dynamically evaluate the
       job description to determine whether it leans towards 'AI Engineer', 'Data Engineer', or 'Data Analyst'.
    4. Otherwise, map cleanly to the target discipline:
       - AI/ML/GenAI -> 'AI Engineer'
       - Data Analytics/BI -> 'Data Analyst'
       - Data Engineering/Lakehouse/Pipelines -> 'Data Engineer'
    """
    t_low = role_title.lower()
    d_low = description.lower() if description else ""

    # Check for AI & Data hybrid roles (e.g. "AI & Data", "Data & AI", "KI & Daten")
    is_ai_and_data = bool(
        re.search(r"\b(ai|ki)\b.*?(&|and|und|\+|/|\bmit\b).*?\b(data|daten)\b", t_low)
        or re.search(r"\b(data|daten)\b.*?(&|and|und|\+|/|\bmit\b).*?\b(ai|ki)\b", t_low)
    )

    if is_ai_and_data and d_low:
        ai_terms = [
            r"\b(llm|llms|large language model|large language models)\b",
            r"\b(rag|retrieval-augmented generation)\b",
            r"\b(agent|agents|ki-agent|ki-agenten)\b",
            r"\b(chatbot|chatbots)\b",
            r"\b(genai|generative ai)\b",
            r"\b(machine learning|deep learning|ml|nlp)\b",
            r"\b(pytorch|tensorflow|scikit-learn|langchain|prompt)\b",
        ]
        de_terms = [
            r"\b(data engineer|data engineering)\b",
            r"\b(data pipeline|data pipelines|etl|elt)\b",
            r"\b(lakehouse|delta lake|databricks|spark|pyspark|airflow|kafka|dbt)\b",
            r"\b(data warehouse|warehousing|data platform)\b",
        ]
        da_terms = [
            r"\b(data analyst|data analytics)\b",
            r"\b(power bi|dax|tableau|looker|dashboard|dashboards)\b",
            r"\b(business intelligence|\bbi\b|kpi|kpis|reporting|insights)\b",
        ]

        ai_score = sum(len(re.findall(pat, d_low)) for pat in ai_terms)
        de_score = sum(len(re.findall(pat, d_low)) for pat in de_terms)
        da_score = sum(len(re.findall(pat, d_low)) for pat in da_terms)

        if ai_score >= de_score and ai_score >= da_score and ai_score > 0:
            return "AI Engineer"
        elif de_score >= da_score and de_score > 0:
            return "Data Engineer"
        elif da_score > 0:
            return "Data Analyst"

    # Machine Learning focus
    if any(k in t_low for k in ["machine learning", "deep learning", "ml engineer", "ml-engineer", "machine-learning"]):
        return "Machine Learning Engineer"

    # AI / Generative AI focus
    if any(k in t_low for k in ["ki-unterst", "ki-gestütz", "genai", "llm", "rag", "artificial intelligence", "künstliche intelligenz"]) or \
       (re.search(r"\b(ai|ki)\b", t_low) and not any(k in t_low for k in ["data", "daten", "analytics", "analyst"])):
        return "AI Engineer"

    # Data Analyst / Analytics focus
    if any(k in t_low for k in ["analyst", "analytics", "business intelligence", "product stewardship", "stewardship"]) or re.search(r"\bbi\b", t_low):
        if any(k in t_low for k in ["platform", "plattform", "pipeline", "engineer"]) and d_low:
            de_hits = len(re.findall(r"\b(pipeline|etl|elt|spark|databricks|lakehouse|warehouse)\b", d_low))
            da_hits = len(re.findall(r"\b(power bi|tableau|dashboard|reporting|kpi|insights|analysis)\b", d_low))
            if de_hits > da_hits:
                return "Data Engineer"
            return "Data Analyst"
        return "Data Analyst"

    # Data Engineer / Lakehouse / Pipelines focus
    if any(k in t_low for k in ["engineer", "engineering", "databricks", "spark", "lakehouse", "pipeline", "plattform", "platform", "etl"]):
        return "Data Engineer"

    # If title mentions AI/KI in combination
    if re.search(r"\b(ai|ki)\b", t_low):
        return "AI Engineer"

    # Description-based fallback
    if d_low:
        ai_count = len(re.findall(r"\b(ai|ki|ml|llm|rag|agent|agents|model)\b", d_low))
        de_count = len(re.findall(r"\b(pipeline|etl|elt|spark|databricks|lakehouse|warehouse)\b", d_low))
        da_count = len(re.findall(r"\b(dashboard|reporting|analyst|analytics|power bi|tableau)\b", d_low))
        if ai_count > de_count and ai_count > da_count:
            return "AI Engineer"
        if da_count > de_count:
            return "Data Analyst"

    return "Data Engineer"


PROFILE_FILE = ROOT / '.claude/skills/job-application-assistant/01-candidate-profile.md'
GENERATOR_VERSION = '2.9.2'


def profile_text():
    return PROFILE_FILE.read_text(encoding='utf-8')


def section_bullets(heading):
    """Read achievements directly from the canonical record, never from a posting."""
    text = profile_text()
    match = re.search(r'^### ' + re.escape(heading) + r'[^\n]*\n(.*?)(?=^##|\Z)', text, re.M | re.S)
    if not match:
        raise ValueError(f'Missing canonical evidence: {heading}')
    return [line[2:].strip() for line in match[1].splitlines()
            if line.startswith('- ') and not line.startswith('- *Tech Stack:')]


def role_family(title, description):
    t_low = title.lower()
    text = f'{title} {description}'.lower()
    # Match operational responsibilities before student status or broad AI terms.
    if re.search(r'platform operations|data\s*center|datacenter|infrastructure as code|\biac\b|site reliability|devops|plattformservices|\bcloud infrastruktur\b', text) and not re.search(r'data engineer|data analyst', t_low):
        return 'platform'
    if re.search(r'analyst|analytics|business intelligence|power bi|dashboard|reporting', t_low):
        return 'analytics'
    if re.search(r'llm|machine learning|genai|artificial intelligence|\bai\b|mlops', t_low):
        return 'ai'
    if re.search(r'data engineer|data engineering|databricks|lakehouse|etl|elt|pipeline', t_low):
        return 'data'
    if re.search(r'platform operations|data\s*center|datacenter|site reliability|devops', text):
        return 'platform'
    if re.search(r'power bi|dashboard|cohort|a/b test', text):
        return 'analytics'
    if re.search(r'\bllms?\b|rag|genai|machine learning', text):
        return 'ai'
    return 'data'


def skill_groups(family, description):
    # Only positive skill statements: exclude caveats listing unconfirmed tools.
    text = profile_text().split('## Technical Skills', 1)[1].split('## Awards', 1)[0]
    from tools.technology_evidence import positive_evidence, review_technologies
    positives = '\n'.join(positive_evidence(profile_text()))
    groups = {
        'cloud': ('Cloud & Automation', ['Terraform', 'Kubernetes', 'Docker', 'CI/CD', 'GitHub Actions', 'Azure', 'AWS', 'GCP', 'Git', 'cloud deployment']),
        'operations': ('Systems & Operations', ['Windows/Linux administration', 'monitoring', 'security']),
        'data': ('Programming & Data Engineering', ['Python', 'SQL', 'Azure Data Factory', 'Databricks', 'Apache Spark', 'Airflow', 'ETL/ELT']),
        'ai': ('AI & Deployment', ['LangChain', 'LlamaIndex', 'LLM deployment', 'LLMs', 'RAG', 'Vector Databases', 'MLflow', 'DVC', 'Flask', 'FastAPI', 'PyTorch', 'TensorFlow']),
        'analytics': ('Analytics & Reporting', ['Power BI', 'DAX', 'Tableau', 'A/B Testing', 'Cohort Analysis', 'Statistical Analysis']),
    }
    order = {'platform': ['cloud', 'operations', 'ai', 'data', 'analytics'],
             'analytics': ['analytics', 'data', 'cloud', 'ai', 'operations'],
             'ai': ['ai', 'cloud', 'data', 'analytics', 'operations'],
             'data': ['data', 'cloud', 'ai', 'analytics', 'operations']}[family]
    # Relevant confirmed tools outside the old fixed lists must not disappear.
    listed = {term.casefold() for _, terms in groups.values() for term in terms}
    extra = [r['technology'] for r in review_technologies(description, profile_text())['technologies']
             if r['status'] == 'confirmed' and r['technology'].casefold() not in listed]
    ai_tools = {'LangGraph','Google ADK','MCP','Vertex AI','Gemini','OpenAI','Anthropic','Llama','Mistral'}
    groups['ai'][1].extend(t for t in extra if t in ai_tools)
    groups['data'][1].extend(t for t in extra if t not in ai_tools)
    result = []
    for key in order:
        label, terms = groups[key]
        supported = [t for t in terms if re.search(r'(?<!\w)' + re.escape(t) + r'(?!\w)', positives, re.I)]
        supported.sort(key=lambda term: term.lower() not in description.lower())
        if supported:
            result.append(r'\item \textbf{' + escape_latex(label) + '}: ' + escape_latex(', '.join(supported)) + '.')
    return result


def reorder_evidence(lines, family, description):
    from tools.responsibility_plan import analyze_posting, EVIDENCE
    duties = analyze_posting('', description)['responsibilities']
    priorities = [term.lower() for d in duties for term in EVIDENCE[d['kind']][2]]
    if family == 'ai':
        priorities.extend(['ci/cd', 'rest api', 'python', 'automated'])
    return sorted(lines, key=lambda line: -sum(term in line.lower() for term in priorities))


def build_tailored_cv(company, company_pascal, role_title, description, is_student, is_data_eng, is_analytics, is_ai_ml):
    from tools.responsibility_plan import analyze_posting
    plan = analyze_posting(role_title, description)
    if not plan['responsibilities']:
        raise ValueError('No supported responsibility match; manual tailoring is required.')
    primary = plan['responsibilities'][0]
    family = primary['family']
    groups = skill_groups(family, description)
    is_student = is_student_role(role_title, description)
    is_senior = is_senior_role(role_title, description)
    header_discipline = determine_header_title(role_title, description)
    if is_student:
        lead = "M.Sc. Web and Data Science student at University of Koblenz (expected graduation September 2027), with data engineering and analytics experience."
    elif is_senior:
        lead = f"{header_discipline} with 5+ years of professional experience across data engineering, scalable software architectures, and analytics pipelines."
    else:
        lead = "Data professional with a background in data engineering, analytics and software consultancy, connecting technical delivery with reporting needs across different teams."
    focus = {'analytics': 'My background includes Python, SQL and Power BI reporting.',
             'data': 'My background includes Python, SQL, data integration and application workflows.',
             'platform': 'My background includes cloud data workflows and CI/CD with GitHub Actions.',
             'ai': 'My projects include machine learning, LLM applications and reproducible deployment.'}[family]
    contribution = f"I can support {company} with {primary['responsibility']}."

    qualities = {
        'analytics': 'Combines analytical problem-solving with careful data preparation and clear reporting to support well-informed operational decisions.',
        'data': 'Brings a structured approach to source integration, data validation and dependable workflows that colleagues can maintain.',
        'platform': 'Combines systematic problem-solving with repeatable deployment practices, automation and attention to reliable technical delivery.',
        'ai': 'Combines analytical problem-solving, careful evaluation and structured workflow automation.'
    }[family]
    if primary['kind'] in ('agents', 'ai_evaluation', 'model_serving', 'ai_safety'):
        lead = (lead if is_student else 'Data and software professional with project experience in LLM applications, retrieval workflows and model deployment.')
        focus = 'Combines Python, RAG, FastAPI and CI/CD with structured analysis and careful validation.'
        qualities = 'My projects connect agent workflows with APIs and reproducible deployment.'
        contribution = f"I would apply this background to {company}'s AI features, evaluation and reliable product integration."
    if primary['kind'] in ('qa', 'test_automation'):
        focus = 'Experience includes Python, SQL, application integration and CI/CD with GitHub Actions.'
        qualities = 'Brings structured analysis and careful validation to learning software testing workflows.'
        # Transferable experience is not labelled as professional QA expertise.
        contribution = f"I would apply this background to {company}'s test cases, defect documentation and automation."
        groups = [line for line in groups if not any(label in line for label in ('AI \\& Deployment', 'Analytics \\& Reporting'))]
    summary = f"{lead} {focus} {qualities} {contribution}"
    code = CV_TEMPLATE
    substitutions = {'__COMPANY__': escape_latex(company), '__COMPANY_PASCAL__': escape_latex(company_pascal),
        '__CLEAN_ROLE__': escape_latex(clean_title(role_title)), '__HEADER_TITLE__': escape_latex(determine_header_title(role_title, description)),
        '__PDF_KEYWORDS__': escape_latex(clean_title(role_title) + ', ' + company + ', Python, SQL'), '__PROFILE__': escape_latex(summary)}

    for i in range(5):
        substitutions[f'__SKILLS_B{i+1}__'] = groups[i] if i < len(groups) else ''
    for token, heading in [('__SOLTECH_BULLETS__','Data Analyst - SolTech'),('__GSR_BULLETS__','Data Engineer - G.S.R')]:
        lines = reorder_evidence(section_bullets(heading), family, description)
        substitutions[token] = '\n'.join(r'\item ' + escape_latex(line) for line in lines)
    projects = {
        'upsc': ('MVP UPSC', 'MVP UPSC (LLM Applications & RAG)'),
        'mlops': ('Kidney Disease Classification', 'Kidney Disease Classification (MLOps)'),
        'twitter': ('Real-Time Twitter', 'Real-Time Twitter Data Pipeline'),
        'sql': ('SQL Data Warehouse', 'SQL Data Warehouse & Analytics'),
        'trading': ('Algo Trading', 'Algo Trading Platform'),
    }
    order = {'platform': ['upsc','mlops','twitter','sql'], 'ai': ['upsc','mlops','twitter','trading'],
             'analytics': ['sql','trading','twitter','upsc'], 'data': ['twitter','sql','mlops','upsc']}[family]
    from tools.responsibility_plan import EVIDENCE
    relevant_sources = [EVIDENCE[d['kind']][1] for d in plan['responsibilities']]
    order.sort(key=lambda key: relevant_sources.index(projects[key][0]) if projects[key][0] in relevant_sources else len(relevant_sources))
    blocks = []
    for key in order:
        heading, label = projects[key]
        lines = reorder_evidence(section_bullets(heading), family, description)[:2]
        blocks.append(r'\needspace{5\baselineskip}\noindent\textbf{' + escape_latex(label) + '}\n' +
            r'\begin{itemize}' + '\n' + '\n'.join(r'\item ' + escape_latex(line) for line in lines) + '\n' + r'\end{itemize}')
    substitutions['__PROJECT_BULLETS__'] = '\n'.join(blocks)
    has_dg = bool(re.search(r'\b(data\s*governance|daten-?governance|data\s*lineage|metadata\s*management|data\s*profiling|data\s*catalog|datenqualitätsmanagement|governance\s*frameworks?)\b', description, re.I))
    substitutions['__KOBLENZ_COURSEWORK__'] = r'\raggedright Coursework: Data Science, Big Data, Machine Learning and Data Mining.'
    if has_dg and 'Data Governance Quality Assurance' in profile_text():
        substitutions['__KOBLENZ_COURSEWORK__'] += r' \,|\, Seminar: Data Governance Quality Assurance.'
    for token,value in substitutions.items():
        code = code.replace(token,value)
    return code


def start_date(application_date=None):
    import calendar
    current = application_date or date.today()
    if '1 month from date of application' not in profile_text():
        return None
    year = current.year + (current.month == 12)
    month = current.month % 12 + 1
    return date(year,month,min(current.day,calendar.monthrange(year,month)[1]))


def availability_text(role_title, application_date=None, description=""):
    start = start_date(application_date)
    text = f'I am available to start on {start.strftime("%d %B %Y").lstrip("0")}.' if start else ''
    if re.search(r'werkstudent|working student', role_title, re.I):
        if 'Up to 20 hours/week during semester' in profile_text():
            cap = re.search(r'(?:up to|max(?:imum)?|bis zu)\s*(\d{1,2})\s*(?:hours|h|stunden)\s*(?:per week|/week|/woche|pro woche)?', description, re.I)
            if cap and 0 < int(cap.group(1)) <= 20:
                text += f' I can work up to {int(cap.group(1))} hours per week, within the weekly limit stated in your posting.'
            else:
                text += ' I can work up to 20 hours per week during the semester and up to 40 during semester breaks.'
    # Internship duration and presence days are not inferred from working-student hours.
    return text


def requisition_id(description):
    match = re.search(r'(?:job[\s-]*(?:id|number)|requisition[\s-]*(?:id|number)|referenznummer|stellennummer|stellen[ -]?id)\s*[:#-]?\s*([A-Za-z0-9][A-Za-z0-9-]*)', description, re.I)
    return match[1] if match else ''


GERMAN_CITY_MAP = {
    'Aachen': 'Aachen', 'Aachener': 'Aachen', 'Augsburg': 'Augsburg', 'Berlin': 'Berlin', 'Berliner': 'Berlin',
    'Bielefeld': 'Bielefeld', 'Bochum': 'Bochum', 'Bonn': 'Bonn', 'Bonner': 'Bonn', 'Bremen': 'Bremen', 'Bremer': 'Bremen',
    'Burgwedel': 'Burgwedel', 'Cologne': 'Cologne', 'Köln': 'Köln', 'Koeln': 'Köln', 'Kölner': 'Köln',
    'Darmstadt': 'Darmstadt', 'Dortmund': 'Dortmund', 'Dortmunder': 'Dortmund', 'Dresden': 'Dresden', 'Dresdner': 'Dresden',
    'Duisburg': 'Duisburg', 'Düsseldorf': 'Düsseldorf', 'Duesseldorf': 'Düsseldorf', 'Düsseldorfer': 'Düsseldorf',
    'Erlangen': 'Erlangen', 'Essen': 'Essen', 'Essener': 'Essen', 'Frankfurt': 'Frankfurt', 'Frankfurter': 'Frankfurt',
    'Freiburg': 'Freiburg', 'Göttingen': 'Göttingen', 'Goettingen': 'Göttingen', 'Gütersloh': 'Gütersloh',
    'Hamburg': 'Hamburg', 'Hamburger': 'Hamburg', 'Hannover': 'Hannover', 'Hanover': 'Hanover',
    'Heidelberg': 'Heidelberg', 'Herzogenaurach': 'Herzogenaurach', 'Ingolstadt': 'Ingolstadt',
    'Jena': 'Jena', 'Karlsruhe': 'Karlsruhe', 'Kassel': 'Kassel',
    'Koblenz': 'Koblenz', 'Leipzig': 'Leipzig', 'Leipziger': 'Leipzig', 'Leverkusen': 'Leverkusen',
    'Ludwigshafen': 'Ludwigshafen', 'Mainz': 'Mainz', 'Mannheim': 'Mannheim',
    'München': 'München', 'Muenchen': 'München', 'Munich': 'Munich', 'Münchner': 'München',
    'Münster': 'Münster', 'Muenster': 'Münster', 'Nürnberg': 'Nürnberg', 'Nürnberger': 'Nürnberg',
    'Nuernberg': 'Nürnberg', 'Nuremberg': 'Nuremberg', 'Paderborn': 'Paderborn',
    'Potsdam': 'Potsdam', 'Regensburg': 'Regensburg', 'Rostock': 'Rostock',
    'Saarbrücken': 'Saarbrücken', 'Stuttgart': 'Stuttgart', 'Stuttgarter': 'Stuttgart', 'Ulm': 'Ulm',
    'Walldorf': 'Walldorf', 'Wiesbaden': 'Wiesbaden', 'Wolfsburg': 'Wolfsburg',
    'Wuppertal': 'Wuppertal', 'Würzburg': 'Würzburg',
    'Bad Friedrichshall': 'Bad Friedrichshall', 'Ehingen': 'Ehingen (Donau)',
    'Eschborn': 'Eschborn', 'Ludwigsfelde': 'Ludwigsfelde', 'Leinfelden-Echterdingen': 'Stuttgart',
    'Bissingen': 'Bissingen', 'Salzgitter': 'Salzgitter',
    'Sindelfingen': 'Sindelfingen', 'Böblingen': 'Böblingen', 'Boeblingen': 'Böblingen',
    'Neckarsulm': 'Neckarsulm', 'Heilbronn': 'Heilbronn', 'Garching': 'Garching',
    'Unterföhring': 'Unterföhring', 'Unterfoehring': 'Unterföhring',
    'Eschweiler': 'Eschweiler', 'Troisdorf': 'Troisdorf', 'Ratingen': 'Ratingen',
    'Hürth': 'Hürth', 'Huerth': 'Hürth'
}

INVALID_CITIES = {
    # Tech / domain buzzwords
    'intelligence', 'ai', 'ki', 'data', 'analytics', 'services', 'service', 'based',
    'reliability', 'engineering', 'engineer', 'operations', 'operation',
    'platform', 'security', 'privacy', 'tracking', 'systems', 'system',
    'technology', 'technologies', 'solutions', 'solution', 'consulting',
    'advisory', 'business', 'development', 'developer', 'architecture',
    'infrastructure', 'cloud', 'digital', 'product', 'management', 'manager',
    'lead', 'head', 'team', 'partner', 'partnering', 'network', 'software',
    'hardware', 'science', 'scientist', 'research', 'researcher', 'specialist',
    # Work arrangement / descriptors
    'germany', 'deutschland', 'remote', 'hybrid', 'bundesweit', 'on-site', 'onsite',
    'vorort', 'vor-ort', 'office', 'offices', 'homeoffice', 'home-office',
    'flexible', 'flexibel', 'flexible-working', 'worldwide', 'weltweit',
    'global', 'international', 'europaweit', 'europe', 'deutschlandweit',
    'übergreifend', 'unabhängig', 'aktuell', 'standortunabhängig', 'standortübergreifend',
    # Roles and employment terms
    'student', 'werkstudent', 'working', 'praktikant', 'intern', 'internship',
    'trainee', 'graduate', 'junior', 'senior', 'associate', 'consultant',
    'analyst', 'director', 'vice', 'president', 'officer', 'lead', 'expert',
    # General non-city nouns
    'requirements', 'qualifications', 'tasks', 'aufgaben', 'benefits', 'vorteile',
    'campus', 'village', 'hub', 'center', 'centre', 'park', 'group', 'holding',
    'gmbh', 'ag', 'se', 'kg', 'inc', 'corp', 'ltd', 'und', 'and', 'oder', 'or',
    'details', 'information', 'kontakt', 'contact', 'bewerbung', 'application',
    'standortleitung', 'standortauswahl', 'standortvorteile', 'arbeitsplatz',
    'standort', 'arbeitsort', 'location', 'site', 'werk', 'plant',
}


def extract_company_location(job_or_desc, description='', company='') -> str:
    """Extract and format verified employer city/location as '[City], Germany'."""
    raw = ''
    desc = ''
    title = ''
    url = ''
    comp = company or ''
    if isinstance(job_or_desc, dict):
        raw = job_or_desc.get('location') or ''
        desc = job_or_desc.get('description') or description or ''
        title = job_or_desc.get('title') or ''
        url = job_or_desc.get('url') or ''
        comp = job_or_desc.get('company') or company or ''
    else:
        if description:
            raw = job_or_desc or ''
            desc = description
        elif isinstance(job_or_desc, str):
            words = job_or_desc.strip().split()
            if len(words) <= 4 and '\n' not in job_or_desc and not any(w.lower() in ['is', 'are', 'we', 'for', 'with', 'hiring', 'building', 'leading', 'located', 'our'] for w in words):
                raw = job_or_desc
                desc = job_or_desc
            else:
                raw = ''
                desc = job_or_desc or description or ''
        else:
            raw = ''
            desc = job_or_desc or description or ''

    # 1. Check explicit location field
    if raw:
        for k in sorted(GERMAN_CITY_MAP.keys(), key=len, reverse=True):
            if re.search(r'\b' + re.escape(k) + r'\b', raw, re.I):
                return f'{GERMAN_CITY_MAP[k]}, Germany'
        parts = [p.strip() for p in raw.split(',') if p.strip()]
        if parts:
            first = parts[0]
            if first.lower() not in INVALID_CITIES:
                clean_city = re.sub(r'^\d{4,5}\s+', '', first).strip()
                if clean_city and len(clean_city.split()) <= 3 and len(clean_city) <= 35 and clean_city.lower() not in INVALID_CITIES:
                    if not any(w in clean_city.lower() for w in ['is', 'are', 'we', 'the', 'for', 'and', 'with', 'in', 'at', 'to', 'consultancy', 'leading']):
                        return f'{GERMAN_CITY_MAP.get(clean_city, clean_city)}, Germany'

    # 2. Check portal URL path (very high precision: portals like StepStone, XING, LinkedIn embed city slug)
    if url:
        for k in sorted(GERMAN_CITY_MAP.keys(), key=len, reverse=True):
            if re.search(r'[-_/]' + re.escape(k).lower() + r'[-_/]', url.lower()):
                return f'{GERMAN_CITY_MAP[k]}, Germany'

    # 3. Check title
    if title:
        for k in sorted(GERMAN_CITY_MAP.keys(), key=len, reverse=True):
            if re.search(r'\b' + re.escape(k) + r'\b', title, re.I):
                return f'{GERMAN_CITY_MAP[k]}, Germany'

    # 4. Check known company names / corporate signatures
    if 'hamburg' in comp.lower():
        return 'Hamburg, Germany'
    if 'netcologne' in comp.lower():
        return 'Köln, Germany'
    if 'berlin-brandenburg' in comp.lower():
        return 'Berlin, Germany'
    if 'flaschenpost' in comp.lower():
        return 'Münster, Germany'

    # 5. Check postal code pattern (e.g. 71063 Sindelfingen)
    m_plz = re.search(r'\b\d{5}\s+((?:(?:Bad|Sankt|St\.)\s+)?[A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?)\b', desc)
    if m_plz:
        city = m_plz.group(1).strip()
        if city.lower() not in INVALID_CITIES:
            return f'{GERMAN_CITY_MAP.get(city, city)}, Germany'

    # 6. Check explicit location headers in description (e.g. Location: Cologne, Standort: Berlin, Office in Munich)
    m_header = re.search(r'(?i:\b(?:location|standort|arbeitsort|sitz|office|hub)\s*(?:[:–—\-]|in\b)\s*)((?:(?:Bad|Sankt|St\.)\s+)?[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)\b', desc)
    if m_header:
        val = m_header.group(1).strip()
        for k in sorted(GERMAN_CITY_MAP.keys(), key=len, reverse=True):
            if re.search(r'\b' + re.escape(k) + r'\b', val, re.I):
                return f'{GERMAN_CITY_MAP[k]}, Germany'
        if val.lower() not in INVALID_CITIES:
            return f'{GERMAN_CITY_MAP.get(val, val)}, Germany'

    # 7. Check plant/werk/standort compounds (e.g. Plant Sindelfingen, Werk Neckarsulm)
    # Exclude bare "location" or "site" which match technical buzzwords like "Location Intelligence" or "Site Reliability"
    m_plant = re.search(r'(?i:\b(?:plant|werk|standort)\s+)((?:(?:Bad|Sankt|St\.)\s+)?[A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?)\b', desc)
    if m_plant:
        city = m_plant.group(1).strip()
        if city.lower() not in INVALID_CITIES:
            if city in GERMAN_CITY_MAP or any(city.endswith(sfx) for sfx in ['stadt', 'burg', 'berg', 'heim', 'dorf', 'ingen', 'bad']):
                return f'{GERMAN_CITY_MAP.get(city, city)}, Germany'

    # 8. Fallback scan across description for recognized cities
    # Sort by length descending so multi-word cities match first
    for k in sorted(GERMAN_CITY_MAP.keys(), key=len, reverse=True):
        if re.search(r'\b' + re.escape(k) + r'\b', desc, re.I):
            return f'{GERMAN_CITY_MAP[k]}, Germany'

    return 'Germany'



def responsibility_approach(plan):
    """Proposed work, grounded in extracted duties, never invented experience."""
    primary = plan['responsibilities'][0]['kind']
    kinds = {d['kind'] for d in plan['all_responsibilities']}
    if primary in ('agents','ai_evaluation','model_serving','ai_safety'):
        context = 'For finance workflows' if any(re.search(r'financ', ' '.join(d.get('sources', [d['source']])), re.I) for d in plan['all_responsibilities']) else 'For these product workflows'
        parts = [context + ', I would agree expected outputs and failure cases with product and engineering teams.']
        if 'ai_evaluation' in kinds:
            parts.append('For evaluation, I would build representative test datasets, compare accuracy, latency and cost across changes, and use regression checks and human review to investigate failures.')
        if 'ai_safety' in kinds:
            parts.append('For sensitive actions, I would clarify permissions, restrict tool access and define approval steps before release.')
        if 'software' in kinds or 'model_serving' in kinds:
            parts.append('I would integrate these checks with backend APIs, monitoring and feedback from the people using the product.')
        return ' '.join(parts)
    approaches = {
        'research':'I would translate the research questions into measurable variables, check survey completeness and compare patterns across relevant groups. I would distinguish associations from causal conclusions and document sampling limitations, so the findings remain useful for the decisions the study is intended to support.',
        'database':'I would first understand the data model, query patterns and downstream users. I would test changes against representative records, compare results with the original queries and document assumptions about joins, missing values and definitions before recommending a database change.',
        'integration':'I would clarify source mappings, refresh requirements and downstream dependencies before changing a pipeline. I would check completeness and consistency at each handover, investigate failed runs and document recovery steps so colleagues can understand both the delivered data and its limitations.',
        'quality':'I would agree validation rules with the people using the data, investigate exceptions at their source and verify corrections before publication. I would document ownership and unresolved issues so that quality checks lead to clear follow-up actions rather than simply producing another report.',
        'reporting':'I would clarify the decisions each report supports, agree metric definitions and check the underlying records before publishing results. I would investigate unusual movements, explain limitations and use feedback from stakeholders to keep dashboards understandable and useful as reporting needs change.',
        'support':'I would learn the application workflows, reproduce reported issues and check the relevant interfaces before proposing changes. I would keep users informed, document reproducible steps and verify the resolution with them, giving technical colleagues a clear record when an issue needs further investigation.',
        'records':'I would clarify the required fields and source standards, check duplicates and verify incomplete records before they are used. I would keep a traceable record of corrections and communicate uncertain matches, helping colleagues distinguish verified information from entries that still need investigation.',
        'software':'I would clarify user workflows and interface contracts before implementing changes. I would agree acceptance criteria, test expected behaviour and failure cases, and document deployment and recovery steps with the team so application updates can be reviewed and maintained consistently.',
        'models':'I would agree the prediction target and evaluation criteria, check data splits for leakage and compare results with a baseline. I would track changes to data and models, examine failure cases and monitor behaviour after deployment before recommending further iterations.',
        'documentation':'I would identify who uses each document and which decisions or operational steps it supports. I would verify examples against source material, make assumptions explicit and ask the intended readers to check whether they can follow the process without additional explanation.',
    }
    return approaches.get(primary, 'I would clarify the expected outputs, check source information and document assumptions before making changes. I would agree review points with the team and use feedback to improve the reliability and clarity of the work.')


def prose_sentences(text):
    # Keep .NET, M.Sc., decimals and abbreviations within their sentence.
    return re.split(r'(?<=[.!?])\s+(?=[A-Z][a-z]|I\s)', text)


def letter_fixed_text(company, title, description):
    return ('I hold full work authorization in Germany with no visa sponsorship required and communicate fluently in English (C1) with an intermediate proficiency in German (B2). '
        + availability_text(title, description=description) + ' I would welcome the opportunity to discuss how my technical background can support '
        + company + "'s initiatives. Thank you for your consideration.")


def fit_letter_content(opening, blocks, interest, company, title, description, plan):
    """Fit 300–350 body words by editing complete prose units, never fonts or margins."""
    from tools.responsibility_plan import EVIDENCE
    blocks = list(blocks)
    fixed = opening + ' ' + letter_fixed_text(company, title, description)
    def count():
        return len((fixed + ' ' + ' '.join(h + '. ' + p for h,p in blocks) + ' ' + interest).split())
    while count() > 350:
        candidates = [(i,prose_sentences(body)) for i,(_,body) in enumerate(blocks)]
        candidates = [(i,parts) for i,parts in candidates if len(parts)>2]
        if candidates:
            i,parts = max(candidates,key=lambda item:len(item[1][1].split()))
            # Preserve the anchored first fact and the prospective bridge.
            del parts[1]
            blocks[i] = (blocks[i][0], ' '.join(parts))
        elif len(prose_sentences(interest)) > 1:
            parts = prose_sentences(interest)
            # Retain specific operational sentences rather than a generic lead-in.
            interest = ' '.join(parts[1:])
        else:
            break
    # Expand with responsibility-specific approaches and unused canonical evidence.
    additions = prose_sentences(responsibility_approach(plan))
    for duty in plan['responsibilities']:
        additions.extend(prose_sentences(EVIDENCE[duty['kind']][3]))
    primary_label = plan['responsibilities'][0]['responsibility']
    # Use unused facts from the selected evidence sources before generic process prose.
    # Preserve attribution and deduplicate by the fact itself, not its introductory clause.
    existing = (fixed + ' ' + interest + ' ' + ' '.join(p for _,p in blocks)).casefold()
    for duty in plan['responsibilities']:
        _, source, priorities, _ = EVIDENCE[duty['kind']]
        heading = {'SolTech':'Data Analyst - SolTech', 'G.S.R Educational Institutions':'Data Engineer - G.S.R', 'ITC Infotech':'Associate IT Consultant'}.get(source, source)
        context = f'At {source}, ' if source in ('SolTech','G.S.R Educational Institutions','ITC Infotech') else f'In my {source} project, '
        for fact in section_bullets(heading):
            if fact.casefold() not in existing and any(t.casefold() in fact.casefold() for t in priorities):
                additions.append(context + 'I ' + fact[0].lower() + fact[1:])
    additions.extend([
        f'For {primary_label}, I would agree the expected outputs and review criteria with the team before making changes.',
        'I would compare results with source information, record unresolved questions and make the reasoning behind proposed changes clear to the colleagues reviewing the work.',
        'I would use feedback from the people relying on these outputs to decide which improvements need attention first and how to verify their effect.'
    ])
    for sentence in additions:
        if count() >= 300:
            break
        existing = fixed + ' ' + interest + ' ' + ' '.join(p for _,p in blocks)
        if sentence and sentence not in existing and count()+len(sentence.split()) <= 350:
            interest += ' ' + sentence
    # A small remaining deficit is recoverable: add a concise, prospective check
    # specific to the selected duty. Never add an unsupported achievement or pad a metric.
    checkpoints = {
        'agents':'I would check that retrieved context supports each answer and investigate unsupported responses.',
        'ai_evaluation':'I would keep difficult evaluation examples so later changes can be checked against known failures.',
        'ai_safety':'I would test access restrictions with representative roles before enabling sensitive actions.',
        'model_serving':'I would document the model version behind each release and verify its API responses.',
        'models':'I would inspect error patterns across data subsets before selecting a model for deployment.',
        'finops':'I would verify allocation assumptions with cost owners before proposing savings.',
        'qa':'I would record the inputs and expected results needed to reproduce each defect.',
        'test_automation':'I would keep test inputs reproducible and distinguish test failures from environment issues.',
        'content':'I would check revised content against approved source material before publication.',
        'research':'I would document missing responses and sampling limitations alongside the findings.',
        'records':'I would retain source references when resolving conflicting or duplicate records.',
        'support':'I would confirm with the affected user that the reported issue is resolved.',
        'software':'I would verify interface behaviour against agreed acceptance criteria before release.',
        'database':'I would check query results against known records before changing database logic.',
        'integration':'I would reconcile source and destination records after each pipeline change.',
        'reporting':'I would verify metric definitions and reporting periods before comparing results.',
        'quality':'I would rerun the relevant checks after correcting a data inconsistency.',
        'platform':'I would verify deployment outcomes and document recovery steps before closing a change.',
        'documentation':'I would ask an intended reader to follow the documented steps and flag ambiguities.',
        'ai_delivery':'I would agree a small, testable use case and review the prototype with its intended users.',
        'general':'I would confirm unresolved exceptions with the responsible colleague before finalizing the work.',
    }
    for duty in plan['responsibilities']:
        if count() >= 300:
            break
        sentence = checkpoints[duty['kind']]
        if sentence not in (fixed + ' ' + interest + ' ' + ' '.join(p for _,p in blocks)) and count() + len(sentence.split()) <= 350:
            interest += ' ' + sentence
    # The last checkpoint can still leave a sparse draft below the minimum.
    # Continue with unused, attributed facts from its existing evidence sources;
    # do not stop after one sentence or invent new skills to reach the count.
    for duty in plan['responsibilities']:
        if count() >= 300:
            break
        _, source, _, _ = EVIDENCE[duty['kind']]
        heading = {'SolTech':'Data Analyst - SolTech', 'G.S.R Educational Institutions':'Data Engineer - G.S.R', 'ITC Infotech':'Associate IT Consultant'}.get(source, source)
        context = f'At {source}, ' if source in ('SolTech','G.S.R Educational Institutions','ITC Infotech') else f'In my {source} project, '
        for fact in section_bullets(heading):
            existing = (fixed + ' ' + interest + ' ' + ' '.join(p for _,p in blocks)).casefold()
            sentence = context + 'I ' + fact[0].lower() + fact[1:]
            if count() < 300 and fact.casefold() not in existing and count()+len(sentence.split()) <= 350:
                # Keep historical evidence in its anchored paragraph, not motivation.
                index = next((i for i,(_,body) in enumerate(blocks) if source in body), None)
                if index is not None:
                    heading_text, body = blocks[index]
                    blocks[index] = (heading_text, body + ' ' + sentence)
                else:
                    interest += ' ' + sentence
    if not 300 <= count() <= 350:
        raise ValueError(f'Cover letter body requires wording review: {count()} words; expected 300–350.')
    return blocks, interest.strip()


def cover_letter_body_words(code):
    """Count prose after the greeting, excluding address/subject/salutation/signature."""
    content = code.split('%     MAIN COVER LETTER CONTENT',1)[-1]
    paragraphs = re.findall(r'\\lettercontent\{(.*?)\}\s*(?=\\|%|$)', content, re.S)
    # First two content paragraphs are the subject and salutation.
    body = ' '.join(paragraphs[2:])
    body = re.sub(r'\\[A-Za-z]+\*?(?:\[[^]]*\])?', '', body)
    body = re.sub(r'[{}]', '', body).replace('\\&','&').replace('\\%','%')
    return len(body.split())


def build_tailored_cover_letter(company, company_pascal, role_title, description, is_student, is_data_eng, is_analytics, is_ai_ml, contact_person='', location=''):
    from tools.responsibility_plan import analyze_posting
    plan = analyze_posting(role_title, description)
    duties = plan['responsibilities']
    primary = duties[0]['kind'] if duties else ''
    family = duties[0]['family'] if duties else role_family(role_title, description)
    is_student = is_student_role(role_title, description)
    is_senior = is_senior_role(role_title, description)
    from tools.responsibility_plan import compose_evidence, EVIDENCE
    if not duties:
        raise ValueError('No supported responsibility match; manual tailoring is required.')

    clean_r = clean_title(role_title)
    background = {'ai':'LLM projects, Python, retrieval workflows and model deployment',
                  'platform':'cloud workflows, application integration and CI/CD delivery',
                  'analytics':'Python, SQL and analytical reporting',
                  'data':'Python, SQL and application integration'}[family]
    if is_student:
        student_intro = "As a Master's student in Web and Data Science at the University of Koblenz, "
        opening = f'I am applying for the {clean_r} position at {company}. ' + student_intro + 'I would draw on my experience with ' + background + ' to support your work in ' + duties[0]['responsibility'] + '.'
    elif is_senior:
        opening = f'I am applying for the {clean_r} position at {company}. Bringing 5+ years of professional engineering experience across {background}, I am well prepared to support your team with {duties[0]["responsibility"]}.'
    else:
        opening = f'I am applying for the {clean_r} position at {company}. I would draw on my experience with ' + background + ' to support your work in ' + duties[0]['responsibility'] + '.'

    if primary in ('agents', 'ai_evaluation', 'model_serving', 'ai_safety'):
        workflow = 'finance workflows' if re.search(r'financ', ' '.join(source for d in plan['all_responsibilities'] for source in d.get('sources', [d['source']])), re.I) else 'product workflows'
        opening = f'I am applying for the {clean_r} position at {company}. My Python, RAG and API project experience provides a foundation for building agent-based features that connect reliable AI behaviour with {workflow} and existing backend services.'
    elif primary in ('qa', 'test_automation'):
        opening = f'I am applying for the {clean_r} position at {company}. As a Master’s student in Web and Data Science, I would bring application-development, Python and CI/CD experience to learning your product workflows and supporting reliable, well-documented testing.'
    elif primary == 'content':
        opening = f'I am applying for the {clean_r} position at {company}. As a Master’s student in Web and Data Science, I would bring my Python, reporting and LLM project experience to maintaining reliable support content and improving AI-assisted workflows.'

    thematic_paragraphs = compose_evidence(plan, section_bullets)

    # When a posting matches only 1 duty, dynamically provide a complementary evidence pillar grounded in verified profile
    if len(thematic_paragraphs) < 2:
        comp_heading = ''
        comp_text = ''
        if primary == 'reporting':
            if is_data_eng or re.search(r'data warehouse|lakehouse|etl|pipeline|sql server', description, re.I):
                comp_heading = 'Relational Modeling & Data Architecture'
                comp_text = 'In my SQL Data Warehouse project, I designed and implemented star-schema dimensional models with automated data quality checks, ensuring accurate, consistent reporting that directly supports analytical decision-making.'
            else:
                comp_heading = 'Exploratory Analysis & Statistical Modeling'
                comp_text = 'At SolTech InfoLabs, I performed exploratory data analysis on datasets exceeding 3 million records using Python and SQL to uncover key business trends. I also conducted A/B testing and hypothesis testing across multiple product lines, improving customer retention by 18% through data-driven cohort analysis and statistical modeling.'
        elif primary == 'integration':
            comp_heading = 'Cloud Infrastructure & Automated Delivery'
            comp_text = 'At G.S.R Educational Institutions, I migrated ~1.5 TB of institutional data to cloud storage, optimizing query performance and reducing infrastructure overhead by 30%. In addition, I implemented CI/CD pipelines for Azure Databricks using GitHub Actions, standardizing deployments and reducing manual errors across the engineering team.'
        elif primary == 'database':
            comp_heading = 'Enterprise Data Pipelines & Delivery'
            comp_text = 'At G.S.R Educational Institutions, I designed and maintained ETL/ELT pipelines using Azure Data Factory and Python to consolidate records across departments into a centralized data warehouse, slashing reporting data latency to under 30 minutes.'
        elif primary == 'quality':
            comp_heading = 'Centralized Pipeline Architecture'
            comp_text = 'At G.S.R Educational Institutions, I designed and maintained ETL/ELT pipelines using Azure Data Factory and Python to consolidate academic and administrative data into a centralized warehouse, reducing data latency to under 30 minutes.'
        elif primary == 'models':
            comp_heading = 'Exploratory Data Analysis & Python Workflows'
            comp_text = 'At SolTech InfoLabs, I performed exploratory data analysis on datasets exceeding 3 million records using Python and SQL, identifying key business trends and anomalies. Furthermore, I automated data analysis workflows in Python, cutting manual effort by 6 hours per week and improving reporting turnaround from 3 days to 1 day.'
        elif primary == 'agents':
            comp_heading = 'Machine Learning Operations & Deployment'
            comp_text = 'In my Kidney Disease Classification project, I implemented a full MLOps pipeline with MLflow for experiment tracking, DVC for data versioning, and Flask REST API for model serving, deployed via CI/CD on AWS.'
        elif primary == 'platform':
            comp_heading = 'Application Modernization & Reliability'
            comp_text = 'At ITC Infotech, I built a cloud-native inspection request application using OutSystems, replacing legacy systems via REST API and .NET integration with automated routing and CI/CD deployment, achieving 40% faster response time and zero unplanned downtime.'
        elif primary == 'support':
            comp_heading = 'System Configuration & Quality Assurance'
            comp_text = 'In my SQL Data Warehouse project, I designed dimensional data models with automated validation checks and reusable queries to identify data inconsistencies and verify system integrity.'
        elif primary == 'records':
            comp_heading = 'Automated Reporting & Workflows'
            comp_text = 'At SolTech InfoLabs, I automated data analysis workflows in Python, cutting manual effort by 6 hours per week and improving reporting turnaround from 3 days to 1 day. I also developed Power BI dashboards to present clear administrative metrics to team leads.'

        if comp_heading and comp_text:
            thematic_paragraphs.append((comp_heading, comp_text))

    body_blocks = [r'\lettercontent{\textbf{' + escape_latex(heading) + '.} ' + escape_latex(evidence) + '}'
                   for heading, evidence in thematic_paragraphs]

    interest = ''
    has_dg = bool(re.search(r'\b(data\s*governance|daten-?governance|data\s*lineage|metadata\s*management|data\s*profiling|data\s*catalog|datenqualitätsmanagement|governance\s*frameworks?)\b', description, re.I))
    if primary in ('qa', 'test_automation'):
        interest = 'My Data Governance Quality Assurance seminar provides academic grounding in validation and systematic quality checks. I would learn your product requirements, clarify acceptance criteria with developers and record test observations consistently. For security-related workflows, I would seek guidance on the expected behaviour and document uncertainties before drawing conclusions.' if (has_dg and 'Data Governance Quality Assurance' in profile_text()) else 'I would learn your product requirements, clarify acceptance criteria with developers and record test observations consistently.'
        if re.search(r'\bPKI\b', description):
            interest += ' I am interested in learning PKI product behaviour.'
    elif primary == 'content':
        interest = 'I would clarify the source of truth for each article, check consistency across publishing surfaces and use content metrics to identify areas for review. My Python and API background provides a foundation for learning your content automation tools and testing repetitive formatting or publishing steps with content specialists, recording the outcomes for repeatable quality checks.'
    elif primary == 'general':
        interest = 'My data engineering work at G.S.R Educational Institutions involved bringing student records, LMS activity and administrative data from different departments into a central warehouse. That work taught me to trace information back to its sources and consider how colleagues would use the resulting outputs. I would bring the same care to learning your processes, asking precise questions and documenting assumptions before making changes.'
    elif primary == 'finops':
        interest = 'I am interested in connecting cloud usage with understandable cost information. I would learn your allocation rules, investigate budget deviations with IT, finance and purchasing, and document the assumptions behind management reports.'
        if re.search(r'\bServiceNow\b', description, re.I):
            interest += ' I would build on my application integration experience while learning your ServiceNow cost-management workflows. For management information, I would make the reporting period, allocation basis and reasons for unusual changes explicit, so colleagues can compare costs consistently and decide which items need investigation.'
    elif family == 'platform':
        skills = '\n'.join(skill_groups(family, description))
        confirmed = [term for term in ['Terraform', 'Kubernetes', 'Docker', 'Windows/Linux administration', 'monitoring', 'security'] if term in skills and term.lower() in description.lower()]
        if confirmed:
            interest = 'My confirmed hands-on skills include ' + ', '.join(confirmed) + '. '
        topics = [label for token, label in [('hardening', 'system hardening'), ('vulnerability', 'vulnerability management'), ('nis2', 'NIS2 compliance')] if token in description.lower()]
        if topics:
            interest += 'I would welcome the opportunity to deepen my experience in ' + ', '.join(topics) + ' through the projects described in the posting.'
        if not interest:
            interest = 'I approach platform operations with an emphasis on automation, observability, and reproducible infrastructure, ensuring robust deployments and minimal downtime.'
    else:
        interest = responsibility_approach(plan)

    from tools.technology_evidence import review_technologies, learning_sentence
    technology_review = review_technologies(description, profile_text())
    learning = learning_sentence({'technologies': [r for r in technology_review['technologies'] if r['technology'] not in interest]})
    # Do not duplicate a learning bridge already present (for example ServiceNow).
    if learning and not re.search(r'(?:do not|don.t) need experience with every|or comparable frameworks', description, re.I):
        interest += ' ' + learning

    thematic_paragraphs, interest = fit_letter_content(opening, thematic_paragraphs, interest,
        company, role_title, description, plan)
    body_blocks = [r'\lettercontent{\textbf{' + escape_latex(heading) + '.} ' + escape_latex(evidence) + '}'
                   for heading, evidence in thematic_paragraphs]

    identifier = requisition_id(description)
    subject = clean_title(role_title) + (f' (Job ID {identifier})' if identifier else '')
    salutation, _ = format_salutation(contact_person)

    if not location or not location.endswith('Germany'):
        location = extract_company_location(location or description, description=description, company=company)

    clean_loc = escape_latex(location) if location else 'Germany'
    recipient_address = f"Hiring Team\\\\{clean_loc}"

    code = COVER_TEMPLATE
    for token, value in {
        '__COMPANY__': escape_latex(company),
        '__COMPANY_PASCAL__': escape_latex(company_pascal),
        '__CLEAN_ROLE__': escape_latex(clean_title(role_title)),
        '__SUBJECT__': escape_latex(subject),
        '__RECIPIENT_ADDRESS__': recipient_address,
        '__SALUTATION__': salutation,
        '__OPENING__': escape_latex(opening),
        '__BODY__': '\n\n'.join(body_blocks),
        '__INTEREST__': r'\lettercontent{' + escape_latex(interest) + '}' if interest else '',
        '__AVAILABILITY__': escape_latex(availability_text(role_title, description=description))
    }.items():
        code = code.replace(token, value)
    return code


def compile_cv_with_summary_fit(engine, source, directory):
    """Retry only summary-length errors, editing prose rather than typography."""
    if compile_latex(engine, source, directory):
        return True
    log = source.with_suffix('.log')
    if not log.is_file():
        return False
    diagnostic = log.read_text(encoding='utf-8', errors='replace')
    if 'CV summary must have exactly 4 rendered lines' not in diagnostic:
        return False
    counts = re.findall(r'CV-SUMMARY-LINES:\s*(\d+)', diagnostic)
    if not counts:
        return False
    code = source.read_text(encoding='utf-8')
    prefix = re.escape(r'{\raggedright\small ')
    suffix = re.escape(r'\par\global\summarylines=\prevgraf}')
    pattern = '(' + prefix + r')(.*?)(' + suffix + ')'
    match = re.search(pattern, code, re.S)
    if not match:
        return False
    original = match.group(2)
    variants = []
    if int(counts[-1]) > 4:
        current = original
        # Preserve role-specific tools, university, graduation and contribution.
        edits = [
            ('with data engineering and analytics experience', 'with data and analytics experience'),
            ('My background includes ', 'Experienced in '),
            ('My projects include ', 'Projects include '),
            ('to support well-informed operational decisions', 'for operational decisions'),
            ('Brings a structured approach to', 'Structured approach to'),
            ('Combines analytical problem-solving with', 'Combines analysis with'),
            ('that colleagues can maintain', 'for colleagues'),
            ('connecting technical delivery with reporting needs across different teams', 'connecting technical delivery with reporting'),
            ('with a background in data engineering, analytics and software consultancy', 'in data engineering, analytics and software consultancy'),
            ('Currently pursuing an M.Sc. in Web and Data Science at the University of Koblenz', 'M.Sc. Web and Data Science student at University of Koblenz'),
            ('Currently pursuing an M.Sc. in Web and Data Science at University of Koblenz', 'M.Sc. Web and Data Science student at University of Koblenz'),
            ('Currently pursuing an M.Sc. in Web and Data Science', 'M.Sc. Web and Data Science student'),
            ('currently pursuing an M.Sc. in Web and Data Science', 'M.Sc. Web and Data Science student'),
            ('Currently pursuing M.Sc. in Web and Data Science', 'M.Sc. Web and Data Science student'),
            ('currently pursuing M.Sc. in Web and Data Science', 'M.Sc. Web and Data Science student'),
            ('M.Sc. Web and Data Science student at University of Koblenz', 'M.Sc. Web and Data Science student, University of Koblenz'),
            (' (expected September 2027)', ', expected September 2027'),
            ('with a strong focus on ', 'focusing on '),
            ('with a focus on ', 'focusing on '),
            ('with expertise in ', 'specializing in '),
            ('with extensive expertise in ', 'specializing in '),
            ('Brings proven experience deploying ', 'Experienced in deploying '),
            ('Brings proven experience in ', 'Experienced in '),
            ('Brings proven experience ', 'Experienced in '),
            ('Brings practical experience in ', 'Experienced in '),
            ('Contributes practical experience in ', 'Experienced in '),
            ('Contributes experience in ', 'Experienced in '),
            ('Demonstrates strong technical capability in ', 'Experienced in '),
            ('Demonstrates practical capability in ', 'Experienced in '),
            ('This background enables dependable support for ', 'Enables dependable support for '),
            ('This background enables strong support for ', 'Enables support for '),
            ('This background enables support for ', 'Enables support for '),
            ('This background enables ', 'Enables '),
            ('This background equips me to support ', 'Equips me to support '),
            ('I can support ', 'Supporting '),
        ]
        phrase_shorteners = [
            (' in order to ', ' to '),
            ('effectively ', ''),
            ('successfully ', ''),
            ('reliably ', ''),
            ('Proven track record in ', 'Experience in '),
            ('proven track record in ', 'experience in '),
            ('extensive experience in ', 'experienced in '),
            ('deep expertise in ', 'experienced in '),
            ('proficiency in ', 'skills in '),
            ('across the organization', ''),
            ('through modern technology', ''),
            ('across enterprise business units', 'across teams'),
            ('at the University of Koblenz', 'at University of Koblenz'),
            ('expected graduation: ', 'grad. '),
            ('expected graduation ', 'grad. '),
            ('delivering business intelligence solutions', 'delivering BI solutions'),
            ('and optimizing complex business activities', ''),
            ('for scalable engineering solutions', 'for scalable solutions'),
            ('scalable cloud applications and robust software delivery', 'scalable cloud applications and delivery'),
            ('practical software engineering background', 'software engineering background'),
            ('practical software engineering experience', 'software engineering experience'),
            ('production-grade APIs', 'APIs'),
            ('scalable REST APIs', 'REST APIs'),
        ]
        for old, new in edits + phrase_shorteners:
            updated = current.replace(old, new)
            if updated != current:
                current = updated
                variants.append(current)
        if len(current.split()) > 56:
            clause_cleaned = re.sub(r'\s+(?:by|through|across|in order to)\s+[^.]+\.', '.', current)
            if clause_cleaned != current and len(clause_cleaned.split()) >= 45:
                variants.append(clause_cleaned)
    else:
        # Supported professional background, only used when more detail fits.
        variants = [original + ' Experience includes Python and SQL analysis of operational data.',
                    original + ' Experience includes Python and SQL analysis of operational data, reporting automation and integration of information from multiple sources.']
    for summary in variants:
        candidate = code[:match.start(2)] + summary + code[match.end(2):]
        source.write_text(candidate, encoding='utf-8')
        if compile_latex(engine, source, directory):
            return True
        diagnostic = log.read_text(encoding='utf-8', errors='replace') if log.is_file() else ''
        if 'CV summary must have exactly 4 rendered lines' not in diagnostic:
            return False
    return False


def compile_latex(engine: str, tex_file: Path, cwd: Path) -> bool:
    """Run LaTeX compiler (lualatex or xelatex) with TinyTeX environment."""
    env = dict(os.environ)
    env["PATH"] = f"{TINYTEX_BIN}:{env.get('PATH', '')}"

    cmd = [str(TINYTEX_BIN / engine), "-interaction=nonstopmode", "-halt-on-error", tex_file.name]
    try:
        res = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=40)
        return res.returncode == 0
    except Exception as e:
        print(f"LaTeX compile error for {tex_file.name}: {e}", file=sys.stderr)
        return False


def record_in_tracker(company: str, role: str, cv_rel: str, cl_rel: str, source_url: str = "", fit_rating: int = 85, contact_person: str = ""):
    """Update or append entry in job_search_tracker.csv."""
    canonical_headers = [
        "date", "company", "sector", "role", "role_type", "channel", "status",
        "contact_person", "fit_rating", "notes", "cv_file", "cover_letter_file",
        "source", "deadline"
    ]
    rows = []
    found = False
    clean_r = clean_title(role)
    today_str = date.today().strftime("%Y-%m-%d")

    target_fieldnames = list(canonical_headers)
    if TRACKER_FILE.is_file():
        with TRACKER_FILE.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                for fn in reader.fieldnames:
                    if fn not in target_fieldnames:
                        target_fieldnames.append(fn)
            for r in reader:
                if r.get("company", "").strip().lower() == company.strip().lower() and \
                   clean_title(r.get("role", "")).lower() == clean_r.lower():
                    if r.get("status") not in ["applied", "interviewing", "offer", "rejected"]:
                        r["status"] = "drafted"
                    r["cv_file"] = cv_rel
                    r["cover_letter_file"] = cl_rel
                    if contact_person:
                        r["contact_person"] = contact_person
                    if source_url and not r.get("source"):
                        r["source"] = source_url
                    found = True
                rows.append(r)

    if not found:
        rows.append({
            "date": today_str,
            "company": company,
            "sector": "Technology",
            "role": clean_r,
            "role_type": "Full-time",
            "channel": "direct",
            "status": "drafted",
            "fit_rating": str(fit_rating),
            "contact_person": contact_person or "",
            "notes": "Generated draft; content, visual and attachment review required",
            "cv_file": cv_rel,
            "cover_letter_file": cl_rel,
            "source": source_url or "",
            "deadline": ""
        })

    sanitized_rows = []
    for r in rows:
        sanitized_rows.append({k: r.get(k, "") for k in target_fieldnames})

    with TRACKER_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=target_fieldnames)
        writer.writeheader()
        writer.writerows(sanitized_rows)


def update_seen_jobs(job_key: str, display_company: str = ""):
    """Mark job as drafted in seen_jobs.json."""
    if not SEEN_JOBS_FILE.is_file():
        return
    try:
        with SEEN_JOBS_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
        seen = data.get("seen", {})
        if job_key in seen:
            seen[job_key]["status"] = "drafted"
            if display_company:
                seen[job_key]["display_company"] = display_company
            with SEEN_JOBS_FILE.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not update seen_jobs.json: {e}", file=sys.stderr)


def verify_generated_pdf(path, pages):
    """Check the embedded text layer as well as page count before exposing links."""
    result = subprocess.run([sys.executable, str(Path(__file__).with_name('verify_pdf.py')),
        str(path), '--pages', str(pages), '--min-chars', '100'], capture_output=True, text=True)
    return result.returncode == 0


def required_attachments(description):
    patterns = [
        (r'enrollment certificate|certificate of enrollment|immatrikulationsbescheinigung', 'Enrollment certificate'),
        (r'academic performance|academic results|transcript|studienleistungen', 'Current academic results / transcript'),
        (r'examination.*regulations|study regulations|prüfungs.*studienordnung', 'Examination and study regulations specifying internship duration'),
    ]
    return [label for pattern, label in patterns if re.search(pattern, description, re.I)]


def generate_for_job(job: dict) -> dict:
    """Retain a private actionable error report without mutating application records."""
    try:
        result = _generate_for_job(job)
    except (ValueError, TypeError, KeyError) as exc:
        result = {'success': False, 'error': str(exc), 'transport':getattr(exc,'diagnostics',None)}
    if not result.get('success'):
        from tools.generation_diagnostics import save_failure
        try:
            result['diagnostics_file'] = save_failure(ROOT, str(job.get('company','')), str(job.get('title','')), result.get('error','Unknown generation failure'), transport=result.get('transport'))
        except TypeError:
            try:
                result['diagnostics_file'] = save_failure(ROOT, str(job.get('company','')), str(job.get('title','')), result.get('error','Unknown generation failure'))
            except Exception:
                result['diagnostics_warning'] = 'Could not save the private error report.'
        except Exception:
            result['diagnostics_warning'] = 'Could not save the private error report.'
    return result


def _generate_for_job(job: dict) -> dict:
    """End-to-end generation for a given job object."""
    from tools import gemini_tailoring
    try:
        llm_config = gemini_tailoring.settings(ROOT)
    except ValueError as exc:
        return {"success": False, "error": str(exc)}
    generation_metadata = {'provider': 'rules'}
    company = job.get("company", "Company").strip()
    title = job.get("title", "Role").strip()
    url = job.get("url", "").strip()
    desc = job.get("description", "").strip()
    job_key = job.get("key", "")

    # Resolve referral stubs as well as empty descriptions before evaluating duties.
    from tools.job_description import needs_resolution
    if not job.get("is_custom") and needs_resolution(desc):
        print("  Fetching the full description from the portal or linked job page...", file=sys.stderr)
        fetched_desc = fetch_description_for_job(job)
        if fetched_desc:
            desc = fetched_desc
            persist_description(job_key, desc)
        else:
            return {"success": False, "verification_status": "description_needed",
                    "error": "Description needed: the full matching job description could not be retrieved. Open the original job link or paste the full description and retry.",
                    "source_url": url, "description_fetch_errors": job.get('description_fetch_errors', [])}

    from tools.responsibility_plan import analyze_posting
    tailoring_plan = analyze_posting(title, desc)
    if tailoring_plan['review_issues'] and llm_config['provider'] != 'gemini':
        return {"success": False, "verification_status": "review_required",
                "error": "Responsibility review required before generation: " + ' '.join(tailoring_plan['review_issues']),
                "tailoring_plan": tailoring_plan}

    from tools.technology_evidence import review_technologies
    technology_review = review_technologies(desc, profile_text())

    # Log keyword extraction results for transparency
    kw = extract_job_keywords(desc, title)
    matched = kw.get("all_labels", [])
    top5 = kw.get("top_5", [])
    print(f"  🔍 Extracted {len(matched)} keywords from description. Top 5: {', '.join(top5) if top5 else 'none'}", file=sys.stderr)

    company_pascal = sanitize_company_name(company)
    clean_r = clean_title(title)
    role_slug = "".join(w.capitalize() for w in clean_r.split() if w.isalnum()) or "Role"

    # Detect individual contact person / recruiter from job data, tracker history, or description
    existing_tracker_cp = ""
    if TRACKER_FILE.is_file():
        try:
            with TRACKER_FILE.open(encoding="utf-8") as tf:
                for r in csv.DictReader(tf):
                    if r.get("company", "").strip().lower() == company.lower() and \
                       clean_title(r.get("role", "")).lower() == clean_r.lower():
                        existing_tracker_cp = (r.get("contact_person") or "").strip()
                        break
        except Exception:
            pass

    contact_person = job.get("contact_person") or existing_tracker_cp or extract_contact_person(desc, company, title)
    if contact_person:
        print(f"  👤 Identified Contact Person: {contact_person}", file=sys.stderr)

    t_low = title.lower()
    is_student = is_student_role(title, desc)
    is_analytics = any(x in t_low for x in ["analyst", "analytics", "business intelligence", "bi", "power bi"])
    is_ai_ml = any(x in t_low for x in ["ai", "machine learning", "ml", "genai", "deep learning", "scientist"])
    is_data_eng = any(x in t_low for x in ["engineer", "databricks", "spark", "lakehouse", "etl", "pipeline", "architect"])

    cv_base = f"YashwanthGotike_{company_pascal}_CV"
    cl_base = f"YashwanthGotike_{company_pascal}_CoverLetter"

    cv_tex_path = CV_DIR / f"{cv_base}.tex"
    cv_pdf_path = CV_DIR / f"{cv_base}.pdf"
    cl_tex_path = COVER_DIR / f"{cl_base}.tex"
    cl_pdf_path = COVER_DIR / f"{cl_base}.pdf"

    location = extract_company_location(job, desc, company)
    try:
        if llm_config['provider'] == 'gemini':
            cv_code, cl_code, generation_metadata = gemini_tailoring.generate(
                sys.modules[__name__], llm_config, job.get('display_company') or company,
                company_pascal, title, desc, contact_person, location)
        else:
            cv_code = build_tailored_cv(job.get('display_company') or company, company_pascal, title, desc, is_student, is_data_eng, is_analytics, is_ai_ml)
            cl_code = build_tailored_cover_letter(job.get('display_company') or company, company_pascal, title, desc, is_student, is_data_eng, is_analytics, is_ai_ml, contact_person=contact_person, location=location)
    except (ValueError, RuntimeError) as exc:
        return {"success": False, "verification_status": "review_required", "error": str(exc), "tailoring_plan": tailoring_plan, "transport":getattr(exc,"diagnostics",None)}

    cv_tex_path.write_text(cv_code, encoding="utf-8")
    cl_tex_path.write_text(cl_code, encoding="utf-8")

    if generation_metadata.get('provider') != 'gemini':
        for engine, source, directory in [
            ("lualatex", cv_tex_path, CV_DIR),
            ("lualatex", cv_tex_path, CV_DIR),
            ("xelatex", cl_tex_path, COVER_DIR),
        ]:
            compile_document = compile_cv_with_summary_fit if source == cv_tex_path else compile_latex
            compiled = compile_document(engine, source, directory)
            if not compiled:
                return {"success": False, "error": f"Compilation failed for {source.name}. Check {source.with_suffix('.log').name}; application records were not updated."}
    else:
        # Parallelize CV (lualatex) and Cover Letter (xelatex) compilation for Gemini
        from concurrent.futures import ThreadPoolExecutor

        def compile_cv():
            compiled = compile_latex("lualatex", cv_tex_path, CV_DIR)
            if not compiled:
                diagnostic = cv_tex_path.with_suffix('.log').read_text(errors='replace') if cv_tex_path.with_suffix('.log').exists() else ''
                if 'CV summary must have exactly 4 rendered lines' in diagnostic and generation_metadata.get('summary_alternatives'):
                    prefix = re.escape(r'{\raggedright\small ')
                    suffix = re.escape(r'\par\global\summarylines=\prevgraf}')
                    pattern = '(' + prefix + r')(.*?)(' + suffix + ')'
                    for summary in generation_metadata['summary_alternatives']:
                        candidate = re.sub(pattern, lambda m: m[1] + escape_latex(summary) + m[3], cv_code, flags=re.S)
                        cv_tex_path.write_text(candidate, encoding='utf-8')
                        if compile_latex("lualatex", cv_tex_path, CV_DIR):
                            compiled = True
                            break
                        if compile_cv_with_summary_fit("lualatex", cv_tex_path, CV_DIR):
                            compiled = True
                            break
                if not compiled:
                    compiled = compile_cv_with_summary_fit("lualatex", cv_tex_path, CV_DIR)
            return compiled

        def compile_cl():
            return compile_latex("xelatex", cl_tex_path, COVER_DIR)

        with ThreadPoolExecutor(max_workers=2) as executor:
            fut_cv = executor.submit(compile_cv)
            fut_cl = executor.submit(compile_cl)
            cv_compiled = fut_cv.result()
            cl_compiled = fut_cl.result()

        if not cv_compiled:
            return {"success": False, "error": f"Compilation failed for {cv_tex_path.name}. Check {cv_tex_path.with_suffix('.log').name}; application records were not updated."}
        if not cl_compiled:
            return {"success": False, "error": f"Compilation failed for {cl_tex_path.name}. Check {cl_tex_path.with_suffix('.log').name}; application records were not updated."}

    cv_pages = get_pdf_page_count(cv_pdf_path) if cv_pdf_path.is_file() else 0
    cl_pages = get_pdf_page_count(cl_pdf_path) if cl_pdf_path.is_file() else 0
    if cl_pages > 1 and r"\geometry{hmargin=2.0cm, top=1.6cm, bottom=1.6cm}" in cl_code:
        # Micro-tighten cover letter geometry if an unusually long title or address caused a spill
        tightened_code = cl_code.replace(r"\geometry{hmargin=2.0cm, top=1.6cm, bottom=1.6cm}", r"\geometry{hmargin=1.9cm, top=1.35cm, bottom=1.35cm}")
        cl_tex_path.write_text(tightened_code, encoding="utf-8")
        if compile_latex("xelatex", cl_tex_path, COVER_DIR):
            try:
                cl_pages = get_pdf_page_count(cl_pdf_path) if cl_pdf_path.is_file() else 0
            except Exception:
                pass

    if cv_pages != 2 or cl_pages != 1:
        return {
            "success": False,
            "error": f"Page verification failed: CV {cv_pages}/2, cover letter {cl_pages}/1. Revise the documents before recording the application.",
            "cv_pages": cv_pages, "cl_pages": cl_pages,
        }

    if not verify_generated_pdf(cv_pdf_path, 2) or not verify_generated_pdf(cl_pdf_path, 1):
        return {"success": False, "error": "PDF text-extraction verification failed; application records were not updated."}

    cv_rel = f"cv/{cv_base}.pdf"
    cl_rel = f"cover_letters/{cl_base}.pdf"

    # 5. Archive
    archive_dir = DOCUMENTS_DIR / f"{company_pascal}_{role_slug}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    if cv_pdf_path.is_file():
        shutil.copy2(cv_pdf_path, archive_dir / cv_pdf_path.name)
    if cl_pdf_path.is_file():
        shutil.copy2(cl_pdf_path, archive_dir / cl_pdf_path.name)
    if cv_tex_path.is_file():
        shutil.copy2(cv_tex_path, archive_dir / cv_tex_path.name)
    if cl_tex_path.is_file():
        shutil.copy2(cl_tex_path, archive_dir / cl_tex_path.name)

    (archive_dir / 'tailoring_review.json').write_text(json.dumps({
        'generator_version': GENERATOR_VERSION,
        'generation': generation_metadata,
        'plan': tailoring_plan,
        'technology_review': technology_review,
        'cover_letter_body_words': cover_letter_body_words(cl_code),
        'discovery_url': job.get('discovery_url', url),
        'description_source_url': job.get('description_source_url', url),
        'status': 'review_required',
        'note': 'Source-linked automatic draft; confirm factual targeting, coverage and visual layout before submission.'
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    # 6. Update Tracker
    record_in_tracker(company, clean_r, cv_rel, cl_rel, source_url=url, fit_rating=job.get("score", 85), contact_person=contact_person)

    # 7. Update Seen Jobs
    if job_key:
        update_seen_jobs(job_key, job.get("display_company", ""))

    return {
        "success": True,
        "generator_version": GENERATOR_VERSION,
        "generation": generation_metadata,
        "tailoring_plan": tailoring_plan,
        "tailoring_warnings": tailoring_plan.get("review_warnings", []) + generation_metadata.get("quality_warnings", []),
        "technology_review": technology_review,
        "cover_letter_body_words": cover_letter_body_words(cl_code),
        "skills_to_confirm": [r["technology"] for r in technology_review["technologies"] if r["status"] != "confirmed"],
        "required_attachments": required_attachments(desc),
        "verification_status": "review_required",
        "review_notes": "Drafts compiled. Review factual targeting, visual layout and required attachments before submission. Internship hours and duration require confirmation.",
        "company": company,
        "role": clean_r,
        "contact_person": contact_person,
        "cv_file": cv_rel,
        "cover_letter_file": cl_rel,
        "cv_pages": cv_pages,
        "cl_pages": cl_pages,
        "archive_dir": str(archive_dir.relative_to(ROOT)),
        "matched_keywords": top5,
        "keyword_count": len(matched)
    }


def main():
    parser = argparse.ArgumentParser(description="Generate tailored CV and Cover Letter for a target job")
    parser.add_argument("--key", help="Key of the job in seen_jobs.json")
    parser.add_argument("--company", help="Company name")
    parser.add_argument("--role", "--title", help="Role title")
    parser.add_argument("--url", default="", help="Job posting URL")
    parser.add_argument("--desc", default="", help="Job description")
    args = parser.parse_args()

    job_data = {}
    if args.key and SEEN_JOBS_FILE.is_file():
        with open(SEEN_JOBS_FILE, encoding="utf-8") as f:
            seen_all = json.load(f).get("seen", {})
            if args.key in seen_all:
                job_data = seen_all[args.key]
                job_data["key"] = args.key

    if not job_data and args.company and args.role:
        job_data = {
            "company": args.company,
            "title": args.role,
            "url": args.url,
            "description": args.desc,
            "key": ""
        }

    if not job_data:
        print("Error: Specify either a valid --key from seen_jobs.json or provide --company and --role.", file=sys.stderr)
        sys.exit(1)

    print(f"Generating documents for {job_data.get('company')} — {job_data.get('title')}...")
    result = generate_for_job(job_data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
