---
framework_version: 1.1.4
---

# Agent Guidelines: AI Job Search

This workspace is structured to manage job search activities, scraper tools, CVs, cover letters, and interview preparation.

## Thin-Pointer Design (Single Source of Truth)

To prevent duplication and configuration drift across different AI agent frameworks (Claude Code, Google Antigravity, Codex, Cursor, Gemini CLI, etc.), this workspace uses a unified thin-pointer design. All agent runtimes should load the canonical specifications and candidate profiles from the files and directories below:

1. **Personal Candidate Profile:**
   - The candidate profile, contact details, education, and target preferences are defined in [CLAUDE.md](CLAUDE.md) and the individual profile methodology files under [.claude/skills/job-application-assistant/](.claude/skills/job-application-assistant/) (specifically `01-*.md` etc.).
2. **Canonical Workflow Specifications:**
   - The step-by-step instructions and triggers for tasks (setup, scrape, rank, apply, upskill, interview) are defined in the [.claude/](.claude/) directory (specifically under `.claude/skills/` and `.claude/commands/`).
   - Do not duplicate these rules or specifications. Treat `.claude/` files as the single source of truth.
3. **Portal Search Skills:**
   - Job-portal search CLIs live under [.agents/skills/](.agents/skills/) in the portable Agent Skills format (with a `SKILL.md` per portal). Installed portals include `linkedin-search`, `freehire-search`, `arbeitsagentur-search` (Bundesagentur für Arbeit), `stepstone-search` (StepStone Germany), and `xing-search` (XING DACH). Codex and Antigravity discover these automatically; the `/scrape` workflow in [.claude/skills/job-scraper/](.claude/skills/job-scraper/) orchestrates them.

## Mandatory Application Rules (Strict Across All Agents)

1. **Professional Experience Ordering:** Strict reverse chronological order — always list the latest role first (SolTech [09/2022–09/2024] $\rightarrow$ G.S.R [04/2019–09/2022] $\rightarrow$ ITC Infotech [08/2018–04/2019]).
2. **CV Omissions:** NEVER include "Availability" or "References: Available upon request" in any CV.
3. **Cover Letter Language:** ALWAYS write cover letters in English, even when applying to German companies or postings written in German.
4. **Page Constraints:** CV must be **exactly 2 pages** (compiled with LuaLaTeX); Cover Letter must be **exactly 1 page** (compiled with XeLaTeX).
5. **Core Project Highlights:** Feature **MVP UPSC** (GenAI, LLM, RAG, Agentic AI, MCP) and **Algo Trading** (time-series, automated quantitative pipelines) on relevant AI/ML/Data roles.
6. **ATS Optimization Standards (Permanent across all future documents):**
   - **Text Contact Labels:** Override ModernCV icon macros (`\renewcommand*{\addresssymbol}{}`, `\renewcommand*{\mobilephonesymbol}{Phone:~}`, `\renewcommand*{\emailsymbol}{Email:~}`) to ensure contact info parses as literal text rather than font ligatures/glyphs.
   - **Direct `\cventry` Placement:** Never wrap `\cventry` in outer `\begin{itemize}\item{...}\end{itemize}`. Place `\cventry` directly under `\section{...}` to avoid overfull hboxes and isolated bullet glyphs in ATS parsers.
   - **Embedded PDF Metadata:** Always embed `pdfauthor`, `pdftitle`, `pdfsubject`, and `pdfkeywords` in `\hypersetup` for both CV and Cover Letter.
   - **Explicit Requisition Subject Line:** In cover letters, include `\lettercontent{\textbf{Re: Application for [Role Title]}}` before salutation.
7. **Cover Letter Language Proficiency (Closing Paragraph Only - Strictly No Duplication):** EVERY cover letter must explicitly highlight the candidate's language capabilities: fluent in **English (C1)** and **intermediate level in German (B2)** (e.g., "I hold full work authorization in Germany with no visa sponsorship required and communicate fluently in English (C1) with an intermediate proficiency in German."). This statement is permanently and exclusively rendered in the host template's closing paragraph. NEVER mention language proficiency, English (C1), German (B2), or CEFR levels in the opening or body paragraphs; doing so causes redundant repetition (e.g., B2 repeated twice).
8. **CV Section Naming & Clean Skills Placement:**
   - Always name the primary skills section `\section{Technical Skills}` — NEVER use 'Core Competencies'.
   - NEVER add tools, frameworks, or technical skills to the 'Languages \& Honors' or 'Languages \& Achievements' section. That section is strictly reserved for languages and honors/awards.
9. **SolTech Experience Location:**
   - Always list the location for SolTech InfoLabs strictly as `Hyderabad, India` — NEVER append '/ Remote & Hybrid'.
10. **CV Education Entry (Omit In-Progress / Expected Dates for Full-Time Roles):**
   - Under `\section{Education}`, list the Master's degree with the date range `10/2024--Present` and relevant coursework.
   - For standard full-time roles, NEVER include "In progress, expected September 2027" or expected graduation dates under Education entries in the CV. (For student applications, see Section 2 below for required Page 1 enrollment/graduation visibility).
11. **Candidate Name Standard:**
   - The candidate's name across all CVs, cover letters, metadata, and application materials is strictly **Yashwanth Gotike** (never include middle name "Chenna Reddy").
   - In ModernCV: use `\name{Yashwanth}{Gotike}`.
   - In Cover Letters: use `\namesection{}{\Huge{Yashwanth Gotike}}{...}` and `\signature{Yashwanth Gotike}`.
   - In PDF metadata: `pdfauthor={Yashwanth Gotike}` and `pdftitle={Yashwanth Gotike - ...}`.
12. **Document & File Naming Conventions:**
   - All tailored CV files must be named strictly as `YashwanthGotike_<CompanyName>_CV` (source: `cv/YashwanthGotike_<CompanyName>_CV.tex`, compiled: `cv/YashwanthGotike_<CompanyName>_CV.pdf`).
   - All tailored Cover Letter files must be named strictly as `YashwanthGotike_<CompanyName>_CoverLetter` (source: `cover_letters/YashwanthGotike_<CompanyName>_CoverLetter.tex`, compiled: `cover_letters/YashwanthGotike_<CompanyName>_CoverLetter.pdf`).
   - `<CompanyName>` should use PascalCase or the company's official identifier without spaces or special characters (e.g., `Pflegia`, `FIEGE`).
   - In `job_search_tracker.csv`, record `cv/YashwanthGotike_<CompanyName>_CV.pdf` and `cover_letters/YashwanthGotike_<CompanyName>_CoverLetter.pdf`.
   - In application archives (`documents/applications/<company>_<role>/`), store `YashwanthGotike_<CompanyName>_CV.pdf` and `YashwanthGotike_<CompanyName>_CoverLetter.pdf`.
13. **Job Scraping Freshness Standard (Strictly Max 2 Days Across All Portals):**
   - Whenever scraping or searching for job postings (via `/scrape`, `tools/scrape.py`, portal CLIs, WebSearch, or any future portals added to the system), the search recency must strictly be set to **max 2 days or newer** (`--jobage 2` / posted within the last 48 hours).
   - **No Fallback to Today:** Missing publication dates must NEVER be defaulted or stamped as "today". If a portal emits no date or an unparseable date, the posting must NOT be assumed fresh.
   - **Strict Client-Side & Server-Side Filtering:** Any posting older than 2 days (or lacking a verified publication date within the last 48 hours) must be discarded immediately. Stale postings (such as sponsored, promoted, or reposted listings like Visium Senior Data Engineer that were published weeks or months ago) must never be admitted into `seen_jobs.json` or served on the dashboard.
14. **German Language Gate (Strictly Exclude Minimum German C1/C2 Requirements):**
   - The candidate communicates fluently in **English (C1)** and possesses an intermediate proficiency in **German (B2)**.
   - NEVER scrape, save, or present any job posting that specifies a minimum requirement of **German C1**, **German C2**, **verhandlungssichere Deutschkenntnisse**, **business-fluent German**, or **native/near-native German**.
   - Any posting with a minimum German C1/C2 requirement must be discarded immediately during scraping (via client-side regex detection on title, description, or detail) and must never be admitted into `seen_jobs.json` or served on the dashboard.
   - Postings requiring German B2, B1, conversational German, English-speaking roles, or German as an optional/plus qualification are fully eligible.
15. **CV Address Header Role Headline Standard:**
   - Beside `Koblenz, Germany` in the CV address block (`\address{Koblenz, Germany \,|\, <Headline>}{}{}`), include a dynamically tailored professional discipline headline in normal text weight (`\mdseries` / regular text, NEVER bolded).
   - NEVER include seniority prefixes (e.g., Senior, Junior, Lead, Principal, Associate, Staff).
   - NEVER include student or internship tags (e.g., Werkstudent, Working Student, Praktikant, Intern, Praktikum).
   - Normalize the headline to an established professional role such as `Data Scientist`, `Machine Learning Engineer`, `Analytics Engineer`, `Data Engineer`, `Data Analyst`, or `AI Engineer`. Preserve recognized disciplines; map generic/branded titles from actual responsibilities. Never copy arbitrary programme titles such as `Flexikum Technical Consultant` into the header.
   - Follow the canonical headline selection and ambiguous-role rules in [.claude/skills/job-application-assistant/05-cv-templates.md](.claude/skills/job-application-assistant/05-cv-templates.md#job-title-based-cv-headline).
16. **Data Governance Quality Assurance Seminar Utilization:**
   - The candidate completed an advanced academic seminar on **"Data Governance Quality Assurance"** at the University of Koblenz.
   - Whenever a target job posting mentions data governance, quality assurance, data quality, schema validation, data profiling, metadata management, or compliance:
     - In the **CV Education section**, feature the seminar (`Coursework: Data Science, Big Data, Machine Learning, Data Mining \,|\, Seminar: Data Governance Quality Assurance`).
     - In the **Cover Letter**, explicitly feature the seminar coupled with practical industry experience in automated validation frameworks and enterprise data trustworthiness.
17. **LinkedIn Easy Apply Gate (Strictly Exclude Easy Apply Postings):**
   - The candidate exclusively targets direct, high-intent employer applications (company career portals / offsite apply) where tailored ModernCV and XeLaTeX cover letters are evaluated.
   - NEVER scrape, save, or present any LinkedIn job posting that is marked as or uses **Easy Apply** (`apply-link-onsite`, `guest-to-member-job-apply`, etc.).
   - Any LinkedIn Easy Apply posting must be discarded immediately during scraping (via detail inspection in `tools/scrape.py` / `fetch_linkedin_details` and `linkedin-search` CLI) and must never be admitted into `seen_jobs.json` or served on the dashboard.
18. **Senior Full-Time Position Experience Standard (5+ Years of Experience):**
   - For all senior full-time roles (postings containing "Senior", "Lead", "Principal", "Staff", or requiring 5+ years of experience):
     - In the **CV Summary**: ALWAYS explicitly state **"5+ years of professional experience"** (or "over 5 years of professional experience") in the lead sentence.
     - In the **Cover Letter Opening**: ALWAYS explicitly highlight the candidate's **"5+ years of professional experience"** (e.g., "Bringing 5+ years of professional engineering experience across [domains], I am well-equipped to support your team with [impact].").

## Canonical Application Guidelines (Tailoring, CV, Cover Letter, Verification & Delivery)

All AI agents generating, tailoring, or reviewing application materials in this workspace must strictly adhere to the following standards across all future CVs and cover letters:

### 1. Dynamic Tailoring Standards
- **Dynamic Prioritization for Every Application:**
  - Select and order technical projects by direct relevance to the target job description.
  - Order skill categories and individual tools/skills by the employer's stated priorities.
  - Reorder professional experience bullets to emphasize the achievements most relevant to the role.
  - Never apply one static project list or fixed section ordering to every application.
- **Requirement-to-Evidence Grounding:** Identify the most critical requirements in the job posting and connect each to concrete, verifiable evidence in the candidate's professional experience or projects.
- **Natural Terminology:** Adopt the job posting's terminology naturally and accurately. Strictly avoid keyword stuffing, redundant buzzwords, and unnecessary technology lists.
- **Factual Integrity & Zero Fabrication:** Preserve confirmed skills and implementations. If the profile contains outdated uncertainty about a claim the candidate has explicitly confirmed, use the latest confirmation. Knowing a technology supports listing it as a skill; claiming an implementation or achievement requires actual completed work. NEVER invent metrics, responsibilities, qualifications, or outcomes.
- **Accurate Historical Records:** Keep historical job titles, employers, and employment dates strictly accurate. Tailor the professional headline (e.g., `Data Engineer`, `Data Analyst`, `AI Engineer`) without implying an employment title the candidate did not hold.

### 2. CV Content and Layout Standards
- **Layout & Structure:** Retain the clean, predominantly single-column professional ModernCV (banking style) layout unless there is a clear readability problem. Use standard, recognizable section headings (`Technical Skills`, `Professional Experience`, `Key Technical Projects`, `Education`, `Languages & Honors`), consistent typography, uniform margins, and visible text labels for phone, email, and links.
- **Left-Aligned, Ragged-Right Text:** Use left-aligned, ragged-right text (`\raggedright` / `\RaggedRight`) for CV summaries, skills lists, and bullet points. Remove stretched word spacing caused by full justification while preserving date/location margin alignment in `\cventry`.
- **Header Proportions:** Keep the candidate's name prominent but proportionate; eliminate excessive header whitespace.
- **Role-Specific Summary & Natural Company Support:** For every role and application type, write a summary of exactly 4 rendered lines. The summary must be dynamically tailored to the target job description and technical domain, concluding with an organic, natural mention of the target company and how the candidate's background enables them to support its team or initiatives (e.g., "This background enables me to support <CompanyName> with dependable data integration, automated delivery, and scalable data architectures."). Strictly avoid blatant or formulaic phrasing like "This is how I can contribute". Always verify the compiled PDF to ensure strictly exactly 4 rendered lines and exact 2-page total length.
- **Project Presentation (Standalone Title without Leading Bullet):** Format project titles as standalone bold text without a leading bullet glyph (`\textbf{Title}`). Use 1 to 2 concise standard bullets underneath with consistent indentation (`\begin{itemize}\item ... \item ... \end{itemize}`). Replace any custom bullet glyphs that extract incorrectly into the text layer with standard bullets. Avoid dense, technology-filled paragraphs.
- **Explicit Technical Skills Grounding:** Ensure core languages and tools emphasized elsewhere in the CV or cover letter (such as Python, SQL, Git, Docker) appear explicitly in `\section{Technical Skills}` when relevant.
- **Student & Academic Applications (Page 1 Visibility):** For student or intern roles (Werkstudent / Praktikum), make current university enrollment and expected graduation (e.g., M.Sc. Web and Data Science at University of Koblenz, expected September 2027) visible on Page 1 (within the same summary paragraph, with the entire paragraph limited to exactly 4 rendered lines). Include confirmed weekly hours (e.g., up to 20h/week during semester) and start date where appropriate. NEVER invent missing details.
- **Prevent Awkward Word Breaks:** Prevent awkward automatic word breaks such as "techni-cal" and "environ-ments" (via high hyphen penalty `\hyphenpenalty=10000`), while preserving legitimate compound-word hyphens (e.g., "end-to-end", "near-real-time", "cloud-native").
- **Strict 2-Page Constraint:** The final compiled CV MUST be **exactly 2 pages**. Balance relevant content evenly across both pages without filler, excessive whitespace, or unreadably small fonts. Ensure entry headings are never orphaned from their supporting text (`\needspace`).

### 3. Cover Letter Content and Layout Standards
- **Cover Letter Format:** Follow `06-cover-letter-templates.md`: compact left-aligned header, matching CV font, evidence-led content, approximately 300–350 substantive body words, justified paragraphs with natural word spacing, exactly one compiled page.
- **Bold Thematic Paragraph Lead-Ins (Mandatory Across All Future Letters):** Every body paragraph must lead with a bold thematic anchor that immediately communicates core engineering impact (e.g., `\textbf{Cloud \& Azure Lakehouse Engineering.}`, `\textbf{Data Quality \& Automated Governance.}`, `\textbf{CI/CD \& Dependable Platform Delivery.}` for data engineering; or `\textbf{Advanced Analytics \& Business Intelligence.}`, `\textbf{Automated Data Pipelines \& Modeling.}` for analytics; or `\textbf{LLM Architectures \& RAG Systems.}`, `\textbf{End-to-End MLOps \& Production Pipelines.}` for AI).
- **Quantified Engineering Impact:** Anchor every technical example to verified, concrete metrics from the candidate profile (e.g., sub-30-minute reporting latency, 1.5 TB cloud migration, 30\% overhead reduction, 40\% turnaround acceleration, 18\% customer retention improvement, zero unplanned downtime). Never invent metrics, but feature all confirmed metrics strongly.
- **Prohibition of Concession Language & Keyword Dumps:** Strictly NEVER include negative concession paragraphs (e.g., "Where I would need to ramp up", "While I don't have experience in X") or raw keyword dump footers. Bridge adjacent technical skills positively, focusing on immediate problem-solving capability and practical implementation.
- **Dynamic Data Governance Integration:** Whenever the target role mentions data governance, quality assurance, data quality, schema validation, data profiling, metadata management, or compliance, dedicate a thematic paragraph to the candidate's advanced academic seminar on \textit{Data Governance Quality Assurance} at the University of Koblenz coupled with practical enterprise validation frameworks.
- **Visual & Typographic Consistency:** Match the CV and cover-letter font families and restrained visual styling. Reduce excessive vertical space between the recipient block, the date, and the subject line.
- **Compact Spacing:** Keep vertical spacing between header, recipient block, date, subject line, and body compact and uniform, leaving sufficient room for the closing and signature.
- **Opening Paragraph (2–3 Concise Sentences):** Limit the opening to 2–3 concise sentences. Mention the target role once and connect relevant experience directly to the work, without redundantly repeating the job title or stating years of experience (except for senior full-time roles, where highlighting the candidate's 5+ years of professional engineering experience is mandatory).
- **Rewrite Around Actual Responsibilities:** Genuinely rewrite cover letters around each role's actual stated responsibilities and technical challenges. Do not merely substitute company names and keywords into a static template. Remove generic praise ("renowned company", "industry leader") and bullets that duplicate the opening or other examples.
- **Targeted Evidence:** Feature 1 or 2 relevant examples, explaining specifically how that past experience will help with the employer's upcoming tasks. Do not repeat the entire CV. Anchor every example to where the work occurred (company, project, or academic seminar).
- **Paragraph & Bullet Structure:** Follow the evidence-led paragraph structure in `06-cover-letter-templates.md`, with approximately 300–350 body words and exactly one page.
- **Accurate Recipient & Contact:** Use the correct employer name, role title, requisition number, and verified contact person. Use a neutral, professional greeting (e.g., "Dear Hiring Team,") when the contact person is unknown.
- **Company Location Address Block (Mandatory Across All Applications):** In the cover letter recipient block (`\companyname{...}\companyaddress{...}`), format `\companyaddress{...}` strictly as `\companyaddress{Hiring Team\\[City], Germany}` (or `\companyaddress{Hiring Team\\Germany}` if no specific city is confirmed). The contact person (e.g., `Ruben Voigtländer`) is addressed strictly in the letter salutation (`\lettercontent{Dear Ruben Voigtländer,}`). Extract the employer's city or headquarters location from the posting metadata, postal codes, or description.
- **Language Standards & Zero Duplication:** ALWAYS write cover letters in English unless explicitly requested otherwise by the candidate. Keep language proficiency claims accurate: English (C1 / Fluent) and German (B2 / Intermediate). Strictly enforce single placement: language capabilities and work authorization are permanently rendered in the host template's closing paragraph. NEVER include language levels (B1/B2/C1/C2) or language proficiency claims in the opening or body paragraphs; doing so causes redundant repetition (such as B2 appearing twice in the same letter).
- **Confirmed Availability Details:** Replace vague availability statements with confirmed details (e.g., "available with 1 month notice" or confirmed earliest start date; up to 20 hours/week for student roles). Avoid "contribute immediately" when the recorded start date is later.
- **Prose Quality:** Avoid clichés, inflated adjectives, repetitive phrases, and awkward sentence structures. Prevent awkward automatic word breaks such as "techni-cal" and "environ-ments" (via high hyphen penalty `\hyphenpenalty=10000`), while preserving legitimate compound-word hyphens.

### 4. Verification Standards
- **Visual PDF Inspection (Mandatory):** Compile both PDFs and visually inspect every page before delivery. Check for and resolve:
  - Text clipping, line overlaps, and unreadable fonts.
  - Stretched word spacing: keep CV prose ragged-right; justify letter paragraphs and rewrite lines with visible gaps.
  - Standalone bold project titles without leading bullet glyphs and consistent indentation.
  - Orphaned section headings or split entry blocks (`\needspace`).
  - Uneven vertical spacing and poorly balanced pages.
  - Awkward hyphenation or line breaks (no "techni-cal", "environ-ments").
  - Excessive spacing between cover letter recipient block and date.
  - Cover letter overflow onto a second page.
- **Text-Layer Extraction Checks:** Extract the text layer from the final PDFs and verify:
  - Logical, human-readable reading order.
  - Complete, uncorrupted contact details.
  - Correct character rendering and standard bullets (no `(cid:NNN)` or replacement glyphs).
  - Explicit inclusion of core emphasized tools (e.g., Python) in `\section{Technical Skills}`.
  - Student enrollment and expected graduation visible on Page 1 for student applications.
  - Cover letter opening limited to 2–3 sentences and free of generic praise or duplicate bullets.
  - Confirmed availability details matching records.
  - No missing text or encoding artifacts.
  - Natural coverage of the most important supported job keywords.
- **Cross-Document Consistency:** Check full consistency between CV, cover letter, candidate profile, and job requisition details.
- **No ATS Guarantees:** Do not claim an arbitrary ATS score or guarantee an interview; distinguish verified PDF readability and ATS optimization from an employer's proprietary screening process.
- **Page Count Confirmation:** Confirm compiled PDF page counts: CV = **exactly 2 pages**; Cover Letter = **exactly 1 page**. If either count is incorrect, revise, recompile, and inspect again before delivery.

### 5. Delivery Standards
- Provide the final compiled CV and cover letter PDFs alongside their editable LaTeX source files.
- Deliver a concise summary detailing:
  - How the application was tailored to the specific role.
  - Which layout and structural improvements were made.
  - Confirmation that visual inspection and text-extraction checks passed.
  - Any remaining information or clarification the user needs to supply.
- Note: Preparing application documents does not authorize submitting the application.
