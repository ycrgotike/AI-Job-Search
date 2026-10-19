"""Regression coverage for private file serving, portal gates and archived previews."""
import csv
import io
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import server
from tools import generate_application as generator, scrape


class FileAccessTests(unittest.TestCase):
    def handler(self, path='/'):
        handler = object.__new__(server.DashboardHandler)
        handler.path = path
        handler.headers = {'Host': 'localhost:8766'}
        handler.send_error = Mock()
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = io.BytesIO()
        return handler

    def test_private_routes_do_not_fall_back_to_repository_server(self):
        for path in ('/CLAUDE.md', '/.env', '/job_search_tracker.csv', '/documents/'):
            handler = self.handler(path)
            handler.do_GET()
            self.assertEqual(handler.send_error.call_args.args[0], 404)

    def test_traversal_and_symlink_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            web = root / 'web'; web.mkdir()
            private = root / '.env'; private.write_text('private')
            (web / 'app.js').symlink_to(private)
            with patch.multiple(server, ROOT=root, WEB_DIR=web):
                for path in ('/web/../.env', '/web/%2e%2e/.env', '/web/app.js'):
                    handler = self.handler(path)
                    handler.do_GET()
                    self.assertEqual(handler.send_error.call_args.args[0], 404)
                    self.assertEqual(handler.wfile.getvalue(), b'')

    def test_assets_and_archived_pdfs_remain_available(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            web = root / 'web'; web.mkdir()
            script = web / 'app.js'; script.write_text('safe script')
            archive = root / 'documents/applications/Example_DataEngineer'; archive.mkdir(parents=True)
            pdf = archive / 'YashwanthGotike_Example_CV.pdf'; pdf.write_bytes(b'%PDF archived')
            with patch.multiple(server, ROOT=root, WEB_DIR=web):
                for path, expected in ((script, b'safe script'), (pdf, b'%PDF archived')):
                    handler = self.handler()
                    handler.serve_file(path)
                    self.assertEqual(handler.wfile.getvalue(), expected)
                    handler.send_error.assert_not_called()
                handler = self.handler()
                handler.serve_file(archive / 'review.json')
                self.assertEqual(handler.send_error.call_args.args[0], 404)

    def test_security_headers_allow_only_same_origin_pdf_embedding(self):
        handler = self.handler()
        with patch('http.server.SimpleHTTPRequestHandler.end_headers'):
            server.DashboardHandler.end_headers(handler)
        headers = dict(call.args for call in handler.send_header.call_args_list)
        self.assertIn("frame-ancestors 'self'", headers['Content-Security-Policy'])
        self.assertIn("script-src 'self'", headers['Content-Security-Policy'])
        self.assertNotIn('Access-Control-Allow-Origin', headers)

    def test_server_binds_only_to_loopback(self):
        with patch.object(server, 'ThreadingHTTPServer') as constructor:
            server.run_server(8766)
        self.assertEqual(constructor.call_args.args[0], ('127.0.0.1', 8766))

    def test_nonlocal_host_is_rejected(self):
        handler = self.handler('/api/jobs')
        handler.headers = {'Host': 'untrusted.example'}
        handler.do_GET()
        self.assertEqual(handler.send_error.call_args.args[0], 403)

    def test_head_never_uses_the_repository_fallback(self):
        handler = self.handler('/.env')
        handler.do_HEAD()
        self.assertEqual(handler.send_error.call_args.args[0], 405)

    def test_cross_origin_mutation_is_rejected_before_payload_read(self):
        handler = self.handler('/api/generate')
        handler.headers = {'Origin': 'https://untrusted.example', 'Host': 'localhost:8766'}
        handler.rfile = Mock()
        handler.do_POST()
        self.assertEqual(handler.send_error.call_args.args[0], 403)
        handler.rfile.read.assert_not_called()


class DetailGateTests(unittest.TestCase):
    def tearDown(self):
        scrape.fetch_linkedin_details.cache_clear()

    def test_timeout_and_missing_metadata_fail_closed(self):
        scrape.fetch_linkedin_details.cache_clear()
        with patch.object(scrape.subprocess, 'run', side_effect=TimeoutError()):
            self.assertFalse(scrape.fetch_linkedin_details('123456789')[1])
        scrape.fetch_linkedin_details.cache_clear()
        response = Mock(returncode=0, stdout=json.dumps({'description': 'Build data pipelines', 'isFresh': True}))
        with patch.object(scrape.subprocess, 'run', return_value=response):
            self.assertFalse(scrape.fetch_linkedin_details('123456789')[1])

    def test_unverified_and_easy_apply_jobs_are_never_saved(self):
        job = {'title': 'Data Engineer', 'company': 'Example', 'url': 'https://linkedin.com/jobs/view/123456789',
               'posted_date': str(date.today()), 'portal': 'linkedin-search', 'description': 'Search snippet'}
        for details in (('', False, None, None), ('Build data pipelines', True, None, True)):
            seen = {}
            with patch.object(scrape, 'run_linkedin_search', return_value=[dict(job)]), \
                 patch.object(scrape, 'fetch_linkedin_details', return_value=details) as fetch, \
                 patch('sys.stdout', new=io.StringIO()):
                scrape.scrape_query('Data Engineer', 'Germany', 10, 2, set(), seen, {'linkedin'})
            fetch.assert_called_once()
            self.assertEqual(seen, {})

    def test_verified_direct_apply_job_is_saved(self):
        job = {'title': 'Data Engineer', 'company': 'Example', 'url': 'https://linkedin.com/jobs/view/123456789',
               'posted_date': str(date.today()), 'portal': 'linkedin-search'}
        seen = {}
        with patch.object(scrape, 'run_linkedin_search', return_value=[job]), \
             patch.object(scrape, 'fetch_linkedin_details', return_value=('Build data pipelines with English C1 and German B2.', True, '1 hour ago', False)), \
             patch('sys.stdout', new=io.StringIO()):
            scrape.scrape_query('Data Engineer', 'Germany', 10, 2, set(), seen, {'linkedin'})
        self.assertEqual(len(seen), 1)


class ArchivePreviewTests(unittest.TestCase):
    def test_two_roles_use_their_own_archives_after_root_pdf_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); tracker = root / 'tracker.csv'
            root_pdf = root / 'cv/YashwanthGotike_Example_CV.pdf'
            root_pdf.parent.mkdir(); root_pdf.write_bytes(b'Newest role')
            rows = []
            with patch.object(generator, 'DOCUMENTS_DIR', root / 'documents/applications'):
                for role in ('Data Engineer', 'Data Analyst'):
                    archive = generator.application_archive_dir('Example', role)
                    archive.mkdir(parents=True)
                    (archive / root_pdf.name).write_bytes(role.encode())
                    rows.append({'company': 'Example', 'role': role, 'cv_file': str(root_pdf.relative_to(root)), 'source': ''})
                with tracker.open('w', newline='') as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                    writer.writeheader(); writer.writerows(rows)
                with patch.multiple(server, ROOT=root, TRACKER_FILE=tracker, SEEN_JOBS_FILE=root / 'missing.json'):
                    applications = server.load_tracker()
                engineer = applications['example_dataengineer']['cv_file']
                analyst = applications['example_dataanalyst']['cv_file']
                self.assertNotEqual(engineer, analyst)
                self.assertEqual((root / engineer).read_bytes(), b'Data Engineer')
                self.assertEqual((root / analyst).read_bytes(), b'Data Analyst')
                # A missing archive must not substitute another role's mutable PDF.
                (root / engineer).unlink()
                with patch.multiple(server, ROOT=root, TRACKER_FILE=tracker, SEEN_JOBS_FILE=root / 'missing.json'):
                    applications = server.load_tracker()
                self.assertIsNone(applications['example_dataengineer']['cv_file'])
                self.assertEqual((root / applications['example_dataanalyst']['cv_file']).read_bytes(), b'Data Analyst')


if __name__ == '__main__':
    unittest.main()
