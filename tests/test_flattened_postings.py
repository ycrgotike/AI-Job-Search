import unittest
from tools.responsibility_plan import analyze_posting
from tools.job_description import needs_resolution

class FlattenedPostings(unittest.TestCase):
    def test_linkedin_flattened_duties_and_about_sections(self):
        desc = ('About This Role We work on content automation. About You You enjoy technology. '
                'As a Working Student, you will... Create and localize support content for Help Center and chatbot '
                'Use AI tools and prompt engineering for repetitive content tasks '
                'Track content performance metrics and improvement opportunities '
                'Document AI workflows and automation processes '
                'About Audible We are a global company. OUR OFFER Flexible hours. '
                'Basic Qualifications Business fluency in Swedish and English; university graduation no earlier than 2028.')
        plan = analyze_posting('Working Student Knowledge Management', desc)
        self.assertEqual([d['kind'] for d in plan['responsibilities']],['content','reporting','documentation'])
        self.assertFalse(plan['review_issues'])
        self.assertFalse(needs_resolution(desc))
        self.assertNotIn('Swedish', ' '.join(d['source'] for d in plan['responsibilities']))

    def test_tasks_inside_sentence_is_not_heading(self):
        desc = 'Your Tasks: Maintain reporting dashboards and automate repetitive tasks. Your Profile: Python and SQL.'
        plan = analyze_posting('Student',desc)
        self.assertEqual(plan['responsibilities'][0]['kind'],'reporting')

    def test_blank_description_still_needs_fetching(self):
        self.assertTrue(needs_resolution(''))

if __name__ == '__main__': unittest.main()
