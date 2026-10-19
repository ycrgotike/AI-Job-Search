import io
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch

import server
from tools import generate_application as generator, scrape, state_io


class StateIOTests(unittest.TestCase):
    def test_concurrent_updates_preserve_every_change_and_valid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'seen.json'
            path.write_text(json.dumps({'seen': {'counter': {'count': 0}}, 'metadata': 'keep'}))
            def increment(_):
                def change(jobs):
                    jobs['counter']['count'] += 1
                    jobs['counter']['text'] = 'data' * jobs['counter']['count']
                    return True
                state_io.update_job_state(path, change)
                state_io.read_job_state(path)
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(increment, range(40)))
            document, jobs = state_io.read_job_state(path)
            self.assertEqual(jobs['counter']['count'], 40)
            self.assertEqual(document['metadata'], 'keep')

    def test_failed_replacement_preserves_original_and_cleans_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'seen.json'
            path.write_text('{"seen": {}}')
            with patch.object(state_io.os, 'replace', side_effect=OSError('disk failure')):
                with self.assertRaises(OSError):
                    state_io.atomic_write_text(path, 'new content')
            self.assertEqual(path.read_text(), '{"seen": {}}')
            self.assertEqual(list(Path(directory).glob('*.tmp')), [])

    def test_malformed_history_is_not_replaced_with_empty_scraper_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'seen.json'
            path.write_text('{"seen": {}} }\n}')
            original = path.read_bytes()
            with patch.object(scrape, 'SEEN_JOBS_FILE', path):
                with self.assertRaisesRegex(ValueError, 'refusing to replace'):
                    scrape.load_seen_jobs()
            with self.assertRaises(ValueError):
                state_io.update_job_state(path, lambda jobs: True)
            self.assertEqual(path.read_bytes(), original)

    def test_generator_updates_do_not_lose_other_jobs_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'seen.json'
            path.write_text(json.dumps({'seen': {str(n): {'status': 'new'} for n in range(20)}}))
            with patch.object(generator, 'SEEN_JOBS_FILE', path):
                with ThreadPoolExecutor(max_workers=8) as pool:
                    list(pool.map(generator.update_seen_jobs, map(str, range(20))))
            self.assertTrue(all(job['status'] == 'drafted' for job in state_io.read_job_state(path)[1].values()))

    def test_dashboard_reports_data_failure_instead_of_zero_postings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'seen.json'
            path.write_text('{"seen": {}} }')
            for route in ('/api/jobs', '/api/stats'):
                handler = object.__new__(server.DashboardHandler)
                handler.path = route
                handler.headers = {'Host': 'localhost:8000'}
                handler.send_json = Mock()
                with patch.multiple(server, SEEN_JOBS_FILE=path, _ENRICHED_CACHE=None), \
                     patch('sys.stderr', new=io.StringIO()):
                    handler.do_GET()
                self.assertEqual(handler.send_json.call_args.kwargs['status'], 503)
                self.assertIn('could not be read', handler.send_json.call_args.args[0]['error'])

    def test_concurrent_dashboard_status_updates_keep_tracker_and_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            history, tracker = root / 'seen.json', root / 'tracker.csv'
            jobs = {str(n): {'title': 'Data Engineer', 'company': 'Company' + chr(65 + n),
                            'url': 'https://example.com/' + str(n)} for n in range(12)}
            history.write_text(json.dumps({'seen': jobs}))
            def status_update(n):
                payload = json.dumps({'company': 'Company' + chr(65 + n), 'role': 'Data Engineer',
                                      'status': 'applied', 'key': str(n), 'url': 'https://example.com/' + str(n)}).encode()
                handler = object.__new__(server.DashboardHandler)
                handler.path = '/api/tracker/update_status'
                handler.headers = {'Host': 'localhost:8000', 'Content-Length': str(len(payload))}
                handler.rfile = io.BytesIO(payload)
                handler.send_json = Mock()
                handler.do_POST()
                self.assertTrue(handler.send_json.call_args.args[0]['success'])
            with patch.multiple(server, SEEN_JOBS_FILE=history, TRACKER_FILE=tracker):
                with ThreadPoolExecutor(max_workers=8) as pool:
                    list(pool.map(status_update, range(12)))
            import csv
            with tracker.open() as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), 12)
            self.assertTrue(all(job['status'] == 'applied' for job in state_io.read_job_state(history)[1].values()))


if __name__ == '__main__':
    unittest.main()
