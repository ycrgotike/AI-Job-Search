import unittest
from unittest.mock import patch
from tools.technology_evidence import review_technologies, learning_sentence
from tools.responsibility_plan import analyze_posting
from tools import generate_application as g

class TechnologyEvidence(unittest.TestCase):
    def test_negated_tools_do_not_become_skills(self):
        profile='- **Python**: automation\n- No experience with Jenkins\n- Do not infer Terraform experience.'
        review=review_technologies('Use Python, Jenkins and Terraform.',profile)
        states={r['technology']:r['status'] for r in review['technologies']}
        self.assertEqual(states['Python'],'confirmed')
        self.assertNotEqual(states['Jenkins'],'confirmed')
        self.assertNotEqual(states['Terraform'],'confirmed')

    def test_transferable_is_not_confirmed(self):
        review=review_technologies('TypeScript, Jenkins and PKI','- **Tools**: Python, GitHub Actions, CI/CD')
        states={r['technology']:r['status'] for r in review['technologies']}
        self.assertEqual(states['TypeScript'],'transferable')
        self.assertEqual(states['Jenkins'],'transferable')
        self.assertEqual(states['PKI'],'needs_confirmation')
        self.assertIn('while learning',learning_sentence(review))

    def test_unfamiliar_tool_requires_review(self):
        review=review_technologies('Experience with NovelFlow and Python.','- **Python**: analysis')
        self.assertIn('NovelFlow',review['unrecognised_terms_to_review'])

    def test_newly_confirmed_tool_can_enter_skills(self):
        with patch.object(g,'profile_text',return_value=g.profile_text()+'\n- **Tools**: Polars\n'):
            skills=' '.join(g.skill_groups('data','Experience with Polars.'))
        self.assertIn('Polars',skills)

    def test_posting_only_tools_are_not_cv_skills(self):
        skills=' '.join(g.skill_groups('data','TypeScript Jenkins PKI Terraform Python SQL'))
        for name in ['TypeScript','Jenkins','PKI']:self.assertNotIn(name,skills)
        for name in ['Python','SQL']:self.assertIn(name,skills)

    def test_qa_is_not_bi_reporting(self):
        desc='Key Responsibilities\nDesign and document traceable test cases.\nPerform manual test execution.\nMaintain test reports.\nSupport automated tests with TypeScript.\nAssist test environment setup and validation.\nRequired Qualifications\nJenkins and PKI interest.'
        plan=analyze_posting('Student QA Engineer',desc)
        self.assertEqual([d['kind'] for d in plan['responsibilities']],['qa','test_automation'])
        letter=g.build_tailored_cover_letter('Example','Example','Working Student QA',desc,True,False,False,False)
        self.assertIn('manual test results',letter)
        self.assertNotIn('Power BI dashboards',letter)
        self.assertIn('learning TypeScript',letter)

    def test_specialist_tasks_outrank_incidental_docs_across_roles(self):
        for task,kind in [('Analyze survey data and AI adoption patterns.','research'),('Develop relational models in PL/SQL.','database'),('Create and localize support content.','content')]:
            plan=analyze_posting('Student','Tasks\nMaintain documentation.\n'+task)
            self.assertEqual(plan['responsibilities'][0]['kind'],kind)

    def test_role_hours_do_not_exceed_posting(self):
        text=g.availability_text('Working Student',description='Working hours: Up to 19 hours per week.')
        self.assertIn('19 hours',text)
        self.assertNotIn('20 hours',text)
        self.assertNotIn('40',text)

if __name__=='__main__':unittest.main()
