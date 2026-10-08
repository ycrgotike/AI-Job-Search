import importlib.util
from datetime import date
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('targeting_generator', ROOT / 'tools/generate_application.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

PLATFORM = 'Job-ID 84590. Automate hybrid cloud with Terraform, Ansible, Puppet, PowerShell. Develop CI/CD for platform services. Operate LLMs; Kubernetes, Windows, Linux, vulnerability management, hardening and NIS2.'


class RoleTargeting(unittest.TestCase):
    def build(self, family='platform', student=True):
        title, desc = ('Praktikum Data Center & Platform Operations', PLATFORM) if family == 'platform' else ('Working Student Data Analyst', 'SQL, Power BI dashboards and reporting')
        args = ('Example GmbH', 'Example', title, desc, student, False, False, False)
        return g.build_tailored_cv(*args), g.build_tailored_cover_letter(*args)

    def test_student_status_does_not_override_platform_responsibilities(self):
        cv, letter = self.build()
        self.assertLess(cv.index('Cloud \\& Automation'), cv.index('Analytics \\& Reporting'))
        self.assertLess(cv.index('MVP UPSC'), cv.index('SQL Data Warehouse \\& Analytics'))
        self.assertIn('GitHub Actions', letter)
        self.assertIn('MVP UPSC', letter)  # Posting asks for LLM operations, not image classification.
        self.assertNotIn('student_hands_on', letter)
        self.assertNotIn('20 hours', letter)
        self.assertNotIn('notice period', letter)
        self.assertIn('Job ID 84590', letter)

    def test_analytics_student_gets_different_evidence(self):
        cv, letter = self.build('analytics')
        self.assertLess(cv.index('Analytics \\& Reporting'), cv.index('Cloud \\& Automation'))
        self.assertIn('Power BI', letter)
        self.assertIn('SolTech', letter)
        self.assertNotIn('Kidney Disease Classification', letter)
        self.assertIn('20 hours', letter)

    def test_posting_tools_do_not_become_skills_or_achievements(self):
        cv, letter = self.build()
        for term in ['Ansible', 'Puppet', 'PowerShell', 'NIS2']:
            self.assertNotIn(term, cv)
        self.assertIn('deepen my experience', letter)
        self.assertNotIn('practical proficiency', letter)

    def test_profile_edits_affect_new_documents(self):
        profile = g.profile_text().replace('Kubernetes, Terraform, ', '')
        with patch.object(g, 'profile_text', return_value=profile):
            cv, letter = self.build()
        self.assertNotIn('Kubernetes', cv)
        self.assertNotIn('Terraform', cv)
        self.assertIn('interested in learning Kubernetes and Terraform', letter)
        self.assertNotIn('practical proficiency', letter)

    def test_future_availability_clamps_month_end(self):
        self.assertEqual(g.start_date(date(2026,1,31)), date(2026,2,28))
        self.assertEqual(g.start_date(date(2026,12,31)), date(2027,1,31))

    def test_no_title_only_generation(self):
        with patch.object(g, 'fetch_description_for_job', return_value=''), patch.object(g, 'build_tailored_cv') as build:
            result = g.generate_for_job({'company':'Example','title':'Internship'})
        self.assertFalse(result['success'])
        build.assert_not_called()

    def test_shared_font_and_no_old_student_boilerplate(self):
        cv, letter = self.build()
        self.assertIn('lmsans10-regular.otf', letter)
        self.assertNotIn('Raleway', letter)
        self.assertNotIn('immediate value', letter)
        self.assertNotIn('with over five years', letter)
        self.assertIn('expected graduation September 2027', cv)

    def test_escape_literal_special_characters_once(self):
        self.assertEqual(g.escape_latex('100% & {x}'), r'100\% \& \{x\}')
        self.assertEqual(g.escape_latex('C:\\tools'), r'C:\textbackslash{}tools')


if __name__ == '__main__':
    unittest.main()
