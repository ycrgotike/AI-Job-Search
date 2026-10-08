"""Private, allowlisted generation failure reports; never log requests or credentials."""
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def save_failure(root, company, role, error, *, stage='generation', draft=None, plan=None, transport=None):
    token=hashlib.sha256((company+'\n'+role).encode()).hexdigest()[:20]
    directory=Path(root)/'reports/generation_failures'/token
    directory.mkdir(parents=True,exist_ok=True)
    path=directory/('draft.json' if draft is not None else 'failure.json')
    record={'timestamp':datetime.now(timezone.utc).isoformat(),'company':company,'role':role,'stage':stage,'error':str(error)}
    if isinstance(transport,dict):
        allowed_transport={'kind','stage','attempts','elapsed_seconds','timeout_seconds','exception_type','reason_type'}
        record['transport']={k:v for k,v in transport.items() if k in allowed_transport}
        record['stage']=record['transport'].get('stage',stage)
    if draft is not None:
        allowed={'summaries','header','skills','soltech','gsr','projects','opening','paragraphs','gaps'}
        record['draft']={k:v for k,v in draft.items() if k in allowed} if isinstance(draft,dict) else None
    if plan is not None:
        record['plan']={k:v for k,v in plan.items() if k in {'duties','gaps','timing_source','project_order'}} if isinstance(plan,dict) else None
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',dir=directory,delete=False,encoding='utf-8') as file:
            temporary=file.name
            json.dump(record,file,ensure_ascii=False,indent=2)
        os.replace(temporary,path)
    finally:
        if temporary and os.path.exists(temporary):os.unlink(temporary)
    return str(path.relative_to(root))
