from datetime import date

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ums')
class TestFinance(TransactionCase):

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
            'total_credit_hours': 120})
        cls.course = cls.env['ums.course'].create({
            'code': 'C1', 'name_en': 'C1', 'name_ar': 'C1',
            'department_id': dept.id, 'credit_hours': 3, 'lecture_hours': 3})
        year = cls.env['ums.academic.year'].create({
            'name': 'AY', 'code': 'AY', 'date_start': date(2026, 9, 1),
            'date_end': date(2027, 6, 30)})
        cls.term = cls.env['ums.term'].create({
            'name': 'F', 'code': 'F', 'academic_year_id': year.id,
            'date_start': date(2026, 9, 1), 'date_end': date(2027, 1, 15),
            'state': 'registration'})
        cls.section = cls.env['ums.section'].create({
            'course_id': cls.course.id, 'term_id': cls.term.id, 'state': 'open'})
        cls.student = cls.env['ums.student'].create({
            'name': 'S', 'national_id': '1234567890',
            'program_id': cls.program.id, 'gender': 'male'})
        cls.structure = cls.env['ums.fee.structure'].create({
            'name': 'BSc Regular', 'program_id': cls.program.id,
            'per_ch_rate': 500.0,
            'item_ids': [(0, 0, {'name': 'Registration Fee', 'amount': 200.0})]})

    # FR-FIN-01 — fee structure tuition math
    def test_compute_tuition(self):
        # 3 CH x 500 + 200 fixed = 1700
        self.assertEqual(self.structure.compute_tuition(3), 1700.0)

    # FR-FIN-01 — best-match structure lookup
    def test_find_for(self):
        found = self.env['ums.fee.structure'].find_for(
            self.program, level=1, student_type='regular')
        self.assertEqual(found, self.structure)

    # FR-FIN-02 — term tuition from registrations
    def test_term_tuition(self):
        self.env['ums.registration'].create({
            'student_id': self.student.id, 'section_id': self.section.id,
            'state': 'registered'})
        # 3 CH x 500 + 200 = 1700
        self.assertEqual(self.student.compute_term_tuition(self.term), 1700.0)

    # FR-FIN-03 — ZATCA QR payload format
    def test_zatca_qr_payload(self):
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.student.partner_id.id,
            'is_student_invoice': True,
            'ums_student_id': self.student.id,
        })
        payload = move._build_zatca_qr_payload()
        # seller | vat | date | total | tax  -> 5 pipe-separated parts
        self.assertEqual(len(payload.split('|')), 5)
