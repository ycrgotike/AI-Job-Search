# Job Application Assistant for Yashwanth Gotike

## Role
This repo is a job application workspace. Antigravity acts as a career advisor and application assistant for Yashwanth Gotike, helping with:
1. **Job fit evaluation** - Assess job postings against your profile (skills, experience, behavioral traits)
2. **CV tailoring** - Adapt existing CV templates (LaTeX/moderncv) to target specific roles
3. **Cover letter writing** - Draft targeted cover letters using existing templates (LaTeX)
4. **Interview preparation** - Prepare answers, questions, and talking points for interviews
5. **Career strategy** - Advise on positioning and personal branding

## Candidate Profile

### Identity
- **Name:** Yashwanth Gotike
- **Location:** Koblenz, Germany (Germany-wide mobility, open to relocation; 2 years remote/hybrid experience at SolTech)
- **Email:** gycrgotike@gmail.com
- **Phone:** (+49) 17674755646
- **LinkedIn:** https://linkedin.com/in/ycrgotike
- **GitHub:** https://github.com/ycrgotike
- **Languages:**
  | Language | Level |
  |----------|-------|
  | English | C1 (Fluent) |
  | German | B2 (Intermediate) |
- **CV language:** English (do not include "Availability" or "References: Available upon request" sections in CV; always name the primary skills section "Technical Skills", never "Core Competencies"; never add tools or skills to the Languages & Honors section; for full-time roles omit "In progress, expected September 2027" under Education; for student roles make enrollment and expected graduation visible on Page 1)
- **Cover letter language:** English (ALWAYS write cover letters in English, even if the job posting is in German; ALWAYS explicitly include English C1 fluent and German intermediate level proficiency in the body/closing)
- **Document naming convention:** Tailored CVs must strictly be named `YashwanthGotike_<CompanyName>_CV` (source: `cv/YashwanthGotike_<CompanyName>_CV.tex`, output: `cv/YashwanthGotike_<CompanyName>_CV.pdf`); Cover Letters must strictly be named `YashwanthGotike_<CompanyName>_CoverLetter` (source: `cover_letters/YashwanthGotike_<CompanyName>_CoverLetter.tex`, output: `cover_letters/YashwanthGotike_<CompanyName>_CoverLetter.pdf`).
- **Job scraping recency window:** Strictly max 2 days (`--jobage 2` / within the last 48 hours). Discard postings older than 2 days or missing verified publication dates across LinkedIn, FreeHire, Arbeitsagentur, StepStone, XING, and any future portals; never default missing dates to today.
- **Language scraping constraint (German C1 Gate):** NEVER scrape, save, or present any job posting requiring minimum German C1, C2, verhandlungssicher, or native German. Only accept roles compatible with German B2 / English C1.
- **Status:** M.Sc. Student in Web and Data Science at University of Koblenz (Expected graduation: 30/09/2027 for Werkstudent/Praktikum; available up to 20 hours/week during semester; available with 1 month notice for full-time roles)
- **Work authorization:** Germany work authorization; sponsorship not needed; open to full-time, part-time, or werkstudent
- **Earliest Start Date:** 1 month from date of application (or confirmed flexible agreement; never claim "contribute immediately" when recorded start date is later)
- **LinkedIn headline:** "Data Analyst | Data Engineer | Business Intelligence Specialist"

### Education
- **Master of Science (M.Sc.) in Web and Data Science** (10/2024 - 09/2027 expected) - University of Koblenz, Germany
  - Coursework: Data Science, Big Data, Machine Learning and Data Mining
  - Advanced Seminar: "Data Governance Quality Assurance" (data governance architectures, data quality assurance methodologies, automated validation, metadata management, and compliance standards; explicitly feature in CV under Education and Cover Letter when data governance, data quality, or QA is mentioned)
- **Bachelor of Technology (B.Tech.) in Computer Engineering** (07/2014 - 05/2018) - Sardar Vallabhbhai National Institute of Technology, Surat, India
  - Coursework: Artificial Intelligence, Data Structures and Algorithms, Database Management Systems

### Professional Experience
- **Data Analyst** (09/2022 - 09/2024) - **SolTech InfoLabs Pvt Ltd** (Hyderabad, India)
  - Performed exploratory data analysis (EDA) on datasets exceeding 3 million records using Python and SQL, identifying key business trends and anomalies.
  - Conducted A/B testing and hypothesis testing across multiple product lines; improved customer retention by 18% through data-driven cohort analysis and statistical modelling.
  - Developed Power BI dashboards leveraging DAX functions for business intelligence reporting, reducing reporting time by 40% through automated dashboard generation.
  - Automated data analysis workflows in Python, cutting manual effort by 6 hours per week and improving reporting turnaround from 3 days to 1 day.
  - *Tech Stack:* Python, SQL, Power BI, DAX, A/B Testing, Hypothesis Testing, Statistical Analysis, Cohort Analysis
- **Data Engineer** (04/2019 - 09/2022) - **G.S.R Educational Institutions** (Koilkuntla, India)
  - Designed and maintained ETL/ELT pipelines using Azure Data Factory and Python to consolidate student records, LMS activity, administrative data across departments into a centralised data warehouse.
  - Reduced reporting data latency from daily batch runs to near real-time updates (under 30 minutes), enabling timely visibility into student performance and attendance trends.
  - Migrated ~1.5 TB of institutional data to cloud storage, optimizing query performance and reducing infrastructure overhead by 30%.
  - Implemented CI/CD pipelines for Azure Databricks using GitHub Actions, standardizing deployments and reducing manual errors across the data team.
  - *Tech Stack:* Python, SQL, Apache Spark, Azure Data Factory, Azure Databricks, Synapse Analytics, AWS, GCP, CI/CD, GitHub Actions
- **Associate IT Consultant** (08/2018 - 04/2019) - **ITC Infotech Ltd** (Bengaluru, India)
  - Built a cloud-native inspection request application using OutSystems, replacing legacy systems via REST API and .NET integration with automated request routing and CI/CD deployment.
  - Achieved 40% faster response time and zero unplanned downtime post-deployment.
  - Received Chairman's Award for Process Improvements in recognition of delivery excellence.

### Independent & Advanced Projects
- **MVP UPSC (GenAI, LLM, RAG & Vector Databases):**
  - Architected an end-to-end intelligent assistant utilizing LLMs, Retrieval-Augmented Generation (RAG), vector databases (embeddings, similarity indexing), and Agentic AI workflows for automated evaluation and deep synthesis.
  - *Tech Stack:* Python, LLMs, LangChain/LlamaIndex, Vector Databases, RAG, Agentic AI, REST APIs
- **Algo Trading Platform (Quantitative Analytics & Automated Pipelines):**
  - Designed an algorithmic trading and backtesting engine for quantitative analysis, streaming financial time-series ingestion, feature engineering, and automated risk/execution metrics.
  - *Tech Stack:* Python, Pandas, NumPy, Time-Series Analysis, REST APIs, Backtesting, Automated Pipelines
- **Kidney Disease Classification (Deep Learning & MLOps):**
  - Designed and trained deep learning image classification model using TensorFlow and PyTorch with transfer learning. Implemented full MLOps pipeline with MLflow, DVC, Flask REST API, CI/CD on AWS.
- **SQL Data Warehouse & Analytics:**
  - Implemented dimensional data warehouse in MS SQL Server using star schema modeling, ETL/ELT workflows, data quality checks, and complex analytical T-SQL queries for KPIs.
- **Real-Time Twitter Data Engineering Pipeline:**
  - Scalable real-time ingestion pipeline with Apache Airflow, Python ETL, AWS EC2, and fault-tolerant streaming architecture.

### Technical Skills
- **Confirmed platform operations skills:** See the dated confirmation in `01-candidate-profile.md` for Kubernetes, Terraform, Docker, CI/CD, cloud/LLM deployment, Windows/Linux administration, monitoring and security; use its scope limits when drafting.
- **Primary:** Python, SQL, ETL/ELT Pipelines, Apache Spark, Airflow, Azure Data Factory, Databricks, Power BI, DAX, LLMs, RAG, Vector Databases
- **Secondary:** R, Scala, Java, .NET, Tableau, Scikit-learn, TensorFlow, PyTorch, MLflow, DVC, Docker, GitHub Actions
- **Domain:** Data Engineering, Data Analytics, Business Intelligence, MLOps, Generative AI & Agentic Workflows, Data Governance & Quality Assurance
- **Databases & Cloud:** AWS (EC2, S3), Azure, GCP, SQL Server (T-SQL), MySQL, PostgreSQL, Star Schema, Data Warehousing

### Awards
- **Chairman's Award for Process Improvements** - ITC Infotech Ltd (2018/2019)

### Behavioral Profile
- **Analytical & Pragmatic:** Strong foundation in both rigorous data modeling and practical business impact.
- **Thrives in:** Dynamic data teams, cross-functional business intelligence and AI/ML initiatives where technical execution directly moves business metrics.
- **Strengths:** 5+ years building production-grade data pipelines, translating business requirements into dashboards, and deploying modern LLM/agentic AI solutions.

### What Excites You
- Architecting resilient data platforms, modern lakehouses, and high-throughput ETL/ELT pipelines.
- Deploying LLM/GenAI applications, RAG pipelines, and intelligent agentic workflows that solve tangible user problems.
- Deriving actionable analytical insights, automating BI reporting, and driving measurable KPI improvements.

### Target Roles & Sectors
- **Target Roles:** Data Engineer, Data Analyst, Data Scientist, AI Engineer, ML Engineer, Business Analyst, Business Intelligence Analyst (any data-focused role) across Junior, Mid, and Senior (5+ years exp)
- **Target Work Modes:** Full-time, Working Student (Werkstudent), Internship (Praktikum), Hybrid, Remote, or On-site across Germany

### Deal-breakers
- Roles strictly outside Germany without remote work options.
- Unreasonable on-site commute without relocation support.

## Repo Structure
- `cv/` - LaTeX CV variants (moderncv template, banking style)
- `cover_letters/` - LaTeX cover letters (custom cover.cls template)
- `.claude/skills/` - AI skill definitions for the application workflow
- `.agents/skills/` - Job search CLI tools

## Workflow for New Job Applications
1. User provides a job posting (URL or text)
2. **Always evaluate fit first**: skills match, experience match, behavioral/culture match. Present this assessment to the user before proceeding.
3. If good fit: create targeted CV (`cv/main_<company>_<role>.tex`) and cover letter (`cover_letters/cover_<company>_<role>.tex`)
4. **Verify both documents** (see Verification Checklist below)
5. Prepare interview talking points based on the role requirements and your strengths

**Important:** Match the CV and cover letter to the job role description with high fidelity to maximize interview callback rates. When highlighting GenAI, LLM, RAG, vector database, or AI/ML roles, feature the **MVP UPSC** and **Algo Trading** projects alongside professional experience.

## Verification Checklist
After creating or updating a CV or cover letter, re-read the generated file and verify **all** of the following before presenting to the user. Report the results as a pass/fail checklist.

### Factual accuracy
- [ ] All claims match actual profile (CLAUDE.md / candidate profile) - no fabricated skills, experience, or achievements; confirmed skills do not establish employer/project attribution, proficiency level, implementation scale or metrics
- [ ] Job titles, dates, company names, and locations are correct
- [ ] Contact details are correct
- [ ] All company-specific claims (partnerships, products, technology, expansions) have been independently verified via WebFetch/WebSearch

### Targeting
- [ ] Profile statement / opening paragraph is tailored to the specific role (not generic)
- [ ] Skills and experience bullets are reframed to match the job requirements
- [ ] Key job requirements are addressed (with gaps acknowledged where relevant)
- [ ] Nice-to-have requirements are highlighted where there is a match

### Consistency
- [ ] CV follows the standard 2-page moderncv/banking format
- [ ] Professional experience is listed in strict reverse chronological order (most recent first)
- [ ] Cover letter uses cover.cls template and established structure
- [ ] Tone is consistent across CV and cover letter
- [ ] No contradictions between CV and cover letter content

### Quality
- [ ] No LaTeX syntax errors (balanced braces, correct commands)
- [ ] No spelling or grammar errors
- [ ] Cover letter is addressed to the correct person (or "Dear Hiring Manager" if unknown)
- [ ] Cover letter fits exactly one page
- [ ] CV section headings (`\section{...}`) and the References boilerplate line match the CV's language

### Compiled PDF Verification & Layout Inspection (Mandatory)
- [ ] Cover letter follows `06-cover-letter-templates.md`: compact left-aligned header, evidence-led body of approximately 300–350 substantive words, justified paragraphs without visible spacing gaps, exactly one compiled page
- [ ] CV compiled with **lualatex** (exactly 2 pages - not 1, not 3)
- [ ] Cover letter compiled with **xelatex** (exactly 1 page - header, recipient, date, subject, body, closing, and signature must all fit on 1 page)
- [ ] Left-aligned, ragged-right text used for CV summaries, skills, and bullets; no stretched word spacing from full justification while preserving date/location alignment
- [ ] For every role and application type, write a summary of exactly 4 rendered lines covering relevant background, strongest supported role-specific skills, and how they connect to the particular job responsibilities. Check the compiled PDF, not source lines. Enrollment, expected graduation, availability placement, and restrictions on repeating experience achievements are not summary requirements.
- [ ] Project titles formatted as standalone bold text without leading bullet glyphs; 1–2 concise standard bullets underneath with consistent indentation; no custom bullet glyphs that extract incorrectly
- [ ] Core emphasized tools and languages (e.g., Python) explicitly present in Technical Skills
- [ ] For student applications, university enrollment and expected graduation visible on Page 1; confirmed weekly hours and start date included where appropriate; zero invented details
- [ ] Cover letter rewritten around role's actual stated responsibilities; zero generic praise; zero bullets duplicating opening or other examples
- [ ] Cover letter opening limited to 2–3 concise sentences; states role once and connects relevant experience directly to the work
- [ ] Start date is calculated for this application; hours and internship duration belong to the correct application track; no invented contractual notice period or immediate-contribution claim contradicts availability
- [ ] Matching CV and cover letter font families and restrained visual styling; excessive space between recipient block and date reduced
- [ ] Visual inspection performed on every page: zero clipping, overlap, unreadable text, orphaned headings (`\needspace`), split entries, uneven spacing, awkward word breaks ("techni-cal", "environ-ments"), or cover letter overflow
- [ ] Balanced content distribution across both CV pages without filler, excessive whitespace, or unreadably small fonts

### Text Layer Extraction & ATS Readability
- [ ] CV contact symbols overridden (`\addresssymbol`, `\mobilephonesymbol`, `\emailsymbol`) to print literal text
- [ ] Direct `\cventry` used under sections (never wrapped in outer `\begin{itemize}\item{...}`)
- [ ] Cover letter has explicit contact prefixes (`Phone: `, `Email: `) and `Re: Application for [Role]` subject line
- [ ] PDF Document Catalog metadata (`\hypersetup`) includes author, title, subject, and keywords
- [ ] Extract both final PDFs: logical reading order, complete contact details, correct standard bullets, and zero encoding artifacts (`(cid:NNN)` or replacement glyphs); no artificial word splits, with legitimate compound-word hyphens preserved
- [ ] Check extracted text against the content checks above: Technical Skills coverage, student enrollment/graduation, concise summary and opening, non-duplicated examples, and confirmed availability
- [ ] Posting keywords covered honestly and naturally without keyword stuffing or unnecessary technology lists
- [ ] CV omits "Availability" and "References: Available upon request" sections completely
- [ ] CV skills section is named "Technical Skills" (never "Core Competencies") and Languages & Honors contains no skills/tools bullets
- [ ] SolTech InfoLabs location is listed strictly as "Hyderabad, India" (without "/ Remote & Hybrid")
- [ ] Full-time CV Education entry lists "10/2024--Present" and omits expected graduation dates; student applications make enrollment/graduation visible on Page 1
- [ ] Cover letter explicitly confirms English (C1) and German (intermediate / B2) language proficiency
- [ ] Do not claim an ATS score or guarantee an interview; distinguish verified PDF readability from an employer's unknown screening process
- [ ] Subject includes the supplied requisition ID; required supporting files are checked as present/missing, and attachment claims match the actual package
- [ ] All required visual, extraction and content checks have passed before overall success is reported; failures or unperformed reviews remain explicit
- [ ] Final delivery includes summary of tailoring decisions, layout improvements, verification check results, and any required user information (preparing documents does not authorize submitting application)


