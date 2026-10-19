import unittest
from tools import generate_application as g
from tools import gemini_tailoring as m


class EvidencePriorityTests(unittest.TestCase):
    def test_model_headline_cannot_override_job_discipline(self):
        self.assertEqual(m.clean_header_title('Data Engineer', 'Werkstudent:in AI & Automations',
                         'Build AI workflows, automations and API integrations.'), 'AI Engineer')
        self.assertEqual(m.clean_header_title('AI Engineer', 'Data Engineer',
                         'Build ETL pipelines and a data warehouse.'), 'Data Engineer')
        self.assertEqual(m.clean_header_title('Data Engineer', 'Data Analyst',
                         'Build dashboards and reporting.'), 'Data Analyst')

    def test_ai_cv_retains_experience_before_projects(self):
        description = 'Train and evaluate machine learning models using Python and PyTorch. Document model results.'
        cv = g.build_tailored_cv('Example', 'Example', 'Machine Learning Engineer',
                                 description, False, False, False, True)
        self.assertLess(cv.index(r'\section{Professional Experience}'),
                        cv.index(r'\section{Key Technical Projects}'))
        self.assertLess(cv.index('SolTech'), cv.index('G.S.R'))
        self.assertLess(cv.index('G.S.R'), cv.index('ITC Infotech'))

    def test_ai_letter_includes_attributed_verified_employer_outcome(self):
        description = ('Train image classification models using TensorFlow, PyTorch and transfer learning. '
                       'Validate models and document results using Python.')
        letter = g.build_tailored_cover_letter('Example', 'Example', 'Machine Learning Engineer',
                                               description, False, False, False, True)
        self.assertRegex(letter, r'(?:SolTech|G\.S\.R|ITC Infotech)')
        self.assertRegex(letter, r'(?:18|30|40|million|minutes|hours)')
        self.assertTrue(300 <= g.cover_letter_body_words(letter) <= 350)


if __name__ == '__main__':
    unittest.main()
