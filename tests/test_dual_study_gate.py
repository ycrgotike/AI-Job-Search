"""Reject dual-study programmes without losing ordinary student opportunities."""
import io
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import server
from tools import job_selection as selection, scrape


class DualStudyTests(unittest.TestCase):
    def test_german_and_english_title_variants_override_data_relevance(self):
        for title in (
            'Duales Studium Data Science & Künstliche Intelligenz',
            'Duales-Studium: Data Engineer',
            'Platz im dualen Studium Data Analytics',
            'Dualer Studiengang Data Science',
            'Duale Studiengänge Data Science',
            'Duales Bachelorstudium Data Science',
            'Dualstudent Data Scientist (m/w/d)',
            'Data Engineer — Dual Study Programme',
            'Dual Studies in Business Intelligence',
        ):
            with self.subTest(title=title):
                self.assertTrue(selection.is_dual_study_posting(title))
                self.assertIsNone(selection.role_category(title, 'Build data pipelines using Python.'))

    def test_job_type_in_details_is_excluded(self):
        for description in (
            '<h1>Duales&nbsp;Studium Data Science</h1>Build ML models.',
            'Employment type: dual-study programme. Build data pipelines.',
            'Anstellungsart: Duales Studium. Entwickle Datenpipelines.',
            'This position is a dual study programme. Build predictive models.',
            'Du absolvierst ein duales Studium in Data Science.',
        ):
            with self.subTest(description=description):
                self.assertIsNone(selection.role_category('Data Scientist', description))

    def test_regular_student_and_full_time_jobs_remain_eligible(self):
        description = ('Build data pipelines with Python. Our company also offers '
                       'apprenticeships and dual study programmes in other departments.')
        for title in ('Data Engineer', 'Werkstudent Data Science', 'Intern Data Analyst',
                      'Master Thesis Machine Learning'):
            with self.subTest(title=title):
                self.assertFalse(selection.is_dual_study_posting(title, description))
                self.assertIsNotNone(selection.role_category(title, description))

    def test_scraper_rejects_titles_before_detail_requests_and_never_saves_them(self):
        job = dict(title='Duales Studium Data Science', company='Example',
                   url='https://linkedin.com/jobs/view/123456789',
                   posted_date=str(date.today()), portal='linkedin-search')
        seen = {}
        with patch.object(scrape, 'run_linkedin_search', return_value=[job]), \
             patch.object(scrape, 'fetch_linkedin_details') as details, \
             patch('sys.stdout', new=io.StringIO()):
            result = scrape.scrape_query('Data Science', 'Germany', 10, 2, set(), seen, {'linkedin'})
        self.assertEqual(result[0], 0)
        self.assertEqual(seen, {})
        details.assert_not_called()

    def test_scraper_rechecks_fetched_descriptions_before_saving(self):
        job = dict(title='Data Scientist', company='Example',
                   url='https://linkedin.com/jobs/view/123456789',
                   posted_date=str(date.today()), portal='linkedin-search')
        seen = {}
        with patch.object(scrape, 'run_linkedin_search', return_value=[job]), \
             patch.object(scrape, 'fetch_linkedin_details', return_value=(
                 'Employment type: Dual Study Programme. Build ML models.', True, '1 hour ago', False)), \
             patch('sys.stdout', new=io.StringIO()):
            result = scrape.scrape_query('Data Science', 'Germany', 10, 2, set(), seen, {'linkedin'})
        self.assertEqual(result[0], 0)
        self.assertEqual(seen, {})

    def test_dashboard_hides_saved_dual_study_opportunities_without_deleting_history(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'seen.json'
            rows = {key: dict(title=title, company=key, url='https://example.com/' + key,
                             posted_date=str(date.today()), description='Build Python data pipelines.', portal='web')
                    for key, title in (('dual', 'Duales Studium Data Science'), ('eligible', 'Werkstudent Data Science'))}
            state.write_text(json.dumps({'seen': rows}))
            original = state.read_bytes()
            with patch.multiple(server, SEEN_JOBS_FILE=state, TRACKER_FILE=Path(directory) / 'none.csv',
                                _ENRICHED_CACHE=None), patch.object(server, 'load_tracker', return_value={}):
                jobs, counts = server.get_enriched_jobs(include_counts=True)
            self.assertEqual([j['key'] for j in jobs], ['eligible'])
            self.assertEqual(counts['hidden_reasons']['dual_study'], 1)
            self.assertEqual(state.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
