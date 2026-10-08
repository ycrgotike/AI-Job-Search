import unittest
from unittest.mock import patch
from tools.responsibility_plan import analyze_posting, compose_evidence
from tools import generate_application as g

FINOPS = '''You can move this:
Analysis of cloud and IT costs and identification of savings potential.
Creation and maintenance of reports and dashboards.
Monitoring of budgets and cost developments.
Support in cost allocation to teams and projects.
Support in development of our cloud cost management application on ServiceNow.
Preparation of presentations and management information.
What you bring with you:
Basic knowledge of cloud infrastructures; Excel and PowerPoint.
Terraform and LLM knowledge is welcome.
'''

class ResponsibilityTailoring(unittest.TestCase):
    def letter(self, title, description):
        return g.build_tailored_cover_letter('Example', 'Example', title, description, True, False, False, False)

    def test_finops_uses_cost_and_reporting_evidence(self):
        letter = self.letter('Working Student FinOps', FINOPS)
        for term in ['infrastructure overhead', 'Power BI', 'budget deviations', 'learning your ServiceNow']:
            self.assertIn(term, letter)
        for term in ['customer retention', 'repeatable deployments', 'RAG', 'directly supports strategic']:
            self.assertNotIn(term, letter)

    def test_qualifications_are_not_tasks(self):
        plan = analyze_posting('AI Cloud', FINOPS)
        self.assertNotIn('platform', [d['kind'] for d in plan['all_responsibilities']])
        self.assertNotIn('agents', [d['kind'] for d in plan['all_responsibilities']])
        self.assertIn('Excel', plan['required_skills'])
        self.assertIn('PowerPoint', plan['required_skills'])

    def test_german_substrings_do_not_trigger_ai_or_etl(self):
        plan = analyze_posting('Student', 'Aufgaben\nErstellung von Berichten als Beitrag für das Team.\nIhr Profil\nCloud Infrastruktur.')
        self.assertEqual([d['kind'] for d in plan['responsibilities']], ['reporting'])

    def test_research_is_not_llm_engineering(self):
        letter = self.letter('Master Thesis Artificial Intelligence', 'Tasks\nAnalyze survey data and organizational AI adoption patterns.\nPrepare reports of findings.\nQualifications\nInterest in LLMs.')
        self.assertIn('hypothesis', letter)
        self.assertNotIn('MVP UPSC', letter)
        self.assertNotIn('deployments', letter)

    def test_support_is_not_cloud_pipeline_boilerplate(self):
        letter = self.letter('IT Support', 'Tasks\nProvide user support for business applications.\nMaintain documentation of issues.')
        self.assertIn('ITC Infotech', letter)
        self.assertNotIn('Azure Databricks', letter)
        self.assertNotIn('customer retention', letter)

    def test_platform_ai_duties_keep_both_examples(self):
        letter = self.letter('Platform Operations', 'Tasks\nDevelop CI/CD for platform services.\nOperate LLMs and retrieval services.')
        self.assertIn('GitHub Actions', letter)
        self.assertIn('MVP UPSC', letter)
        self.assertNotIn('customer retention', letter)

    def test_unknown_work_gets_flagged_transferable_draft(self):
        desc = 'Tasks\nManage insurance claims and negotiate settlements.\nQualifications\nPython SQL.'
        plan = analyze_posting('Analyst', desc)
        self.assertFalse(plan['review_issues'])
        self.assertTrue(plan['review_warnings'])
        letter = self.letter('Analyst', desc)
        self.assertIn('SolTech', letter)
        self.assertNotIn('I managed insurance claims', letter)

    def test_profile_removal_changes_evidence(self):
        bullets = g.section_bullets
        def filtered(heading):
            return [x for x in bullets(heading) if 'Power BI' not in x]
        with patch.object(g, 'section_bullets', side_effect=filtered):
            letter = self.letter('Reporting Analyst', 'Tasks\nMaintain reports and dashboards.')
        self.assertNotIn('Power BI', letter)

    def test_cv_summary_is_responsibility_driven(self):
        cv = g.build_tailored_cv('Example','Example','AI Student',FINOPS,True,False,False,True)
        self.assertIn('cloud cost analysis and cost transparency',cv)
        self.assertNotIn('advanced DAX modeling', cv)

    def test_other_disciplines_select_matching_evidence(self):
        cases = [
            ('Develop relational models and PL/SQL database workflows.', 'SQL Data Warehouse', 'MVP UPSC'),
            ('Build ETL data pipelines integrating data sources.', 'Azure Data Factory', 'customer retention'),
            ('Train machine learning models and evaluate predictive performance.', 'Kidney Disease Classification', 'MVP UPSC'),
            ('Check data quality and validation rules.', 'SQL Data Warehouse', 'customer retention'),
            ('Conduct contact research and maintain CRM records.', 'G.S.R', 'Kidney Disease Classification'),
        ]
        for task, expected, unrelated in cases:
            with self.subTest(task=task):
                letter = self.letter('Working Student', 'Tasks\n' + task)
                self.assertIn(expected, letter)
                self.assertNotIn(unrelated, letter)

    def test_no_repeated_facts_for_overlapping_duties(self):
        plan = analyze_posting('Analyst', 'Tasks\nMaintain reporting dashboards.\nPrepare documentation and presentations.')
        blocks = compose_evidence(plan, g.section_bullets)
        self.assertEqual(' '.join(x[1] for x in blocks).count('reducing reporting time by 40%'),1)

    def test_model_validation_maps_to_models_not_data_quality(self):
        plan = analyze_posting('Werkstudent Data Science', 'Aufgaben\nEntwicklung und Validierung datenbasierter Modelle.')
        self.assertEqual(plan['responsibilities'][0]['kind'], 'models')

    def test_cv_coursework_includes_seminar_only_when_governance_present(self):
        cv_no_dg = g.build_tailored_cv('Example', 'Example', 'Data Engineer', 'Tasks\nBuild Python data pipelines and Docker containers.', True, True, False, False)
        self.assertNotIn('Seminar: Data Governance Quality Assurance', cv_no_dg)

        cv_with_dg = g.build_tailored_cv('Example', 'Example', 'Data Engineer', 'Tasks\nDefine data governance architectures and data quality rules.', True, True, False, False)
        self.assertIn('Seminar: Data Governance Quality Assurance', cv_with_dg)


if __name__ == '__main__':
    unittest.main()
