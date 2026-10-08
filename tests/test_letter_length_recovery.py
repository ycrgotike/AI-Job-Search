import json
from pathlib import Path
import unittest
from unittest.mock import patch
from tools import generate_application as g
from tools.responsibility_plan import analyze_posting

class LetterLengthRecovery(unittest.TestCase):
    def test_exhausted_299_word_draft_recovers_without_changing_layout_or_facts(self):
        data=json.loads((Path(__file__).parent/'fixtures/short_letter_299.json').read_text())
        data.pop('count')
        original=list(map(tuple,data['blocks']))
        # Simulate the worst case: there is no unused candidate evidence available.
        with patch.object(g,'section_bullets',return_value=[]):
            blocks,interest=g.fit_letter_content(**data)
        count=len((data['opening']+' '+g.letter_fixed_text(data['company'],data['title'],data['description'])+' '+' '.join(h+'. '+p for h,p in blocks)+' '+interest).split())
        self.assertEqual(list(map(tuple,blocks)),original)
        self.assertTrue(300<=count<=350,count)
        self.assertIn('I would check that retrieved context supports each answer',interest)

    def test_length_edges_preserve_anchored_evidence(self):
        data=json.loads((Path(__file__).parent/'fixtures/short_letter_299.json').read_text());data.pop('count')
        for extra in ['', 'I would verify the source.', 'I would verify the source. '*11]:
            with self.subTest(extra_words=len(extra.split())):
                item=dict(data,interest=data['interest']+' '+extra)
                blocks,interest=g.fit_letter_content(**item)
                count=len((item['opening']+' '+g.letter_fixed_text(item['company'],item['title'],item['description'])+' '+' '.join(h+'. '+p for h,p in blocks)+' '+interest).split())
                self.assertTrue(300<=count<=350,count)
                self.assertIn('MVP UPSC',' '.join(p for _,p in blocks))

    def test_flattened_german_sections_do_not_include_qualifications(self):
        desc='Einleitung Wir suchen Dich. Aufgaben Du entwickelst LLM und RAG Systeme Du analysierst die Retrieval-Qualität Du entwickelst Pipelines und Modelle in Python Du unterstützt die Pipeline-Architektur. Qualifikation Du hast Erfahrung mit Terraform und Kubernetes. Benefits Flexible Zeiten.'
        plan=analyze_posting('Praktikant LLM RAG Engineer',desc)
        kinds=[d['kind'] for d in plan['all_responsibilities']]
        self.assertIn('ai_evaluation',kinds)
        self.assertIn('models',kinds)
        self.assertNotIn('platform',kinds)
        self.assertNotIn('Qualifikation',' '.join(plan['duty_fragments']))
        code=g.build_tailored_cover_letter('Example','Example','Praktikant LLM RAG Engineer',desc,True,False,False,True)
        self.assertTrue(300<=g.cover_letter_body_words(code)<=350)

if __name__=='__main__':unittest.main()
