"""Role-specific grouping keeps skills readable without inventing evidence."""
import unittest

from tools import generate_application as generator
from tools import gemini_tailoring


class SkillGroupTests(unittest.TestCase):
    def test_scientist_has_four_distinct_relevant_groups(self):
        groups = generator.skill_groups('analytics',
            'Build predictive models with Python, SQL, scikit-learn and MLflow.', 'Data Scientist')
        self.assertEqual(len(groups), 4)
        for index, label in enumerate(('Machine Learning', 'Programming', 'MLOps', 'Cloud')):
            self.assertIn(label, groups[index])
        self.assertNotIn('MLflow', groups[0])
        self.assertIn('MLflow', groups[2])
        self.assertIn('Git', groups[2])
        self.assertIn('PostgreSQL', groups[3])

    def test_other_disciplines_use_different_categories(self):
        data = generator.skill_groups('data', 'Build data pipelines with Python and SQL.', 'Data Engineer')
        analytics = generator.skill_groups('analytics', 'Power BI dashboards and SQL reporting.', 'Data Analyst')
        self.assertEqual(len(data), 4)
        self.assertEqual(len(analytics), 4)
        self.assertIn('Data Integration', data[0])
        self.assertIn('Business Intelligence', analytics[0])
        self.assertNotEqual(data, analytics)

    def test_distinct_governance_requirement_gets_a_fifth_group(self):
        groups = generator.skill_groups('data',
            'Build data pipelines with data governance, data profiling and metadata management.', 'Data Engineer')
        self.assertEqual(len(groups), 5)
        self.assertIn('Data Governance', groups[-1])

    def test_ai_categories_follow_predictive_or_generative_responsibilities(self):
        predictive = generator.skill_groups('ai',
            'Train classification and regression machine learning models.', 'AI Engineer')
        generative = generator.skill_groups('ai',
            'Build agentic RAG and LLM applications.', 'AI Engineer')
        self.assertIn('Machine Learning', predictive[0])
        self.assertIn('GenAI', generative[0])

    def test_legacy_crowded_draft_is_split_without_adding_or_losing_skills(self):
        groups = [
            {'label': 'Machine Learning & AI', 'terms': ['TensorFlow', 'PyTorch', 'MLflow', 'DVC', 'Statistical Analysis', 'A/B Testing']},
            {'label': 'Programming & Data Engineering', 'terms': ['Python', 'SQL', 'Pandas', 'Scikit-learn', 'Airflow', 'ETL/ELT']},
            {'label': 'Cloud & DevOps', 'terms': ['AWS', 'Docker', 'Git', 'CI/CD', 'Flask', 'MS SQL Server']},
        ]
        result = gemini_tailoring.rebalance_skill_groups(groups)
        self.assertEqual(len(result), 4)
        self.assertEqual(sorted(t for g in result for t in g['terms']),
                         sorted(t for g in groups for t in g['terms']))
        self.assertTrue(all(len(g['terms']) >= 2 for g in result))
        self.assertIn('MLflow', result[-1]['terms'])

    def test_sparse_evidence_is_not_padded_with_unrelated_skills(self):
        groups = [{'label': label, 'terms': [term]} for label, term in
                  [('Programming', 'Python'), ('Databases', 'SQL'), ('Delivery', 'Git')]]
        self.assertEqual(gemini_tailoring.rebalance_skill_groups(groups), groups)

    def test_requested_office_skills_survive_rule_based_analytics_selection(self):
        groups = generator.skill_groups('analytics',
            'Proficient in MS Office, especially Excel and PowerPoint. Python and Power BI are an advantage.',
            'Working Student Market & Data Analytics')
        self.assertEqual(len(groups), 4)
        self.assertIn('MS Office', groups[0])
        for tool in ('Excel', 'PowerPoint', 'Power BI'):
            self.assertIn(tool, groups[0])


if __name__ == '__main__':
    unittest.main()
