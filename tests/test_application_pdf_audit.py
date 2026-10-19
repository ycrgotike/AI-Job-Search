import unittest
from unittest.mock import patch
from tools import application_pdf_audit as a
from tools.verify_pdf import VerificationError

SOURCE=r'''\name{Yashwanth}{Gotike}\phone[mobile]{(+49)~17674755646}\email{gycrgotike@gmail.com}
\section{Technical Skills}\section{Professional Experience}\cventry{09/2022--09/2024}{}{}{}{}{}
\section{Key Technical Projects}\section{Education}\section{Languages \& Honors}'''
TEXT='''Yashwanth Gotike Phone: +49 17674755646 Email: gycrgotike@gmail.com
Technical Skills Python SQL Professional Experience SolTech 09/2022–09/2024 G.S.R ITC Infotech
Key Technical Projects Education Languages & Honors'''


class AuditTests(unittest.TestCase):
    def test_complete_contacts_sections_and_dates_pass(self):
        errors, warnings=a.inspect_text(TEXT,a.contact_contract(SOURCE),SOURCE,'cv')
        self.assertEqual((errors,warnings),([],[]))

    def test_missing_contact_is_reported(self):
        errors,_=a.inspect_text(TEXT.replace('gycrgotike@gmail.com',''),a.contact_contract(SOURCE),SOURCE,'cv')
        self.assertTrue(any('email' in error for error in errors))

    def test_bad_glyphs_and_order_are_warnings(self):
        errors, notes=a.inspect_text(TEXT.replace('Technical Skills Python SQL Professional Experience','Professional Experience Python SQL Technical Skills')+' (cid:123)',a.contact_contract(SOURCE),SOURCE,'cv')
        self.assertFalse(errors)
        self.assertTrue(any('reading order' in note for note in notes))
        self.assertTrue(any('Encoding' in note for note in notes))

    def test_optional_missing_extractor_does_not_fail_good_document(self):
        with patch.object(a.verify_pdf,'_extract_pypdf',return_value=(TEXT,2)),patch.object(a.verify_pdf,'_extract_pdftotext',side_effect=VerificationError('missing tool')):
            report=a.audit_document('example.pdf',SOURCE,'cv',a.contact_contract(SOURCE))
        self.assertFalse(report['errors'])
        self.assertEqual(report['extractors'],['pypdf'])
        self.assertTrue(report['warnings'])

    def test_second_parser_can_recover_first_parser_missing_contact(self):
        with patch.object(a.verify_pdf,'_extract_pypdf',return_value=(TEXT.replace('gycrgotike@gmail.com',''),2)),patch.object(a.verify_pdf,'_extract_pdftotext',return_value=(TEXT,2)):
            report=a.audit_document('example.pdf',SOURCE,'cv',a.contact_contract(SOURCE))
        self.assertFalse(report['errors'])
        self.assertEqual(len(report['extractors']),2)
        self.assertTrue(any('Extractors differ' in note for note in report['warnings']))

    def test_both_parsers_confirm_missing_contact(self):
        missing=TEXT.replace('gycrgotike@gmail.com','')
        with patch.object(a.verify_pdf,'_extract_pypdf',return_value=(missing,2)),patch.object(a.verify_pdf,'_extract_pdftotext',return_value=(missing,2)):
            report=a.audit_document('example.pdf',SOURCE,'cv',a.contact_contract(SOURCE))
        self.assertEqual(report['status'],'failed')
        self.assertTrue(report['errors'])

    def test_no_optional_extractors_preserves_basic_verified_result(self):
        with patch.object(a.verify_pdf,'_extract_pypdf',return_value=None),patch.object(a.verify_pdf,'_extract_pdftotext',side_effect=VerificationError('unavailable')):
            report=a.audit_document('example.pdf',SOURCE,'cv',{})
        self.assertEqual(report['status'],'review_required')
        self.assertFalse(report['errors'])

    def test_keyword_coverage_separates_unconfirmed_skills(self):
        review={'technologies':[{'technology':'Python','status':'confirmed'},{'technology':'SQL','status':'confirmed'},{'technology':'Snowflake','status':'needs_confirmation'}]}
        with patch.object(a.verify_pdf,'_extract_pypdf',return_value=(TEXT,2)),patch.object(a.verify_pdf,'_extract_pdftotext',return_value=(TEXT,2)):
            report=a.audit_application('cv.pdf','letter.pdf',SOURCE,'letter',review)
        self.assertEqual(report['keyword_coverage']['missing_from_skills'],[])
        self.assertEqual(report['keyword_coverage']['unconfirmed_job_terms'],['Snowflake'])
        self.assertNotIn('Snowflake',report['keyword_coverage']['supported_job_terms'])
        self.assertNotIn('text',report['cv'])

if __name__=='__main__':unittest.main()
