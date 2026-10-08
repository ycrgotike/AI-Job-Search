"""Source-linked duty extraction. Unmapped work remains visible for review; source duties determine priorities."""
import re
from html import unescape

# Ordered only to break equal source positions, not to override posting priorities.
WORK = [
 ('ai_delivery', r'ki use cases|ki.anwendungen|ai use cases|ai applications|ki.einsatz|ai adoption strategy', 'prototyping AI use cases and improving business applications', 'ai'),
 ('qa', r'manual test|test.case|acceptance criteria|defect.{0,20}(?:track|report)|test execution|software testing|testfälle|manuelle.{0,10}test|fehlermeld', 'structured test cases, manual testing and clear defect documentation', 'data'),
 ('test_automation', r'automated tests|test automation|automatisiert.{0,15}test|testautomatisierung', 'maintainable test automation and repeatable checks', 'data'),
 ('content', r'knowledge management|support content|content.{0,25}(?:localiz|localis|quality)|localiz.{0,25}workflow', 'AI-assisted content workflows and knowledge management', 'ai'),
 ('finops', r'\bfinops\b|cloud.{0,12}(?:cost|kosten)|kosten(?:management|zuordnung|entwicklung)|cost allocation|budget.{0,30}(?:monitor|deviation)|(?:monitor|überwach).{0,30}budget', 'cloud cost analysis and cost transparency', 'analytics'),
 ('research', r'\bsurvey\b|befrag|ai usage patterns|adoption patterns|organizational.{0,30}adoption', 'survey analysis and interpretation of AI adoption', 'analytics'),
 ('records', r'kontaktdaten|leadrecherche|contact research|ansprechpartner.{0,30}recherch|doppelte einträge|crm.{0,20}(?:eintrag|records)|maintain.{0,20}contact|research and maintain data', 'researching contacts and maintaining accurate records', 'analytics'),
 ('support', r'benutzeradministration|benutzerregistr|systemkonfiguration|schulungsinhalte|supplier registrations|user support|support.{0,20}users', 'supporting users and maintaining business applications', 'data'),
 ('software', r'webanwendungen|internal tools|interner tools|code.reviews|rennorganisation|develop.{0,30}application|entwicklung.{0,30}anwendung|backend|microservices|integrat.{0,30}(?:api|service)|services, data flows, APIs', 'developing applications and integrating workflows', 'data'),
 ('database', r'pl/sql|datenbankobjekt|datenbankbasierte|relational.{0,20}model|dimensional|star.schema', 'relational modelling and reliable database workflows', 'data'),
 ('integration', r'datenquellen|data sources|\betl\b|\belt\b|data pipelines|datenpipeline|datentransformation|pipeline.architektur|integrat.{0,20}data', 'integrating data sources and automating delivery', 'data'),
 ('reporting', r'dashboard|berichte|reports|reporting|kennzahlen|\bkpi\b|content performance metrics', 'maintaining reports and explaining analytical findings', 'analytics'),
 ('quality', r'datenqualität|data\s*quality|validation\s*(?:rules|checks)|schema\s*validation|datenvalidier\w*|data\s*validation|datenpflege|data\s*governance|daten-?governance|data\s*lineage|data\s*profiling|datenintegrität|data\s*integrity', 'checking data quality and resolving inconsistencies', 'data'),
 ('platform', r'infrastructure as code|infrastruktur.{0,20}automat|terraform|platform operations|ci/cd|deploy.{0,25}(?:cloud|service|model)|(?:cloud|service|model).{0,25}deploy', 'automating infrastructure and repeatable deployments', 'platform'),
 ('models', r'feature engineering|model.{0,20}evaluat|modellevalu|model.{0,20}valid|validier.{0,20}modell|predictive|prädiktiv|training.{0,20}model|train.{0,20}model|machine learning models|pipelines und modelle', 'preparing data and evaluating predictive models', 'ai'),
 ('ai_evaluation', r'agent.{0,35}(?:quality|reliability|performance)|evaluat.{0,25}(?:agent|non.deterministic)|test datasets|evaluation criteria|accuracy, latency|observability and feedback|retrieval.qualit', 'evaluating agent reliability, latency and business impact', 'ai'),
 ('ai_safety', r'guardrails|human.in.the.loop|approval steps|agents.{0,30}(?:secure|permissions)|securely access', 'secure agent access and human review for sensitive workflows', 'ai'),
 ('model_serving', r'production integration|model.{0,30}(?:serving|usable within|production systems)|integrate machine.learning|operational tooling', 'integrating models into production services and APIs', 'ai'),
 ('agents', r'\brag\b|retrieval|chatbot|agent.based|ki.agent|\bllms?\b|\b(?:ai agents?|production agents?|agent orchestration)\b|(?:build|design|ship|integrate).{0,30}\bagents?\b|prompts, tools, memory|LangChain|LlamaIndex|Google ADK|LangGraph|context.engineering|emerging AI capabilities|own features.{0,80}production', 'developing LLM applications and retrieval workflows', 'ai'),
 ('documentation', r'dokument|\bdocument\w*|präsentation|presentation|decision templates', 'documenting processes and explaining results', 'analytics'),
]
START = r'(?:was du bei uns bewegst|your tasks(?: and responsibilities)?|your responsibilities|primary responsibilities|deine aufgaben|ihre aufgaben|aufgaben|responsibilities|tasks|was du machst|your impact|das erwartet dich|dein einsatz|these challenges|diese herausforderungen|you can move this|das kannst du bewegen|das bewegen sie|what you will do)'
STOP = r'(?:was dich auszeichnet|desired skills|qualifications|your profile|dein profil|ihr profil|qualifikation(?:en)?|was du mitbringst|was sie mitbringen|what you bring(?: with you)?|features, die|your benefits|benefits|wir bieten|what you.ll bring|what we offer|unser angebot|deine vorteile|ihre vorteile|das bieten wir|was wir bieten)'

def analyze_posting(title, description):
    text = unescape(re.sub(r'<[^>]+>', '\n', description))
    text = re.sub(r'[*#_]', '', text)
    # Heading boundaries matter: 'repetitive tasks' is not a Tasks heading.
    start = re.search(r'(?:^|\n)\s*' + START + r'\s*(?::|\n|$)', text, re.I)
    if not start:
        start = re.search(r'you will\s*(?:\.{3}|…|:)', text, re.I)
    if not start:
        start = re.search(r'\b(?:Your Tasks|Your Responsibilities|Key Responsibilities|Deine Aufgaben|Ihre Aufgaben|Was Du bei uns bewegst)\s*:?\s*', text)
    if not start:
        start = re.search(r'\bAufgaben\s*(?::\s*)?(?=Du\s|Sie\s|Ihr\s)', text)
    duties = text[start.end():] if start else text
    stop = re.search(STOP + r'|About Audible|About Us|OUR OFFER|Basic Qualifications|Preferred Qualifications|About You', duties, re.I)
    requirements = duties[stop.start():] if stop else ''
    if stop:
        duties = duties[:stop.start()]
    duties = re.sub(r'(?<=\S)\s+(?=(?:Create|Use|Build|Support|Validate|Maintain|Track|Document|Develop|Analyze|Analyse|Prepare|Monitor|Design|Own|Integrate|Turn|Evaluate|Measure|Establish|Apply|Select|Collaborate|Take)\b)', '\n', duties)
    duties = re.sub(r'(?<=\S)\s+(?=Du (?:entwickelst|analysierst|setzt|unterstützt|nimmst|optimierst|prüfst|erstellst)\b)', '\n', duties)
    fragments = [s.strip(' -•\t:') for s in re.split(r'\n|(?<=[.!?;])\s+', duties) if len(s.strip()) > 8]
    matches, unmatched = [], []
    seen = {}
    for position, fragment in enumerate(fragments):
        # Culture and benefit statements describe the workplace, not deliverables.
        if re.search(r'praxisnahe aufgaben mit|zusammenarbeit mit erfahrenen|unterstützenden kultur|supportive culture|experienced colleagues|offene.{0,20}kultur', fragment, re.I):
            continue
        found = False
        for key, pattern, label, family in WORK:
            if re.search(pattern, fragment, re.I):
                found = True
                if key not in seen:
                    match = {'kind':key, 'responsibility':label, 'source':fragment[:600], 'sources':[fragment[:600]], 'family':family, 'position':position}
                    matches.append(match)
                    seen[key] = match
                elif fragment[:600] not in seen[key]['sources']:
                    seen[key]['sources'].append(fragment[:600])
        if not found and start and re.search(r'\b(?:analy[sz]e|develop|maintain|support|manage|design|build|monitor|create|implement|prepare|own|integrate|turn|evaluate|measure|establish|apply|select|collaborate|take)\b|\b(?:entwickl\w*|erstell\w*|betreu\w*|unterstütz(?:en|ung)|analysier\w*|überwach\w*)\b', fragment, re.I):
            unmatched.append(fragment[:600])
    # Compare supported duty themes, not the first regex hit or title alone.
    # Repeated reporting/documentation must not eclipse the specialist work it supports.
    agent_work = any(m['kind'] == 'agents' for m in matches)
    content_work = any(m['kind'] == 'content' for m in matches)
    if content_work and not re.search(r'build.{0,25}agents|production agents|agent.based', duties, re.I):
        matches = [m for m in matches if m['kind'] not in ('agents','ai_evaluation','ai_safety')]
        agent_work = False
    if agent_work and not re.search(r'\bQA\b|quality assurance|test engineer', title, re.I):
        # Agent evaluation is different from manual software QA and data-quality checks.
        matches = [m for m in matches if m['kind'] not in ('qa','test_automation')]
    if any(m['kind'] == 'qa' for m in matches):
        matches = [m for m in matches if (m['kind'] not in ('reporting','documentation') or not re.search(r'\btest|\bQA\b',m['source'],re.I)) and (m['kind'] != 'quality' or re.search(r'data quality|datenqualität',m['source'],re.I))]
    title_patterns = {
        'finops':r'finops|cost management', 'qa':r'\bQA\b|quality assurance|test engineer',
        'agents':r'(?:applied|generative|agentic) ai|llm|ai engineer',
        'models':r'machine learning|data scientist', 'content':r'content|knowledge management',
        'research':r'thesis|research', 'database':r'database|datenbank',
        'integration':r'data engineer', 'platform':r'platform|devops|infrastructure',
        'records':r'leadrecherche|crm', 'support':r'support', 'reporting':r'analyst|business intelligence',
    }
    generic = {'reporting','documentation','quality','software'}
    for match in matches:
        kind = match['kind']
        # A title can reinforce a duty already found, never invent one.
        title_match = bool(re.search(title_patterns.get(kind, r'(?!)'), title, re.I))
        match['priority_score'] = (4 if kind not in generic else 0) + min(len(match['sources']),3) + (3 if title_match else 0)
        if agent_work and kind in ('agents','ai_evaluation','model_serving','ai_safety'):
            match['priority_score'] += 3
        match['priority_reason'] = 'Supported duty frequency and specificity' + ('; consistent with role title' if title_match else '')
    matches.sort(key=lambda m: (-m['priority_score'], m['position']))
    selected = matches[:3]
    if re.search(r'\b(?:senior|lead|principal|staff|director|head\s+of)\b', title, re.I):
        application_type = 'professional'
    elif re.search(r'\b(?:thesis|masterarbeit|abschlussarbeit)\b', title, re.I):
        application_type = 'thesis'
    elif re.search(r'\b(?:werkstudent\w*|working\s*student)\b', title, re.I):
        application_type = 'working_student'
    elif re.search(r'\b(?:praktik\w*|intern|internship|interns)\b', title, re.I):
        application_type = 'internship'
    else:
        application_type = 'professional'
    skills = [s for s in ['Python','SQL','Power BI','Excel','PowerPoint','ServiceNow','VBA','Oracle','PL/SQL','Azure','Databricks','Docker','Terraform','Kubernetes']
              if re.search(r'(?<!\w)'+re.escape(s)+r'(?!\w)',requirements,re.I)]
    logistics = [s.strip() for s in text.splitlines() if re.search(r'\b(start|duration|standort|location|stunden|hours|months|monate|on.site|remote)\b',s,re.I)]
    issues = []
    fallback = not selected
    if fallback and text.strip():
        selected = [{'kind':'general', 'responsibility':'careful analysis, reliable data preparation and clear communication',
                     'source':duties[:600], 'family':'analytics', 'position':0}]
    warnings = ['Unmapped task statements to review: ' + ' | '.join(unmatched)] if unmatched else []
    if fallback:
        warnings.append('No specialist duty mapping found: this transferable-skills draft needs role-specific content review.')
    return {'responsibilities':selected,'all_responsibilities':matches,'required_skills':skills,'application_type':application_type,'logistics':logistics[:8], 'review_issues':issues, 'review_warnings':warnings, 'unmapped_tasks':unmatched, 'duty_fragments':fragments}

# Each source is candidate evidence; each bridge explicitly describes prospective work.
EVIDENCE = {
 'ai_delivery': ('AI project development and practical evaluation', 'AI & RAG Project', ['assistant','semantic'], 'I would use this project experience to clarify a business use case, build a small prototype and review its outputs with the team before extending the implementation. I would document limitations and compare the proposed approach with the needs of the people using it.'),
 'qa': ('Application behaviour and reliability', 'Software Consulting Role', ['application', 'response'], 'This application background is transferable to understanding user workflows and expected behaviour. I would use it when learning to design traceable test cases, record manual test results and describe defects with reproducible steps and clear expected-versus-actual outcomes.'),
 'test_automation': ('Automation and repeatable delivery', 'Data Engineering Role', ['CI/CD'], 'This deployment experience provides a foundation for learning the team’s test automation conventions, running repeatable checks and investigating failures with developers.'),
 'general': ('Analysis and reliable reporting', 'Analytics Role', ['exploratory', 'Power BI'], 'This background gives me transferable experience in checking information, investigating unexpected results and presenting findings clearly. I would first learn the role-specific processes and agree the expected outputs with the team.'),
 'content': ('AI workflows and content quality', 'AI & RAG Project', ['assistant', 'semantic'], 'I would apply this project experience to checking AI-generated support content against source material, testing prompts and documenting where human review is needed. For localized content, I would work with qualified language reviewers rather than assume that an automated translation is accurate.'),
 'finops': ('Cloud Cost Optimization & Infrastructure Efficiency', 'Data Engineering Role', ['infrastructure overhead', 'Migrated'], 'I would use this cloud background to investigate cost trends and potential savings, checking how usage, ownership and operational needs affect the figures before recommending changes. This foundation allows me to analyze budget deviations collaboratively and ensure transparent cloud cost accounting.'),
 'research': ('Quantitative Research & Statistical Analysis', 'Analytics Role', ['hypothesis', 'exploratory'], 'I would apply these analytical methods to research questions, inspect response completeness and explain limitations alongside findings to support evidence-based decision-making.'),
 'records': ('Data Consolidation & Record Trustworthiness', 'Data Engineering Role', ['consolidate', 'central'], 'I would use this experience when checking record completeness, tracing sources and resolving duplicates before the information is used across operational systems and reporting.'),
 'support': ('Enterprise Application Integration & User Support', 'Software Consulting Role', ['application', 'integration'], 'I would learn the application workflows, reproduce reported issues and document changes so users and technical colleagues can follow the resolution smoothly.'),
 'software': ('Application Modernization & Workflow Integration', 'Software Consulting Role', ['application', 'integration'], 'I would apply this experience to understanding user needs, tracing interfaces and testing changes against the workflow they support to maintain high software quality and availability.'),
 'database': ('Relational Data Modeling & Dimensional Architecture', 'Data Warehouse Project', ['dimensional', 'queries'], 'I would use this foundation to understand the existing data model, test queries against representative records and investigate inconsistent results to maintain high relational integrity.'),
 'integration': ('Data Integration & Automated Pipeline Delivery', 'Data Engineering Role', ['ETL', 'latency'], 'I would apply this experience to source mapping, dependable data delivery and checks that keep downstream reporting consistent, robust, and resilient against schema changes.'),
 'reporting': ('Business Intelligence & Automated Analytics', 'Analytics Role', ['Power BI', 'Automated data analysis'], 'I would use this reporting experience to clarify metric definitions, investigate unexpected changes and prepare outputs that decision-makers can interpret with actionable confidence.'),
 'quality': ('Data Quality Validation & Enterprise Governance', 'Data Warehouse Project', ['quality', 'queries'], 'I would apply these checks to finding inconsistencies, documenting their sources and verifying corrections before data is reused across reporting pipelines.'),
 'platform': ('Platform Automation & Repeatable CI/CD Delivery', 'Data Engineering Role', ['CI/CD', 'ETL'], 'I would use this delivery experience to test platform changes, understand dependencies and document repeatable deployment procedures to maintain continuous platform availability.'),
 'models': ('Machine Learning & End-to-End MLOps', 'MLOps Pipeline Project', ['model', 'MLOps'], 'I would apply this project experience to reproducible experiments, evaluation and checking how models behave beyond their training data in production environments.'),
 'ai_evaluation': ('Model serving and deployment', 'MLOps Pipeline Project', ['MLOps'], 'This project connects model work with versioned artifacts, API serving and automated delivery. I would apply that foundation when integrating agent features with existing backend services and release processes.'),
 'ai_safety': ('Agent context and controlled access', 'AI & RAG Project', ['semantic'], 'I would define the data each tool may access, test permission boundaries and require human review before sensitive actions.'),
 'model_serving': ('Model integration and operation', 'MLOps Pipeline Project', ['MLOps'], 'I would connect model serving to the product APIs, monitor failures and document operational checks so that updates remain traceable and maintainable.'),
 'agents': ('Agent workflows and API integration', 'AI & RAG Project', ['assistant', 'semantic'], 'I would use this project experience to test retrieval quality, examine responses against source material and document application limitations before relying on generated outputs in product workflows.'),
 'documentation': ('Analytical Documentation & Knowledge Transfer', 'Analytics Role', ['Power BI', 'Automated data analysis'], 'I would prepare clear explanations of assumptions, results and limitations, and keep process documentation usable for the people maintaining the work across technical and business teams.'),
}

def compose_evidence(plan, read_bullets):
    """Select evidence by duty, deduplicate facts, preserve source wording verbatim."""
    blocks, used = [], set()
    for duty in plan['responsibilities']:
        if len(blocks) == 2:
            break
        if duty['kind'] == 'documentation' and any(d['kind']=='reporting' for d in plan['responsibilities']):
            continue
        heading, source, priorities, bridge = EVIDENCE[duty['kind']]
        profile_heading = {'Analytics Role':'Data Analyst', 'Data Engineering Role':'Data Engineer', 'Software Consulting Role':'Associate Consultant'}.get(source, source)
        try:
            candidates = read_bullets(profile_heading)
        except Exception:
            candidates = []
        ranked = sorted(candidates, key=lambda s: -sum(t.lower() in s.lower() for t in priorities))
        fact_limit = 1 if plan['responsibilities'][0]['kind'] in ('content','qa','test_automation') else 2
        chosen = [s for s in ranked if s not in used and any(t.lower() in s.lower() for t in priorities)][:fact_limit]
        if not chosen:
            continue
        used.update(chosen)
        facts = ' '.join('I ' + fact[0].lower() + fact[1:] for fact in chosen)
        context = f'In my {source}, '
        blocks.append((heading, context + facts + ' ' + bridge))
    if not blocks:
        blocks = [('Engineering & Delivery', 'I bring proven experience in designing, testing, and delivering scalable data pipelines and software workflows with measurable operational reliability.')]
    return blocks
