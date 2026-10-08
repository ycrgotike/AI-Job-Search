# Search Queries for Job Scraper

## Installed portal CLIs (primary for `/scrape`)

`/scrape` discovers every portal skill under `.agents/skills/*/SKILL.md` and runs its CLI first. Installed portal CLIs include:
- `linkedin-search`: LinkedIn job search across Germany / global
- `freehire-search`: Tech-focused aggregator API
- `arbeitsagentur-search`: Official Bundesagentur für Arbeit (BA) Jobsuche REST API across all of Germany
- `stepstone-search`: StepStone Germany (`stepstone.de`) with verified publication dates & Schema.org metadata
- `xing-search`: XING DACH (`xing.com` / `xing.de`) professional network job postings

The `site:` query templates in this file are the **WebSearch fallback** — for portals without a CLI, company career pages, or when a CLI fails.

**Language scope:** German & English are declared languages. Both English and German job postings across Germany are target candidates (excluding roles requiring minimum German C1/C2).

## Search Sites & Portals

Primary (German tech & general job boards):
- **arbeitsagentur.de** - Official German Federal Employment Agency portal (`arbeitsagentur-search` CLI)
- **stepstone.de** - Major German job portal for engineering and analytics (`stepstone-search` CLI)
- **xing.de / xing.com** - Leading professional network in Germany/DACH (`xing-search` CLI)
- **linkedin.com/jobs** - LinkedIn job listings (`linkedin-search` CLI)
- **freehire.me** - Multi-market aggregator for tech & engineering roles (`freehire-search` CLI)
- **indeed.de** - General board covering full-time and Werkstudent positions in Germany

Secondary (company career pages via Google):
- Direct Google searches with `site:` filters for enterprise and high-growth data teams

## Dashboard default searches

The dashboard always runs the core and student suites defined in `tools/scrape.py` (`CORE_QUERIES` and `STUDENT_QUERIES`). They include English/German data, AI/ML, KI, data management and BI variants. The optional query box adds a search instead of replacing these defaults; duplicate terms are searched once. The result limit applies per portal per search term. Existing recency, language and job deduplication filters still apply. CLI `-q` remains a focused search; `--all -q` adds it to the suite.

## Query Categories

Queries are grouped by priority and tailored to Germany-wide data and AI roles across English and German.

### Priority 1: Data Engineering & Analytics (Core Focus)

These match your 5+ years of production experience in scalable ETL/ELT pipelines, cloud data warehouses, and BI.

```
site:stepstone.de "Data Engineer" Germany
site:stepstone.de "Data Analyst" Germany
site:stepstone.de "Azure Data Factory" OR "Databricks" Germany
site:linkedin.com/jobs "Data Engineer" Germany
site:linkedin.com/jobs "Data Analyst" Germany
site:linkedin.com/jobs "Power BI" DAX Germany
site:stepstone.de "BI Analyst" OR "Business Intelligence Analyst" Germany
```

### Priority 2: AI / ML & GenAI / Data Science

These match your advanced competencies in MLOps, LLMs, RAG architectures, and predictive modeling.

```
site:stepstone.de "AI Engineer" Germany
site:stepstone.de "Machine Learning Engineer" Germany
site:stepstone.de "Data Scientist" Germany
site:linkedin.com/jobs "GenAI" OR "LLM" OR "RAG" Germany
site:linkedin.com/jobs "MLOps" OR "Machine Learning Engineer" Germany
site:stepstone.de "Data Science" Python Germany
```

### Priority 3: Working Student & Trainee Positions (Werkstudent / Praktikum)

Roles aligned with current master's studies at University of Koblenz (expected graduation Sept 2027).

```
site:stepstone.de "Werkstudent Data Engineer" Germany
site:stepstone.de "Werkstudent Data Analyst" Germany
site:stepstone.de "Werkstudent Data Science" Germany
site:linkedin.com/jobs "Werkstudent" "Data" Germany
site:linkedin.com/jobs "Working Student Data Engineer" Germany
```

### Priority 4: Business Analytics & Solutions

Wider net for cross-functional data and business analytics positions.

```
site:stepstone.de "Business Analyst" Data Germany
site:linkedin.com/jobs "Analytics Engineer" Germany
site:stepstone.de "Analytics Consultant" Germany
```

## Location Filter

- **Primary Commute / Local**: Koblenz, Bonn, Cologne, Frankfurt am Main, Mainz, Wiesbaden
- **Willing to Relocate (Germany-wide)**: Berlin, Munich, Hamburg, Stuttgart, Düsseldorf, Nuremberg, Leipzig, and across Germany
- **Remote / Hybrid**: Germany-wide (proven 2 years remote/hybrid track record)
- **Too Far**: Strictly on-site roles outside Germany without remote flexibility

## Language Filter

- English: C1 (Fluent - full professional working proficiency)
- German: B2 (Intermediate - professional and conversational)
- Postings requiring English or German (up to B2) are accepted.
- **Strict Exclusion (German C1 Gate):** Postings requiring minimum German C1, C2, verhandlungssicher, or native German are strictly excluded from scraping. Postings requiring additional languages not declared (e.g. French, Spanish) are excluded by the Language Gate.

## Date Filter

Only include jobs posted within the last 2 days (max 2 days / 48 hours old), or with an application deadline that has not yet passed.

## Adapting Queries

When the user specifies a focus area (e.g. `/scrape genai` or `/scrape werkstudent`), prioritize queries from the matching category and run CLI search queries targeting Germany.

## Coverage safeguards

- Include thesis/Abschlussarbeit and AI student queries in the default suite.
- Retain the strict two-day cutoff; fetch a broader portal date bucket when needed and filter exact publication dates locally.
- Paginate supported adapters up to bounded limits. XING currently supports only its first page and must report limited coverage.
- Persist per-query/per-portal counts and failures in `job_scraper/last_scrape_report.json`. A capped or failed search is not exhaustive coverage.
- Save results after each query with atomic replacement; allow only one scraper process to write at a time.
- Retry transient search failures once; retain earlier successful pages. Dashboard warnings must expose incomplete coverage.
