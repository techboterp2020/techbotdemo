from datetime import date

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ums')
class TestAdmission(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        inst = cls.env['ums.institution'].create(
            {'code': 'I', 'name_en': 'I', 'name_ar': 'I'})
        college = cls.env['ums.college'].create(
            {'code': 'C', 'name_en': 'C', 'name_ar': 'C', 'institution_id': inst.id})
        dept = cls.env['ums.department'].create(
            {'code': 'D', 'name_en': 'D', 'name_ar': 'D', 'college_id': college.id})
        cls.program = cls.env['ums.program'].create({
            'code': 'P', 'name_en': 'P', 'name_ar': 'P',
            'department_id': dept.id, 'degree_type': 'bachelor',
            'total_credit_hours': 120,
            'weight_qiyas': 0.3, 'weight_tahsili': 0.3, 'weight_gpa': 0.4})
        year = cls.env['ums.academic.year'].create({
            'name': 'AY', 'code': 'AY', 'date_start': date(2026, 9, 1),
            'date_end': date(2027, 6, 30)})
        cls.term = cls.env['ums.term'].create({
            'name': 'Fall', 'code': 'F', 'academic_year_id': year.id,
            'date_start': date(2026, 9, 1), 'date_end': date(2027, 1, 15)})
        cls.intake = cls.env['ums.intake'].create({
            'name': 'Fall Intake', 'code': 'IN1', 'term_id': cls.term.id,
            'date_open': date(2026, 1, 1), 'date_close': date(2026, 8, 1),
            'state': 'open'})
        cls.env['ums.seat.quota'].create({
            'intake_id': cls.intake.id, 'program_id': cls.program.id,
            'gender': 'any', 'seats': 2})

    def _application(self, **kw):
        vals = {
            'partner_name': 'Applicant', 'program_id': self.program.id,
            'intake_id': self.intake.id, 'gender': 'male',
            'qiyas_score': 80, 'tahsili_score': 90, 'hs_gpa': 95,
            'fee_paid': True}
        vals.update(kw)
        return self.env['ums.application'].create(vals)

    # FR-ADM-03 — composite score from program weights
    def test_composite_score(self):
        app = self._application()
        # 80*0.3 + 90*0.3 + 95*0.4 = 24 + 27 + 38 = 89
        self.assertAlmostEqual(app.composite_score, 89.0, places=2)

    def test_application_number(self):
        app = self._application()
        self.assertTrue(app.name.startswith('APP/'))

    # FR-ADM-04/06 — cannot submit without fee
    def test_submit_requires_fee(self):
        app = self._application(fee_paid=False)
        with self.assertRaises(UserError):
            app.action_submit()

    # FR-ADM-07/09 — offer requires verified documents
    def test_offer_requires_documents(self):
        app = self._application()
        app.action_submit()
        app.action_start_review()
        app.action_shortlist()
        with self.assertRaises(UserError):
            app.action_issue_offer()  # no documents yet

    # FR-ADM-06/08 — full lifecycle through to SIS handover
    def test_full_lifecycle_to_enrollment(self):
        app = self._application()
        self.env['ums.application.document'].create({
            'application_id': app.id, 'doc_type': 'national_id',
            'name': 'ID', 'required': True, 'state': 'verified'})
        app.action_submit()
        app.action_start_review()
        app.action_shortlist()
        app.action_issue_offer()
        self.assertEqual(app.state, 'offer')
        app.action_accept_offer()
        app.action_enroll()
        self.assertEqual(app.state, 'enrolled')
        self.assertTrue(app.student_id)
        self.assertEqual(app.student_id.program_id, self.program)

    # FR-ADM-01 — lead converts to application
    def test_lead_conversion(self):
        lead = self.env['ums.lead'].create({
            'name': 'Prospect', 'program_id': self.program.id,
            'intake_id': self.intake.id})
        lead.action_convert_to_application()
        self.assertEqual(lead.stage, 'applied')
        self.assertTrue(lead.application_id)

    # FR-ADM-05 — ranking by composite score
    def test_ranking(self):
        high = self._application(qiyas_score=95, tahsili_score=95, hs_gpa=95)
        low = self._application(qiyas_score=60, tahsili_score=60, hs_gpa=60)
        high.action_submit()
        low.action_submit()
        self.env['ums.application'].rank_intake(self.intake)
        self.assertEqual(high.rank, 1)
        self.assertEqual(low.rank, 2)
