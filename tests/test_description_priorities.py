"""Regression fixtures: actual work outranks incidental words across role types."""
import unittest
from tools.responsibility_plan import analyze_posting
from tools.technology_evidence import review_technologies
from tools import generate_application as g

AGENTS = '''Your Responsibilities Build and Ship AI Agents Design and build agents that automate finance workflows. Own features from initial concept through production deployment. Integrate agents with backend services and APIs. Build systematic evaluations for agent quality and reliability. Create representative test datasets and regression tests. Measure accuracy, latency and cost. Establish observability and feedback loops. Apply RAG and MCP. Select orchestration frameworks such as LangChain and LlamaIndex. Build guardrails, approval steps and human-in-the-loop controls. Integrate machine-learning models into production systems. Build operational tooling. About You Python or Java. You do not need experience with every technology below. Kafka, Google ADK, LangGraph, BigQuery and Vertex AI.'''

class DescriptionPriorities(unittest.TestCase):
    def letter(self,title,desc):
        return g.build_tailored_cover_letter('Example','Example',title,desc,'Student' in title,False,False,False)

    def test_agent_work_has_source_coverage_and_correct_priority(self):
        plan=analyze_posting('Applied AI Engineer',AGENTS)
        kinds=[d['kind'] for d in plan['all_responsibilities']]
        self.assertEqual(kinds[0],'agents')
        for kind in ('ai_evaluation','ai_safety','model_serving','software'):self.assertIn(kind,kinds)
        self.assertNotIn('qa',kinds)
        self.assertFalse(plan['unmapped_tasks'])
        self.assertGreater(len(plan['responsibilities'][0]['sources']),1)
        self.assertNotIn('Kafka',' '.join(d['source'] for d in plan['all_responsibilities']))

    def test_ai_document_focus_and_no_optional_skill_dump(self):
        cv=g.build_tailored_cv('Example','Example','Applied AI Engineer',AGENTS,False,False,False,True)
        letter=self.letter('Applied AI Engineer',AGENTS)
        self.assertLess(cv.index('AI \\& Deployment'),cv.index('Analytics \\& Reporting'))
        self.assertLess(cv.index('MVP UPSC'),cv.index('Kidney Disease Classification'))
        self.assertLess(cv.index('Kidney Disease Classification'),cv.index('Real-Time Twitter'))
        self.assertIn('LlamaIndex',cv)
        for term in ('finance workflows','representative test datasets','permissions','backend','latency'):
            self.assertIn(term,letter)
        for term in ('learning Java','learning Kafka','I built guardrails','Power BI dashboards'):
            self.assertNotIn(term,letter)

    def test_unconfirmed_ai_tools_remain_review_items(self):
        ledger=review_technologies(AGENTS,g.profile_text())
        states={r['technology']:r['status'] for r in ledger['technologies']}
        self.assertEqual(states['LlamaIndex'],'confirmed')
        for term in ('MCP','LangGraph','Google ADK','Vertex AI','BigQuery'):
            self.assertNotEqual(states[term],'confirmed')

    def test_title_never_invents_duties(self):
        plan=analyze_posting('AI Engineer','Your Tasks: Analyze survey data and organizational AI adoption patterns. Your Profile: Experience with RAG and LangChain.')
        self.assertEqual(plan['responsibilities'][0]['kind'],'research')
        self.assertNotIn('agents',[d['kind'] for d in plan['all_responsibilities']])

    def test_source_order_is_not_the_only_priority(self):
        desc='Tasks\nMaintain documentation.\nDevelop internal applications.\nDesign and build AI agents.\nEvaluate agent performance.\nCreate representative test datasets.'
        plan=analyze_posting('Applied AI Engineer',desc)
        self.assertEqual(plan['responsibilities'][0]['kind'],'agents')
        self.assertEqual(plan['responsibilities'][1]['kind'],'ai_evaluation')

    def test_lengths_and_distinct_evidence_across_roles(self):
        cases=[
            ('Applied AI Engineer',AGENTS,'MVP UPSC'),
            ('Working Student FinOps','Tasks\nAnalyze cloud costs and cost allocation.\nMonitor budgets.\nMaintain reporting dashboards.\nDevelop our ServiceNow application.','infrastructure overhead'),
            ('Working Student QA','Tasks\nDesign manual test cases and record test execution.\nSupport test automation.\nQualifications\nTypeScript, Jenkins, PKI.','ITC Infotech'),
            ('Master Thesis AI','Tasks\nAnalyze survey data and organizational AI adoption patterns.\nPrepare reports.','hypothesis'),
            ('Data Engineer','Tasks\nBuild ETL data pipelines integrating data sources.\nCheck data quality.','Azure Data Factory'),
            ('Database Developer','Tasks\nDevelop relational models and PL/SQL workflows.','SQL Data Warehouse'),
            ('IT Support','Tasks\nProvide user support and maintain business applications.\nDocument issues.','ITC Infotech'),
            ('Data Analyst','Tasks\nMaintain reports and dashboards.','Power BI'),
            ('Machine Learning Engineer','Tasks\nTrain machine learning models and evaluate predictive performance.','Kidney Disease Classification'),
            ('Platform Operations','Tasks\nDevelop CI/CD for platform services.\nOperate LLMs and retrieval services.','GitHub Actions'),
            ('Working Student Content','Tasks\nCreate and localize support content.\nTrack content performance metrics.','MVP UPSC'),
            ('Working Student CRM','Tasks\nResearch and maintain data.\nConduct contact research and maintain CRM records.','G.S.R'),
            ('Insurance Analyst','Tasks\nManage insurance claims and negotiate settlements.','SolTech'),
        ]
        for title,desc,evidence in cases:
            with self.subTest(title=title):
                letter=self.letter(title,desc)
                self.assertIn(evidence,letter)
                self.assertTrue(300<=g.cover_letter_body_words(letter)<=350,g.cover_letter_body_words(letter))
                self.assertIn(r'\fontsize{11pt}{14pt}',letter)
                self.assertNotIn('idempotent',letter)

    def test_unmapped_duties_are_visible(self):
        plan=analyze_posting('Operations','Tasks\nOwn supplier negotiations and manage freight contracts.')
        self.assertTrue(plan['unmapped_tasks'])
        self.assertTrue(plan['review_warnings'])

if __name__=='__main__':unittest.main()
