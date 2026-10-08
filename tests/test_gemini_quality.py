import copy
import unittest
from tools import gemini_tailoring as m
from tools import generate_application as g

class TailoringQuality(unittest.TestCase):
    def plan(self):
        return {'duties':[{'source':'Develop predictive models for journeys', 'priority':'primary', 'evidence':'Python and statistical analysis'}],
                'gaps':[], 'timing_source':'Start from mid November 2026', 'project_order':['trading','mlops','upsc','twitter','sql']}

    def test_source_and_evidence_are_verified(self):
        description='Develop predictive models for journeys. Start from mid November 2026. Sehr gute Deutschkenntnisse.'
        profile='Python and statistical analysis. German (B2)'
        plan=m.validate_plan(self.plan(),description,profile,self.plan()['project_order'])
        self.assertIn('B2',plan['gaps'][0]['explanation'])
        for field,value in [('source','Made up task not in posting'),('evidence','Invented experience')]:
            bad=self.plan();bad['duties'][0][field]=value
            with self.assertRaises(ValueError):m.validate_plan(bad,description,profile,bad['project_order'])

    def test_markdown_and_html_duty_sources_pass_validation(self):
        description = '- Du entwickelst unser **Business-Operations-Dashboard** mit **Claude Code** weiter und bindest Daten an. Start from mid November 2026.'
        profile = '- **Languages**: Python, SQL and statistical analysis. German (B2)'
        plan = {
            'duties': [{'source': 'Du entwickelst unser Business-Operations-Dashboard mit Claude Code weiter und bindest Daten an', 'priority': 'primary', 'evidence': 'Python, SQL and statistical analysis'}],
            'gaps': [],
            'timing_source': 'Start from mid November 2026',
            'project_order': ['trading', 'mlops', 'upsc', 'twitter', 'sql']
        }
        res = m.validate_plan(plan, description, profile, plan['project_order'])
        self.assertEqual(len(res['duties']), 1)

    def test_missing_primary_coverage_and_fabricated_quotes_rejected(self):
        draft={'opening':'I build predictive baselines.', 'paragraphs':['I would evaluate errors across different journeys.']}
        good={'issues':[], 'gaps':[], 'coverage':[{'source':self.plan()['duties'][0]['source'],'draft_quote':draft['paragraphs'][0]}]}
        m.validate_audit(good,draft,self.plan())
        for bad in [{'issues':[],'gaps':[],'coverage':[]}, {'issues':[], 'gaps':[], 'coverage':[{'source':self.plan()['duties'][0]['source'],'draft_quote':'This sentence was never written.'}]}]:
            with self.assertRaises(ValueError):m.validate_audit(bad,draft,self.plan())

    def test_substantive_issues_never_filtered_by_word_or_line(self):
        for issue in ['Pipeline expertise is unsupported.', 'The wording implies unconfirmed German fluency.', 'The closing ignores the employer start date.']:
            with self.assertRaisesRegex(ValueError,'Revise'):
                m.validate_audit({'issues':[issue],'coverage':[],'gaps':[]},{},self.plan())

    def test_gaps_survive_optimistic_review(self):
        plan=self.plan();plan['duties']=[];plan['gaps']=[{'source':'Very good German','explanation':'B2 requires confirmation.'}]
        gaps=m.validate_audit({'issues':[],'coverage':[],'gaps':['None']},{'opening':'','paragraphs':[]},plan)
        self.assertEqual(gaps,['B2 requires confirmation.'])

    def test_interests_filler_generic_opening_and_project_order(self):
        plan=self.plan()
        draft={'projects':plan['project_order'][:4], 'skills':[{'label':'Research Interests','terms':['neural rendering']}], 'opening':'I apply with Python experience.', 'summaries':['Relevant background.'], 'paragraphs':['Specific prospective approach.']}
        profile='Python\n## Research Interests\nneural rendering'
        with self.assertRaisesRegex(ValueError,'not requested'):m.validate_targeting(draft,plan,'Predictive time-series modelling',profile)
        draft['skills'][0]['label']='Technical Skills'
        with self.assertRaisesRegex(ValueError,'proven skills'):m.validate_targeting(draft,plan,'neural rendering',profile)
        draft['skills']=[{'label':'Programming','terms':['Python']}]
        m.validate_targeting(draft,plan,'Predictive models',profile)
        draft['opening']='I am writing to express my interest.'
        with self.assertRaisesRegex(ValueError,'generic'):m.validate_targeting(draft,plan,'Predictive models',profile)
        draft['opening']='I apply with Python experience.'
        draft['summaries']=['Experience includes Python and SQL analysis of operational data.']
        with self.assertRaisesRegex(ValueError,'filler'):m.validate_targeting(draft,plan,'Predictive models',profile)
        draft['summaries']=['Relevant background.'];draft['projects'].reverse()
        with self.assertRaisesRegex(ValueError,'priority order'):m.validate_targeting(draft,plan,'Predictive models',profile)

    def test_hyphenated_posting_terms_are_not_false_gaps(self):
        plan=self.plan()
        draft={'projects':plan['project_order'][:4], 'skills':[{'label':'Research Interests','terms':['Machine Learning']}], 'opening':'I apply with relevant experience.', 'summaries':['Relevant background.'], 'paragraphs':['Specific approach.']}
        m.validate_targeting(draft,plan,'Machine-Learning-Algorithmen','Machine Learning')

    def test_machine_learning_group_is_not_an_interest_label(self):
        plan=self.plan()
        draft={'projects':plan['project_order'][:4], 'skills':[{'label':'Machine Learning & AI','terms':['PyTorch']}], 'opening':'I apply with relevant experience.', 'summaries':['Relevant background.'], 'paragraphs':['Specific approach.']}
        m.validate_targeting(draft,plan,'Develop prediction models','PyTorch')

    def test_ml_intern_role_resolves_to_machine_learning_engineer_without_intern_tags(self):
        # 1. Header cleans out intern and student noise to Machine Learning Engineer
        self.assertEqual(
            m.clean_header_title('Machine Learning Intern | M.Sc. Web and Data Science Student', 'Machine Learning Intern'),
            'Machine Learning Engineer'
        )
        self.assertEqual(
            g.determine_header_title('Machine Learning Intern'),
            'Machine Learning Engineer'
        )
        self.assertEqual(
            m.clean_header_title('Working Student - Machine Learning', 'Working Student - Machine Learning'),
            'Machine Learning Engineer'
        )
        # 2. Target validation rejects intern label in CV summary
        plan = self.plan()
        draft = {'projects': plan['project_order'][:4], 'skills': [{'label': 'Technical Skills', 'terms': ['Python']}],
                 'opening': 'I apply with relevant experience.',
                 'summaries': ['Machine Learning Intern with 5+ years of experience building predictive models.'],
                 'paragraphs': ['Specific approach.']}
        profile = 'Python\nGerman (B2)'
        with self.assertRaisesRegex(ValueError, 'intern'):
            m.validate_targeting(draft, plan, 'Develop machine learning models', profile)

    def test_student_cover_letter_opening_behavior(self):
        # 1. Student role without student intro gets Master's student intro inserted
        opening_without = "I am applying for the Machine Learning Internship at osapiens. My technical background in deep learning aligns with your software requirements."
        res = m.ensure_student_cover_letter_opening(opening_without, is_student=True)
        self.assertIn("Master's student in Web and Data Science at the University of Koblenz", res)
        self.assertTrue(res.startswith("I am applying for the Machine Learning Internship at osapiens."))

        # 2. Student role that already has student intro is preserved unchanged
        opening_with = "I am applying for the Werkstudent Data Science role at Bosch. As a Master's student in Web and Data Science at the University of Koblenz, I bring hands-on experience in Python."
        res2 = m.ensure_student_cover_letter_opening(opening_with, is_student=True)
        self.assertEqual(res2, opening_with)

        # 3. Full-time role does NOT add student intro
        full_time_opening = "I am applying for the Data Engineer position at Siemens. With extensive experience in Azure Databricks..."
        res3 = m.ensure_student_cover_letter_opening(full_time_opening, is_student=False)
        self.assertEqual(res3, full_time_opening)
        self.assertNotIn("student", res3.lower())

    def test_language_proficiency_stripped_and_forbidden_in_body_paragraphs(self):
        fixed = g.letter_fixed_text('Avelios Medical', 'Intern Machine Learning', 'Python and ML')
        profile = 'Python and SQL\nGerman (B2)'
        evidence = {'soltech': ['bullet1'], 'gsr': ['bullet2'], 'projects': dict.fromkeys(['upsc', 'mlops', 'trading', 'sql'])}
        opening = 'I am applying for the role.'
        count = 320 - len(fixed.split()) - len(opening.split())
        draft = {
            'summaries': ['Python and SQL engineering background. ' * 10] * 3,
            'header': 'Machine Learning Engineer',
            'skills': [{'label': 'Tools', 'terms': ['Python']}] * 3,
            'soltech': [0], 'gsr': [0],
            'projects': ['upsc', 'mlops', 'trading', 'sql'],
            'opening': opening,
            'paragraphs': [
                'engineering ' * (count // 3),
                'pipelines ' * (count // 3),
                'cloud ' * (count - 2 * (count // 3) - 10) + ' and automated schema validation, utilizing my B2 German proficiency for day-to-day professional communication.'
            ],
            'gaps': []
        }
        # 1. validate() automatically scrubs the language proficiency clause
        m.validate(draft, evidence, profile, fixed)
        self.assertNotIn('B2', draft['paragraphs'][2])
        self.assertNotIn('German proficiency', draft['paragraphs'][2])

        # 2. validate_targeting raises ValueError if B2 or German proficiency remains in body
        draft['paragraphs'][0] += ' I also hold B2 German.'
        plan = self.plan()
        plan['project_order'] = ['upsc', 'mlops', 'trading', 'sql', 'twitter']
        with self.assertRaises(ValueError) as ctx:
            m.validate_targeting(draft, plan, 'Python and ML', profile)
        self.assertIn('strictly reserved for the fixed closing paragraph', str(ctx.exception))

    def test_requisition_german_and_english(self):
        for text in ['Stellennummer: MER000450F Aufgaben','Job-ID MER000450F','Requisition Number: MER000450F']:
            self.assertEqual(g.requisition_id(text),'MER000450F')


if __name__=='__main__':unittest.main()

