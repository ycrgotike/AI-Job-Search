#!/usr/bin/env python3
"""CLI Job Scraper for ai-job-search workspace.

Runs installed portal CLIs (.agents/skills/linkedin-search, freehire-search),
deduplicates against job_search_tracker.csv and job_scraper/seen_jobs.json,
and updates seen_jobs.json with newly found positions.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from functools import lru_cache
import argparse
import os
import time
import fcntl
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.job_key import make_key
from tools.rank_state import tracker_pairs, norm

SEEN_JOBS_FILE = ROOT / "job_scraper" / "seen_jobs.json"
TRACKER_FILE = ROOT / "job_search_tracker.csv"


def load_seen_jobs():
    if not SEEN_JOBS_FILE.is_file():
        return {"seen": {}}
    try:
        data = json.loads(SEEN_JOBS_FILE.read_text(encoding="utf-8"))
        if "seen" not in data:
            data = {"seen": data}
        return data
    except Exception as e:
        print(f"Warning: Could not parse {SEEN_JOBS_FILE}: {e}", file=sys.stderr)
        return {"seen": {}}


def save_seen_jobs(data):
    SEEN_JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = SEEN_JOBS_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(SEEN_JOBS_FILE)


SEARCH_AUDIT = []
AUDIT_LOCK = Lock()
AUDIT_FILE = ROOT / "job_scraper" / "last_scrape_report.json"


def audit_search(entry):
    with AUDIT_LOCK:
        SEARCH_AUDIT.append(entry)
        AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = AUDIT_FILE.with_suffix('.tmp')
        tmp.write_text(json.dumps(SEARCH_AUDIT, indent=2) + '\n')
        tmp.replace(AUDIT_FILE)
    if entry.get('warning'):
        print(f"Coverage warning: {entry['portal']} / {entry['query']}: {entry['warning']}", file=sys.stderr)


def search_portal(cmd, portal, query, limit):
    """Bounded pagination and retries; retain successful pages after a later failure."""
    started = time.monotonic()
    items, seen = [], set()
    warning = ''
    # XING's adapter does not implement page navigation; never pretend it does.
    max_pages = 1 if portal in ('xing', 'arbeitsagentur') else 5
    for page in range(1, max_pages + 1):
        page_cmd = cmd + (['--page', str(page)] if page > 1 else [])
        data = None
        for attempt in range(2):
            try:
                result = subprocess.run(page_cmd, capture_output=True, text=True, check=True, timeout=120)
                data = json.loads(result.stdout)
                if not isinstance(data.get('results'), list):
                    raise ValueError('Portal returned no valid results array')
                break
            except Exception as exc:
                warning = str(exc)
                if attempt == 0:
                    time.sleep(1)
        if data is None:
            break
        warning = ''
        rows = data['results']
        added = 0
        for row in rows:
            key = row.get('url') or row.get('id') or json.dumps(row, sort_keys=True)
            if key not in seen:
                seen.add(key); items.append(row); added += 1
        if len(items) >= limit:
            warning = 'Result cap reached; additional matching listings may exist.'
            break
        if portal == 'arbeitsagentur':
            if data.get('meta', {}).get('truncated'):
                warning = 'Portal page cap reached; additional matching listings may exist.'
            break
        if portal == 'xing':
            warning = 'Only the first page is supported by the XING adapter; coverage is limited.'
            break
        if not rows:
            break
        if not added:
            warning = 'Portal repeated a page; stopped to avoid a pagination loop.'
            break
        if page == max_pages:
            warning = 'Page cap reached; coverage may be incomplete.'
    audit_search({'portal': portal, 'query': query, 'fetched': len(items[:limit]), 'pages': page, 'elapsed_seconds': round(time.monotonic() - started, 3), 'warning': warning})
    return {'results': items[:limit]}


def run_linkedin_search(query: str, location: str, limit: int, jobage: int = 2):
    cli_path = ROOT / ".agents" / "skills" / "linkedin-search" / "cli" / "src" / "cli.ts"
    if not cli_path.is_file():
        audit_search({"portal": "linkedin", "query": query, "fetched": 0, "warning": "CLI missing"})
        return []
    cmd = [
        "bun", "run", str(cli_path),
        "search",
        "-q", query,
        "-l", location,
        "--jobage", str(jobage),
        "--limit", str(limit),
        "--format", "json"
    ]
    try:
        data = search_portal(cmd, "linkedin", query, limit)
        results = []
        for item in data.get("results", []):
            raw_date = item.get("date") or item.get("posted_date")
            results.append({
                "title": item.get("title", "").strip(),
                "company": item.get("company", "").strip(),
                "url": item.get("url", "").strip(),
                "posted_date": raw_date.split("T")[0] if raw_date else None,
                "portal": "linkedin-search"
            })
        return results
    except Exception as e:
        print(f"LinkedIn search warning: {e}", file=sys.stderr)
        return []


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


def requires_german_c1(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    for pat in GERMAN_C1_PATTERNS:
        if re.search(pat, lower):
            return True
    return False


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


@lru_cache(maxsize=2048)
def fetch_linkedin_details(id_or_url: str):
    cli_path = ROOT / ".agents" / "skills" / "linkedin-search" / "cli" / "src" / "cli.ts"
    if not cli_path.is_file():
        return "", True, None, False
    m = re.search(r"(\d{6,})", id_or_url)
    jid = m.group(1) if m else id_or_url
    cmd = ["bun", "run", str(cli_path), "detail", jid, "--format", "json"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            desc = data.get("description", "") or ""
            is_fresh = data.get("isFresh", True)
            repost = data.get("repostDetected", False)
            time_ago = data.get("postedTimeAgo")
            easy_apply = data.get("easyApply", False)
            return desc, (is_fresh and not repost), time_ago, easy_apply
    except Exception:
        pass
    return "", True, None, False


def run_freehire_search(query: str, country: str, limit: int, jobage: int = 2):
    cli_path = ROOT / ".agents" / "skills" / "freehire-search" / "cli" / "src" / "cli.ts"
    if not cli_path.is_file():
        audit_search({"portal": "freehire", "query": query, "fetched": 0, "warning": "CLI missing"})
        return []
    cmd = [
        "bun", "run", str(cli_path),
        "search",
        "-q", query,
        "--country", country,
        "--jobage", str(jobage),
        "--limit", str(limit),
        "--format", "json"
    ]
    try:
        data = search_portal(cmd, "freehire", query, limit)
        results = []
        for item in data.get("results", []):
            raw_date = item.get("date") or item.get("posted_date")
            results.append({
                "title": item.get("title", "").strip(),
                "company": item.get("company", "").strip(),
                "url": item.get("url", "").strip(),
                "posted_date": raw_date.split("T")[0] if raw_date else None,
                "description": item.get("description", "").strip(),
                "portal": "freehire-search"
            })
        return results
    except Exception as e:
        print(f"FreeHire search warning: {e}", file=sys.stderr)
        return []


def run_arbeitsagentur_search(query: str, location: str, limit: int, jobage: int = 2):
    cli_path = ROOT / ".agents" / "skills" / "arbeitsagentur-search" / "cli" / "src" / "cli.ts"
    if not cli_path.is_file():
        audit_search({"portal": "arbeitsagentur", "query": query, "fetched": 0, "warning": "CLI missing"})
        return []
    loc = "Deutschland" if not location or location.lower() in ["germany", "deutschland", "de"] else location
    cmd = [
        "bun", "run", str(cli_path),
        "search",
        "-q", query,
        "-l", loc,
        "--jobage", str(jobage),
        "--limit", str(limit),
        "--format", "json"
    ]
    try:
        data = search_portal(cmd, "arbeitsagentur", query, limit)
        results = []
        for item in data.get("results", []):
            raw_date = item.get("date") or item.get("posted_date")
            results.append({
                "id": item.get("id"),
                "title": (item.get("title") or "").strip(),
                "company": (item.get("company") or "").strip(),
                "url": (item.get("url") or "").strip(),
                "posted_date": raw_date.split("T")[0] if raw_date else None,
                "portal": "arbeitsagentur-search"
            })
        return results
    except Exception as e:
        print(f"Arbeitsagentur search warning: {e}", file=sys.stderr)
        return []


@lru_cache(maxsize=2048)
def fetch_arbeitsagentur_description(refnr_or_url: str) -> str:
    cli_path = ROOT / ".agents" / "skills" / "arbeitsagentur-search" / "cli" / "src" / "cli.ts"
    if not cli_path.is_file():
        return ""
    cmd = ["bun", "run", str(cli_path), "detail", refnr_or_url, "--format", "json"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            return data.get("description", "") or ""
    except Exception:
        pass
    return ""


def run_stepstone_search(query: str, location: str, limit: int, jobage: int = 2):
    cli_path = ROOT / ".agents" / "skills" / "stepstone-search" / "cli" / "src" / "cli.ts"
    if not cli_path.is_file():
        audit_search({"portal": "stepstone", "query": query, "fetched": 0, "warning": "CLI missing"})
        return []
    loc = "Deutschland" if not location or location.lower() in ["germany", "deutschland", "de"] else location
    cmd = [
        "bun", "run", str(cli_path),
        "search",
        "-q", query,
        "-l", loc,
        "--jobage", str(jobage),
        "--limit", str(limit),
        "--format", "json"
    ]
    try:
        data = search_portal(cmd, "stepstone", query, limit)
        results = []
        for item in data.get("results", []):
            raw_date = item.get("date") or item.get("posted_date")
            results.append({
                "title": (item.get("title") or "").strip(),
                "company": (item.get("company") or "").strip(),
                "url": (item.get("url") or "").strip(),
                "posted_date": raw_date.split("T")[0] if raw_date else None,
                "description": (item.get("description") or "").strip(),
                "portal": "stepstone-search"
            })
        return results
    except Exception as e:
        print(f"StepStone search warning: {e}", file=sys.stderr)
        return []


@lru_cache(maxsize=2048)
def fetch_stepstone_description(url: str) -> str:
    cli_path = ROOT / ".agents" / "skills" / "stepstone-search" / "cli" / "src" / "cli.ts"
    if not cli_path.is_file():
        return ""
    cmd = ["bun", "run", str(cli_path), "detail", url, "--format", "json"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            return data.get("description", "") or ""
    except Exception:
        pass
    return ""


def run_xing_search(query: str, location: str, limit: int, jobage: int = 2):
    cli_path = ROOT / ".agents" / "skills" / "xing-search" / "cli" / "src" / "cli.ts"
    if not cli_path.is_file():
        audit_search({"portal": "xing", "query": query, "fetched": 0, "warning": "CLI missing"})
        return []
    loc = "Deutschland" if not location or location.lower() in ["germany", "deutschland", "de"] else location
    cmd = [
        "bun", "run", str(cli_path),
        "search",
        "-q", query,
        "-l", loc,
        "--jobage", str(jobage),
        "--limit", str(limit),
        "--format", "json"
    ]
    try:
        data = search_portal(cmd, "xing", query, limit)
        results = []
        for item in data.get("results", []):
            raw_date = item.get("date") or item.get("posted_date")
            results.append({
                "title": (item.get("title") or "").strip(),
                "company": (item.get("company") or "").strip(),
                "url": (item.get("url") or "").strip(),
                "posted_date": raw_date.split("T")[0] if raw_date else None,
                "description": (item.get("description") or "").strip(),
                "portal": "xing-search"
            })
        return results
    except Exception as e:
        print(f"XING search warning: {e}", file=sys.stderr)
        return []


@lru_cache(maxsize=2048)
def fetch_xing_description(url: str) -> str:
    cli_path = ROOT / ".agents" / "skills" / "xing-search" / "cli" / "src" / "cli.ts"
    if not cli_path.is_file():
        return ""
    cmd = ["bun", "run", str(cli_path), "detail", url, "--format", "json"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            return data.get("description", "") or ""
    except Exception:
        pass
    return ""


STUDENT_QUERIES = [
    "Werkstudent Data",
    "Werkstudent Data Science",
    "Werkstudent Data Engineer",
    "Werkstudent Data Analyst",
    "Praktikum Data",
    "Master Thesis Artificial Intelligence",
    "Masterarbeit KI",
    "Master Thesis Data Science",
    "Abschlussarbeit Datenanalyse",
    "Working Student AI",
    "Praktikum Künstliche Intelligenz",
    "Working Student Data Analytics",
    "Working Student Data Engineer",
]

CORE_QUERIES = [
    "Data Engineer",
    "Data Analyst",
    "Data Scientist",
    "AI Engineer",
    "Machine Learning Engineer",
    "Business Intelligence Analyst",
    "Business Analyst",
    "Analytics Engineer",
    "Artificial Intelligence",
    "ML Engineer",
    "KI",
    "KI Engineer",
    "Künstliche Intelligenz",
    "Data Management",
    "Datenmanagement",
    "Business Intelligence",
    "BI Analyst",
    "BI Entwickler",
    "Datenanalyse",
    "Data Science",
    "MLOps",
    "GenAI",
]


def search_queries(query=None, student=False, include_defaults=False):
    """Explicit CLI queries stay focused; dashboard queries extend the default suite."""
    extra = (query or '').strip()
    base = STUDENT_QUERIES if student else CORE_QUERIES + STUDENT_QUERIES
    queries = (base + ([extra] if extra else [])) if include_defaults or not extra else [extra]
    seen = set()
    return [q for q in queries if not (q.casefold() in seen or seen.add(q.casefold()))]


def scrape_query(query: str, location: str, limit: int, jobage: int, applied_pairs, seen, enabled_portals=None):
    if enabled_portals is None:
        enabled_portals = {"linkedin", "freehire", "arbeitsagentur", "stepstone", "xing"}

    print(f"\n🔍 Searching for '{query}' in '{location}' (max {jobage} days old)...")
    all_raw = []

    searches = [
        ('linkedin', run_linkedin_search, location),
        ('freehire', run_freehire_search, 'DE'),
        ('arbeitsagentur', run_arbeitsagentur_search, location),
        ('stepstone', run_stepstone_search, location),
        ('xing', run_xing_search, location),
    ]
    # Queries remain sequential, so no portal gets concurrent requests from this run.
    # Collect in the original order to preserve deterministic duplicate precedence.
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = [pool.submit(fn, query, loc, limit, jobage=jobage)
                   for name, fn, loc in searches if name in enabled_portals]
        for future in pending:
            all_raw.extend(future.result())

    new_count = 0
    skipped_tracker = 0
    skipped_seen = 0
    skipped_old = 0
    skipped_german_c1 = 0
    skipped_easy_apply = 0

    print(f"📥 Fetched {len(all_raw)} total candidates across portals.")

    today = date.today()
    for job in all_raw:
        title = job.get("title")
        company = job.get("company")
        url = job.get("url")
        portal = job.get("portal")

        if not title or not company:
            continue

        # Skip known jobs before any detail network request.
        pair = (norm(company), norm(title))
        if pair in applied_pairs:
            skipped_tracker += 1
            continue

        key = make_key(company=company, title=title, url=url)
        if key in seen:
            skipped_seen += 1
            continue

        # Strict recency filter: discard postings older than jobage days or missing date
        posted_str = job.get("posted_date")
        if not posted_str:
            skipped_old += 1
            continue
        try:
            posted_dt = date.fromisoformat(posted_str[:10])
            diff_days = (today - posted_dt).days
            if diff_days > jobage or diff_days < 0:
                skipped_old += 1
                continue
        except Exception:
            skipped_old += 1
            continue

        # Language Gate: Exclude minimum German C1/C2 / verhandlungssicher requirements
        if requires_german_c1(title):
            skipped_german_c1 += 1
            continue

        desc = job.get("description", "")
        posted_time_ago = None
        easy_apply = False
        if not desc and url:
            if portal == "linkedin-search":
                desc, is_fresh, time_ago, easy_apply = fetch_linkedin_details(url)
                posted_time_ago = time_ago
                if not is_fresh:
                    skipped_old += 1
                    print(f"  ⏰ [SKIPPED - Reposted/Stale LinkedIn Listing ({time_ago})] {company} — {title}")
                    continue
                if easy_apply:
                    skipped_easy_apply += 1
                    print(f"  ⚡ [SKIPPED - LinkedIn Easy Apply] {company} — {title}")
                    continue
            elif portal == "arbeitsagentur-search":
                desc = fetch_arbeitsagentur_description(url)
            elif portal == "stepstone-search":
                desc = fetch_stepstone_description(url)
            elif portal == "xing-search":
                desc = fetch_xing_description(url)
            job["description"] = desc

        # Repost Detection: Discard postings containing repost markers or relative stale dates
        if is_reposted_or_stale(title) or is_reposted_or_stale(desc):
            skipped_old += 1
            print(f"  ⏰ [SKIPPED - Repost marker detected in posting] {company} — {title}")
            continue

        if requires_german_c1(desc):
            skipped_german_c1 += 1
            print(f"  🇩🇪 [SKIPPED - German C1/C2 required] {company} — {title}")
            continue

        seen[key] = {
            "title": title,
            "company": company,
            "url": url,
            "first_seen": str(date.today()),
            "posted_date": job.get("posted_date"),
            "posted_time_ago": posted_time_ago,
            "deadline": None,
            "fit": "high",
            "status": "new",
            "portal": portal,
            "source": "cli",
            "description": desc,
            "easy_apply": easy_apply
        }
        new_count += 1
        print(f"  ✨ [NEW] ({portal}) {company} — {title}")
        print(f"     URL: {url}")

    return new_count, skipped_seen, skipped_tracker, skipped_old, skipped_german_c1, skipped_easy_apply


def main():
    parser = argparse.ArgumentParser(description="Scrape jobs using installed portal CLIs")
    parser.add_argument("-q", "--query", default=None, help="Job query keyword (default: runs core + student suites)")
    parser.add_argument("-l", "--location", default="Germany", help="Location (default: 'Germany')")
    parser.add_argument("-n", "--limit", type=int, default=10, help="Max results per portal per query (default: 10)")
    parser.add_argument("--jobage", type=int, default=2, help="Max age of job postings in days (default: 2)")
    parser.add_argument("--student", "--werkstudent", action="store_true", help="Scrape only Werkstudent & Praktikum positions")
    parser.add_argument("--all", action="store_true", help="Search the default role suite plus any supplied query")
    parser.add_argument("--portals", default="all", help="Comma-separated portals to scrape: linkedin, freehire, arbeitsagentur, stepstone, xing (default: all)")
    args = parser.parse_args()

    if not 0 <= args.jobage <= 2 or args.limit < 1:
        parser.error("Recency must be 0–2 days and limit must be positive")
    ROOT.joinpath("job_scraper").mkdir(exist_ok=True)
    lock = ROOT.joinpath("job_scraper/scrape.lock").open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error("A scrape is already running; wait for it to finish")
    SEARCH_AUDIT.clear()
    applied_pairs = tracker_pairs(TRACKER_FILE)
    state = load_seen_jobs()
    seen = state["seen"]

    if args.portals == "all":
        enabled_portals = {"linkedin", "freehire", "arbeitsagentur", "stepstone", "xing"}
    else:
        enabled_portals = set(p.strip().lower() for p in args.portals.split(","))

    queries = search_queries(args.query, args.student, args.all)
    print(f"Searching {len(queries)} role queries across {len(enabled_portals)} portals.")

    total_new = 0
    total_skipped_seen = 0
    total_skipped_tracker = 0
    total_skipped_old = 0
    total_skipped_c1 = 0
    total_skipped_easy_apply = 0

    for q in queries:
        n, s, t, o, c, ea = scrape_query(q, args.location, args.limit, args.jobage, applied_pairs, seen, enabled_portals=enabled_portals)
        total_new += n
        total_skipped_seen += s
        total_skipped_tracker += t
        total_skipped_old += o
        total_skipped_c1 += c
        total_skipped_easy_apply += ea
        save_seen_jobs(state)

    save_seen_jobs(state)
    print(f"Coverage report: {AUDIT_FILE}; {sum(bool(x.get('warning')) for x in SEARCH_AUDIT)} searches need attention")

    print("\n" + "=" * 50)
    print("Summary:")
    print(f"  ✨ Added new:                 {total_new}")
    print(f"  🔄 Already seen:              {total_skipped_seen}")
    print(f"  📝 Skipped (in tracker):       {total_skipped_tracker}")
    print(f"  ⏰ Skipped (> {args.jobage} days old):     {total_skipped_old}")
    print(f"  🇩🇪 Skipped (German C1 required): {total_skipped_c1}")
    print(f"  ⚡ Skipped (LinkedIn Easy Apply): {total_skipped_easy_apply}")
    print(f"  📁 Total seen pool:           {len(seen)}")
    print("=" * 50)


if __name__ == "__main__":
    main()
