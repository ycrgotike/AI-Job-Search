"""Application-specific PDF checks, with optional independent extraction.

Formatting differences and missing optional tools are review warnings, never new
compilation failures. A readable extractor can satisfy the contact contract.
"""
import re
import unicodedata
from pathlib import Path
from tools import verify_pdf
from tools.technology_evidence import contains


def compact(text):
    return re.sub(r'[^\w@+]', '', unicodedata.normalize('NFKC', text).casefold())


def tex_text(text):
    return text.replace(r'\&', '&').replace('~', ' ').replace(r'\,', ' ').replace(r'\%', '%')


def contact_contract(cv_source):
    name = re.search(r'\\name\{([^{}]+)\}\{([^{}]+)\}', cv_source)
    email = re.search(r'\\email\{([^{}]+)\}', cv_source)
    phone = re.search(r'\\phone(?:\[[^]]*\])?\{([^{}]+)\}', cv_source)
    return {key: value for key, value in {
        'name': ' '.join(name.groups()) if name else '',
        'email': email.group(1) if email else '',
        'phone': tex_text(phone.group(1)) if phone else '',
    }.items() if value}


def inspect_text(text, contract, source, kind):
    normalized = compact(text)
    errors, warnings = [], []
    for label, expected in contract.items():
        # Phone formatting (parentheses, hyphens, spaces, optional +) varies by parser.
        found = re.sub(r'\D', '', expected) in re.sub(r'\D', '', text) if label == 'phone' else compact(expected) in normalized
        if not found:
            errors.append('Missing or corrupted ' + label + ' in extracted ' + kind + '.')
    if re.search(r'\(cid:\d+\)|\ufffd|\x00', text):
        warnings.append('Encoding artifacts detected; review the extracted text and rendered PDF.')
    if kind == 'cv':
        headings = [tex_text(value) for value in re.findall(r'\\section\{([^{}]+)\}', source)]
        readable = ' '.join(unicodedata.normalize('NFKC', text).split()).casefold()
        lines = list(re.finditer(r'^.*$', text, re.M))
        positions = []
        for heading in headings:
            exact = next((line.start() for line in lines if compact(line.group()) == compact(heading)), None)
            if exact is not None:
                # Use one coordinate system for all headings, including wrapped ones.
                positions.append(len(' '.join(text[:exact].split())))
                continue
            match = re.search(r'(?<!\w)' + r'\s+'.join(re.escape(word) for word in heading.casefold().split()) + r'(?!\w)', readable)
            positions.append(match.start() if match else -1)
        if any(position < 0 for position in positions):
            warnings.append('Some CV section headings were not recovered intact.')
        elif positions != sorted(positions):
            warnings.append('CV sections may extract in an unexpected reading order.')
        # Check historical date ranges from cventry, never infer or recalculate them.
        for dates in re.findall(r'\\cventry\{([^{}]+)\}', source):
            if compact(tex_text(dates)) not in normalized:
                warnings.append('Check date extraction: ' + dates)
        employers = ['SolTech', 'G.S.R', 'ITC Infotech']
        employment = normalized.split(compact('Professional Experience'), 1)[-1].split(compact('Key Technical Projects'), 1)[0]
        found = [employment.find(compact(name)) for name in employers]
        if all(pos >= 0 for pos in found) and found != sorted(found):
            warnings.append('Employment entries may not extract in reverse chronological order.')
    return errors, warnings


def audit_document(path, source, kind, contract):
    errors, warnings, extractions = [], [], {}
    try:
        result = verify_pdf._extract_pypdf(Path(path))
        if result and result[0].strip():
            extractions['pypdf'] = result
    except Exception:
        warnings.append('Optional pypdf extraction unavailable.')
    try:
        result = verify_pdf._extract_pdftotext(Path(path))
        if result and result[0].strip():
            extractions['pdftotext'] = result
    except Exception:
        warnings.append('Optional Poppler comparison unavailable; primary verification remains in effect.')
    if not extractions:
        return {'status': 'review_required', 'errors': [], 'warnings': warnings + ['Additional readability audit unavailable; basic PDF verification already ran.'], 'extractors': [], 'text': ''}
    evaluations = []
    for extractor, (text, pages) in extractions.items():
        issues, notes = inspect_text(text, contract, source, kind)
        evaluations.append((issues, notes, text, extractor, pages))
    # Don't fail a good PDF solely because another extractor handles typography differently.
    chosen = min(evaluations, key=lambda item: (len(item[0]), len(item[1])))
    errors, notes, text, _, _ = chosen
    warnings.extend(notes)
    if len(extractions) < 2:
        warnings.append('Only one PDF extractor was available for comparison.')
    elif any(issues != chosen[0] or notes != chosen[1] for issues, notes, *_ in evaluations):
        warnings.append('Extractors differ on document structure; inspect the text preview.')
    return {'status': 'failed' if errors else ('review_required' if warnings else 'passed'),
            'errors': errors, 'warnings': list(dict.fromkeys(warnings)), 'extractors': list(extractions), 'text': text}


def audit_application(cv_path, letter_path, cv_source, letter_source, technology_review):
    contract = contact_contract(cv_source)
    cv = audit_document(cv_path, cv_source, 'cv', contract)
    letter = audit_document(letter_path, letter_source, 'cover_letter', contract)
    supported = [item['technology'] for item in technology_review.get('technologies', []) if item['status'] == 'confirmed']
    cv_text, letter_text = cv.pop('text'), letter.pop('text')
    cv_text = ' '.join(unicodedata.normalize('NFKC', cv_text).split())
    letter_text = ' '.join(unicodedata.normalize('NFKC', letter_text).split())
    match = re.search(r'technical\s+skills(.*?)(?:professional\s+experience|$)', cv_text, re.I | re.S)
    skills = match.group(1) if match else ''
    coverage = {'supported_job_terms': supported,
                'present_in_cv': [term for term in supported if contains(term, cv_text)],
                'missing_from_cv': [term for term in supported if not contains(term, cv_text)],
                'missing_from_skills': [term for term in supported if not contains(term, skills)],
                'present_in_letter': [term for term in supported if contains(term, letter_text)],
                'unconfirmed_job_terms': [item['technology'] for item in technology_review.get('technologies', []) if item['status'] != 'confirmed']}
    return {'cv': cv, 'cover_letter': letter, 'keyword_coverage': coverage,
            'errors': cv['errors'] + letter['errors'],
            'warnings': cv['warnings'] + letter['warnings']}
