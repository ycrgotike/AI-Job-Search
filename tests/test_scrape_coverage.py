import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('coverage_scraper', ROOT / 'tools/scrape.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
class CoverageTests(unittest.TestCase):
    def test_airbus_and_thesis_queries_are_default(self):
        q = g.search_queries()
        self.assertIn('Artificial Intelligence', q)
        self.assertIn('Master Thesis Artificial Intelligence', q)
        self.assertIn('Masterarbeit KI', q)
        self.assertEqual(len(q), len(g.search_queries('artificial intelligence', include_defaults=True)))
    def test_retry_then_later_page_retains_results(self):
        results = [subprocess.TimeoutExpired('bun',120),subprocess.CompletedProcess([],0,json.dumps({'results':[{'id':'1'}]})),subprocess.CompletedProcess([],0,json.dumps({'results':[{'id':'2'}]}))]
        with patch.object(g.subprocess,'run',side_effect=results) as run, patch.object(g.time,'sleep'), patch.object(g,'audit_search') as audit:
            data=g.search_portal(['bun'],'linkedin','AI',2)
        self.assertEqual([x['id'] for x in data['results']],['1','2'])
        self.assertIn('--page',run.call_args.args[0])
        self.assertIn('cap',audit.call_args.args[0]['warning'])
    def test_failure_is_not_silent_empty_success(self):
        with patch.object(g.subprocess,'run',side_effect=RuntimeError('offline')),patch.object(g.time,'sleep'),patch.object(g,'audit_search') as audit:
            g.search_portal(['bun'],'freehire','AI',10)
        self.assertIn('offline',audit.call_args.args[0]['warning'])
    def test_xing_limited_coverage_is_explicit(self):
        with patch.object(g.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'{"results":[]}')),patch.object(g,'audit_search') as audit:
            g.search_portal(['bun'],'xing','AI',10)
        self.assertIn('first page',audit.call_args.args[0]['warning'])
