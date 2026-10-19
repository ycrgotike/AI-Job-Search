import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools import bullet_tailoring as b, gemini_tailoring as m, generate_application as g
from tests import test_gemini_tailoring as fixtures


class BulletTests(unittest.TestCase):
    def proposal(self):
        original = g.section_bullets('Data Analyst - SolTech')[2]
        text = 'Developed automated Power BI dashboards using DAX for business intelligence reporting, reducing reporting time by 40%.'
        return original, {'role':'soltech','source_index':2,'text':text}

    def test_rewrite_preserves_metrics_and_tools(self):
        original, proposal = self.proposal()
        self.assertEqual(b.check_rewrite(original, proposal['text']), '')
        for bad in (proposal['text'].replace('40%', '60%'), proposal['text']+' Used Snowflake.', proposal['text'].replace('Developed', 'Led'), proposal['text'].replace('DAX', 'Python')):
            self.assertTrue(b.check_rewrite(original, bad))

    def test_profile_skill_cannot_be_reassigned_to_an_employer(self):
        original, proposal = self.proposal()
        self.assertTrue(b.check_rewrite(original, proposal['text']+' Used Docker.'))
        original = g.section_bullets('Data Engineer - G.S.R')[1]
        self.assertTrue(b.check_rewrite(original, original.replace('under 30 minutes', '30 minutes')))

    def test_missing_review_and_changed_approval_keep_originals(self):
        original, proposal = self.proposal()
        evidence={'soltech':['unused','unused',original]}
        accepted, notes = b.prepare_rewrites([proposal], evidence)
        self.assertFalse(notes)
        self.assertEqual(b.approve_rewrites(accepted, None), [])
        self.assertEqual(b.approve_rewrites(accepted, [{**proposal,'text':'Something different'}]), [])
        self.assertEqual(b.approve_rewrites(accepted, [proposal]), accepted)
        self.assertEqual(b.render_bullet('soltech',2,evidence,[]), original)

    def test_malformed_optional_edits_never_raise_or_replace_evidence(self):
        for raw in (None, {}, 'text', [None], [{'role':'gsr','source_index':-1,'text':'x'}], [{'role':[], 'source_index':0, 'text':'x'}]):
            proposals, warnings = b.prepare_rewrites(raw, {'soltech':[]})
            self.assertEqual(proposals, [])
            self.assertTrue(warnings)

    def test_optional_schema_keeps_legacy_drafts_valid(self):
        self.assertIn('experience_rewrites', m.SCHEMA['properties'])
        self.assertNotIn('experience_rewrites', m.SCHEMA['required'])
        draft,evidence=fixtures.GeminiTests().fixture()
        m.validate(draft,evidence,'Python','closing')

    def test_approved_rewrite_renders_without_extra_requests_or_letter_changes(self):
        original, proposal = self.proposal()
        def generate(approved):
            draft,plan=fixtures.GeminiTests().review_fixture()
            draft['experience_rewrites']=[proposal]
            with patch.object(m,'build_plan',return_value=plan), patch.object(m,'request_json',side_effect=[draft,{'issues':[],'coverage':[],'gaps':[],'approved_bullet_rewrites':approved},{'issues':[]}]) as api:
                cv,letter,metadata=m.generate(g,{'provider':'gemini','key':'test','model':'test'},'Example','Example','Data Analyst','Python and SQL reporting')
            self.assertEqual(api.call_count,3)
            return cv,letter,metadata
        cv,letter,metadata=generate([proposal])
        self.assertIn(g.escape_latex(proposal['text']),cv)
        self.assertEqual(len(metadata['bullet_rewrites']['applied']),1)
        baseline_cv,baseline_letter,metadata=generate([])
        self.assertEqual(letter,baseline_letter)
        self.assertIn(g.escape_latex(original),baseline_cv)
        self.assertEqual(metadata['bullet_rewrites']['applied'],[])

    def test_layout_recovery_restores_originals_once(self):
        original, proposal=self.proposal()
        applied=[{**proposal,'original':original}]
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'cv.tex'
            source.write_text(r'\item '+g.escape_latex(proposal['text']))
            metadata={'bullet_rewrites':{'applied':applied}}
            self.assertTrue(g.restore_experience_if_needed(source,metadata))
            self.assertIn(g.escape_latex(original),source.read_text())
            self.assertFalse(g.restore_experience_if_needed(source,metadata))
            self.assertTrue(metadata['bullet_rewrites']['layout_fallback'])

if __name__=='__main__':unittest.main()

class GenerationFallbackTests(unittest.TestCase):
    def run_fallback(self, *, initial_failure=False, audit_failure=False):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);cv=root/'cv';cover=root/'cover_letters'
            cv.mkdir();cover.mkdir()
            for path in (cv/'YashwanthGotike_Example_CV.pdf',cover/'YashwanthGotike_Example_CoverLetter.pdf'):
                path.write_bytes(b'%PDF fixture')
            original,proposal=BulletTests().proposal()
            metadata={'provider':'gemini','summary_alternatives':[], 'bullet_rewrites':{'applied':[{**proposal,'original':original}]}}
            def compile_(engine,*args):
                return engine!='lualatex' or not initial_failure
            with patch.multiple(g, ROOT=root,CV_DIR=cv,COVER_DIR=cover,DOCUMENTS_DIR=root/'documents/applications',TRACKER_FILE=root/'tracker.csv',SEEN_JOBS_FILE=root/'seen.json'), \
                 patch.object(m,'settings',return_value={'provider':'gemini'}), \
                 patch.object(m,'generate',return_value=(r'\item '+g.escape_latex(proposal['text']),'letter',metadata)) as draft, \
                 patch.object(g,'compile_latex',side_effect=compile_), \
                 patch.object(g,'compile_cv_with_summary_fit',side_effect=[False,True] if initial_failure else [True]) as fit, \
                 patch.object(g,'get_pdf_page_count',side_effect=[2,1] if initial_failure else [3,1,2]), \
                 patch.object(g,'verify_generated_pdf',return_value=True), \
                 patch('tools.application_pdf_audit.audit_application',side_effect=RuntimeError('optional unavailable') if audit_failure else None,return_value={'errors':[],'warnings':[]}), \
                 patch.object(g,'record_in_tracker') as record:
                result=g.generate_for_job({'company':'Example','title':'Data Analyst','description':'Build Power BI dashboards using SQL','is_custom':True})
            self.assertTrue(result['success'])
            self.assertEqual((result['cv_pages'],result['cl_pages']),(2,1))
            self.assertTrue(metadata['bullet_rewrites']['layout_fallback'])
            self.assertIn(g.escape_latex(original),(cv/'YashwanthGotike_Example_CV.tex').read_text())
            self.assertEqual(draft.call_count,1)
            record.assert_called_once()
            return result

    def test_page_overflow_restores_originals_and_still_generates(self):
        self.run_fallback()

    def test_rewrite_compile_failure_restores_originals_and_still_generates(self):
        self.run_fallback(initial_failure=True)

    def test_optional_audit_exception_is_a_warning_not_generation_failure(self):
        result=self.run_fallback(audit_failure=True)
        self.assertTrue(result['ats_readability']['warnings'])
