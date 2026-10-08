import json
import socket
import unittest
from unittest.mock import patch
from tools.job_description import resolve_description, needs_resolution, public_url
from tools.responsibility_plan import analyze_posting
from tools import generate_application as g

BODY = '''Your tasks
Maintain reporting dashboards and analyze cloud costs for teams and projects. Investigate unexpected changes and explain findings to finance colleagues. Develop useful reports from multiple data sources and document the methods used to prepare reliable management information. Monitor budgets and prepare presentations with clearly defined reporting periods and allocation rules.
Your profile
You are enrolled at university and have knowledge of cloud infrastructure, Excel and PowerPoint. You enjoy working with colleagues and learning new methods.'''
JOB = {'title':'Working Student FinOps Cloud Cost Management', 'company':'Heraeus GmbH', 'url':'https://www.arbeitsagentur.de/jobsuche/jobdetail/123', 'posted_date':'2026-09-23', 'description':'Die vollständige Stellenbeschreibung finden Sie auf unserer Website.'}


def page(body=BODY, title=JOB['title'], company='Heraeus GmbH', **extra):
    data={'@type':'JobPosting','title':title,'hiringOrganization':{'name':company},'description':body,**extra}
    return '<script type="application/ld+json">'+json.dumps(data)+'</script>'

class DescriptionResolution(unittest.TestCase):
    def test_referral_and_empty_need_resolution_but_full_text_does_not(self):
        self.assertTrue(needs_resolution(JOB['description']))
        self.assertTrue(needs_resolution(''))
        self.assertFalse(needs_resolution(BODY))

    def test_external_metadata_fetch_preserves_dates_and_links(self):
        job=dict(JOB); before=dict(job)
        result=resolve_description(job, {'externalUrls':['https://careers.example/job/12']}, lambda u:(u,page()))
        self.assertEqual(result['description_status'],'ready')
        self.assertEqual(result['description_source_url'],'https://careers.example/job/12')
        self.assertEqual(result['discovery_url'],JOB['url'])
        self.assertEqual(job,before)
        self.assertNotIn('posted_date',result)

    def test_two_hop_referral(self):
        pages={JOB['url']:'<a href="https://recruiter.example/job/12">Zum Stellenangebot</a>',
               'https://recruiter.example/job/12':'<a href="https://careers.example/job/12">Full job description</a>',
               'https://careers.example/job/12':page()}
        result=resolve_description(dict(JOB),fetcher=lambda u:(u,pages[u]))
        self.assertEqual(result['description_status'],'ready')
        self.assertEqual(result['description'],BODY)

    def test_wrong_employer_role_expired_and_blocked_are_not_used(self):
        cases=[page(company='Other GmbH'),page(title='Senior Legal Counsel'),page(validThrough='2020-01-01'),'<h1>Access denied</h1>']
        for html in cases:
            with self.subTest(html=html):
                result=resolve_description(dict(JOB),fetcher=lambda u:(u,html))
                self.assertEqual(result['description_status'],'description_needed')
                self.assertEqual(result['description'],JOB['description'])

    def test_plain_html_needs_matching_heading(self):
        for title,expected in [(JOB['title'],'ready'),('All careers','description_needed')]:
            html='<h1>'+title+'</h1><p>Heraeus GmbH</p><main>'+BODY+'</main>'
            self.assertEqual(resolve_description(dict(JOB),fetcher=lambda u:(u,html))['description_status'],expected)

    def test_loop_and_errors_are_bounded(self):
        calls=[]
        def fetch(u):
            calls.append(u)
            return u,'<a href="'+u+'">Job description</a>'
        result=resolve_description(dict(JOB),fetcher=fetch)
        self.assertEqual(len(calls),1)
        self.assertEqual(result['description_status'],'description_needed')
        def blocked(u):raise TimeoutError('blocked')
        self.assertEqual(resolve_description(dict(JOB),fetcher=blocked)['description_status'],'description_needed')

    def test_private_destinations_rejected(self):
        with patch.object(socket,'getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',80))]):
            with self.assertRaises(ValueError):public_url('http://localhost/job')
        for u in ['file:///tmp/job','http://user:secret@example.com/job','http://example.com:8000/job']:
            with self.assertRaises(ValueError):public_url(u)

    def test_culture_does_not_block_real_duties(self):
        text='Aufgaben\nErstellung von Reporting Dashboards.\nPraxisnahe Aufgaben mit konkretem Nutzen für Controlling, Fachbereiche und Management\nZusammenarbeit mit erfahrenen Kolleginnen und Kollegen in einer offenen und unterstützenden Kultur'
        plan=analyze_posting('Student',text)
        self.assertFalse(plan['review_issues'])
        self.assertFalse(plan['review_warnings'])

    def test_unmapped_secondary_work_is_a_warning(self):
        plan=analyze_posting('Analyst','Tasks\nMaintain reporting dashboards.\nManage insurance claims and negotiate settlements.')
        self.assertFalse(plan['review_issues'])
        self.assertTrue(plan['review_warnings'])

    def test_failed_resolution_never_generates_documents(self):
        with patch.object(g,'fetch_description_for_job',return_value=''),patch.object(g,'build_tailored_cv') as build:
            result=g.generate_for_job(dict(JOB))
        self.assertEqual(result['verification_status'],'description_needed')
        build.assert_not_called()

    def test_unknown_work_is_flagged_without_blocking_draft(self):
        plan=analyze_posting('Legal','Tasks\nManage insurance claims and negotiate settlements.')
        self.assertFalse(plan['review_issues'])
        self.assertTrue(plan['review_warnings'])

if __name__=='__main__':unittest.main()
