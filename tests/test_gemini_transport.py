import json
import os
import socket
import ssl
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
from tools import gemini_tailoring as m
from tools.generation_diagnostics import save_failure

class TransportTests(unittest.TestCase):
    def test_timeout_is_configurable_and_bounded(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{},clear=True):
            self.assertEqual(m.settings(d)['timeout'],120)
            for value in ['29','181','bad']:
                Path(d,'.env').write_text('GEMINI_REQUEST_TIMEOUT_SECONDS='+value)
                with self.assertRaises(ValueError):m.settings(d)
            Path(d,'.env').write_text('GEMINI_REQUEST_TIMEOUT_SECONDS=150')
            self.assertEqual(m.settings(d)['timeout'],150)

    def test_timeout_error_has_phase_elapsed_and_no_secret(self):
        with patch.object(m.urllib.request,'urlopen',side_effect=TimeoutError('secret')), patch.object(m.time,'sleep'):
            with self.assertRaises(m.GeminiTransportError) as caught:
                m.request_json({'key':'secret','model':'test','timeout':150},'',{},m.PLAN_SCHEMA)
        diag=caught.exception.diagnostics
        self.assertEqual(diag['kind'],'timeout');self.assertEqual(diag['stage'],'responsibility_plan')
        self.assertEqual(diag['attempts'],3);self.assertEqual(diag['timeout_seconds'],150)
        self.assertNotIn('secret',str(caught.exception));self.assertNotIn('secret',json.dumps(diag))

    def test_certificate_errors_are_not_retried_or_masked(self):
        exc=urllib.error.URLError(ssl.SSLCertVerificationError('secret'))
        with patch.object(m.urllib.request,'urlopen',side_effect=exc) as request,patch.object(m.time,'sleep') as sleep:
            with self.assertRaises(m.GeminiTransportError) as caught:m.request_json({'key':'secret','model':'test'},'',{},m.SCHEMA)
        request.assert_called_once();sleep.assert_not_called()
        self.assertEqual(caught.exception.diagnostics['kind'],'tls_certificate')

    def test_dns_is_distinct_from_timeout(self):
        exc=urllib.error.URLError(socket.gaierror(-2,'secret'))
        failure=m.transport_failure(exc,'draft',1,m.time.monotonic(),120)
        self.assertEqual(failure.diagnostics['kind'],'dns')
        with tempfile.TemporaryDirectory() as root:
            path=save_failure(Path(root),'Example','Internship',str(failure),transport={**failure.diagnostics,'key':'secret'})
            report=json.loads((Path(root)/path).read_text())
            self.assertEqual(report['stage'],'draft')
            self.assertNotIn('secret',json.dumps(report))

if __name__=='__main__':unittest.main()
