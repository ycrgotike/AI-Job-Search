<p align="center">
  <img src="assets/mascot/pip_flight_loop.gif" alt="Pip, the courier bird" width="200">
</p>

# AI Job Search

*The intelligent, local-first job search and application engine for modern tech careers.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Bun](https://img.shields.io/badge/Bun-1.0%2B-black.svg)](https://bun.sh)
[![LaTeX](https://img.shields.io/badge/LaTeX-LuaLaTeX%20%7C%20XeLaTeX-green.svg)](https://tug.org/texlive/)

An AI-powered job application framework and localhost radar dashboard engineered for data professionals and software engineers. Powered by multi-agent architectures (**Claude Code**, **Google Antigravity**, **Gemini**, and **Codex**), it evaluates live postings across German and international job portals, dynamically tailors ATS-optimized ModernCVs, drafts evidence-grounded cover letters in LaTeX, and prepares you for technical interviews.

> **Note:** This is an independent open-source project and is not affiliated with, endorsed by, sponsored by, or maintained by Anthropic or Google. Claude Code, Google Antigravity, and Gemini are referenced only to describe the supported toolchains.
>
> This project has **no affiliated cryptocurrency, token, or paid sponsorship program**. Anything claiming otherwise is unauthorized and should be treated as a scam.

---

## About the Developer

I'm **Yashwanth Gotike**, a Data Engineer and Data Analyst currently pursuing my M.Sc. in Web and Data Science at the University of Koblenz, Germany. With over 5 years of professional engineering experience across production data pipelines (Python, SQL, Apache Spark, Azure Databricks, Azure Data Factory, AWS, Airflow), business intelligence (Power BI, DAX), and advanced GenAI / LLM architectures (RAG, agentic workflows, vector search), I expanded and customized this framework to run my own career search in Germany and across Europe.

I developed major extensions to adapt the original architecture for high-intent European and German data roles: adding custom portal scrapers (Bundesagentur für Arbeit, StepStone Germany, XING), building an interactive localhost dashboard, engineering intelligent German language and freshness gates, integrating Google Gemini/Antigravity LLM runtimes, and enforcing strict ATS-compliant LaTeX document generation standards.

* **GitHub:** [@ycrgotike](https://github.com/ycrgotike)
* **LinkedIn:** [Yashwanth Gotike](https://linkedin.com/in/ycrgotike)
* **Location:** Koblenz, Germany

---

## Key Features & New Developments

* 🚀 **Interactive Localhost Dashboard (`./app 8000` / `python3 server.py`):**
  A sleek, dark-mode web application running at [http://localhost:8000](http://localhost:8000). Features a live opportunity radar, fit scoring breakdown, portal filtering, PDF previewing for compiled ModernCVs and cover letters, application status tracking, and one-click scraping/generation.
* 🇩🇪 **German & DACH Job Portal Ecosystem:**
  Fully integrated, standalone CLI search skills under `.agents/skills/` tailored for the German and European job markets:
  * **`arbeitsagentur-search`** — Bundesagentur für Arbeit official job portal API.
  * **`stepstone-search`** — StepStone Germany live postings and detailed requisitions.
  * **`xing-search`** — XING professional network for Germany, Austria, and Switzerland.
  * **`linkedin-search`** — LinkedIn public guest API for country-agnostic listings.
  * **`freehire-search`** — Tech aggregator with structured skills and remote/hybrid facets.
* 🤖 **Multi-Agent & Gemini Integration:**
  Full support for Google Antigravity, Gemini CLI (`gemini-3.8-flash`), Claude Code, and Codex via unified thin-pointer specifications ([`AGENTS.md`](AGENTS.md), [`CLAUDE.md`](CLAUDE.md), [`GEMINI_SETUP.md`](GEMINI_SETUP.md)). Includes automated Gemini-powered responsibility planning, evidence grounding, and iterative quality audit loops.
* 🛡️ **Intelligent Filtering & Quality Gates:**
  * **Strict 48-Hour Freshness Gate (`--jobage 2`):** Eliminates stale or reposted listings across all portals; missing publication dates are never defaulted to today.
  * **German Language Gate:** Automatically filters out postings requiring German C1, C2, or *verhandlungssicher*, matching English C1 / German B2 target profiles.
  * **LinkedIn Easy Apply Gate:** Bypasses 1-click Easy Apply postings to focus exclusively on high-intent direct employer career portals.
* 📄 **ATS & Page Budget Verification:**
  Compiles pixel-perfect, **strictly 2-page ModernCVs** (`lualatex`) and **strictly 1-page cover letters** (`xelatex`) with automated text-layer extraction, keyword coverage checks, and zero factual fabrication.
* ⚡ **Convenient Root CLI Runners:**
  * `./app [port]` — Launch dashboard server and automatically open browser.
  * `./scrape` — Fast multi-portal scraper runner.
  * `./apply [company/url]` — CLI application shortlist viewer and helper.

---

## Architecture & Workflow

```
       ┌────────────────────────────────────────────────────────┐
       │               Candidate Profile Setup                  │
       │    CLAUDE.md  |  .claude/skills/  |  documents/        │
       └──────────────────────────┬─────────────────────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
┌──────────────────┐                             ┌──────────────────┐
│  CLI Workflow    │                             │  Web Dashboard   │
│  /scrape         │                             │  http://localhost:8000
└────────┬─────────┘                             └────────┬─────────┘
         │                                                 │
         ├────────────────────────┬────────────────────────┤
         ▼                        ▼                        ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Bundesagentur für│     │ StepStone Germany│     │ LinkedIn, XING,  │
│      Arbeit      │     │   & FreeHire     │     │   Job Portals    │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  ▼
                   ┌──────────────────────────────┐
                   │    Filters & Quality Gates   │
                   │  • Max 2 days old (--jobage 2)│
                   │  • German C1/C2 Gate         │
                   │  • Deduplication & Ranking   │
                   └──────────────┬───────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │   Drafter-Reviewer /apply    │
                   │  • Tailor ModernCV (2 pages) │
                   │  • Tailor Letter (1 page)    │
                   │  • LaTeX Compile & ATS check │
                   └──────────────┬───────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │  Job Search Tracker & Archive│
                   │  job_search_tracker.csv      │
                   │  documents/applications/     │
                   └──────────────────────────────┘
```

---

## Prerequisites

- **AI Agent Tool:** [Claude Code](https://claude.com/claude-code) (CLI) or [Google Antigravity](https://deepmind.google/technologies/antigravity/) / Gemini CLI. See [`AGENTS.md`](AGENTS.md) and [`GEMINI_SETUP.md`](GEMINI_SETUP.md).
- **Python 3.10+**
- **[Bun](https://bun.sh):** For running job search CLI skills.
- **LaTeX Distribution:** With `lualatex` and `xelatex`: [TeX Live](https://tug.org/texlive/), [MacTeX](https://tug.org/mactex/), [TinyTeX](https://yihui.org/tinytex/), or [MiKTeX](https://miktex.org/).
  - ModernCV compiles with `lualatex`.
  - Cover letters compile with `xelatex` (requires `fontspec` and bundled OpenFonts).
- **Optional:** `pip install pypdf` or `poppler` (`pdftotext`) for ATS text-layer extraction verification.

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/ycrgotike/ai-job-search.git
cd ai-job-search
```

> [!IMPORTANT]
> Your profile files (`CLAUDE.md`, `.claude/skills/job-application-assistant/`, `job_search_tracker.csv`) contain personal career data. If you are using this repo for your own job search, keep your personal repository **private**.

### 2. Install portal search tools

Install dependencies for the portable CLI skills:

```bash
for tool in arbeitsagentur-search stepstone-search xing-search linkedin-search freehire-search; do
  (cd .agents/skills/$tool/cli && bun install)
done
```

*Note: `linkedin-search` and `freehire-search` have zero runtime dependencies and run with plain `bun`; `bun install` only pulls dev types.*

### 3. Configure your candidate profile

You can configure your profile in two ways:

* **Interactive Onboarding:** Run `claude` (or your agent runtime) and type:
  ```bash
  /setup
  ```
  `/setup` can parse your existing `documents/` folder (CV PDF, LinkedIn export, certificates), import a single CV pasted in chat, or walk you through an interview.
* **Direct File Editing:** Directly update [`CLAUDE.md`](CLAUDE.md) and the profile files in `.claude/skills/job-application-assistant/` (`01-candidate-profile.md`, `04-job-evaluation.md`, etc.).

### 4. Launch the Web Dashboard

Start the interactive dashboard server:

```bash
./app 8000
```

*(On macOS, this automatically opens [http://localhost:8000](http://localhost:8000) in your default browser).*

Alternatively, start it inside your AI assistant with:
```bash
/serverstart
```

### 5. Search for jobs

To search across active portals (Bundesagentur für Arbeit, StepStone, XING, LinkedIn, FreeHire) with 48-hour recency and language filters:

```bash
./scrape
```

Or run the interactive command inside your AI assistant:
```bash
/scrape
```

Matches are deduplicated, scored against your profile, and stored in `job_scraper/seen_jobs.json`.

### 6. Apply to a job

To generate a tailored application:

```bash
# In your AI assistant chat:
/apply https://www.stepstone.de/stellenangebote--...
```

If a URL cannot be fetched directly, paste the job description text:
```bash
/apply <paste the full job description here>
```

You can also run `./apply` in your terminal to see unapplied shortlisted opportunities, or click **Generate** directly on any job card in the Web Dashboard.

---

## Available Commands

| Command | Purpose |
|---------|---------|
| `/setup` | Onboarding assistant: imports CV, LinkedIn PDF, or runs interactive profiling. |
| `/serverstart` | Launches or verifies the localhost web dashboard at `http://localhost:8000`. |
| `/scrape` | Searches all configured portals (Bundesagentur für Arbeit, StepStone, XING, LinkedIn, FreeHire). |
| `/rank` | Batch-evaluates and scores newly scraped jobs against your fit framework. |
| `/apply <url\|text>` | Runs the drafter-reviewer workflow to tailor CV and Cover Letter in LaTeX. |
| `/interview` | Builds a stage-specific interview prep pack and conducts a mock interview using STAR examples. |
| `/outcome` | Logs application outcomes (interview stages, offers, rejections) and archives documents. |
| `/upskill` | Analyzes skill gaps across target postings and drafts a structured learning roadmap. |
| `/expand` | Enriches profile skills by scanning linked GitHub repos, portfolios, and course syllabi. |
| `/html-report` | Generates a standalone offline HTML application tracking report. |
| `/notion-sync` | Publishes a read-only pipeline overview to a Notion database. |
| `/gmail-sync` | Scans Gmail for application status updates (interviews, assessments, rejections). |
| `/add-template` | Registers custom CV or Cover Letter templates (LaTeX, Typst, etc.). |
| `/add-portal` | Scaffolds a new job portal search CLI skill for an additional job board. |
| `/reset` | Safely resets profile data or application documents. |

---

## How `/apply` Works

The application workflow implements a strict **drafter-reviewer pipeline** with mandatory LaTeX PDF compilation and ATS verification:

1. **Parse & Deconstruct:** Extracts title, company, requirements, qualifications, and core duties from the posting.
2. **Evaluate Fit:** Scores match dimensions (technical competencies, domain alignment, location, culture) and checks deal-breakers.
3. **Drafting (LaTeX):**
   * **ModernCV:** Dynamically prioritizes relevant technical projects, reorders experience bullets to highlight direct evidence, and writes a role-specific 4-line summary mentioning the target company organically.
   * **Cover Letter:** Writes an evidence-led, 300–350 word letter with bold thematic lead-ins, verified engineering metrics, and clear English C1 / German B2 proficiency statements.
4. **Independent Reviewer Critique:** A second agent call researches company context, audits claims against your verified profile, and checks for keyword alignment without keyword stuffing.
5. **Revision & Formatting:** The drafter revises content to incorporate critique notes.
6. **PDF Compilation & Layout Verification:**
   * Compiles the CV with `lualatex` and verifies it is **strictly 2 pages** with no orphaned headers.
   * Compiles the Cover Letter with `xelatex` and verifies it is **strictly 1 page**.
7. **ATS Text-Layer Extraction:** Extracts embedded text using `pdftotext`/`pypdf` to ensure contact info parses as literal text (not font ligatures), reading order is sane, and keyword coverage is authentic.
8. **Archive & Delivery:** Records the application in `job_search_tracker.csv` and archives compiled PDFs and LaTeX source files under `documents/applications/<company>_<role>/`.

---

## File Structure

```
ai-job-search/
├── AGENTS.md                          # Thin-pointer guidelines for AI agents
├── CLAUDE.md                          # Master candidate profile and application rules
├── GEMINI_SETUP.md                    # Setup and config for Gemini LLM drafting
├── app                                # Root launcher for localhost web dashboard
├── scrape                             # Root runner for multi-portal scraper
├── apply                              # Root helper for application shortlists
├── server.py                          # Localhost HTTP & API server (port 8000)
├── web/                               # Interactive web dashboard
│   ├── index.html                     # Dashboard HTML interface
│   ├── styles.css                     # Modern dark-mode styling
│   └── app.js                         # Dynamic radar, filters, and API client
├── .agents/skills/                    # Portable job portal CLI tools (Agent Skills)
│   ├── arbeitsagentur-search/         # Bundesagentur für Arbeit (Germany)
│   ├── stepstone-search/              # StepStone Germany
│   ├── xing-search/                   # XING DACH (Germany, Austria, Switzerland)
│   ├── linkedin-search/               # LinkedIn public guest API
│   ├── freehire-search/               # freehire.me tech job aggregator
│   ├── jobindex-search/               # Jobindex.dk (Denmark)
│   ├── jobnet-search/                 # Jobnet.dk (Denmark)
│   ├── jobdanmark-search/             # Jobdanmark.dk (Denmark)
│   └── jobbank-search/                # Akademikernes Jobbank (Denmark)
├── .claude/
│   ├── commands/                      # Slash command definitions (/apply, /setup, etc.)
│   └── skills/
│       ├── job-application-assistant/ # Core CV/Cover Letter/Interview methodology
│       ├── job-scraper/               # Scraper orchestration and search queries
│       └── upskill/                   # Gap analysis and learning roadmap generator
├── cv/
│   ├── main_example.tex               # ModernCV LaTeX banking template
│   └── YashwanthGotike_*_CV.tex       # Tailored CV sources and PDFs
├── cover_letters/
│   ├── cover.cls                      # Custom XeLaTeX cover letter class
│   ├── cover_example.tex              # Reference cover letter template
│   ├── OpenFonts/                     # Lato & Raleway typography
│   └── YashwanthGotike_*_CoverLetter  # Tailored cover letter sources and PDFs
├── documents/                         # Candidate career materials
│   ├── cv/                            # Master CV source documents
│   ├── linkedin/                      # LinkedIn profile export PDF
│   ├── diplomas/                      # Degrees, transcripts, certifications
│   └── applications/                  # Application archives (<company>_<role>/)
├── job_scraper/
│   ├── seen_jobs.json                 # Scraped jobs database and match metadata
│   └── last_scrape_report.json        # Portal audit report and coverage diagnostics
├── job_search_tracker.csv             # Central application tracking spreadsheet
├── tools/
│   ├── scrape.py                      # Multi-portal orchestration engine
│   ├── gemini_tailoring.py            # Gemini LLM responsibility planner & drafter
│   ├── generate_application.py        # Application generation pipeline
│   ├── verify_pdf.py                  # PDF page count and text-layer verifier
│   └── verify_layout.py               # Visual layout and orphan detector
└── tests/                             # Comprehensive test and regression suite
```

---

## Customization

### Which files to edit

To personalize this repository for your own career search:

| File | What to customize |
|------|-------------------|
| [`CLAUDE.md`](CLAUDE.md) | Identity, headline, target roles, experience, degrees, and core projects |
| `.claude/skills/job-application-assistant/01-candidate-profile.md` | Detailed career history, verified tools, metrics, and achievements |
| `.claude/skills/job-application-assistant/02-behavioral-profile.md` | Working style, leadership traits, and collaboration preferences |
| `.claude/skills/job-application-assistant/04-job-evaluation.md` | Fit evaluation dimensions, weights, and deal-breaker criteria |
| `.claude/skills/job-application-assistant/07-interview-prep.md` | STAR interview stories and technical scenario examples |
| `.claude/skills/job-scraper/search-queries.md` | Target search keywords, role titles, and geographic locations |

### Custom templates

The repository ships with **ModernCV** (banking style) and a custom **XeLaTeX cover letter class (`cover.cls`)**.

To register your own custom template (LaTeX, [Typst](https://typst.app/), etc.):
```bash
/add-template
```
Follow the interactive prompt to set file extensions, compile commands, font directories, and page limits.

---

## Tips for Best Results

* **Detail Drives Quality:** Tailored applications are grounded strictly in the evidence in your profile. Provide concrete numbers, tools used, and business impacts in `01-candidate-profile.md` to give the AI substance to work with.
* **Keep Recency Tight:** Job markets move quickly. The default 48-hour window (`--jobage 2`) ensures you apply to freshly opened postings before review pools close.
* **Review Before Sending:** While the drafter-reviewer loop and automated PDF verifiers enforce layout and factual constraints, always inspect your compiled PDFs and verify company specifics before final submission.

---

## Acknowledgements

* **[Mads Lorentzen](https://github.com/MadsLorentzen):** Creator of the original foundational framework and concept.
* **[Mikkel Krogholm](https://github.com/mikkelkrogsholm):** Original creator of the Danish job search CLI skills.
* **Anthropic Claude Code & Google DeepMind Antigravity Teams:** For the multi-agent CLI and agentic execution environments.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
