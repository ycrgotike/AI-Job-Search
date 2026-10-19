import unittest
from unittest.mock import patch
from tools.technology_evidence import review_technologies, learning_sentence, ensure_office_skill_coverage
from tools.responsibility_plan import analyze_posting
from tools import generate_application as g

class TechnologyEvidence(unittest.TestCase):
    def test_office_entries_use_tool_names_without_proficiency_labels(self):
        groups = [{'label': 'Office', 'terms': ['Microsoft Excel (Proficient)', 'Microsoft PowerPoint (Proficient)']}]
        result = ensure_office_skill_coverage(groups, 'Use Excel and PowerPoint.', g.profile_text())
        self.assertEqual(result[0]['terms'], ['Microsoft Excel', 'Microsoft PowerPoint'])

    def test_office_confirmation_does_not_imply_vba(self):
        review = review_technologies('Use Excel, PowerPoint and VBA.', g.profile_text())
        statuses = {r['technology']: r['status'] for r in review['technologies']}
        self.assertEqual(statuses['Excel'], 'confirmed')
        self.assertEqual(statuses['PowerPoint'], 'confirmed')
        self.assertNotEqual(statuses['VBA'], 'confirmed')

    def test_model_office_omission_is_repaired_without_growing_group_count(self):
        groups = [
            {'label': 'Programming', 'terms': ['Python', 'SQL']},
            {'label': 'Business Intelligence & Visualization', 'terms': ['Power BI', 'DAX', 'Tableau', 'Plotly', 'Seaborn', 'Matplotlib']},
            {'label': 'Data', 'terms': ['PostgreSQL', 'MySQL']},
            {'label': 'Statistics', 'terms': ['Statistical Analysis', 'A/B Testing']},
        ]
        repaired = ensure_office_skill_coverage(groups,
            'You are proficient in Excel and PowerPoint. Power BI is an advantage.', g.profile_text())
        self.assertEqual(len(repaired), 4)
        self.assertIn('MS Office', repaired[1]['label'])
        self.assertTrue({'Excel', 'PowerPoint', 'Power BI'}.issubset(repaired[1]['terms']))
        self.assertEqual(len(repaired[1]['terms']), 6)
        self.assertNotIn('Excel', groups[1]['terms'])

    def test_posting_alone_cannot_add_office_proficiency(self):
        groups = [{'label': 'Programming', 'terms': ['Python', 'SQL']}]
        self.assertEqual(ensure_office_skill_coverage(groups,
            'Proficient in Excel and PowerPoint.', '- Tools: Python, SQL'), groups)

    def test_office_aliases_do_not_create_duplicate_skills(self):
        groups = [{'label': 'Office', 'terms': ['Microsoft Excel', 'Microsoft PowerPoint']}]
        self.assertEqual(ensure_office_skill_coverage(groups,
            'Use Excel and PowerPoint.', g.profile_text()), groups)

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
