import json
from pathlib import Path
import unittest
from tools import generate_application as g
from tools.responsibility_plan import analyze_posting

class SpeiraRecovery(unittest.TestCase):
    def test_295_words_after_checkpoint_still_recovers(self):
        data=json.loads((Path(__file__).parent/'fixtures/short_letter_295.json').read_text());data.pop('count')
        original=' '.join(p for _,p in data['blocks'])
        blocks,interest=g.fit_letter_content(**data)
        final=' '.join(h+'. '+p for h,p in blocks)
        count=len((data['opening']+' '+g.letter_fixed_text(data['company'],data['title'],data['description'])+' '+final+' '+interest).split())
        self.assertTrue(300<=count<=350,count)
        self.assertGreater(len(final),len(original))
        self.assertIn('At ITC Infotech,',final)
        self.assertEqual(final.count('At ITC Infotech, I achieved 40% faster response time'),1)

    def test_flattened_ai_business_tasks_exclude_profile_and_benefits(self):
        desc='Einleitung. Was Du bei uns bewegst Du unterstützt die Umsetzung von KI Use Cases. Die Weiterentwicklung bestehender KI-Anwendungen gehört dazu. Was Dich auszeichnet Du studierst Informatik und kennst Python. Was wir bieten Flexible Zeiten und Cloud-Kurse.'
        plan=analyze_posting('Werkstudent AI & Analytics',desc)
        self.assertEqual(plan['responsibilities'][0]['kind'],'ai_delivery')
        self.assertNotIn('Du studierst',' '.join(plan['duty_fragments']))
        letter=g.build_tailored_cover_letter('Speira','Speira','Werkstudent AI & Analytics',desc,True,False,True,True)
        self.assertTrue(300<=g.cover_letter_body_words(letter)<=350)
        self.assertIn('MVP UPSC',letter)
        self.assertIn('ITC Infotech',letter)
        self.assertNotIn('I implemented AI use cases at Speira',letter)

if __name__=='__main__':unittest.main()
