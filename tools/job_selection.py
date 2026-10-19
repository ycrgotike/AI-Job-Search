"""Shared role relevance and conservative posting deduplication.

Target scope follows CLAUDE.md and the canonical scraper search strategy.
Search keywords and student status alone are not evidence of relevant work.
"""
import html
import re
import unicodedata
from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


DATA_ENGINEERING = 'Data Engineering'
ANALYTICS = 'Data Analytics & BI'
AI = 'AI / ML & GenAI'
STUDENT = re.compile(r'\b(?:werkstudent\w*|working\s+student|intern(?:ship)?|praktik\w*|master(?:arbeit|\s+thesis)|abschlussarbeit|studentische\s+hilfskraft)\b', re.I)
DUAL_STUDY = re.compile(
    r'\b(?:dual(?:e[snmr]?)?\s+(?:(?:bachelor|master)\s*)?'
    r'(?:studium|studieng(?:ang|änge)|stud(?:y|ies)|students?)|'
    r'dualstud(?:ium|ent(?:in|en)?))\b', re.I)


def is_dual_study_posting(title, description=''):
    """Identify the posting's study programme, not an employer's other offers."""
    def plain(value):
        text = re.sub(r'<[^>]+>', ' ', html.unescape(str(value or '')))
        return re.sub(r'[\s\-–—‐‑]+', ' ', text).strip()

    if DUAL_STUDY.search(plain(title)):
        return True
    text = plain(description)
    if re.match(r'(?:(?:stellenbeschreibung|job description|about this role)\s*:?\s*)?'
                + DUAL_STUDY.pattern, text, re.I):
        return True
    # Explicit job-type labels and statements remain detectable when the title
    # is simply "Data Scientist". Generic careers-page boilerplate is ignored.
    context = (
        r'\b(?:position|role|job title|job type|employment type|contract type|'
        r'stellenbezeichnung|beschäftigungsart|anstellungsart|vertragsart)\s*:\s*',
        r'\bthis\s+(?:role|position|programme|program)\s+is\s+(?:a\s+)?',
        r'\b(?:du\s+(?:absolvierst|beginnst|startest)|wir\s+bieten\s+dir)\s+(?:ein\s+)?',
        r'\byou\s+will\s+(?:complete|start|begin|undertake)\s+(?:a\s+)?',
    )
    return any(re.search(prefix + DUAL_STUDY.pattern, text, re.I) for prefix in context)

# Match whole role terms, not incidental substrings such as "AI" in "Retail".
ROLE_PATTERNS = (
    (AI, r'\b(?:data\s+(?:science|scientist\w*)|machine\s+learning|deep\s+learning|computer\s+vision|mlops|genai|generative\s+ai|llms?|nlp|artificial\s+intelligence|künstliche\s+intelligenz)\b'),
    (DATA_ENGINEERING, r'\b(?:data\s+(?:engineer\w*|warehouse|platform|lake|integration|quality|governance|management|architect\w*|operations)|analytics\s+engineer\w*|daten(?:ingenieur\w*|management|plattform\w*|qualität|integration)|etl|elt|databricks|lakehouse)\b'),
    (ANALYTICS, r'\b(?:data\s+(?:analyst\w*|science|scientist\w*|analytics)|business\s+(?:intelligence|analytics|analyst\w*)|daten(?:analyse|analyst\w*|wissenschaft\w*)|analytics|power\s*bi|bi\s+(?:analyst\w*|developer\w*|engineer\w*|entwickler\w*|consultant\w*)|reporting\s+analyst\w*|quantitative\s+(?:analyst\w*|research\w*))\b'),
)
TECHNICAL_ROLE = re.compile(r'\b(?:engineer\w*|developer\w*|entwickler\w*|architect\w*|architekt\w*|analyst\w*|scientist\w*|research\w*|forscher\w*|berater\w*|consultant\w*|experte\w*|specialist\w*|spezialist\w*)\b', re.I)
UNRELATED = re.compile(r'\b(?:social\s+media|content\s+(?:creation|creator|show|marketing)|graphic\s+design|grafik|mediendesign|product\s+design|customer\s+(?:support|service)|kundenservice|talent\s+acquisition|recruit\w*|human\s+resources|employer\s+branding|key\s+account|vertrieb\w*|sales|marketing|pflege\w*|nurse|handwerk\w*)\b', re.I)
ACTION = r'\b(?:build\w*|develop\w*|design\w*|implement\w*|maintain\w*|deploy\w*|train\w*|evaluate\w*|automat\w*|optim[izs]\w*|analys[ei]\w*|analyz\w*|ingest\w*|model\w*|architect\w*|operat\w*|entwick\w*|erstell\w*|aufbau\w*|betreib\w*|auswert\w*|implementier\w*|konzipier\w*|analyse\w*)\b'
DUTIES = (
    (DATA_ENGINEERING, r'\b(?:data\s+(?:pipelines?|warehouses?|lakes?|platforms?|integration)|etl|elt|datenpipelines?|datenplattform\w*|datenintegration|lakehouse)\b'),
    (AI, r'\b(?:machine\s+learning|ml\s+models?|llms?|rag\s+(?:systems?|pipelines?)|agentic\s+(?:systems?|workflows?)|ai\s+(?:systems?|models?|solutions?)|computer\s+vision|sprachmodel\w*)\b'),
    (ANALYTICS, r'\b(?:dashboards?|power\s*bi|business\s+intelligence|data\s+analysis|datenanalyse|statistical\s+(?:analysis|models?)|predictive\s+(?:models?|analytics)|analytical\s+(?:reports?|models?))\b'),
)


def role_category(title, description=''):
    """Return a target discipline, or None for an unrelated/unsupported role."""
    if is_dual_study_posting(title, description):
        return None
    title = re.sub(r'[-–—/&]+', ' ', html.unescape(str(title or '')))
    # Explicit core job titles are stronger evidence than department names.
    direct = re.search(r'\b(?:data\s+(?:engineer\w*|analyst\w*|scientist\w*)|analytics\s+engineer\w*|bi\s+(?:analyst\w*|entwickler\w*|developer\w*)|analytics|business\s+intelligence|power\s*bi)\b', title, re.I)
    if not UNRELATED.search(title) or direct:
        for category, pattern in ROLE_PATTERNS:
            if re.search(pattern, title, re.I):
                # ML/AI terms can also describe sales or product jobs; require
                # an engineering/research/consulting or student role context.
                if category != AI or TECHNICAL_ROLE.search(title) or STUDENT.search(title):
                    return category
        if re.search(r'\b(?:ai|ki|ml)\b', title, re.I) and (TECHNICAL_ROLE.search(title) or STUDENT.search(title)):
            return AI
    elif not direct:
        return None

    # Adjacent titles qualify through explicit technical responsibilities,
    # rather than a tools list, an employer bio, or working alongside engineers.
    text = responsibility_text(description)
    for category, noun in DUTIES:
        if re.search(ACTION + r'[^.!?;\n]{0,120}' + noun, text, re.I):
            return category
    return None


def responsibility_text(description):
    """Limit adjacent-role evidence to task sections or imperative duty sentences."""
    text = html.unescape(re.sub(r'<[^>]+>', ' ', str(description or '')))
    text = re.sub(r'[-–—]+', ' ', text)
    start = re.search(r"\b(?:responsibilities|your\s+(?:tasks|responsibilities|impact)|in\s+this\s+role|what\s+you(?:'ll|\s+will)\s+do|(?:deine|ihre)\s+aufgaben|aufgaben|damit\s+unterstützen\s+sie\s+uns)\b", text, re.I)
    if start:
        text = text[start.end():]
        end = re.search(r"\b(?:requirements|qualifications|your\s+profile|what\s+you\s+bring|benefits|(?:dein|ihr)\s+profil|das\s+wünschen\s+wir|das\s+bringst\s+du)\b", text, re.I)
        return text[:end.start()] if end else text
    # Employer introductions and technology wishlists do not establish duties.
    sentences = re.split(r'[.!?;\n]+', text)
    return '\n'.join(sentence for sentence in sentences if re.match(
        r"\s*(?:[-*•]|\d+[.)])?\s*(?:(?:you(?:'ll|\s+will)?|du|sie)\s+)?" + ACTION,
        sentence, re.I))


def display_category(title, description=''):
    family = role_category(title, description)
    return 'Werkstudent & Intern' if family and STUDENT.search(title or '') else family


def _plain(text):
    text = html.unescape(re.sub(r'<[^>]+>', ' ', str(text or ''))).replace('ß', 'ss')
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()


def company_identity(company):
    text = _plain(company)
    text = re.split(r'\s+von\s+jobs[-.]|\s*[-–]\s*welcome\s+traveler', text)[0]
    text = re.sub(r'\b(?:gmbh|ag|se|kg|kgaa|eg|ltd|limited|inc|corp|llc|personalservice)\b', ' ', text)
    return re.sub(r'[^a-z0-9]', '', text)


def title_identity(title, company=''):
    text = _plain(title)
    text = re.sub(r'[\(\[\{]\s*(?:[mwfdx](?:\s*[/|,]\s*[mwfdx]){1,3}|all\s+genders?(?:\s+welcome)?|alle\s+geschlechter|f/m/div|m/w/div|gn)\s*[\)\]\}]', ' ', text)
    text = re.sub(r'\b(?:all\s+genders?(?:\s+welcome)?|alle\s+geschlechter)\b', ' ', text)
    # Aggregators sometimes append the employer, even truncating its legal suffix.
    parts = re.split(r'\s+-\s+', text)
    employer = company_identity(company)
    if len(parts) > 1:
        suffix = company_identity(parts[-1])
        if employer and suffix and (suffix == employer or (min(len(employer), len(suffix)) >= 12 and (suffix.startswith(employer) or employer.startswith(suffix)))):
            text = ' - '.join(parts[:-1])
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def posting_url(url):
    """Normalize tracking variants without conflating IDs from different portals."""
    try:
        parts = urlsplit(url or '')
        host = (parts.hostname or '').lower().removeprefix('www.')
        if not host or parts.scheme not in ('http', 'https'):
            return ''
        if host.endswith('.linkedin.com') or host == 'linkedin.com':
            match = re.search(r'/jobs/view/(?:[^/?]*-)?(\d+)(?:/|$)', parts.path)
            if match:
                return 'linkedin:' + match.group(1)
        query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith('utm_') and k.lower() not in {'trk', 'trackingid', 'ref', 'refid', 'source', 'fbclid', 'gclid'}]
        return urlunsplit(('https', host, parts.path.rstrip('/'), urlencode(sorted(query)), ''))
    except ValueError:
        return ''


@lru_cache(maxsize=512)
def _description_fingerprint(description):
    plain = re.sub(r'(?m)^\s*\d+[.)]\s+', '', _plain(description))
    words = re.findall(r'[a-z0-9]+', plain)
    return ' '.join(words), frozenset(tuple(words[i:i+5]) for i in range(len(words)-4))


def same_description(left, right):
    if not left or not right:
        return False
    left_tasks, right_tasks = responsibility_text(left), responsibility_text(right)
    # Shared employer boilerplate must not merge jobs with different duties.
    if min(len(_plain(left_tasks)), len(_plain(right_tasks))) >= 160:
        left, right = left_tasks, right_tasks
    a, sa = _description_fingerprint(left)
    b, sb = _description_fingerprint(right)
    if len(a) < 160 or len(b) < 160:
        return False
    if a == b:
        return True
    if min(len(sa), len(sb)) < 25:
        return False
    return len(sa & sb) / min(len(sa), len(sb)) >= .85


class DuplicateIndex:
    """Index URLs and company/title pairs; inspect descriptions only on matches."""
    def __init__(self, jobs=()):
        self.urls = {}
        self.roles = {}
        for job in jobs:
            self.add(job)

    def add(self, job):
        url = posting_url(job.get('url'))
        if url:
            self.urls.setdefault(url, job)
        key = (company_identity(job.get('company')), title_identity(job.get('title'), job.get('company')))
        if all(key):
            self.roles.setdefault(key, []).append(job)

    def match(self, job):
        url = posting_url(job.get('url'))
        if url and url in self.urls:
            return self.urls[url]
        key = (company_identity(job.get('company')), title_identity(job.get('title'), job.get('company')))
        for other in self.roles.get(key, ()):
            left_location = _plain(job.get('location')).strip()
            right_location = _plain(other.get('location')).strip()
            if left_location and right_location and left_location != right_location:
                continue
            if same_description(job.get('description', job.get('_description', '')), other.get('description', other.get('_description', ''))):
                return other
        return None


def consolidate_jobs(jobs):
    """Prefer tracked records; retain source provenance and stable action keys."""
    def preference(job):
        host = urlsplit(job.get('url') or '').hostname or ''
        source_rank = 2 if any(name in host for name in ('whatjobs.com', 'adzuna.', 'jobgether.')) else (1 if 'linkedin.com' in host else 0)
        return (not bool(job.get('is_applied')), not bool(job.get('cv_file')), source_rank,
                len(job.get('title') or ''), -len(job.get('_description', job.get('description', ''))), job.get('key', ''))
    ordered = sorted(jobs, key=preference)
    index = DuplicateIndex()
    groups = []
    for job in ordered:
        match = index.match(job)
        source = {name: job.get(name) for name in ('key', 'portal', 'url', 'location')}
        if match is None:
            grouped = dict(job, source_listings=[source], portals=[job.get('portal') or 'web'])
            groups.append(grouped)
            index.add(grouped)
        else:
            match['source_listings'].append(source)
            if job.get('portal') not in match['portals']:
                match['portals'].append(job.get('portal'))
            # Index aliases too, so later URL variants join the same group.
            url = posting_url(job.get('url'))
            if url:
                index.urls[url] = match
    for job in groups:
        job.pop('_description', None)
        job['listing_count'] = len(job['source_listings'])
    return groups
