#!/usr/bin/env python3
"""Localhost HTTP & API Server for AI Job Search Dashboard.

Serves the interactive web interface at http://localhost:8000,
exposing endpoints for job listings, match scoring, tracker status,
and static previewing of generated CV and cover letter PDFs.
"""

import csv
import json
import mimetypes
import os
import re
import subprocess
import sys
from datetime import date
from functools import wraps
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse, unquote

from tools.job_selection import role_category, display_category, consolidate_jobs, is_dual_study_posting
from tools.state_io import atomic_write_csv, file_lock, read_job_state, update_job_state

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
SEEN_JOBS_FILE = ROOT / "job_scraper" / "seen_jobs.json"
TRACKER_FILE = ROOT / "job_search_tracker.csv"

# Keyword matching sets for fit evaluation
KEYWORDS = {
    "core_data_eng": [
        "azure", "databricks", "spark", "pyspark", "lakehouse", "medallion",
        "lakeflow", "delta lake", "etl", "elt", "data pipeline", "airflow"
    ],
    "cloud_cicd": [
        "github actions", "ci/cd", "devops", "docker", "git", "aws", "gcp", "azure devops"
    ],
    "analytics_bi": [
        "power bi", "dax", "tableau", "data analyst", "bi analyst", "sql", "t-sql",
        "query optimization", "a/b testing", "cohort"
    ],
    "ai_ml_genai": [
        "machine learning", "ml engineer", "ai engineer", "rag", "llm", "vector",
        "agent", "agentic", "mcp", "langchain", "deep learning", "nlp", "tensorflow", "pytorch"
    ]
}


def clean_title(t):
    """Remove parenthetical/bracketed and delimited gender markers, diversity tags, and clean role title."""
    if not t:
        return ""
    s = str(t).strip()
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


GERMAN_C1_PATTERNS = [
    # German/Deutsch directly followed by C1/C2: "German: C1", "German (C1)", "German C1", "Deutsch C1", "Deutsch (C1)"
    r"\b(?:deutsch|german)\b[\s:–—\-(]{0,5}\b(?:c1|c2)\b",
    # C1/C2 directly followed by German/Deutsch: "C1 German", "C1-Deutsch", "C1 in German", "C1 in Deutsch"
    r"\b(?:c1|c2)\b[\s:–—\-)]{0,5}(?:in\s+)?(?:deutsch|german)\b",
    # CEFR level attached: "C1-Niveau", "C1 Niveau", "C2-Niveau"
    r"\b(?:c1|c2)[\s-]niveau\b",
    # Specific German level requirements
    r"\b(?:c1|c2)\s+(?:level|kenntnisse)\b.*?\b(?:deutsch|german)\b",
    r"\b(?:deutsch|german)\b.*?\b(?:c1|c2)\s+(?:level|kenntnisse)\b",
    # Verhandlungssicher (negotiation-level = C1/C2 standard in DACH)
    r"\bverhandlungssicher(?:e|es|en|em)?\b",
    # Business-fluent German
    r"\bbusiness[\s-]fluent\s+german\b",
    r"\bgerman\b[^\.\n;]{0,15}\bbusiness[\s-]fluent\b",
    # Native / Muttersprache German
    r"\b(?:native|near[\s-]native)\s+german\b",
    r"\bmuttersprachlich(?:e|es|en)?\b",
    r"\bmuttersprachenniveau\b",
    # Mindestens / min C1 in German context
    r"(?:mindestens|mind\.)\s+(?:auf\s+level\s+)?c[12]",
    r"(?:at\s+least|minimum)\s+c[12]\s+(?:in\s+)?german",
    r"deutsch[^\.\n;]{0,25}?\bflie(?:ß|ss)end[^\.\n;]{0,15}?(?:c1|verhandlungssicher)",
]


REPOST_PATTERNS = [
    r"\b(?:re-?posted|re-?posting|erneut\s+veröffentlicht)\b",
    r"\bvor\s+(?:[3-9]|\d{2,})\s+tagen?\b",
    r"\bvor\s+\d+\s+(?:wochen?|monaten?|jahren?)\b",
    r"\b(?:[3-9]|\d{2,})\s+days?\s+ago\b",
    r"\b\d+\s+(?:weeks?|months?|years?)\s+ago\b",
]


def is_reposted_or_stale(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    for pat in REPOST_PATTERNS:
        if re.search(pat, lower):
            return True
    return False


def requires_german_c1(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    for pat in GERMAN_C1_PATTERNS:
        if re.search(pat, lower):
            return True
    return False


def calculate_match_score(title, description=""):
    """Calculate transparent fit score 0-100% based on candidate profile match."""
    combined = (f"{title} {description}").lower()
    score = 50.0  # baseline
    matched_tags = []

    family = role_category(title, description)
    if family is None:
        return 0, "Outside target roles", []
    bonuses = {"Data Engineering": 25, "Data Analytics & BI": 20, "AI / ML & GenAI": 22}
    score += bonuses[family]
    matched_tags.append(family)
    from tools.job_selection import STUDENT
    if STUDENT.search(title or ""):
        score += 2
        matched_tags.append("Working Student")

    # Keyword scanning
    tech_hits = 0
    for category, terms in KEYWORDS.items():
        for term in terms:
            if re.search(rf"\b{re.escape(term)}\b", combined):
                tech_hits += 1
                if len(matched_tags) < 6 and term.title() not in matched_tags:
                    matched_tags.append(term.title())

    score += min(tech_hits * 3.5, 25.0)

    # Germany / Remote bonus
    if any(loc in combined for loc in ["germany", "deutschland", "remote", "hybrid", "münster", "berlin", "frankfurt", "köln"]):
        score += 5

    final_score = int(min(max(score, 45), 98))
    tier = "Strong Fit" if final_score >= 75 else ("Good Fit" if final_score >= 60 else "Moderate Fit")
    return final_score, tier, matched_tags[:6]


def load_tracker():
    applications = {}
    if not TRACKER_FILE.is_file():
        return applications

    seen_state = {}
    if SEEN_JOBS_FILE.is_file():
        try:
            seen_state = json.loads(SEEN_JOBS_FILE.read_text(encoding="utf-8")).get("seen", {})
        except Exception:
            pass

    seen_by_comp = {}
    for sv in seen_state.values():
        c = re.sub(r"[^a-z0-9]", "", (sv.get("company") or "").lower())
        if c:
            seen_by_comp.setdefault(c, []).append(sv)

    try:
        from tools.generate_application import extract_contact_person
    except Exception:
        extract_contact_person = lambda d, c, t: ""

    try:
        with TRACKER_FILE.open(encoding="utf-8") as f:
            records = list(csv.DictReader(f))
            file_roles = {}
            for record in records:
                identity = (record.get("company"), clean_title(record.get("role") or ""))
                for field in ("cv_file", "cover_letter_file"):
                    if record.get(field):
                        file_roles.setdefault(record[field], set()).add(identity)
            for row in records:
                comp = re.sub(r"[^a-z0-9]", "", (row.get("company") or "").lower())
                role = re.sub(r"[^a-z0-9]", "", clean_title(row.get("role") or "").lower())
                source_url = (row.get("source") or "").strip()
                match_id = None
                m = re.search(r"(\d{6,})", source_url)
                if m:
                    match_id = m.group(1)

                cp = (row.get("contact_person") or "").strip()
                if not cp and comp in seen_by_comp:
                    for sv in seen_by_comp[comp]:
                        sr = re.sub(r"[^a-z0-9]", "", clean_title(sv.get("title") or "").lower())
                        if sr in role or role in sr:
                            cp = sv.get("contact_person") or extract_contact_person(sv.get("description", ""), sv.get("company", ""), sv.get("title", ""))
                            if cp:
                                break

                cv_f = row.get("cv_file")
                cl_f = row.get("cover_letter_file")
                from tools.generate_application import application_archive_dir
                archive = application_archive_dir(row.get("company") or "", row.get("role") or "")
                for field, value in (("cv_file", cv_f), ("cover_letter_file", cl_f)):
                    if value:
                        archived = archive / Path(value).name
                        if archived.is_file():
                            if field == "cv_file":
                                cv_f = str(archived.relative_to(ROOT))
                            else:
                                cl_f = str(archived.relative_to(ROOT))
                        elif len(file_roles.get(value, ())) > 1:
                            # An unarchived shared file cannot identify an earlier role.
                            if field == "cv_file":
                                cv_f = None
                            else:
                                cl_f = None

                entry = {
                    "date": row.get("date"),
                    "company": row.get("company"),
                    "role": row.get("role"),
                    "status": (row.get("status") or "drafted").strip(),
                    "fit_rating": row.get("fit_rating"),
                    "contact_person": cp or "",
                    "notes": row.get("notes"),
                    "cv_file": cv_f if cv_f and (ROOT / cv_f).is_file() else None,
                    "cover_letter_file": cl_f if cl_f and (ROOT / cl_f).is_file() else None,
                    "source": source_url,
                    "deadline": row.get("deadline")
                }
                if comp and role:
                    applications[f"{comp}_{role}"] = entry
                if match_id:
                    applications[f"id_{match_id}"] = entry
                if source_url:
                    applications[source_url] = entry
    except Exception as e:
        print(f"Error reading tracker: {e}", file=sys.stderr)
    return applications


_ENRICHED_CACHE = None
_ENRICHED_CACHE_KEY = None


def get_enriched_jobs(*, include_counts=False):
    global _ENRICHED_CACHE, _ENRICHED_CACHE_KEY

    try:
        seen_mtime = SEEN_JOBS_FILE.stat().st_mtime if SEEN_JOBS_FILE.is_file() else 0
    except Exception:
        seen_mtime = 0
    try:
        tracker_mtime = TRACKER_FILE.stat().st_mtime if TRACKER_FILE.is_file() else 0
    except Exception:
        tracker_mtime = 0
    today = date.today()
    cache_key = (seen_mtime, tracker_mtime, str(today))

    if _ENRICHED_CACHE is not None and _ENRICHED_CACHE_KEY == cache_key:
        cached_jobs, cached_counts = _ENRICHED_CACHE
        if include_counts:
            return cached_jobs, cached_counts
        return cached_jobs

    state = {}
    if SEEN_JOBS_FILE.is_file():
        try:
            _, state = read_job_state(SEEN_JOBS_FILE)
        except Exception as e:
            print(f"Error loading seen jobs: {e}", file=sys.stderr)
            raise ValueError('Saved postings could not be read. The job-history file needs repair; it has not been replaced.') from e

    tracker_apps = load_tracker()
    unique_entries = {id(e): e for e in tracker_apps.values()}.values()
    tracker_by_comp = {}
    for t_val in unique_entries:
        t_comp = re.sub(r"[^a-z0-9]", "", (t_val.get("company") or "").lower())
        t_role = re.sub(r"[^a-z0-9]", "", clean_title(t_val.get("role") or "").lower())
        t_url = (t_val.get("source") or "").strip()
        t_m = re.search(r"(\d{6,})", t_url) if t_url else None
        t_jid = t_m.group(1) if t_m else None
        if t_comp:
            tracker_by_comp.setdefault(t_comp, []).append((t_role, t_jid, t_url, t_val))

    jobs = []
    hidden = {"date": 0, "repost": 0, "language": 0, "easy_apply": 0, "relevance": 0, "duplicates": 0, "dual_study": 0}

    for key, item in state.items():
        title = item.get("title", "")
        company = item.get("company", "")
        url = item.get("url", "")
        desc = item.get("description", "")

        # Check tracker match
        comp_norm = re.sub(r"[^a-z0-9]", "", company.lower())
        role_norm = re.sub(r"[^a-z0-9]", "", clean_title(title).lower())
        m = re.search(r"(\d{6,})", url)
        jid = m.group(1) if m else None

        app_info = (
            tracker_apps.get(f"{comp_norm}_{role_norm}")
            or (tracker_apps.get(f"id_{jid}") if jid else None)
            or tracker_apps.get(url)
        )
        if not app_info and comp_norm in tracker_by_comp:
            for t_role, t_jid, t_url, t_val in tracker_by_comp[comp_norm]:
                if (jid and t_jid and jid == t_jid) or (url and t_url and url == t_url):
                    app_info = t_val
                    break
                if t_role == role_norm or (t_role and role_norm and (t_role in role_norm or role_norm in t_role)):
                    app_info = t_val
                    break

        # Filter out opportunities (unless tracked in tracker_apps)
        if not app_info:
            if is_dual_study_posting(title, desc):
                hidden["dual_study"] += 1
                continue
            posted_str = item.get("posted_date")
            if not posted_str:
                hidden["date"] += 1
                continue
            try:
                posted_dt = date.fromisoformat(posted_str[:10])
                diff_days = (today - posted_dt).days
                if diff_days > 2 or diff_days < 0:
                    hidden["date"] += 1
                    continue
            except Exception:
                hidden["date"] += 1
                continue

            # Repost Gate
            time_ago = item.get("posted_time_ago")
            if (time_ago and is_reposted_or_stale(time_ago)) or is_reposted_or_stale(title) or is_reposted_or_stale(desc):
                hidden["repost"] += 1
                continue

            # Language Gate
            if requires_german_c1(title) or requires_german_c1(desc):
                hidden["language"] += 1
                continue

            # LinkedIn Easy Apply Gate
            is_li = ("linkedin" in item.get("portal", "").lower()) or ("linkedin.com" in url.lower())
            if is_li and item.get("easy_apply") is True:
                hidden["easy_apply"] += 1
                continue

        category = display_category(title, desc)
        if category is None and not app_info:
            hidden["relevance"] += 1
            continue
        category = category or "Other"
        score, tier, tags = calculate_match_score(title, desc)

        status = app_info["status"] if app_info else item.get("status", "new")
        if app_info and app_info.get("fit_rating"):
            try:
                score = int(app_info["fit_rating"])
                tier = "Strong Fit" if score >= 75 else ("Good Fit" if score >= 60 else "Moderate Fit")
            except Exception:
                pass

        detected_cp = item.get("contact_person")
        if not detected_cp:
            try:
                from tools.generate_application import extract_contact_person
                detected_cp = extract_contact_person(item.get("description", ""), company, title)
            except Exception:
                detected_cp = ""

        contact_person = (app_info.get("contact_person") if app_info and app_info.get("contact_person") else None) or detected_cp or None

        p_date = item.get("posted_date") or item.get("first_seen")
        is_today = False
        is_yesterday = False
        if p_date:
            try:
                p_dt = date.fromisoformat(str(p_date)[:10])
                diff = (today - p_dt).days
                is_today = (diff == 0)
                is_yesterday = (diff == 1)
            except Exception:
                pass

        jobs.append({
            "key": key,
            "_description": desc,
            "location": item.get("location") or "",
            "title": title,
            "company": company,
            "clean_title": clean_title(title),
            "url": url,
            "category": category,
            "posted_date": p_date,
            "is_today": is_today,
            "is_yesterday": is_yesterday,
            "portal": item.get("portal") or "web",
            "score": score,
            "tier": tier,
            "tags": tags,
            "status": status,
            "is_applied": (app_info is not None) or (item.get("status") in ["applied", "drafted"]),
            "cv_file": app_info.get("cv_file") if app_info else None,
            "cover_letter_file": app_info.get("cover_letter_file") if app_info else None,
            "contact_person": contact_person,
            "easy_apply": item.get("easy_apply", False)
        })

    before_dedup = len(jobs)
    jobs = consolidate_jobs(jobs)
    hidden["duplicates"] = before_dedup - len(jobs)
    jobs.sort(key=lambda x: ((x.get("status") or "").lower() == "applied", -x["score"]))
    reasons = {"date": hidden["date"], "repost": hidden["repost"], "language": hidden["language"]}
    for reason in ("easy_apply", "relevance", "duplicates", "dual_study"):
        if hidden[reason]:
            reasons[reason] = hidden[reason]
    counts = {"stored_jobs": len(state), "hidden_jobs": sum(hidden.values()), "hidden_reasons": reasons}
    _ENRICHED_CACHE = (jobs, counts)
    _ENRICHED_CACHE_KEY = cache_key

    if include_counts:
        return jobs, counts
    return jobs


def serialize_tracker_updates(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        if urlparse(self.path).path in ('/api/tracker/update_status', '/api/tracker/update_contact'):
            with file_lock(TRACKER_FILE):
                return method(self, *args, **kwargs)
        return method(self, *args, **kwargs)
    return wrapped


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def valid_host(self):
        try:
            host = urlparse("http://" + self.headers.get("Host", "")).hostname
        except ValueError:
            host = None
        if host not in {"localhost", "127.0.0.1", "::1"}:
            self.send_error(HTTPStatus.FORBIDDEN, "Only localhost requests are allowed")
            return False
        return True

    def do_HEAD(self):
        self.send_error(HTTPStatus.METHOD_NOT_ALLOWED, "Use GET for public resources")

    def do_GET(self):
        if not self.valid_host():
            return
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path in ["/", "/index.html"]:
            self.serve_file(WEB_DIR / "index.html", "text/html")
            return
        elif path.startswith("/web/"):
            rel = path[5:]
            target = WEB_DIR / rel
            self.serve_file(target)
            return
        elif path == "/api/jobs":
            try:
                jobs = get_enriched_jobs()
            except ValueError as exc:
                self.send_json({'error': str(exc)}, status=503)
                return
            self.send_json(jobs)
            return
        elif path == "/api/tracker":
            apps = list(load_tracker().values())
            # Deduplicate by company+role
            seen_combos = set()
            unique_apps = []
            for a in apps:
                combo = (a.get("company"), a.get("role"))
                if combo not in seen_combos:
                    seen_combos.add(combo)
                    unique_apps.append(a)
            self.send_json(unique_apps)
            return
        elif path == "/api/stats":
            try:
                jobs, counts = get_enriched_jobs(include_counts=True)
            except ValueError as exc:
                self.send_json({'error': str(exc)}, status=503)
                return
            total = len(jobs)
            tracker = load_tracker()
            seen_combos = set()
            unique_tracker = []
            for a in tracker.values():
                combo = (a.get("company"), a.get("role"))
                if combo not in seen_combos:
                    seen_combos.add(combo)
                    unique_tracker.append(a)
            tracker_applied = sum(1 for a in unique_tracker if (a.get("status") or "").strip().lower() == "applied")
            tracker_drafted = sum(1 for a in unique_tracker if (a.get("status") or "").strip().lower() != "applied")
            applied = sum(1 for j in jobs if j["is_applied"])
            unapplied = sum(1 for j in jobs if not j["is_applied"])
            posted_today = sum(1 for j in jobs if j.get("is_today"))
            posted_yesterday = sum(1 for j in jobs if j.get("is_yesterday"))
            strong_fits = sum(1 for j in jobs if j["score"] >= 75)
            avg_score = round(sum(j["score"] for j in jobs) / total, 1) if total else 0
            stats = {
                "total_jobs": total,
                "today": str(date.today()),
                "posted_today": posted_today,
                "posted_yesterday": posted_yesterday,
                "unapplied_count": unapplied,
                **counts,
                "applied_count": len(unique_tracker),
                "tracker_applied": tracker_applied,
                "tracker_drafted": tracker_drafted,
                "strong_matches": strong_fits,
                "avg_score": avg_score,
                "categories": {
                    "Data Engineering": sum(1 for j in jobs if j["category"] == "Data Engineering"),
                    "Data Analytics & BI": sum(1 for j in jobs if j["category"] == "Data Analytics & BI"),
                    "AI / ML & GenAI": sum(1 for j in jobs if j["category"] == "AI / ML & GenAI"),
                    "Werkstudent & Intern": sum(1 for j in jobs if j["category"] == "Werkstudent & Intern")
                }
            }
            self.send_json(stats)
            return
        elif path.startswith(("/cv/", "/cover_letters/", "/documents/applications/")):
            target = ROOT / path.lstrip("/")
            if target.is_file() and target.suffix.lower() == ".pdf":
                self.serve_file(target, "application/pdf")
                return

        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    @serialize_tracker_updates
    def do_POST(self):
        if not self.valid_host():
            return
        parsed = urlparse(self.path)
        origin = self.headers.get("Origin")
        if origin and origin != f"http://{self.headers.get('Host')}":
            self.send_error(HTTPStatus.FORBIDDEN, "Cross-origin requests are not allowed")
            return
        if parsed.path == "/api/scrape":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            try:
                payload = json.loads(body)
            except Exception:
                payload = {}

            query = str(payload.get("query") or "").strip()
            location = payload.get("location", "Germany")
            limit = str(payload.get("limit", 10))
            jobage = str(payload.get("jobage", 2))
            portals = payload.get("portals")

            cmd = [sys.executable, str(ROOT / "tools" / "scrape.py"), "--all", "-l", location, "-n", limit, "--jobage", jobage]
            if query:
                cmd.extend(["-q", query])
            if portals:
                cmd.extend(["--portals", str(portals)])
            try:
                res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=3600)
                self.send_json({
                    "success": res.returncode == 0,
                    "stdout": res.stdout,
                    "warning": "Some searches were capped, unavailable or incomplete. See job_scraper/last_scrape_report.json." if "Coverage warning:" in res.stderr else "",
                    "stderr": res.stderr
                })
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        if parsed.path == "/api/analyze_jd":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            try:
                payload = json.loads(body)
            except Exception:
                payload = {}

            desc = payload.get("description", "").strip()
            comp = payload.get("company", "").strip()
            role = payload.get("title", "").strip()

            detected_comp = comp
            detected_role = role

            if not detected_comp and desc:
                m_comp = re.search(r"(?:company|unternehmen|arbeitgeber|firma|about|über|bei|join)\s*[:\-]?\s*([A-Za-z0-9&.\- ]{2,35})", desc, re.I)
                if m_comp:
                    cand = m_comp.group(1).strip()
                    if not any(w in cand.lower() for w in ["us", "uns", "the", "a", "an", "our", "ihr"]):
                        detected_comp = cand
                if not detected_comp:
                    m_legal = re.search(r"\b([A-Z][A-Za-z0-9&.\- ]{2,30}\s+(?:GmbH|AG|SE|KG|KGaA|GmbH & Co\.? KG|Inc\.|Corp\.))\b", desc)
                    if m_legal:
                        detected_comp = m_legal.group(1).strip()

            if not detected_role and desc:
                for line in desc.splitlines()[:6]:
                    cleaned = re.sub(r"^(?:role|position|titel|title|stelle|job)\s*[:\-]\s*", "", line.strip(), flags=re.I)
                    cleaned = clean_title(cleaned)
                    if cleaned and re.search(r'\b(?:engineer|analyst|developer|architect|scientist|manager|werkstudent\w*|intern(?:ship)?|praktik\w*)\b', cleaned, re.I):
                        detected_role = cleaned
                        break

            import tools.generate_application as ga
            kw = ga.extract_job_keywords(desc, detected_role)
            top5 = kw.get("top_5", [])
            all_kw = kw.get("all_labels", [])
            loc = ga.extract_company_location({}, desc, detected_comp)
            contact = ga.extract_contact_person(desc, detected_comp, detected_role)

            t_low = f"{detected_role} {desc}".lower()
            if ga.is_student_role(detected_role, desc):
                category = "Werkstudent & Intern"
            elif any(x in t_low for x in ["ai", "machine learning", "ml", "genai", "deep learning", "llm", "rag", "agent"]):
                category = "AI / ML & GenAI"
            elif any(x in t_low for x in ["analyst", "analytics", "business intelligence", "bi", "power bi"]):
                category = "Data Analytics & BI"
            else:
                category = "Data Engineering"

            if category == "AI / ML & GenAI":
                headline = "Machine Learning Engineer" if re.search(r"machine\s+learning|\bml\b", detected_role, re.I) else "AI Engineer"
            elif category == "Data Analytics & BI":
                headline = "Data Analyst"
            else:
                headline = "Data Engineer"

            c1_req = requires_german_c1(desc)
            has_dg = bool(re.search(r"\b(data\s*governance|daten-?governance|data\s*lineage|metadata\s*management|data\s*profiling|data\s*catalog|datenqualitätsmanagement|governance\s*frameworks?)\b", desc, re.I))

            score = min(98, max(50, 50 + len(all_kw) * 5))

            self.send_json({
                "success": True,
                "detected_company": detected_comp,
                "detected_title": detected_role,
                "detected_location": loc,
                "detected_contact_person": contact,
                "category": category,
                "headline": headline,
                "keywords": kw,
                "top_5": top5,
                "all_keywords_count": len(all_kw),
                "fit_score": score,
                "german_gate": {
                    "requires_c1_c2": c1_req,
                    "warning": "Minimum German C1/C2 or verhandlungssicher requirement detected. Workspace profile rules designate Yashwanth communicates in English (C1) and intermediate German (B2)." if c1_req else None
                },
                "data_governance": {
                    "detected": has_dg,
                    "seminar_highlight": "Academic Seminar Active: University of Koblenz 'Data Governance Quality Assurance' will be featured in CV Education & Cover Letter." if has_dg else None
                },
                "word_count": len(desc.split()),
                "char_count": len(desc)
            })
            return

        if parsed.path == "/api/generate":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            try:
                payload = json.loads(body)
            except Exception:
                payload = {}

            job_key = payload.get("key", "").strip()
            company = payload.get("company", "").strip()
            title = payload.get("title", "").strip()
            url = payload.get("url", "").strip()
            desc = payload.get("description", "").strip()
            location = payload.get("location", "").strip()
            contact_person = payload.get("contact_person", "").strip()
            is_custom = bool(payload.get("is_custom", False) or not job_key)

            job_data = {}
            if job_key and SEEN_JOBS_FILE.is_file():
                try:
                    with SEEN_JOBS_FILE.open(encoding="utf-8") as f:
                        seen = json.load(f).get("seen", {})
                        if job_key in seen:
                            job_data = dict(seen[job_key])
                            job_data["key"] = job_key
                except Exception:
                    pass

            if not job_data:
                # If company or title are missing, attempt auto-extraction from description
                if not company and desc:
                    m_comp = re.search(r"(?:company|unternehmen|arbeitgeber|firma|about|über|bei|join)\s*[:\-]?\s*([A-Za-z0-9&.\- ]{2,35})", desc, re.I)
                    if m_comp:
                        cand = m_comp.group(1).strip()
                        if not any(w in cand.lower() for w in ["us", "uns", "the", "a", "an", "our", "ihr"]):
                            company = cand
                if not title and desc:
                    for line in desc.splitlines()[:6]:
                        cleaned = re.sub(r"^(?:role|position|titel|title|stelle|job)\s*[:\-]\s*", "", line.strip(), flags=re.I)
                        cleaned = clean_title(cleaned)
                        if cleaned and re.search(r'\b(?:engineer|analyst|developer|architect|scientist|manager|werkstudent\w*|intern(?:ship)?|praktik\w*)\b', cleaned, re.I):
                            title = cleaned
                            break

                job_data = {
                    "key": job_key,
                    "company": company or "Company",
                    "title": title or "Data Engineer",
                    "url": url,
                    "description": desc,
                    "location": location,
                    "contact_person": contact_person,
                    "is_custom": is_custom
                }
            else:
                if desc and not job_data.get("description"):
                    job_data["description"] = desc
                if location and not job_data.get("location"):
                    job_data["location"] = location
                if contact_person and not job_data.get("contact_person"):
                    job_data["contact_person"] = contact_person

            if not job_data.get("company") or not job_data.get("title"):
                self.send_json({"success": False, "error": "Missing company or title for generation. Please provide Company and Role."}, status=400)
                return

            try:
                import tools.generate_application
                res = tools.generate_application.generate_for_job(job_data)
                self.send_json(res)
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json({"success": False, "error": str(e)}, status=500)
            return
        elif parsed.path == "/api/tracker/update_contact":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            try:
                payload = json.loads(body)
            except Exception:
                payload = {}

            company = payload.get("company", "").strip()
            role = payload.get("role", "").strip()
            contact_person = payload.get("contact_person", "").strip()

            if not company or not role:
                self.send_json({"success": False, "error": "Missing company or role"}, status=400)
                return

            updated = False
            rows = []
            headers = []
            if TRACKER_FILE.is_file():
                with TRACKER_FILE.open(encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    headers = list(reader.fieldnames or [])
                    for r in reader:
                        if (r.get("company") or "").strip().lower() == company.lower() and \
                           clean_title(r.get("role") or "").lower() == clean_title(role).lower():
                            r["contact_person"] = contact_person
                            updated = True
                        rows.append(r)

            if updated and headers:
                atomic_write_csv(TRACKER_FILE, headers, rows)

            self.send_json({"success": True, "company": company, "role": role, "contact_person": contact_person})
            return
        elif parsed.path == "/api/tracker/update_status":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            try:
                payload = json.loads(body)
            except Exception:
                payload = {}

            company = payload.get("company", "").strip()
            role = payload.get("role", "").strip()
            status_val = payload.get("status", "").strip().lower()
            source_url = payload.get("url", "").strip()
            job_key = payload.get("key", "").strip()

            if not company or not role or not status_val:
                self.send_json({"success": False, "error": "Missing company, role, or status"}, status=400)
                return

            updated = False
            rows = []
            headers = []
            req_comp_clean = re.sub(r"[^a-z0-9]", "", company.lower())
            req_role_clean = re.sub(r"[^a-z0-9]", "", clean_title(role).lower())
            req_m = re.search(r"(\d{6,})", source_url) if source_url else None
            req_jid = req_m.group(1) if req_m else None

            if TRACKER_FILE.is_file():
                with TRACKER_FILE.open(encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    headers = list(reader.fieldnames or [])
                    for r in reader:
                        r_comp_raw = (r.get("company") or "").strip().lower()
                        r_comp_clean = re.sub(r"[^a-z0-9]", "", r_comp_raw)
                        r_role_raw = (r.get("role") or "").strip().lower()
                        r_role_clean = re.sub(r"[^a-z0-9]", "", clean_title(r.get("role") or "").lower())
                        r_source = (r.get("source") or "").strip()
                        r_m = re.search(r"(\d{6,})", r_source) if r_source else None
                        r_jid = r_m.group(1) if r_m else None

                        comp_match = (
                            r_comp_raw == company.lower()
                            or r_comp_clean == req_comp_clean
                            or (req_comp_clean and (req_comp_clean in r_comp_clean or r_comp_clean in req_comp_clean))
                        )
                        role_match = (
                            r_role_raw == role.lower()
                            or r_role_clean == req_role_clean
                            or (req_role_clean and (req_role_clean in r_role_clean or r_role_clean in req_role_clean))
                        )
                        url_match = bool(source_url and r_source and (source_url == r_source or (req_jid and r_jid and req_jid == r_jid)))

                        if (comp_match and role_match) or url_match:
                            r["status"] = status_val
                            if status_val == "applied" and not r.get("date"):
                                r["date"] = date.today().isoformat()
                            if source_url and not r.get("source"):
                                r["source"] = source_url
                            updated = True
                        rows.append(r)

            # If not yet tracked in job_search_tracker.csv, create entry
            if not updated:
                canonical_headers = [
                    "date", "company", "sector", "role", "role_type", "channel",
                    "status", "contact_person", "fit_rating", "notes",
                    "cv_file", "cover_letter_file", "source", "deadline"
                ]
                if not headers:
                    headers = list(canonical_headers)
                else:
                    for h in canonical_headers:
                        if h not in headers:
                            headers.append(h)

                contact_p = ""
                if SEEN_JOBS_FILE.is_file():
                    try:
                        seen_data = json.loads(SEEN_JOBS_FILE.read_text(encoding="utf-8"))
                        seen_dict = seen_data.get("seen", seen_data)
                        matched_job = seen_dict.get(job_key)
                        if not matched_job:
                            for sk, sv in seen_dict.items():
                                sc = re.sub(r"[^a-z0-9]", "", (sv.get("company") or "").lower())
                                sr = re.sub(r"[^a-z0-9]", "", clean_title(sv.get("title") or "").lower())
                                if (sc == req_comp_clean or req_comp_clean in sc) and (sr == req_role_clean or req_role_clean in sr):
                                    matched_job = sv
                                    break
                        if matched_job:
                            contact_p = matched_job.get("contact_person", "")
                            if not source_url:
                                source_url = matched_job.get("url", "")
                    except Exception:
                        pass

                new_row = {
                    "date": date.today().isoformat() if status_val == "applied" else "",
                    "company": company,
                    "sector": "Technology",
                    "role": clean_title(role),
                    "role_type": "Full-time",
                    "channel": "direct",
                    "status": status_val,
                    "contact_person": contact_p,
                    "fit_rating": "85",
                    "notes": "Marked applied directly via dashboard",
                    "cv_file": "",
                    "cover_letter_file": "",
                    "source": source_url,
                    "deadline": ""
                }
                rows.append(new_row)
                updated = True

            if updated and headers:
                atomic_write_csv(TRACKER_FILE, headers, rows)

            # Sync with seen_jobs.json if entry exists
            if SEEN_JOBS_FILE.is_file():
                try:
                    def sync_status(seen_dict):
                        seen_updated = False
                        for k, item in seen_dict.items():
                            c_clean = re.sub(r"[^a-z0-9]", "", (item.get("company") or "").strip().lower())
                            t_clean = re.sub(r"[^a-z0-9]", "", clean_title(item.get("title") or "").lower())
                            i_url = (item.get("url") or "").strip()
                            if (c_clean == req_comp_clean or req_comp_clean in c_clean or c_clean in req_comp_clean) and \
                               (t_clean == req_role_clean or req_role_clean in t_clean or t_clean in req_role_clean) or \
                               (source_url and i_url and source_url == i_url) or (job_key and k == job_key):
                                item["status"] = status_val
                                seen_updated = True
                        return seen_updated
                    update_job_state(SEEN_JOBS_FILE, sync_status)
                except Exception as e:
                    print(f"Error updating seen_jobs.json status: {e}", file=sys.stderr)

            self.send_json({
                "success": True,
                "company": company,
                "role": role,
                "status": status_val,
                "is_applied": status_val == "applied"
            })
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    def serve_file(self, path: Path, content_type: str = None):
        # Resolve before checking containment, including symlink targets.
        path = path.resolve()
        public_web = { ROOT.resolve() / "web" / name for name in ("index.html", "styles.css", "app.js") }
        document_roots = [ROOT.resolve() / "cv", ROOT.resolve() / "cover_letters", ROOT.resolve() / "documents/applications"]
        allowed_pdf = path.suffix.lower() == ".pdf" and any(
            path.is_relative_to(directory) for directory in document_roots)
        if path not in public_web and not allowed_pdf:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, f"File {path.name} not found")
            return
        if not content_type:
            content_type, _ = mimetypes.guess_type(str(path))
            content_type = content_type or "application/octet-stream"

        try:
            content = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            try:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))
            except Exception:
                pass

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; frame-src 'self'; object-src 'self'; base-uri 'none'; frame-ancestors 'self'")
        super().end_headers()

    def send_json(self, data, status=200):
        try:
            body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            try:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))
            except Exception:
                pass


def run_server(port=8000):
    server = ThreadingHTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"\n==================================================")
    print(f"🚀 AI Job Search Dashboard running at:")
    print(f"👉 http://localhost:{port}")
    print(f"==================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard server...")
        server.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
