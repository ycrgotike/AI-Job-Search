"""Regression checks for role-accurate headlines in both generation paths."""
import unittest

from tools import generate_application as generator
from tools import gemini_tailoring


class HeaderTitleTests(unittest.TestCase):
    def test_explicit_title_wins_over_conflicting_description(self):
        cases = (
            ('Data Scientist', 'Build ML models, ML models and data pipelines.', 'Data Scientist'),
            ('Senior Data Scientist (m/f/d) — Estimations', 'Build ETL pipelines and dashboards.', 'Data Scientist'),
            ('Lead Analytics Engineer', 'Develop ML models and AI workflows.', 'Analytics Engineer'),
            ('Junior Business Analyst (m/w/d)', 'Python data pipelines and ML models.', 'Business Analyst'),
            ('Business Intelligence Analyst', 'Develop data pipelines and ML models.', 'Business Intelligence Analyst'),
            ('Data Analyst — AI Engineer team', 'Train ML models.', 'Data Analyst'),
            ('Principal Machine Learning Engineer', 'Build BI dashboards and reports.', 'Machine Learning Engineer'),
            ('Staff Data Engineer', 'Build ML models and AI workflows.', 'Data Engineer'),
            ('Data Engineer — AI & Data', 'ML models, ML models, LLM models.', 'Data Engineer'),
        )
        for title, description, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(generator.determine_header_title(title, description), expected)
                # Even a conflicting model-proposed header cannot change the role.
                self.assertEqual(gemini_tailoring.clean_header_title('AI Engineer', title, description), expected)

    def test_other_professions_are_preserved_without_employment_labels(self):
        cases = (
            ('Senior Research Scientist (m/f/d) — Berlin', 'Research Scientist'),
            ('Working Student - Software Developer (m/w/d)', 'Software Developer'),
            ('Werkstudent/in Software Developer (m/w/d)', 'Software Developer'),
            ('Lead Data Architect — Cloud Platform', 'Data Architect'),
            ('Senior BI Developer (m/w/d) | Remote', 'BI Developer'),
            ('Senior Full-time Research Scientist', 'Research Scientist'),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(generator.determine_header_title(title, 'ML models and dashboards'), expected)

    def test_ambiguous_and_domain_only_titles_still_resolve(self):
        self.assertEqual(generator.determine_header_title('Werkstudent AI & Data',
                         'Build ETL data pipelines in Spark and Databricks.'), 'Data Engineer')
        self.assertEqual(generator.determine_header_title('Machine Learning Intern'), 'Machine Learning Engineer')
        self.assertEqual(generator.determine_header_title('Werkstudent:in Data Science'), 'Data Scientist')

    def test_branded_consultant_titles_map_to_established_roles(self):
        cases = (
            ('Flexikum Technical Consultant - ServiceNow Agentic AI Solutions',
             'Deine Aufgaben: Implementierung von agentenbasierten KI-Workflows mit LLMs und MCP.', 'AI Engineer'),
            ('Flexikum Technical Consultant',
             'Your tasks: Build agentic workflows using LLMs, RAG and MCP. Integrate REST APIs.', 'AI Engineer'),
            ('Acme Technical Consultant',
             'Your tasks: Build ETL pipelines and maintain a data warehouse using Spark.', 'Data Engineer'),
            ('Technical Consultant',
             'Your tasks: Build Power BI dashboards and prepare KPI reporting.', 'Data Analyst'),
            ('BrandX Technical Specialist',
             'Your tasks: Train machine learning models for classification and regression using PyTorch.', 'Machine Learning Engineer'),
            ('Flexikum Technical Consultant',
             'Your tasks: Develop backend applications and REST APIs.', 'Software Engineer'),
            ('BrandX Research Scientist - Machine Learning', '', 'Research Scientist'),
        )
        for title, description, expected in cases:
            with self.subTest(title=title, expected=expected):
                self.assertEqual(generator.determine_header_title(title, description), expected)
                self.assertEqual(gemini_tailoring.clean_header_title(title, title, description), expected)

    def test_employer_ai_boilerplate_does_not_override_generic_roles_actual_tasks(self):
        self.assertEqual(generator.determine_header_title('Technical Consultant',
            'Our company develops LLMs, agents and MCP products. '
            'Your tasks: Build Power BI dashboards and prepare reporting. '
            'Requirements: Python and SQL.'), 'Data Analyst')

    def test_arbitrary_engineering_prefix_is_not_copied_into_the_header(self):
        self.assertEqual(generator.determine_header_title('Flexikum HyperAutomation Engineer',
            'Your tasks: Train machine learning models with TensorFlow.'), 'Machine Learning Engineer')

    def test_rules_cv_uses_data_scientist_in_rendered_header_source(self):
        cv = generator.build_tailored_cv('Example', 'Example', 'Data Scientist',
            'Train and validate predictive machine learning models using Python and SQL.',
            False, False, False, True)
        self.assertIn(r'\address{Koblenz, Germany \,|\, Data Scientist}{}{}', cv)


if __name__ == '__main__':
    unittest.main()
