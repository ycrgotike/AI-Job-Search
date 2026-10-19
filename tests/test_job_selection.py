import csv
import io
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import server
from tools import job_selection as selection, scrape

DESCRIPTION = ('Build and maintain scalable ingestion pipelines using Python and SQL. '
               'Design dimensional models and deploy automated validation for reliable reporting. '
               'Integrate cloud storage and implement orchestration with Airflow. '
               'Monitor warehouse performance and improve query latency with the analytics team.')
OTHER_DESCRIPTION = ('Develop platform authentication services and maintain API authorization. '
                     'Implement deployment automation and monitor access control across business units. '
                     'Build application integration services and optimize cloud service monitoring.')


def posting(key='one', **values):
    return dict(key=key, company='Example GmbH', title='Data Engineer (m/w/d)',
                url='https://example.com/jobs/'+key, portal='linkedin-search',
                _description=DESCRIPTION, is_applied=False, **values)


class RelevanceTests(unittest.TestCase):
    def test_core_roles_and_german_roles_remain_eligible(self):
        for title in ('Senior Data Engineer', 'Data Analyst', 'Data Scientist', 'Business Analyst',
                      'Werkstudent Data Science', 'BI Entwickler', 'KI-Plattform-Experte',
                      'Machine Learning Engineer', 'Consultant Data Governance', 'Analytics Engineer',
                      'Marketing Data Analyst', 'Marketing Analytics Manager', 'Quantitative Analyst',
                      'Data-Engineer', 'Business-Intelligence Analyst'):
            with self.subTest(title=title):
                self.assertIsNotNone(selection.role_category(title))

    def test_student_and_incidental_technology_mentions_do_not_establish_relevance(self):
        for title in ('Werkstudent Social Media', 'Werkstudent Product Design',
                      'Intern Talent Acquisition & Employer Branding', 'Retail Assistant',
                      'Working Student Customer Support', 'AI Sales Manager'):
            with self.subTest(title=title):
                self.assertIsNone(selection.role_category(title, 'Our company builds AI solutions and uses Python, SQL, Power BI.'))
                self.assertEqual(server.calculate_match_score(title, 'Python, SQL, Azure, Docker, Germany')[0], 0)

    def test_adjacent_role_requires_real_duties_not_company_bio(self):
        self.assertEqual(selection.role_category('Werkstudent Controlling', 'Your tasks: Build Power BI dashboards and automate reporting.'), selection.ANALYTICS)
        self.assertEqual(selection.role_category('Werkstudent Controlling', 'Deine Aufgaben: Erstellen Sie Power-BI-Dashboards und automatisieren Sie das Reporting.'), selection.ANALYTICS)
        self.assertEqual(selection.role_category('Frontier Engineer', 'In this role you will develop agentic workflows for enterprise customers.'), selection.AI)
        self.assertIsNone(selection.role_category('Frontend Developer', 'We develop AI solutions for our customers. Requirements: Python and SQL.'))
        self.assertIsNone(selection.role_category('Werkstudent Controlling', 'Work alongside data engineers. Familiarity with Power BI is a plus.'))

    def test_category_uses_word_boundaries(self):
        self.assertEqual(selection.display_category('Data Engineer for Retail'), selection.DATA_ENGINEERING)
        self.assertEqual(selection.display_category('Data Analyst - Mobility'), selection.ANALYTICS)
        self.assertEqual(selection.display_category('Working Student ML Engineer'), 'Werkstudent & Intern')


class DuplicateTests(unittest.TestCase):
    def test_same_linkedin_id_and_tracking_parameters_merge(self):
        left=posting(); left['url']='https://de.linkedin.com/jobs/view/data-engineer-123456789?trk=foo'
        right=posting('two'); right['url']='https://www.linkedin.com/jobs/view/123456789?utm_source=bar'
        merged=selection.consolidate_jobs([left,right])
        self.assertEqual(len(merged),1)
        self.assertEqual(merged[0]['listing_count'],2)

    def test_company_suffix_gender_and_aggregator_title_variants_merge(self):
        left=posting();left.update(company='Sparda Bank Hannover eG Personalservice', title='KI-Plattform-Experte (m/w/d) - Sparda Bank Hannover e')
        right=posting('two');right.update(company='Sparda-Bank Hannover eG', title='KI-Plattform-Experte (all genders)', portal='freehire-search', _description='About the team. '+DESCRIPTION)
        merged=selection.consolidate_jobs([left,right])
        self.assertEqual(len(merged),1)
        self.assertEqual(set(merged[0]['portals']),{'linkedin-search','freehire-search'})
        self.assertEqual(len(merged[0]['source_listings']),2)

    def test_distinct_employers_roles_locations_and_descriptions_stay_separate(self):
        for difference in ({'company':'Other GmbH'}, {'title':'Senior Data Engineer'},
                           {'location':'Munich'}, {'_description':OTHER_DESCRIPTION}, {'_description':''}):
            with self.subTest(difference=difference):
                left=posting(location='Berlin');right=posting('two');right.update(difference)
                self.assertEqual(len(selection.consolidate_jobs([left,right])),2)

    def test_numbered_and_flattened_descriptions_of_one_posting_merge(self):
        paragraphs = DESCRIPTION.split('. ')
        numbered = '\n'.join(f'{i}. {part}' for i, part in enumerate(paragraphs, 1))
        left = posting(); left['_description'] = 'Responsibilities:\n' + numbered
        right = posting('two'); right['_description'] = 'Responsibilities: ' + DESCRIPTION
        self.assertEqual(len(selection.consolidate_jobs([left, right])), 1)

    def test_shared_company_boilerplate_does_not_merge_different_duties(self):
        intro = 'About our company: We are a global employer providing enterprise services. ' * 40
        left = posting(); left['_description'] = intro + 'Responsibilities: ' + DESCRIPTION
        right = posting('two'); right['_description'] = intro + 'Responsibilities: ' + OTHER_DESCRIPTION
        self.assertEqual(len(selection.consolidate_jobs([left, right])), 2)

    def test_query_requisition_ids_are_not_removed(self):
        self.assertNotEqual(selection.posting_url('https://example.com/jobs?id=1'),selection.posting_url('https://example.com/jobs?id=2'))

    def test_tracked_record_keeps_action_key_status_and_documents(self):
        left=posting();right=posting('tracked');right.update(is_applied=True,status='interviewing',cv_file='cv/example.pdf')
        merged=selection.consolidate_jobs([left,right])[0]
        self.assertEqual((merged['key'],merged['status'],merged['cv_file']),('tracked','interviewing','cv/example.pdf'))
        self.assertNotIn('_description',merged)


class PipelineTests(unittest.TestCase):
    def test_dashboard_hides_irrelevant_jobs_without_mutating_history(self):
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'seen.json'
            entries={}
            for key,title in (('data','Data Engineer'),('irrelevant','Werkstudent Social Media'),('tracked','Customer Support')):
                entries[key]=dict(title=title,company='Example',url='https://example.com/'+key,
                                  posted_date=str(date.today()),description=DESCRIPTION,portal='web')
            file.write_text(json.dumps({'seen':entries}))
            before=file.read_bytes()
            tracked={'company':'Example','role':'Customer Support','status':'applied','source':'https://example.com/tracked','fit_rating':'','contact_person':'','cv_file':None,'cover_letter_file':None}
            with patch.multiple(server,SEEN_JOBS_FILE=file,TRACKER_FILE=Path(temp)/'none.csv',_ENRICHED_CACHE=None), \
                 patch.object(server,'load_tracker',return_value={'https://example.com/tracked':tracked}):
                jobs,counts=server.get_enriched_jobs(include_counts=True)
            self.assertEqual({j['key'] for j in jobs},{'data','tracked'})
            self.assertEqual(counts['hidden_reasons']['relevance'],1)
            self.assertEqual(file.read_bytes(),before)

    def test_scraper_rejects_irrelevant_and_legacy_url_duplicates(self):
        existing={'legacy':dict(company='Example',title='Data Engineer',url='https://example.com/1',description=DESCRIPTION)}
        rows=[dict(company='Example',title='Data Engineer',url='https://example.com/1?utm_source=test',description=DESCRIPTION,posted_date=str(date.today()),portal='freehire-search'),
              dict(company='Example',title='Werkstudent Social Media',url='https://example.com/2',description=DESCRIPTION,posted_date=str(date.today()),portal='freehire-search'),
              dict(company='New',title='Data Analyst',url='https://example.com/3',description=DESCRIPTION,posted_date=str(date.today()),portal='freehire-search')]
        with patch.object(scrape,'run_freehire_search',return_value=rows),patch('sys.stdout',new=io.StringIO()):
            result=scrape.scrape_query('Data','Germany',10,2,set(),existing,{'freehire'})
        self.assertEqual(result[0],1)
        self.assertEqual(result[1],1)
        self.assertEqual(len(existing),2)
        self.assertFalse(any(j['title']=='Werkstudent Social Media' for j in existing.values()))

if __name__=='__main__':unittest.main()
