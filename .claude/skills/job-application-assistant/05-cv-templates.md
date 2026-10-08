---
framework_version: 1.5.8
---

# CV Templates and Tailoring Guide

<!-- SETUP: Profile statements and section ordering are personalized by running /setup -->

## Template: LaTeX moderncv (Banking Style)

All CVs use the moderncv LaTeX package with the "banking" style and "blue" color scheme.

**Output file:** `cv/YashwanthGotike_<CompanyName>_CV.tex` (compiled to `cv/YashwanthGotike_<CompanyName>_CV.pdf`)
**Compile with:** **lualatex** on MiKTeX/TeX Live. pdflatex often fails on modern MiKTeX installs with `fontawesome5` font-expansion errors; lualatex handles the same sources cleanly.
**Master reference:** `cv/main_example.tex` (comprehensive CV with all competencies, experience, and achievements - use as source when building targeted CVs)

### Compile command

```bash
cd cv && lualatex -interaction=nonstopmode YashwanthGotike_<CompanyName>_CV.tex
```

Expected output: `Output written on YashwanthGotike_<CompanyName>_CV.pdf (2 pages, ...)`. Any page count other than 2 is a failure that must be fixed before presenting to the user.

## Document Structure

```latex
\documentclass[11pt,a4paper,sans]{moderncv}
\moderncvstyle{banking}
\moderncvcolor{blue}

% Force the name and section headings to render in moderncv blue (color1).
% Default banking leaves them black: moderncvstylebanking.sty's \colorlet
% copies (not aliases) the pre-scheme accent colour, so the name colours are
% frozen before \moderncvcolor runs. Re-let them after. \namefont is the hook
% every name-style macro routes through, so this also works on moderncv 2.3.1
% (Debian/Ubuntu apt), which has no \firstnamestyle/\lastnamestyle at all.
\renewcommand*{\namefont}{\fontsize{34}{36}\bfseries\upshape}
\colorlet{firstnamecolor}{color1}
\colorlet{lastnamecolor}{color1}
\colorlet{namecolor}{color1}
\renewcommand*{\sectionstyle}[1]{{\sectionfont\color{color1}#1}}

\usepackage[utf8]{inputenc}
% moderncv loads hyperref itself in an \AtEndPreamble hook, so \hypersetup
% must go in an \AtEndPreamble of our own: on moderncv < 2.4 a top-level
% \usepackage{hyperref} clashes with the class's own
% \RequirePackage[unicode]{hyperref}. From 2.4.0 the class passes its options
% through \PassOptionsToPackage instead, which is what removes that clash.
\AtEndPreamble{\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,
    urlcolor=blue,
    pdftitle={[FIRST_NAME] [LAST_NAME] - CV},
    pdfauthor={[FIRST_NAME] [LAST_NAME]},
    pdfsubject={[Target Role / Field]},
    pdfkeywords={[Target keywords, Tools, Frameworks]},
    pdfpagemode=UseNone,
}}
\usepackage[scale=0.82]{geometry}
\usepackage{import}
\usepackage{needspace}
\usepackage{ragged2e}

% Prevent awkward automatic word breaks across lines while preserving legitimate compound-word hyphens
\hyphenpenalty=10000
\exhyphenpenalty=50

% Left-aligned, ragged-right formatting for lists and summaries to prevent stretched word gaps
% while preserving date/location alignment in \cventry
\AtBeginEnvironment{itemize}{\raggedright}

% ATS Optimization: Clean text labels for contact info instead of font glyph ligatures
\renewcommand*{\addresssymbol}{}
\renewcommand*{\mobilephonesymbol}{Phone:~}
\renewcommand*{\emailsymbol}{Email:~}

% Personal data (Template placeholders: [FIRST_NAME], [LAST_NAME], [YOUR_EMAIL], [YOUR_PHONE])
\name{Yashwanth}{Gotike}
\address{Koblenz, Germany \,|\, <Tailored Role Headline, e.g. Data Engineer / Data Analyst / AI Engineer>}{}{}
\phone[mobile]{(+49)~17674755646}
\email{gycrgotike@gmail.com}
\extrainfo{\href{https://linkedin.com/in/ycrgotike}{LinkedIn: in/ycrgotike} \,|\, \href{https://github.com/ycrgotike}{GitHub: ycrgotike}}

\begin{document}
\makecvtitle
\vspace{-12pt}

% 1. Profile statement: exactly 4 rendered lines, ragged-right; background, role-specific skills, connection to job
% 2. Technical Skills: ragged-right; explicitly include core tools like Python; \section{Technical Skills}
% 3. Professional Experience: strict reverse chronological (SolTech -> GSR -> ITC Infotech); ragged-right bullets
% 4. Key Technical Projects: standalone bold title without leading bullet; 1-2 standard sub-bullets
% 5. Education: strict reverse chronological (M.Sc. Koblenz -> B.Tech. Sardar Vallabhbhai National Institute of Technology); omit expected date for full-time
% 6. Languages & Honors: strictly languages and honors/awards (no tools/skills)
% (NOTE: NEVER include "Availability" or "References" sections)

\end{document}
```

### Color overrides

The `\renewcommand*` on `\namefont` and the three `\colorlet` lines in the preamble are required on lualatex+MiKTeX. Without them the name and section headings render in black even though `\moderncvcolor{blue}` is set, which looks inconsistent with the rest of the blue accent scheme (links, bullet markers, contact icons). The cause: `moderncvstylebanking.sty` defines the name colours with `\colorlet`, which *copies* the accent colour as it is before the scheme is applied, so the name colours are frozen to the pre-scheme value; re-assigning them with `\colorlet` after `\moderncvcolor{blue}` (as the preamble does) re-pins them to `color1`. `\namefont` is the shared hook every name-style macro routes through, so the block is version-agnostic - including moderncv 2.3.1 from Debian/Ubuntu apt, which has no `\firstnamestyle`/`\lastnamestyle` at all. Both names render bold; if you prefer regular weight, change `\bfseries` to `\mdseries` in the `\namefont` line (the weight now lives there, so it applies to the whole name). Don't drop the overrides - on most modern installs the defaults render visibly wrong.

### Spacing inside itemize lists (important)

**Do not place `\vspace{...}` between `\item` entries in an `itemize` list.** Even though the source looks symmetric, this pattern occasionally produces a noticeably oversized gap before a single item: the inter-item `\vspace` creates a paragraph break that interacts unpredictably with the list's internal `\itemsep`, so LaTeX renders one of the gaps wider than the rest. Remove the inter-item `\vspace` and let `itemize` use its native uniform spacing.

```latex
% WRONG - intermittently produces an oversized gap before one bullet
\begin{itemize}
\item \textbf{Foo}: ...
\vspace{1pt}
\item \textbf{Bar}: ...
\vspace{1pt}
\item \textbf{Baz}: ...
\end{itemize}

% RIGHT - uniform spacing using the list's native itemsep
\begin{itemize}
\item \textbf{Foo}: ...
\item \textbf{Bar}: ...
\item \textbf{Baz}: ...
\end{itemize}
```

Two related patterns are fine and should be kept:
- `\vspace{1pt}` immediately after `\section{...}` (between section heading and first item) - this is between the heading and the list, not between list items.
- `\vspace{3pt}` between top-level `\cventry` blocks in Professional Experience or Education - this gives breathing room between roles and renders consistently.

### Section headings must match the CV's language (important)

Section headings such as `\section{Core Competencies}`, `Professional Experience`, `Education`, `Languages`, `Publications`, `Honors and Awards`, `References` (and any others your template defines), plus the `Available upon request.` line under References, are all **literal English text baked into the template** - they do not translate themselves. Whenever the CV language (see `CV language` in the candidate profile) is not English, translate every one of these too, whatever they are, not just the body prose - a CV with a fully localized profile statement and bullets sitting under untouched English section headers reads as sloppy and inconsistent, and it's an easy thing to forget precisely because the prose translation is the obvious, visible part of the job. Worked example for Spanish: `Competencias Clave`, `Experiencia Profesional`, `Educaci\'on`, `Idiomas`, `Publicaciones`, `Distinciones y Premios`, `Referencias`, `Disponibles a solicitud.` The same rule applies for any other target language - check this explicitly during the verification pass.

## Section-by-Section Tailoring

### Profile Statement / Elevator Pitch (Best Practice)
This is the most important section to customize. It appears right after `\makecvtitle`.

For every role and application type, write a summary of exactly 4 rendered lines covering relevant background, strongest supported role-specific skills, evidence-backed working qualities (such as analytical problem-solving, careful validation or clear communication), and concluding with an organic, natural mention of the target company and how the candidate's background enables them to support its team or initiatives (e.g., "This background enables me to support <CompanyName> with dependable data integration, automated delivery, and scalable data architectures."). Avoid blatant or formulaic phrasing like "This is how I can contribute". Check the compiled PDF, not source lines. If the summary wraps to more or fewer than four lines, revise its wording and recompile automatically; preserve factual content, role relevance, font size, margins and the two-page CV requirement. Enrollment, expected graduation, availability placement, and restrictions on repeating experience achievements are not summary requirements.

When the role sits outside your home domain, **lead with the domain-transfer argument** - the one or two sentences connecting your background to their problem (e.g. wave physics to radar signal processing) belong in the profile statement's opening, not buried in the cover letter. It is the strongest card a domain-changer holds; play it first.

**Create 2-3 profile statement templates for your main role types:**

<!-- SETUP: These are populated based on your background -->
**For Data Engineering roles:**
> Data Engineer with 5+ years of experience designing scalable ETL/ELT pipelines, distributed data warehouses, and cloud infrastructure across Azure, AWS, and GCP. Proven track record migrating ~1.5 TB of institutional data to cloud storage, reducing query latency to sub-30-minute cycles, and implementing CI/CD pipelines for Azure Databricks with GitHub Actions. Currently pursuing M.Sc. in Web and Data Science at University of Koblenz, specializing in big data architectures, Apache Spark, and Airflow. Available within 1 month.

**For Data Analytics & BI roles:**
> Data Analyst and Business Intelligence Specialist with 5+ years of analytical experience translating complex datasets into high-impact strategic insights. Expert in Python, SQL, and Power BI/DAX, having delivered exploratory analysis across 3M+ records, automated weekly reporting workflows by 40%, and driven an 18% customer retention lift via A/B testing and statistical modeling. Currently pursuing M.Sc. in Web & Data Science at University of Koblenz. Available within 1 month.

**For AI/ML, Data Science & GenAI / Agentic AI roles:**
> AI/ML Engineer with solid foundations in production data engineering, MLOps, and modern LLM application development. Experienced building end-to-end RAG systems, vector search indexing, and agentic workflows (MVP UPSC project), as well as automated time-series analytics and algorithmic trading pipelines. Skilled in Python, PyTorch, TensorFlow, MLflow, DVC, and cloud deployments on AWS. Available within 1 month.

Statements labeled *[Used for: <company>_<role>]* were extracted from archived application drafts by `/setup` Path A. They are **phrasing references, never fact sources**: when drafting from one, every factual claim still comes from `01-candidate-profile.md` - a past tailored draft does not vouch for its own accuracy.

### Technical Skills Section (Best Practice)
Always name this section `\section{Technical Skills}` (never `Core Competencies`). Reorder and emphasize based on the role. Use bold category labels.

List **5-7 key competencies/skill groups** in bullet format, tailored to the specific job. For each category, briefly explain how it adds value to the position.

Use the posting's own core term in the matching bullet's bold label when it truthfully applies - ATS and skim-reading hiring managers match literally, and "MLOps" in a heading outperforms a paraphrase like "ML Deployment".

### Education
- Always include your highest degrees
- For senior roles, keep education brief (dates and titles only)
- Include thesis topics when relevant to the target role

**Candidate-Specific Rule for Education:**
For Yashwanth's Master of Science entry (`10/2024--Present`), NEVER include "In progress, expected September 2027" or any expected completion dates in the body of the Education entry. The date column `10/2024--Present` already conveys ongoing status. Only list coursework directly:
```latex
\cventry{10/2024--Present}{Master of Science (M.Sc.) -- Web and Data Science}{University of Koblenz}{Koblenz, Germany}{}{\vspace{1pt}
Coursework: Data Science, Big Data, Machine Learning and Data Mining.
}
```
*Note on Seminars:* Yashwanth completed an advanced academic seminar on **"Data Governance Quality Assurance"** at the University of Koblenz. When data governance, quality assurance, data quality, data profiling, or compliance is mentioned in a target job description, dynamically include the seminar beside the coursework:
```latex
\cventry{10/2024--Present}{Master of Science (M.Sc.) -- Web and Data Science}{University of Koblenz}{Koblenz, Germany}{}{\vspace{1pt}
Coursework: Data Science, Big Data, Machine Learning, Data Mining \,|\, Seminar: Data Governance Quality Assurance.
}
```

### Professional Experience
- **Strict reverse chronological order:** Always list the most recent (latest) role first, followed by previous roles in descending order by date.
- Rewrite bullet points to emphasize aspects most relevant to the target role
- Use 4-6 bullets for most recent role, 3-4 for previous, 2-3 for older
- **Emphasize measurable results** where possible: "Reduced processing time by X%", "Model adopted by the team"

#### Check tenure against visible output

Before finalizing, look at each role the way a stranger will: **date span versus how much work is shown.** A two-year role represented by a single project reads as low output, whether or not that is fair. The reader cannot know what filled the time, so they guess, and the guess is unflattering.

This bites hardest on **career changers** (part of the tenure went into learning the new field), on **long-cycle work** (industrial deployment, clinical or regulatory projects, research — one delivery genuinely takes quarters), and on anyone whose employer kept them on a single account or product.

Three honest fixes, in order of preference:

1. **Surface more real work.** Ask what else the period contained. There are often real secondary projects, internal tooling, or support work that never reached the CV because it felt minor. Best fix when the material exists.
2. **Make the phases within the role explicit.** If the span genuinely had stages, say so — an initial period learning the domain or supporting the team, then ownership of the named work through to delivery. A phased arc reads as a growth curve; an undifferentiated multi-year block reads as stagnation.
3. **Name what made the cycle long.** Data collection from a live environment, validation with domain experts, deployment and iteration against real output. Reviewers who know the domain accept this immediately.

**Never** pad with invented projects, and **never** quietly shorten the employment dates so the ratio looks better. Both are discoverable, and both are worse than the perception problem being solved.

**Prepare the interview answer too.** If a long span against little visible output survives these fixes, the question is coming. The candidate needs a ready two-part answer — what actually filled the time, and what the outcome was — recorded in their interview prep rather than improvised in the room.

### Handling Employment Gaps (Best Practice)
If there is a gap in your employment history:
- The gap should be explained matter-of-factly if needed
- Describe how professional development continued during the gap
- Frame as deliberate skill-building and career repositioning

### Publications
- Include Google Scholar link if applicable
- Select 3-4 most relevant publications (not always all of them)
- For non-academic roles, keep brief

### Evidence Links
Wherever the CV names a verifiable artifact - a public project, a hackathon entry, a publication - carry its link (`\href`) so a reader can verify the claim in one click. A CV whose strongest claims are checkable reads as more credible everywhere else too.

### Honors and Awards
- Keep format brief, one line each

### Mandatory Omissions (Strict Rule)
- **NEVER include "Availability"** in the CV. Availability and work authorization belong in the Cover Letter, not the CV.
- **NEVER include "References: Available upon request"** or a References section in the CV. Employers request references separately during background checks; a references line consumes valuable page budget and signals an outdated CV layout.

### LaTeX Special Characters (important)

Postings and profile data arrive as plain text; the CV is LaTeX. Escape these wherever they land in body text - company names, achievement bullets, skill lists:

| Character | Write | Typical trigger |
|---|---|---|
| `&` | `\&` | company names: Bang \& Olufsen, Brüel \& Kjær, H\&M |
| `%` | `\%` | quantified achievements: "cut latency by 40\%" |
| `$` | `\$` | salary and cost figures |
| `#` | `\#` | "ranked \#1", C\# |
| `_` | `\_` | file names, code identifiers |
| `~` | `\textasciitilde{}` | URLs, "approx. 5 years" tildes |
| `^` | `\textasciicircum{}` | version strings, math |

Two failure modes deserve special care:

- **`%` fails silently.** An unescaped `%` starts a LaTeX comment: the compile succeeds with zero errors, and everything after the `%` on that line vanishes from the PDF. `Cut inference latency by 40% and saved DKK 2M annually` renders as "Cut inference latency by 40" - the bullet keeps its impressive-looking fragment and loses the actual result. Quantified achievement bullets are exactly where the guidance steers you ("use numbers where possible"), so check every `%` in every bullet before compiling.
- **`&` fails loudly** inside `\cventry` (alignment-tab errors, `Missing } inserted`). The compile loop catches it, but escape employer names up front rather than debugging the compile.

Related trap: a bullet whose text begins with a literal `[` must be braced - `\item {[text]}` - or LaTeX parses the bracketed text as `\item`'s optional label and renders it clipped off the left page edge with a clean compile. The example CV's placeholder bullets are braced for exactly this reason.

## Compile-and-Inspect Loop (MANDATORY)

After writing the CV and before presenting to the user, always compile and visually inspect the PDF. Iterate until the layout is clean. Workflow:

1. Run `lualatex -interaction=nonstopmode main_<company>_<role>.tex`
2. Check the output page count: must be exactly 2
3. Read the PDF via the Read tool and visually inspect both pages
4. Check for **orphaned entries**: a `\cventry` title line must never sit alone at the bottom of page 1 with its bullets on page 2

### Fixing common page-break problems

**Problem: entry title on page 1, bullets orphaned to page 2**
Add `\needspace{5\baselineskip}` immediately before the problematic `\cventry`:
```latex
\needspace{5\baselineskip}
\cventry{YEAR--YEAR}{Role Title}{Organization}{Location}{}{...}
```
Include `\usepackage{needspace}` in the preamble.

**Caveat - use `\needspace` before entries, never before `\section` headings.** A section-level `\needspace` pushes the entire section (heading plus content) to the next page whenever the request does not fit, stranding empty space above and typically *adding* a page instead of saving one. Apply it only to the individual `\cventry` that actually orphans, and only after a compile shows the orphan.

**Problem: one trailing section spills to page 3 (e.g., References alone on page 3)**
Add `\enlargethispage{2-3\baselineskip}` before a late section (e.g., before `\section{Honors and Awards}`) to stretch page 2 by a few lines. This is the standard LaTeX rescue for near-miss overflows.

**Problem: 3 pages with significant content on page 3**
Cut content — do not compress geometry or `\vspace`. See "Relevance-weighted cutting" below for the rule.

**Problem: content finishes early on page 2 (feels thin)**
Restore the highest-relevance item that was previously cut — a CV that ends mid-page 2 looks incomplete.

## ATS Parseability

Most employers run CVs through an ATS before a human sees them, and the ATS reads the PDF's embedded **text layer**, not the rendered page. A CV can pass visual inspection and still extract as garbage. After the layout passes the compile-and-inspect loop, verify the text layer:

```bash
python tools/verify_pdf.py cv/main_<company>_<role>.pdf --dump-text cv/main_<company>_<role>.txt
```

Extraction tries **pypdf** first (`pip install pypdf`, BSD license), then Poppler `pdftotext`. If a fallback still uses `pdftotext -layout`, it must also pass `-enc UTF-8`: Xpdf-based builds default to Latin-1, which makes every non-ASCII character in a perfectly good CV read back as a replacement character. If neither extractor is available, skip the mechanical check with a warning and rely on the visual PDF read for keyword coverage.

What to check in the extraction:

- **Contact details as literal text.** The stock template's fontawesome contact icons extract as glyph names (`MOBILE-ALT`, `Envelope`) - harmless noise, because the actual address and number are printed beside them. The failure mode is a contact detail carried *only* by an icon or a hyperlink (like the `LinkedIn` link text, whose URL is not in the text layer): invisible to an ATS. The email address must always appear as printed text.
- **No garbled output.** `(cid:NNN)` markers or `�` characters mean a font is embedded without a Unicode mapping - an ATS sees the same garbage. This shows up with unusual fonts in custom templates, not with the stock moderncv setup under lualatex.
- **Reading order.** The stock banking style is single-column, so extraction order matches visual order. Custom templates (via `/add-template`) with sidebars or multi-column layouts can interleave unrelated lines; if extraction order is scrambled, the user is trading ATS compatibility for looks and should be told.
- **Keyword coverage.** Match the posting's required/preferred terms against the extracted text, in the posting's language. Prefer the posting's exact term over a synonym when it is truthfully applicable - ATS matching is often literal. Never add a keyword the profile does not support.

### Date fields must be ASCII ranges (confirmed ATS import failure)

This one is worth knowing about because it fails **silently**. A CV that passes every other check in this section - clean extraction, no `(cid:)` markers, contact details intact, correct reading order - can still have its dates dropped on import. In a real Workday resume import, a CV built from this template lost the end date of a short contract role and failed to import **any** education entry at all, forcing manual re-entry. Nothing about the PDF or its text layer looked wrong.

Two independent causes, both easy to avoid:

1. **`--` in a `\cventry` date renders as an en-dash (U+2013), not a hyphen.** LaTeX ligatures `--` (two ASCII hyphens, U+002D) into a single en-dash glyph, so `2016--2024` reaches the PDF text layer as `2016<U+2013>2024`. Many parsers split date ranges only on an ASCII hyphen and see no range at all. Write the date argument with a **single hyphen**:

   ```latex
   \item{\cventry{2016-2024}{Role Title}{Organization}{Location}{}{...}}   % parses
   \item{\cventry{2016--2024}{Role Title}{Organization}{Location}{}{...}}  % en-dash, may not
   ```

   This applies to the **date argument only**. Keep `--` everywhere it is typographically correct in prose, for example a numeric range like `EUR 600k--1M`.

2. **A bare single year gives the parser no end date.** A short contract, mandate or internship written as `\cventry{2016}` imports as a start date with nothing to close it. Use an explicit range, with months where the role ran under a year:

   ```latex
   \item{\cventry{Mar 2016 - Jul 2016}{Contract Role}{Client}{Location}{}{...}}
   ```

   Where a genuine range exists, use it even when a single year would be factually accurate - a degree written `1995` is true but imports worse than `1992-1995`. Do not invent a start date you do not have; a lone graduation year is fine, just expect it to be typed in by hand.

**Add this to the step 5d checks**: after extracting the text layer, confirm every experience entry shows a start *and* an end separated by an ASCII hyphen. Because the failure is silent and invisible in the PDF, the candidate otherwise discovers it only while filling in the application form.

## Page Budget - Hard 2-Page Limit

The CV **must** fit on exactly 2 pages when compiled. Use these content limits as a guide:

| Section | Max budget |
|---------|-----------|
| Profile statement | Exactly 4 rendered lines |
| Skills | 5 items, each 1-2 lines |
| Most recent role | 4-5 bullets |
| Previous role | 2-3 bullets |
| Older roles | 2 bullets (1 line each) |
| Projects | 3-4 projects (1-2 lines each) |
| Education | 2-3 entries |
| Languages & Honors | 2 items (1 line each) |

**If in doubt, cut rather than squeeze.** Reducing `\vspace` or geometry scale to force-fit content makes the CV look cramped.

## Relevance-weighted cutting (the right way to shrink a CV)

**Cut by signal, not by section.** Static priority lists ("remove oldest education first, then shorten the earliest role...") are wrong when a relevant "lower-priority" item is competing with an irrelevant "higher-priority" item. An older-role bullet that speaks directly to the posting is worth more than a recent-role bullet that does not.

For every candidate line, score three things:

1. **Relevance to THIS posting** — does the line hit a named tool, keyword, or stated responsibility in the job ad?
2. **Uniqueness** — is it the only place this claim appears, or is it duplicated elsewhere in the CV?
3. **Narrative load** — does the cover letter depend on it? If cutting the line would force you to rewrite a cover-letter paragraph, it is load-bearing.

Cut the lowest-total-score line first, regardless of which section it sits in.

### Practical order of cuts (easiest → last resort)

1. **Redundancy.** If an achievement appears in both Core Competencies AND a role bullet, the Core Competencies version is usually the cleaner cut (the experience bullet is more concrete evidence).
2. **Profile-statement fluff.** A sentence that just restates what Publications or Skills will show.
3. **Low-relevance experience bullets.** A bullet about work that does not touch posting keywords, wherever it sits.
4. **Low-relevance supporting content.** An older-role bullet that does not speak to the target role. A language entry that can be condensed to one line.
5. **Last-resort structural cuts.** Tightening an older role to 2 bullets, condensing coursework.

### Pitfalls to avoid

- Do not mechanically cut from the bottom of a static section list without checking relevance.
- Do not cut the one concrete example the cover letter leans on.
- Do not cut to fit if the fit is borderline (2.02 pages). Prefer `\enlargethispage{2-3\baselineskip}` on a late section for near-misses; reserve content cuts for genuine overflow.

## Canonical CV Tailoring Standards

All CVs generated in this workspace must adhere to the following dynamic tailoring and layout rules:

### 1. Dynamic Tailoring for Every Application
- **Project Selection & Ordering:** Dynamically select and order projects by direct relevance to the job posting. For example, prioritize MVP UPSC for LLM/RAG/GenAI roles, Algo Trading Platform for time-series/quantitative roles, SQL Data Warehouse for BI/analytics/modeling roles, and Real-Time Pipeline for streaming/Airflow roles. For platform operations, prioritize projects demonstrating supported deployment, containers, CI/CD and infrastructure automation; do not default to trading or dashboard examples.
- **Skill Ordering by Employer Priorities:** Order skill categories and individual tools/skills to reflect the employer's stated requirements. Never present a static skill list.
- **Reordering Experience Bullets:** Reorder the bullet points within SolTech InfoLabs and G.S.R to foreground the achievements most relevant to the target role's day-to-day responsibilities.
- **Natural Terminology:** Use the posting's exact terms naturally where accurate; avoid keyword stuffing and artificial technology lists.
- **Factual Grounding & Zero Fabrication:** Knowing a technology supports listing it as a skill; claiming an implementation or achievement requires actual completed work. Preserve confirmed skills and implementations; NEVER invent metrics, responsibilities, qualifications, or outcomes.
- **Historical Accuracy:** Keep historical job titles and dates strictly accurate. Tailor the professional headline beside `Koblenz, Germany` (e.g. `Data Engineer`, `Data Analyst`, or `AI Engineer`) without implying an employment title not held.

### 2. Layout, Structure & Content Rules
- **Left-Aligned, Ragged-Right Text:** Use left-aligned, ragged-right text (`\raggedright` / `\RaggedRight`) for CV summaries, skills lists, and bullet points. Remove stretched word spacing caused by full justification while preserving date/location margin alignment in `\cventry`.
- **Role-Specific Summary:** For every role and application type, write a summary of exactly 4 rendered lines covering relevant background, strongest supported role-specific skills, evidence-backed working qualities (such as analytical problem-solving, careful validation or clear communication), and how they connect to the particular job responsibilities. Check the compiled PDF, not source lines. If the summary wraps to more or fewer than four lines, revise its wording and recompile automatically; preserve factual content, role relevance, font size, margins and the two-page CV requirement. Enrollment, expected graduation, availability placement, and restrictions on repeating experience achievements are not summary requirements.
- **Project Presentation (Standalone Title without Leading Bullet):** Format project titles as standalone bold text without a leading bullet glyph (`\textbf{Project Title (Stack)}`). Use 1 to 2 concise standard bullets underneath with consistent indentation (`\begin{itemize}\item ... \item ... \end{itemize}`). Replace any custom bullet glyphs that extract incorrectly with standard bullets. Avoid dense, technology-filled paragraphs.
- **Explicit Technical Skills Grounding:** Ensure core languages and tools emphasized elsewhere in the CV or cover letter (such as Python, SQL, Git, Docker) appear explicitly in `\section{Technical Skills}` when relevant.
- **Student Applications (Page 1 Visibility):** For student or intern roles (Werkstudent / Praktikum), make current university enrollment and expected graduation (e.g. M.Sc. Web and Data Science at University of Koblenz, expected September 2027) visible on Page 1 (within the same summary paragraph, with the entire paragraph limited to exactly 4 rendered lines). Use the application-specific availability rule in `06-cover-letter-templates.md`; never assume working-student hours apply to an internship. (For full-time roles, omit expected graduation under Education).
- **Prevent Awkward Word Breaks:** Prevent awkward automatic word breaks such as "techni-cal" and "environ-ments" (set `\hyphenpenalty=10000`), while preserving legitimate compound-word hyphens (e.g. "end-to-end", "near-real-time", "cloud-native").
- **Strict 2-Page Constraint:** The final compiled CV MUST be **exactly 2 pages**. Balance content evenly across both pages without filler, excessive whitespace, or unreadably small fonts. Keep headings with their supporting text (`\needspace`).
- **Section Naming:** Always name the primary skills section `\section{Technical Skills}` — NEVER use 'Core Competencies'.
- **Languages & Honors:** Strictly reserved for languages and honors/awards; never add tools or technical skills here.
- **Omissions:** NEVER include "Availability" or "References: Available upon request" sections in the CV.

## Recommended Section Order

The standard section order for all technical / data engineering / AI / analytics roles:

1. Profile statement / elevator pitch (exactly 4 rendered lines for every role, ragged-right; relevant background, strongest role-specific skills, connection to the job)
2. Technical Skills (ordered by employer priorities; always `\section{Technical Skills}`; ragged-right; explicitly includes core tools like Python)
3. Professional Experience (strict reverse chronological: SolTech $\rightarrow$ G.S.R $\rightarrow$ ITC Infotech; ragged-right bullets)
4. Key Technical Projects (ordered dynamically by role relevance: 3-4 projects; standalone bold titles without leading bullet; 1-2 standard sub-bullets each)
5. Education (strict reverse chronological: M.Sc. Koblenz $\rightarrow$ B.Tech. Sardar Vallabhbhai National Institute of Technology; omit expected date for full-time)
6. Languages & Honors (languages and awards only)

### Technology evidence for every role

Use `tools/technology_evidence.py` to separate positively confirmed skills, transferable experience with related tools, and technologies requiring confirmation. Only positively recorded technologies belong in Technical Skills; posting text never creates candidate facts. Preserve source evidence and unfamiliar tool candidates in the application review report. Confirmed relevant tools outside the fixed skill lists must still be considered. Rank source-backed responsibilities by specificity, repeated emphasis and supporting title context; a title never creates a duty absent from the task section. Retain all matched source excerpts and unmapped tasks in the review report. Use this priority order consistently for the summary, skills, experience and projects. Distinguish agent development, AI evaluation, controlled access and model serving; for applied AI product roles, lead with confirmed agent/API work and deployment evidence rather than generic data integration. Reprioritize specific work such as software QA, research or content operations ahead of generic reporting/documentation. Software testing is distinct from A/B testing and data-quality checks.
