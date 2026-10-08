"""Separate posting requirements from positively recorded candidate technology evidence."""
import re

TECHNOLOGIES = (
    'Python', 'SQL', 'TypeScript', 'JavaScript', 'Java', 'C++', 'C#', '.NET', 'R', 'Scala', 'Rust',
    'Power BI', 'DAX', 'Excel', 'PowerPoint', 'Tableau', 'VBA', 'ServiceNow', 'Airtable',
    'GitHub Actions', 'Jenkins', 'GitLab CI', 'Azure DevOps', 'CI/CD', 'Git',
    'Docker', 'Kubernetes', 'Terraform', 'Ansible', 'Puppet', 'PowerShell',
    'Azure Data Factory', 'Databricks', 'Azure', 'AWS', 'GCP', 'Snowflake', 'dbt', 'Kafka', 'Airflow',
    'Apache Spark', 'PySpark', 'SQL Server', 'PostgreSQL', 'MySQL', 'Oracle', 'PL/SQL',
    'MLflow', 'DVC', 'TensorFlow', 'PyTorch', 'FastAPI', 'Flask', 'LangChain', 'LlamaIndex', 'LangGraph', 'Google ADK', 'MCP', 'Vertex AI', 'BigQuery', 'Gemini', 'OpenAI', 'Anthropic', 'Llama', 'Mistral', 'RAG', 'LLMs',
    'Selenium', 'Playwright', 'Cypress', 'pytest', 'Jest', 'JUnit', 'Jira', 'TestRail',
    'PKI', 'NIS2', 'REST APIs', 'Windows', 'Linux', 'HTML', 'JSON', 'OutSystems',
)
BRIDGES = {
    'Jenkins': ('GitHub Actions', 'CI/CD'),
    'GitLab CI': ('GitHub Actions', 'CI/CD'),
    'Azure DevOps': ('GitHub Actions', 'CI/CD'),
    'TypeScript': ('Python', '.NET'),
    'JavaScript': ('Python', '.NET'),
    'ServiceNow': ('OutSystems', 'REST APIs'),
    'Airtable': ('SQL', 'Python'),
    'Snowflake': ('SQL', 'Databricks'),
    'dbt': ('SQL', 'Azure Data Factory'),
    'Selenium': ('Python',), 'Playwright': ('Python',), 'Cypress': ('Python',),
    'pytest': ('Python',), 'Jest': ('Python',),
}


def contains(term, text):
    return bool(re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', text, re.I))


def positive_evidence(profile):
    """Exclude instructions, caveats and negated claims even when they name a tool."""
    result = []
    for line in profile.splitlines():
        if not line.startswith(('- ', '*Tech Stack:')):
            continue
        if re.search(r'never|not confirmed|unconfirmed|unverified|no experience|not experienced|do not|require separate|not a particular|include these|missing|learning interest', line, re.I):
            # Confirmation and scope caveat can share a line. Keep only the confirmation.
            if line.startswith('- User confirmed'):
                line = line.split('. This confirms')[0]
            else:
                continue
        result.append(line)
    return result


def review_technologies(description, profile):
    positives = positive_evidence(profile)
    terms = [term for term in TECHNOLOGIES if contains(term, description)]
    # Surface unrecognised product names near explicit tool cues for human confirmation.
    # These candidates never enter skills or automated learning claims.
    candidates = []
    for match in re.finditer(r'(?:tools? (?:such as|like)|experience (?:with|using)|familiarity with|kenntnisse in)\s+([^.;\n]{1,100})', description, re.I):
        for token in re.findall(r'\b[A-Z][A-Za-z0-9+#.-]{2,}\b', match.group(1)):
            if token not in terms and not any(contains(token, term) for term in TECHNOLOGIES):
                candidates.append(token)
    terms.extend(token for token in dict.fromkeys(candidates) if any(contains(token,line) for line in positives))
    candidates = [token for token in candidates if token not in terms]
    records = []
    for term in terms:
        source = next((line for line in positives if contains(term, line)), '')
        related = [t for t in BRIDGES.get(term, ()) if any(contains(t,line) for line in positives)]
        records.append({'technology':term, 'status':'confirmed' if source else ('transferable' if related else 'needs_confirmation'),
                        'evidence':source, 'related_confirmed_skills':related})
    return {'technologies':records, 'unrecognised_terms_to_review':list(dict.fromkeys(candidates))}


def learning_sentence(review):
    items = [r for r in review['technologies'] if r['status'] != 'confirmed'][:2]
    if not items:
        return ''
    names = ' and '.join(r['technology'] for r in items)
    related = list(dict.fromkeys(t for r in items for t in r['related_confirmed_skills']))[:4]
    if related:
        related_text = ', '.join(related[:-1]) + ' and ' + related[-1] if len(related) > 1 else related[0]
        return 'I would build on my ' + related_text + ' experience while learning ' + names + ' for the work described.'
    return 'I am interested in learning ' + names + ' in the context of the responsibilities described.'
