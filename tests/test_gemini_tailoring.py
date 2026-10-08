import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError
from tools import gemini_tailoring as m
from tools import generate_application as g


class GeminiTests(unittest.TestCase):
    def fixture(self):
        evidence = {'soltech': ['a', 'b'], 'gsr': ['c'], 'projects': dict.fromkeys(['a','b','c','d'])}
        d = {'summaries': ['Python ' * 60]*3, 'header': 'Data professional',
             'skills': [{'label': 'Tools', 'terms': ['Python']}]*3,
             'soltech': [1,0], 'gsr': [0], 'projects': ['a','b','c','d'],
             'opening': 'I am applying.', 'paragraphs': ['word '*100, 'word '*100, 'word '*110], 'gaps': []}
        return d, evidence

    def test_configuration_and_environment_precedence(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            p=Path(directory)/'.env';p.write_text('APPLICATION_LLM_PROVIDER=gemini\nGEMINI_API_KEY="local-secret"\nGEMINI_MODEL=gemini-test\n')
            self.assertEqual(m.settings(directory)['key'],'local-secret')
            with patch.dict(os.environ, {'GEMINI_API_KEY':'env-secret'}):
                self.assertEqual(m.settings(directory)['key'],'env-secret')
            p.write_text('GEMINI_MODEL=https://evil.invalid\n')
            with self.assertRaises(ValueError): m.settings(directory)

    def test_defaults_off_and_missing_key_does_not_call_network(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {}, clear=True):
            self.assertEqual(m.settings(d)['provider'],'rules')
        with patch.object(m.urllib.request,'urlopen') as network:
            with self.assertRaisesRegex(ValueError,'missing'):
                m.request_json({'key':'','model':'test'},'',{},m.SCHEMA)
            network.assert_not_called()

    def test_api_uses_header_and_json_schema(self):
        response=MagicMock();response.__enter__.return_value.read.return_value=json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'{"ok": true}'}]}}]}).encode()
        with patch.object(m.urllib.request,'urlopen',return_value=response) as call:
            self.assertTrue(m.request_json({'key':'secret','model':'test'},'system',{},m.SCHEMA)['ok'])
            request=call.call_args.args[0]
            self.assertNotIn('secret',request.full_url)
            self.assertEqual(request.get_header('X-goog-api-key'),'secret')
            self.assertIn('responseJsonSchema',json.loads(request.data)['generationConfig'])

    def test_errors_redact_provider_body(self):
        error=HTTPError('https://example','429','secret',{},None)
        with patch.object(m.urllib.request,'urlopen',side_effect=error):
            with self.assertRaises(ValueError) as caught:
                m.request_json({'key':'secret','model':'test'},'',{},m.SCHEMA)
            self.assertNotIn('secret',str(caught.exception))
            self.assertIn('429',str(caught.exception))

    def test_temporary_503_retries_and_recovers(self):
        response=MagicMock()
        response.__enter__.return_value.read.return_value=b'{"candidates":[{"finishReason":"STOP","content":{"parts":[{"text":"{\\"ok\\":true}"}]}}]}'
        error=HTTPError('https://example',503,'unavailable',{'Retry-After':'5'},None)
        with patch.object(m.urllib.request,'urlopen',side_effect=[error,response]) as call, patch.object(m.time,'sleep') as sleep:
            self.assertTrue(m.request_json({'key':'secret','model':'test'},'',{},m.SCHEMA)['ok'])
            self.assertEqual(call.call_count,2)
            sleep.assert_called_once_with(5)

    def test_service_retry_limit_and_clear_error(self):
        error=HTTPError('https://example',503,'secret',{},None)
        with patch.object(m.urllib.request,'urlopen',side_effect=error) as call, patch.object(m.time,'sleep') as sleep:
            with self.assertRaisesRegex(ValueError,'after 3 attempts') as caught:
                m.request_json({'key':'secret','model':'test'},'',{},m.SCHEMA)
            self.assertEqual(call.call_count,3)
            self.assertEqual([x.args[0] for x in sleep.call_args_list],[2,4])
            self.assertNotIn('secret',str(caught.exception))

    def test_auth_and_quota_are_not_retried(self):
        for status in (401,403,404,429):
            with self.subTest(status=status), patch.object(m.urllib.request,'urlopen',side_effect=HTTPError('https://example',status,'secret',{},None)) as call, patch.object(m.time,'sleep') as sleep:
                with self.assertRaises(ValueError):
                    m.request_json({'key':'secret','model':'test'},'',{},m.SCHEMA)
                self.assertEqual(call.call_count,1)
                sleep.assert_not_called()

    def test_connection_retries_are_bounded(self):
        with patch.object(m.urllib.request,'urlopen',side_effect=TimeoutError()) as call, patch.object(m.time,'sleep'):
            with self.assertRaisesRegex(ValueError,'after 3 attempts'):
                m.request_json({'key':'secret','model':'test'},'',{},m.SCHEMA)
            self.assertEqual(call.call_count,3)

    def test_truncated_response_rejected(self):
        response=MagicMock();response.__enter__.return_value.read.return_value=b'{"candidates":[{"finishReason":"MAX_TOKENS"}]}'
        with patch.object(m.urllib.request,'urlopen',return_value=response):
            with self.assertRaisesRegex(ValueError,'incomplete'):
                m.request_json({'key':'secret','model':'test'},'',{},m.SCHEMA)

    def test_grounding_indexes_word_count_and_latex(self):
        draft,evidence=self.fixture()
        self.assertEqual(m.validate(draft,evidence,'Python','closing'),314)
        for key,value in [('soltech',[0,0]),('projects',['a']*4),('opening',r'\input{secret}'),('paragraphs',['short']*3)]:
            d=copy.deepcopy(draft);d[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate(d,evidence,'Python','closing')
        draft['skills'][0]['terms']=['InventedTool']
        with self.assertRaisesRegex(ValueError,'grounded'):m.validate(draft,evidence,'Python','closing')

    def test_fixed_closing_is_not_duplicated_or_audited_as_generated_claim(self):
        draft,evidence=self.fixture()
        fixed='I am available to start on 1 November 2026. Thank you for your consideration.'
        draft['paragraphs'][-1] += ' ' + fixed
        words=m.validate(draft,evidence,'Python',fixed)
        self.assertNotIn('1 November',draft['paragraphs'][-1])
        self.assertEqual(words,313+len(fixed.split()))

    def test_rendering_and_bounded_word_repair(self):
        fixed=g.letter_fixed_text('Example','Data Analyst','Python reports')
        draft,_=self.fixture()
        draft['soltech']=list(range(len(g.section_bullets('Data Analyst - SolTech'))))
        draft['gsr']=list(range(len(g.section_bullets('Data Engineer - G.S.R'))))
        draft['projects']=['sql','trading','twitter','upsc']
        count=320-len(fixed.split())-len(draft['opening'].split())
        draft['paragraphs']=['analysis '*(count//3),'data '*(count//3),'reporting '*(count-2*(count//3))]
        bad=copy.deepcopy(draft);bad['paragraphs']=['short']*3
        with patch.object(m,'build_plan',return_value={'project_order':draft['projects'], 'duties':[], 'gaps':[]}), patch.object(m.time,'sleep'), patch.object(m,'request_json',side_effect=[bad,draft,{'issues':[], 'coverage':[], 'gaps':[]},{'issues':[]}]) as api:
            cv,letter,meta=m.generate(g,{'provider':'gemini','key':'x','model':'test'},'Example','Example','Data Analyst','Python reports')
        self.assertEqual(api.call_count,4)
        self.assertEqual(g.cover_letter_body_words(letter),320)
        self.assertIn('PROFILE STATEMENT',cv)
        self.assertNotIn('__PROFILE__',cv)
        self.assertEqual(meta['provider'],'gemini')

    def review_fixture(self):
        draft,_=self.fixture()
        draft['soltech']=list(range(len(g.section_bullets('Data Analyst - SolTech'))))
        draft['gsr']=list(range(len(g.section_bullets('Data Engineer - G.S.R'))))
        draft['projects']=['sql','trading','twitter','upsc']
        fixed=g.letter_fixed_text('Example','Data Analyst','Python reports')
        count=320-len(fixed.split())-len(draft['opening'].split())
        draft['paragraphs']=['analysis '*(count//3),'data '*(count//3),'reporting '*(count-2*(count//3))]
        plan={'project_order':draft['projects'], 'duties':[], 'gaps':[]}
        return draft,plan

    def test_quality_warnings_preserved_after_bounded_repairs(self):
        draft,plan=self.review_fixture()
        audit={'issues':['Make the opening more concrete.'], 'coverage':[], 'gaps':[]}
        responses=[copy.deepcopy(x) for _ in range(3) for x in (draft,audit,{'issues':[]})]
        with patch.object(m,'build_plan',return_value=plan), patch.object(m,'request_json',side_effect=responses) as api, patch.object(m.time,'sleep'):
            _,_,meta=m.generate(g,{'provider':'gemini','key':'x','model':'test'},'Example','Example','Data Analyst','Python reports')
        self.assertEqual(meta['quality_warnings'],audit['issues'])
        self.assertEqual(api.call_count,9)
        audit_inputs=api.call_args_list[4].args[2]
        self.assertNotIn('revision_history',audit_inputs)
        self.assertNotIn('previous_draft',audit_inputs)
        self.assertNotIn('writing_rules',audit_inputs)

    def test_service_exhaustion_does_not_restart_content_loop(self):
        _,plan=self.review_fixture()
        with patch.object(m,'build_plan',return_value=plan), patch.object(m,'request_json',side_effect=ValueError('Gemini is temporarily unavailable after 3 attempts')) as api, patch.object(m.time,'sleep'):
            with self.assertRaisesRegex(ValueError,'temporarily unavailable'):
                m.generate(g,{'provider':'gemini','key':'x','model':'test'},'Example','Example','Data Analyst','Python reports')
        api.assert_called_once()

    def test_factual_issues_remain_blocking(self):
        draft,plan=self.review_fixture()
        responses=[copy.deepcopy(x) for _ in range(6) for x in (draft,{'issues':[], 'coverage':[], 'gaps':[]},{'issues':['Unsupported prior vehicle testing experience.']})]
        with patch.object(m,'build_plan',return_value=plan), patch.object(m,'request_json',side_effect=responses), patch.object(m.time,'sleep'):
            with self.assertRaisesRegex(ValueError,'Factual corrections required'):
                m.generate(g,{'provider':'gemini','key':'x','model':'test'},'Example','Example','Data Analyst','Python reports')

    def test_failed_gemini_never_records_or_uses_rules(self):
        job={'company':'Example','title':'Novel Role','description':'Custom research duties','is_custom':True}
        with patch.object(m,'settings',return_value={'provider':'gemini','key':'x','model':'test'}), \
             patch.object(m,'generate',side_effect=ValueError('Gemini unavailable')), \
             patch.object(g,'build_tailored_cv') as rules,patch.object(g,'record_in_tracker') as record,patch.object(g,'compile_latex') as compile_:
            result=g.generate_for_job(job)
        self.assertFalse(result['success']);rules.assert_not_called();record.assert_not_called();compile_.assert_not_called()

    def test_recipient_address_formats_location_only_without_contact_person(self):
        # 1. Rules-based cover letter test
        letter_rules = g.build_tailored_cover_letter(
            company='Mercedes-Benz AG',
            company_pascal='MercedesBenz',
            role_title='Data Engineer',
            description='Mercedes-Benz Plant Sindelfingen 71063. We need Python and SQL.',
            is_student=False,
            is_data_eng=True,
            is_analytics=False,
            is_ai_ml=False,
            contact_person='Ruben Voigtländer',
            location=''
        )
        self.assertIn(r'\companyname{Mercedes-Benz AG}', letter_rules)
        self.assertIn(r'\companyaddress{Hiring Team\\Sindelfingen, Germany}', letter_rules)
        self.assertNotIn('Ruben Voigtländer', letter_rules.split(r'\companyaddress{')[1].split('}')[0])
        self.assertIn(r'\lettercontent{Dear Ruben Voigtländer,}', letter_rules)

        # 2. Gemini cover letter test
        fixed = g.letter_fixed_text('Mercedes-Benz AG', 'Data Engineer', 'Python and SQL')
        draft, _ = self.fixture()
        draft['soltech'] = list(range(len(g.section_bullets('Data Analyst - SolTech'))))
        draft['gsr'] = list(range(len(g.section_bullets('Data Engineer - G.S.R'))))
        draft['projects'] = ['sql', 'trading', 'twitter', 'upsc']
        count = 320 - len(fixed.split()) - len(draft['opening'].split())
        draft['paragraphs'] = ['engineering ' * (count // 3), 'pipelines ' * (count // 3), 'cloud ' * (count - 2 * (count // 3))]
        with patch.object(m,'build_plan',return_value={'project_order':draft['projects'], 'duties':[], 'gaps':[]}), patch.object(m, 'request_json', side_effect=[draft, {'issues': [], 'coverage':[], 'gaps':[]}, {'issues': []}]):
            _, letter_gemini, _ = m.generate(
                g, {'provider': 'gemini', 'key': 'x', 'model': 'test'},
                'Mercedes-Benz AG', 'MercedesBenz', 'Data Engineer',
                'Mercedes-Benz Plant Sindelfingen 71063. We need Python and SQL.',
                contact='Ruben Voigtländer'
            )
        self.assertIn(r'\companyname{Mercedes-Benz AG}', letter_gemini)
        self.assertIn(r'\companyaddress{Hiring Team\\Sindelfingen, Germany}', letter_gemini)
        self.assertNotIn('Ruben Voigtländer', letter_gemini.split(r'\companyaddress{')[1].split('}')[0])
        self.assertIn(r'\lettercontent{Dear Ruben Voigtländer,}', letter_gemini)

    def test_extract_company_location_detects_plz_and_plant(self):
        loc1 = g.extract_company_location('Mercedes-Benz Plant Sindelfingen is hiring.')
        self.assertEqual(loc1, 'Sindelfingen, Germany')
        loc2 = g.extract_company_location('Office located at 71063 Sindelfingen.')
        self.assertEqual(loc2, 'Sindelfingen, Germany')
        loc3 = g.extract_company_location('Audi AG Standort Neckarsulm.')
        self.assertEqual(loc3, 'Neckarsulm, Germany')
        # Regression: Location Intelligence and Site Reliability must never be extracted as cities
        loc4 = g.extract_company_location('Building the leading consultancy for AI and Location Intelligence in Germany.')
        self.assertEqual(loc4, 'Germany')
        loc5 = g.extract_company_location('We specialize in Site Reliability Engineering across Germany.')
        self.assertEqual(loc5, 'Germany')
        # Portal URL city slug extraction takes precedence over body text buzzwords
        loc6 = g.extract_company_location({
            'url': 'https://www.stepstone.de/stellenangebote--Werkstudent-in-Software-Engineering-for-AI-Systems-m-w-d-Cologne-Niologic-GmbH--14514156-inline.html',
            'description': 'At Niologic, we are building consultancy for AI and Location Intelligence in Germany.'
        })
        self.assertEqual(loc6, 'Cologne, Germany')
        # Demonyms like Kölner Büro
        loc7 = g.extract_company_location('Bereitschaft zur Arbeit im Kölner Büro an 3 Tagen.')
        self.assertEqual(loc7, 'Köln, Germany')

    def test_skills_empty_group_pruned_and_supplemented(self):
        draft, evidence = self.fixture()
        # 2 valid groups + 1 empty group
        draft['skills'] = [
            {'label': 'Technical Skills', 'terms': ['Python', 'SQL', 'PyTorch']},
            {'label': 'AI & Infrastructure', 'terms': ['AWS', 'GCP']},
            {'label': 'Research Interests', 'terms': []}
        ]
        profile = g.profile_text()
        words = m.validate(draft, evidence, profile, 'closing text')
        self.assertGreaterEqual(words, 300)
        self.assertGreaterEqual(len(draft['skills']), 3)
        self.assertTrue(all(len(group['terms']) > 0 for group in draft['skills']))

    def test_skills_mixed_unsupported_terms_pruned(self):
        draft, evidence = self.fixture()
        draft['skills'] = [
            {'label': 'Technical Skills', 'terms': ['Python', 'SQL', 'CompletelyInventedTerm123']},
            {'label': 'Cloud', 'terms': ['Docker', 'Git']},
            {'label': 'ML', 'terms': ['PyTorch']}
        ]
        profile = g.profile_text()
        words = m.validate(draft, evidence, profile, 'closing text')
        self.assertGreaterEqual(words, 300)
        self.assertNotIn('CompletelyInventedTerm123', draft['skills'][0]['terms'])
        self.assertIn('Python', draft['skills'][0]['terms'])

if __name__=='__main__':unittest.main()

