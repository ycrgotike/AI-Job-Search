import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tools import generate_application as g

class SummaryFitting(unittest.TestCase):
    def test_long_summary_retries_prose_only(self):
        with TemporaryDirectory() as temp:
            p=Path(temp)/'cv.tex'
            initial=r'FONT MARGINS {\raggedright\small Student with data engineering and analytics experience. Python, SQL.\par\global\summarylines=\prevgraf} BODY'
            p.write_text(initial)
            calls=[]
            def compile(*args):
                calls.append(p.read_text())
                p.with_suffix('.log').write_text('CV-SUMMARY-LINES: 5\nCV summary must have exactly 4 rendered lines')
                return len(calls)>1
            with patch.object(g,'compile_latex',side_effect=compile):
                self.assertTrue(g.compile_cv_with_summary_fit('lualatex',p,p.parent))
            self.assertEqual(len(calls),2)
            self.assertIn('with data and analytics experience',p.read_text())
            self.assertTrue(p.read_text().startswith('FONT MARGINS'))
            self.assertTrue(p.read_text().endswith(' BODY'))
            self.assertIn('Python, SQL',p.read_text())

    def test_other_compile_failures_are_not_hidden(self):
        with TemporaryDirectory() as temp:
            p=Path(temp)/'cv.tex';p.write_text('original')
            p.with_suffix('.log').write_text('Undefined control sequence')
            with patch.object(g,'compile_latex',return_value=False) as run:
                self.assertFalse(g.compile_cv_with_summary_fit('lualatex',p,p.parent))
            self.assertEqual(run.call_count,1)
            self.assertEqual(p.read_text(),'original')

    def test_successful_compile_is_not_rewritten(self):
        with TemporaryDirectory() as temp:
            p=Path(temp)/'cv.tex';p.write_text('original')
            with patch.object(g,'compile_latex',return_value=True) as run:
                self.assertTrue(g.compile_cv_with_summary_fit('lualatex',p,p.parent))
            self.assertEqual(run.call_count,1)
            self.assertEqual(p.read_text(),'original')
