"""Resolve referral listings into identity-checked job descriptions; never change dates."""
import ipaddress
import json
import re
import socket
from datetime import date
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urldefrag
from urllib.request import Request, build_opener, HTTPRedirectHandler

REFERRAL = re.compile(r'vollständige.{0,30}(?:stellenbeschreibung|stellenanzeige)|weitere informationen.{0,40}(?:link|website)|(?:job|stellen)(?:beschreibung|description).{0,30}(?:extern|website)|(?:full|complete) job description.{0,35}(?:link|website)|externe stellenbörse|zum stellenangebot|weiter zum stellenangebot', re.I)
TASK = re.compile(r'aufgaben|responsibilities|\btasks\b|what you.{0,8}do|you can move this|das beweg|tätigkeiten', re.I)
QUAL = re.compile(r'qualifications|requirements|your profile|ihr profil|dein profil|mitbringen|bring with you|anforderungen', re.I)
LINK = re.compile(r'stellen|job|career|karriere|bewerb|apply|vacanc|position', re.I)


def plain(value):
    return unescape(re.sub(r'<[^>]+>', ' ', value or '')).strip()


def needs_resolution(description):
    text = plain(description)
    if not text:
        return True
    if REFERRAL.search(text) and not (TASK.search(text) and QUAL.search(text) and len(text.split()) >= 80):
        return True
    if TASK.search(text) and re.search(r'\b(?:manage|develop|maintain|build|analyze|analyse|create|design|monitor)\b', text, re.I):
        return False
    # A recognisable task statement may be brief but substantive; boilerplate is not.
    from tools.responsibility_plan import analyze_posting
    plan = analyze_posting('', text)
    return (not plan['responsibilities'] or (plan['responsibilities'][0]['kind'] == 'general' and len(text.split()) < 60)) or (bool(re.search(r'https?://', text)) and len(text.split()) < 45)


def public_url(url):
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Unsupported job URL')
    if parsed.port not in (None, 80, 443):
        raise ValueError('Unsupported job URL port')
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80), type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Job URL does not resolve to a public address')
    return url


class CheckedRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_page(url):
    public_url(url)
    request = Request(url, headers={'User-Agent': 'AIJobSearch/1.0', 'Accept': 'text/html,application/xhtml+xml,application/json'})
    with build_opener(CheckedRedirect()).open(request, timeout=12) as response:
        final_url = response.geturl()
        public_url(final_url)
        kind = response.headers.get('Content-Type', '')
        if not any(t in kind for t in ('html', 'json', 'text/plain')):
            raise ValueError('Destination is not a readable job page')
        content = response.read(2_000_001)
        if len(content) > 2_000_000:
            raise ValueError('Job page exceeds size limit')
        return final_url, content.decode(response.headers.get_content_charset() or 'utf-8', errors='replace')


class Page(HTMLParser):
    def __init__(self, content):
        super().__init__(convert_charrefs=True)
        self.text, self.links, self.jobs = [], [], []
        self.ignored = 0
        self.script = None
        self.script_data = []
        self.anchor = None
        self.heading = False
        self.headings = []
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('h1', 'title'):
            self.heading = True
        if tag == 'script':
            self.script = a.get('type', '')
            self.script_data = []
        if tag in ('nav', 'footer', 'style', 'noscript'):
            self.ignored += 1
        if tag == 'a' and a.get('href'):
            self.anchor = [a['href'], '']
        if tag in ('p', 'li', 'div', 'br', 'h1', 'h2', 'h3'):
            self.text.append('\n')

    def handle_endtag(self, tag):
        if tag in ('h1', 'title'):
            self.heading = False
        if tag == 'script':
            if self.script == 'application/ld+json':
                try:
                    self.collect(json.loads(''.join(self.script_data)))
                except (ValueError, TypeError):
                    pass
            self.script = None
        if tag in ('nav', 'footer', 'style', 'noscript'):
            self.ignored = max(0, self.ignored-1)
        if tag == 'a' and self.anchor:
            self.links.append(tuple(self.anchor)); self.anchor = None
        if tag in ('p', 'li', 'div', 'h1', 'h2', 'h3'):
            self.text.append('\n')

    def handle_data(self, data):
        if self.script is not None:
            self.script_data.append(data)
        elif not self.ignored:
            self.text.append(data)
            if self.heading:
                self.headings.append(data)
            if self.anchor:
                self.anchor[1] += data

    def collect(self, value):
        if isinstance(value, list):
            for x in value: self.collect(x)
        elif isinstance(value, dict):
            types = value.get('@type', [])
            if types == 'JobPosting' or isinstance(types, list) and 'JobPosting' in types:
                self.jobs.append(value)
            for key in ('@graph', 'mainEntity', 'itemListElement', 'item'):
                if key in value: self.collect(value[key])

    @property
    def visible(self):
        return '\n'.join(re.sub(r'\s+', ' ', line).strip() for line in ''.join(self.text).splitlines() if line.strip())


STOPWORDS = set('gmbh ag se kg co ltd limited inc consulting solutions hr hrdirekt m w d working student werkstudent internship intern praktikum prakt ikant the and und für for of in im bei at'.split())

def tokens(value):
    return {t for t in re.findall(r'\w+', plain(value).casefold()) if len(t) > 1 and t not in STOPWORDS}


def identity_matches(job, title, company):
    wanted_title, wanted_company = tokens(job.get('title', '')), tokens(job.get('company', ''))
    if not wanted_title or not wanted_company:
        return False
    return (len(wanted_title & tokens(title)) / len(wanted_title) >= .75 and
            len(wanted_company & tokens(company)) / len(wanted_company) >= .5)


def full_description(text):
    return len(plain(text).split()) >= 60 and bool(TASK.search(text)) and not needs_resolution(text)


def resolve_description(job, detail=None, fetcher=None):
    """Bounded traversal of posting links only. Failure retains the original job."""
    detail = detail or {}
    fetcher = fetcher or fetch_page
    original = job.get('description', '')
    if detail.get('title') and detail.get('company') and not identity_matches(job, detail['title'], detail['company']):
        return {'description': original, 'discovery_url':job.get('url', ''), 'description_status':'description_needed', 'description_fetch_errors':['Portal detail did not match the employer and role']}
    description = detail.get('description') or original
    origin = job.get('url', '')
    if not needs_resolution(description):
        return {'description': description, 'description_source_url': origin, 'discovery_url': origin, 'description_status': 'ready'}
    queue = []
    for obj in (job, detail):
        for key in ('externalUrls', 'external_urls', 'external_url', 'apply_url', 'application_url'):
            values = obj.get(key, [])
            for url in values if isinstance(values, list) else [values]:
                if isinstance(url, str) and url:
                    queue.append((urljoin(origin, url), 0))
    stub = Page(description)
    queue.extend((urljoin(origin, u), 0) for u, label in stub.links if LINK.search(label+' '+u))
    queue.extend((u.rstrip('.,);'), 0) for u in re.findall(r'https?://[^\s<>"\]]+', description))
    if origin: queue.append((origin, 0))
    visited, errors = set(), []
    while queue and len(visited) < 5:
        url, depth = queue.pop(0)
        url = urldefrag(url)[0]
        if url in visited: continue
        visited.add(url)
        try:
            final, html = fetcher(url)
            page = Page(html)
            for posting in page.jobs:
                org = posting.get('hiringOrganization', {})
                company = org.get('name', '') if isinstance(org, dict) else str(org)
                if not identity_matches(job, posting.get('title',''), company): continue
                expiry = posting.get('validThrough', '')
                if expiry and str(expiry)[:10] < date.today().isoformat():
                    errors.append('Matching posting has expired'); continue
                body = Page(posting.get('description', '')).visible
                if full_description(body):
                    return {'description':body,'description_source_url':final,'discovery_url':origin,'description_status':'ready'}
            # Plain HTML requires both employer and role in the page, not just the URL.
            if not page.jobs and identity_matches(job, ' '.join(page.headings), page.visible) and full_description(page.visible) and not re.search(r'position.{0,15}(?:filled|closed)|stelle.{0,15}(?:besetzt|geschlossen)|posting.{0,15}expired', page.visible, re.I):
                return {'description':page.visible,'description_source_url':final,'discovery_url':origin,'description_status':'ready'}
            if depth < 2:
                queue.extend((urljoin(final, u), depth+1) for u,label in page.links if LINK.search(label+' '+u))
            errors.append('No complete matching description at '+final)
        except Exception as exc:
            errors.append(type(exc).__name__ + ': ' + str(exc)[:200])
    return {'description':original, 'discovery_url':origin, 'description_status':'description_needed',
            'description_fetch_errors':errors or ['No external job link was available']}
