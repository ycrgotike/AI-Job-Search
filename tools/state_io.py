"""Locked updates and atomic replacement for shared local job-search records."""
import csv
import fcntl
import io
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def file_lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_name(path.name + '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def atomic_write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def read_job_state(path):
    document = json.loads(Path(path).read_text(encoding='utf-8'))
    jobs = document.get('seen', document) if isinstance(document, dict) else None
    if not isinstance(jobs, dict) or any(not isinstance(job, dict) for job in jobs.values()):
        raise ValueError('Expected an object containing job records')
    return document, jobs


def update_job_state(path, mutate):
    """Read the latest records under a shared lock; never replace malformed data."""
    with file_lock(path):
        document, jobs = read_job_state(path)
        if mutate(jobs):
            atomic_write_text(path, json.dumps(document, indent=2, ensure_ascii=False) + '\n')


def atomic_write_csv(path, headers, rows):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    atomic_write_text(path, output.getvalue())
