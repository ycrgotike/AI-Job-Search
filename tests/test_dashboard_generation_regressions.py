import csv
import importlib.util
import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = load_module('generation_regression', ROOT / 'tools/generate_application.py')
dashboard = load_module('dashboard_regression', ROOT / 'server.py')


class GenerationChecks(unittest.TestCase):
    def test_role_percent_is_escaped_in_metadata(self):
        code = generator.build_tailored_cv('BDE Sales Partners GmbH', 'BdeSalesPartners',
            'Werkstudent Leadrecherche & Datenpflege – 100 % Homeoffice / Remote',
            'Research and maintain data.', True, False, False, False)
        keywords = next(line for line in code.splitlines() if 'pdfkeywords=' in line)
        self.assertIn(r'100 \%', keywords)
        self.assertIn(r'Leadrecherche \& Datenpflege', keywords)
        self.assertNotIn('100 %', keywords)

    def run_generation(self, compile_result=True, pages=(2, 1), stale=False, pdf_valid=True):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            cv, cover = root / 'cv', root / 'cover'
            cv.mkdir(); cover.mkdir()
            (cv / 'YashwanthGotike_Example_CV.pdf').write_bytes(b'test PDF')
            (cover / 'YashwanthGotike_Example_CoverLetter.pdf').write_bytes(b'test PDF')
            if stale:
                (cv / 'YashwanthGotike_Example_CV.pdf').write_bytes(b'old PDF')
            with patch.multiple(generator, ROOT=root, CV_DIR=cv, COVER_DIR=cover,
                    TRACKER_FILE=root / 'tracker.csv', DOCUMENTS_DIR=root / 'archives'), \
                 patch.object(generator, 'compile_latex', side_effect=compile_result if isinstance(compile_result, list) else None,
                    return_value=compile_result) as compile_mock, \
                 patch.object(generator, 'get_pdf_page_count', side_effect=pages), \
                 patch.object(generator, 'verify_generated_pdf', return_value=pdf_valid), \
                 patch.object(generator, 'record_in_tracker') as tracker, \
                 patch.object(generator, 'update_seen_jobs') as seen:
                result = generator.generate_for_job({'company': 'Example', 'title': 'Data Analyst',
                    'description': 'Maintain reporting data using SQL.', 'key': 'example'})
                return result, tracker.call_count, seen.call_count, compile_mock.call_count, (root / 'archives').exists()

    def test_compile_failure_never_records_even_with_old_pdf(self):
        result, tracker, seen, calls, archived = self.run_generation(False, stale=True)
        self.assertFalse(result['success'])
        self.assertNotIn('cv_file', result)
        self.assertEqual((tracker, seen, calls, archived), (0, 0, 1, False))

    def test_cover_failure_never_records(self):
        result, tracker, seen, calls, archived = self.run_generation([True, True, False])
        self.assertFalse(result['success'])
        self.assertEqual((tracker, seen, calls, archived), (0, 0, 3, False))

    def test_wrong_or_missing_pages_never_record(self):
        for pages in [(0, 1), (3, 1), (2, 2), (2, 0)]:
            with self.subTest(pages=pages):
                result, tracker, seen, _, archived = self.run_generation(pages=pages)
                self.assertFalse(result['success'])
                self.assertEqual((tracker, seen, archived), (0, 0, False))

    def test_bad_text_layer_never_records(self):
        result, tracker, seen, _, archived = self.run_generation(pdf_valid=False)
        self.assertFalse(result['success'])
        self.assertEqual((tracker, seen, archived), (0, 0, False))

    def test_verified_page_counts_allow_recording(self):
        result, tracker, seen, calls, archived = self.run_generation()
        self.assertTrue(result['success'])
        self.assertEqual((tracker, seen, calls, archived), (1, 1, 3, True))


class DashboardCounts(unittest.TestCase):
    def test_midnight_filter_keeps_stored_count_and_explains_hidden(self):
        class Today(date):
            @classmethod
            def today(cls):
                return cls(2026, 9, 14)
        entries = {
            'recent': {'title': 'Data Analyst', 'posted_date': '2026-09-12'},
            'old': {'title': 'Data Analyst', 'posted_date': '2026-09-11'},
            'unknown': {'title': 'Data Analyst'},
            'language': {'title': 'Data Analyst German C1', 'posted_date': '2026-09-12'},
            'repost': {'title': 'Data Analyst reposted', 'posted_date': '2026-09-12'},
        }
        with TemporaryDirectory() as temp:
            seen = Path(temp) / 'seen.json'
            seen.write_text(json.dumps({'seen': entries}))
            with patch.object(dashboard, 'SEEN_JOBS_FILE', seen), \
                 patch.object(dashboard, 'date', Today), \
                 patch.object(dashboard, 'load_tracker', return_value={}):
                jobs, counts = dashboard.get_enriched_jobs(include_counts=True)
                self.assertEqual(len(jobs), 1)
                self.assertEqual(counts, {'stored_jobs': 5, 'hidden_jobs': 4,
                    'hidden_reasons': {'date': 2, 'repost': 1, 'language': 1}})
                self.assertEqual(len(dashboard.get_enriched_jobs()), 1)
                self.assertEqual(json.loads(seen.read_text())['seen'], entries)

    def test_missing_pdf_links_are_not_exposed(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            tracker = root / 'tracker.csv'
            tracker.write_text('company,role,cv_file,cover_letter_file\nExample,Analyst,missing.pdf,letter.pdf\n')
            (root / 'letter.pdf').write_bytes(b'PDF')
            with patch.multiple(dashboard, ROOT=root, TRACKER_FILE=tracker, SEEN_JOBS_FILE=root/'absent.json'):
                entry = next(iter(dashboard.load_tracker().values()))
                self.assertIsNone(entry['cv_file'])
                self.assertEqual(entry['cover_letter_file'], 'letter.pdf')


if __name__ == '__main__':
    unittest.main()
