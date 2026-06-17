from datetime import date

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ums')
class TestHr(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        inst = cls.env['ums.institution'].create(
            {'code': 'I', 'name_en': 'I', 'name_ar': 'I'})
        college = cls.env['ums.college'].create(
            {'code': 'C', 'name_en': 'C', 'name_ar': 'C', 'institution_id': inst.id})
        cls.dept = cls.env['ums.department'].create(
            {'code': 'D', 'name_en': 'D', 'name_ar': 'D', 'college_id': college.id})
        year = cls.env['ums.academic.year'].create({
            'name': 'AY', 'code': 'AY', 'date_start': date(2026, 9, 1),
            'date_end': date(2027, 6, 30)})
        cls.term = cls.env['ums.term'].create({
            'name': 'F', 'code': 'F', 'academic_year_id': year.id,
            'date_start': date(2026, 9, 1), 'date_end': date(2027, 1, 15)})
        cls.faculty = cls.env['hr.employee'].create({
            'name': 'Dr. Faculty', 'is_faculty': True,
            'academic_rank': 'professor', 'max_teaching_load': 9})

    def _section(self, code, ch):
        course = self.env['ums.course'].create({
            'code': code, 'name_en': code, 'name_ar': code,
            'department_id': self.dept.id, 'credit_hours': ch, 'lecture_hours': ch})
        return self.env['ums.section'].create({
            'course_id': course.id, 'term_id': self.term.id})

    # FR-FAC-02 — workload computation and overload flag
    def test_teaching_load(self):
        s1 = self._section('L1', 3)
        s2 = self._section('L2', 3)
        load = self.env['ums.teaching.load'].create({
            'employee_id': self.faculty.id, 'term_id': self.term.id,
            'section_ids': [(6, 0, [s1.id, s2.id])]})
        self.assertEqual(load.total_credit_hours, 6)
        self.assertFalse(load.is_overloaded)
        s3 = self._section('L3', 6)
        load.section_ids = [(4, s3.id)]
        self.assertEqual(load.total_credit_hours, 12)
        self.assertTrue(load.is_overloaded)  # 12 > max 9
