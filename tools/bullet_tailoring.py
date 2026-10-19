"""Optional, source-linked experience rewrites. Rejected edits retain originals."""
import re
from tools.technology_evidence import TECHNOLOGIES, contains

ROLES = ('soltech', 'gsr', 'itc')


def quantities(text):
    return sorted(re.sub(r'\s+', '', x.lower()) for x in re.findall(
        r'\b(?:\d+(?:\.\d+)?|zero)\b(?:\s*(?:%|tb\b|gb\b|million\b|hours?\b|days?\b|minutes?\b))?', text, re.I))


def check_rewrite(original, text):
    if not isinstance(text, str) or not text.strip() or any(c in text for c in ('\\', '\x00', '\n', '\r')):
        return 'Rewrite must be one plain-text bullet.'
    if len(text) > max(len(original) + 25, int(len(original) * 1.12)) or len(text.split()) < len(original.split()) * .6:
        return 'Rewrite exceeds its source bullet length budget or omits too much detail.'
    if quantities(text) != quantities(original):
        return 'Rewrite changed or omitted a verified metric.'
    introduced = [term for term in TECHNOLOGIES if contains(term, text) and not contains(term, original)]
    omitted = [term for term in TECHNOLOGIES if contains(term, original) and not contains(term, text)]
    if introduced or omitted:
        return 'Rewrite changed source technology attribution: ' + ', '.join(introduced + omitted)
    for claim in ('led', 'managed', 'owned', 'architected', 'supervised', 'mentored', 'expert', 'certified', 'enterprise', 'production'):
        if contains(claim, text) and not contains(claim, original):
            return 'Rewrite introduced an unsupported scope or leadership claim: ' + claim
    for qualifier in ('under', 'near', 'approximately'):
        if contains(qualifier, original) and not contains(qualifier, text):
            return 'Rewrite removed a source qualifier: ' + qualifier
    if '~' in original and not ('~' in text or re.search(r'approx|about|around', text, re.I)):
        return 'Rewrite removed an approximate quantity qualifier.'
    return ''


def prepare_rewrites(proposals, evidence):
    accepted, warnings, used = [], [], set()
    if not isinstance(proposals, list):
        return [], ['Optional bullet rewrites were malformed; original bullets retained.']
    for proposal in proposals:
        if not isinstance(proposal, dict):
            warnings.append('Malformed optional rewrite ignored; original retained.')
            continue
        role, index, text = proposal.get('role'), proposal.get('source_index'), proposal.get('text')
        if role not in ROLES or type(index) is not int or not 0 <= index < len(evidence.get(role, [])) or (role, index) in used:
            warnings.append('Optional rewrite had an invalid or duplicate source; original retained.')
            continue
        used.add((role, index))
        original = evidence[role][index]
        problem = check_rewrite(original, text)
        if problem:
            warnings.append(f'{role}[{index}]: {problem} Original retained.')
        elif text.strip() != original.strip():
            accepted.append({'role': role, 'source_index': index, 'text': text.strip(), 'original': original})
    return accepted, warnings


def approve_rewrites(proposals, approvals):
    """An independent factual reviewer must approve the exact proposed text."""
    if not isinstance(approvals, list):
        approvals = []
    approved = {(item.get('role'), item.get('source_index'), item.get('text')) for item in approvals
                if isinstance(item, dict) and isinstance(item.get('role'), str)
                and type(item.get('source_index')) is int and isinstance(item.get('text'), str)}
    return [item for item in proposals if (item['role'], item['source_index'], item['text']) in approved]


def render_bullet(role, index, evidence, applied):
    return next((item['text'] for item in applied if item['role'] == role and item['source_index'] == index), evidence[role][index])


def restore_original_bullets(code, applied, escape):
    for item in applied:
        code = code.replace(r'\item ' + escape(item['text']), r'\item ' + escape(item['original']), 1)
    return code
