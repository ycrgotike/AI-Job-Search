import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools import gemini_tailoring as m, generate_application as g
from tools.generation_diagnostics import save_failure
from tests import test_gemini_tailoring as fixtures

class ReliabilityTests(unittest.TestCase):
    def test_day_one_marketing_is_not_a_start_date(self):
        plan={'duties':[{'source':'Build internal AI tools', 'priority':'primary','evidence':''}], 'gaps':[], 'timing_source':'Ready to make an impact from day one?', 'project_order':['upsc']}
        result=m.validate_plan(plan,'Build internal AI tools. Ready to make an impact from day one?','Python',{'upsc':{}})
        self.assertEqual(result['timing_source'],'')
        plan['timing_source']='Start on 15 November 2026'
        result=m.validate_plan(plan,'Build internal AI tools. Start on 15 November 2026','Python',{'upsc':{}})
        self.assertEqual(result['timing_source'],'Start on 15 November 2026')

    def test_letter_only_repair_and_authoritative_logistics(self):
        fixture=fixtures.GeminiTests();draft,plan=fixture.review_fixture()
        bad=dict(draft,paragraphs=['short']*3)
        repaired={'opening':draft['opening'],'paragraphs':draft['paragraphs']}
        with tempfile.TemporaryDirectory() as temp, patch.object(m,'build_plan',return_value=plan), patch.object(m,'request_json',side_effect=[bad,repaired,{'issues':[],'coverage':[],'gaps':[]},{'issues':[]}]) as api, patch.object(m.time,'sleep'), patch('tools.generation_diagnostics.save_failure',return_value='report.json'):
            cv,_,_=m.generate(g,{'key':'secret','model':'test'},'Example','Example','Data Analyst','Python reports')
        self.assertEqual(set(api.call_args_list[1].args[3]['properties']),{'opening','paragraphs'})
        factual=api.call_args_list[-1].args[2]
        self.assertNotIn('fixed_closing',factual)
        self.assertIn(g.start_date().strftime('%B %Y'),factual['authoritative_logistics']['calculated_availability'])
        self.assertIn('do NOT imply previous employment',api.call_args_list[-1].args[1])
        self.assertIn(draft['header'],cv)

    def test_summary_only_repair_and_allowed_range(self):
        fixture=fixtures.GeminiTests();draft,plan=fixture.review_fixture()
        # 40-word summary should be accepted without repair
        draft['summaries'] = ['Data Engineer with 5+ years experience. ' * 8] * 3
        with tempfile.TemporaryDirectory() as temp, patch.object(m,'build_plan',return_value=plan), patch.object(m,'request_json',side_effect=[draft,{'issues':[],'coverage':[],'gaps':[]},{'issues':[]}]) as api, patch.object(m.time,'sleep'), patch('tools.generation_diagnostics.save_failure',return_value='report.json'):
            cv,_,_=m.generate(g,{'key':'secret','model':'test'},'Example','Example','Data Analyst','Python reports')
        self.assertIn(draft['header'], cv)

        # A summary under 38 words triggers targeted summary repair
        too_short = dict(draft, summaries=['Too short summary.'] * 3)
        repaired_summaries = {'summaries': ['Data Engineer with 5+ years experience. ' * 11] * 3}
        with tempfile.TemporaryDirectory() as temp, patch.object(m,'build_plan',return_value=plan), patch.object(m,'request_json',side_effect=[too_short, repaired_summaries, {'issues':[],'coverage':[],'gaps':[]},{'issues':[]}]) as api, patch.object(m.time,'sleep'), patch('tools.generation_diagnostics.save_failure',return_value='report.json'):
            cv,_,_=m.generate(g,{'key':'secret','model':'test'},'Example','Example','Data Analyst','Python reports')
        self.assertEqual(set(api.call_args_list[1].args[3]['properties']), {'summaries'})

    def test_failure_report_allowlist_and_atomic_private_output(self):
        with tempfile.TemporaryDirectory() as temp:
            relative=save_failure(Path(temp),'Example','AI Engineer','Word count needs repair',stage='draft',draft={'opening':'Supported experience.','api_key':'never-save-this'},plan={'timing_source':'','key':'never-save-this'})
            file=Path(temp)/relative
            data=json.loads(file.read_text())
            self.assertEqual(data['stage'],'draft')
            self.assertNotIn('never-save-this',file.read_text())
            self.assertEqual(file.stat().st_mode & 0o777,0o600)

if __name__=='__main__':unittest.main()
