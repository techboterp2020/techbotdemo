from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ums')
class TestAssessment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        inst = cls.env['ums.institution'].create(
            {'code': 'I', 'name_en': 'I', 'name_ar': 'I'})
        college = cls.env['ums.college'].create(
            {'code': 'C', 'name_en': 'C', 'name_ar': 'C', 'institution_id': inst.id})
        cls.dept = cls.env['ums.department'].create(
            {'code': 'D', 'name_en': 'D', 'name_ar': 'D', 'college_id': college.id})
        # Program total CH = 6 (two 3-CH courses) for a quick graduation test.
        cls.program = cls.env['ums.program'].create({
            'code': 'P', 'name_en': 'P', 'name_ar': 'P',
            'department_id': cls.dept.id, 'degree_type': 'bachelor',
            'total_credit_hours': 6})
        cls.year = cls.env['ums.academic.year'].create({
            'name': 'AY', 'code': 'AY', 'date_start': date(2026, 9, 1),
            'date_end': date(2027, 6, 30)})
        cls.term = cls.env['ums.term'].create({
            'name': 'F', 'code': 'F', 'academic_year_id': cls.year.id,
            'date_start': date(2026, 9, 1), 'date_end': date(2027, 1, 15),
            'state': 'registration'})
        cls.student = cls.env['ums.student'].create({
            'name': 'S', 'national_id': '1234567890',
            'program_id': cls.program.id, 'gender': 'male'})

    def _graded_reg(self, code, mark):
        course = self.env['ums.course'].create({
            'code': code, 'name_en': code, 'name_ar': code,
            'department_id': self.dept.id, 'credit_hours': 3, 'lecture_hours': 3})
        section = self.env['ums.section'].create({
            'course_id': course.id, 'term_id': self.term.id, 'state': 'open'})
        reg = self.env['ums.registration'].create({
            'student_id': self.student.id, 'section_id': section.id,
            'state': 'registered'})
        entry = self.env['ums.grade.entry'].create({
            'registration_id': reg.id, 'total_mark': mark})
        entry.action_submit()
        entry.action_approve()
        return reg, entry

    # FR-ASM-03 — mark maps to Saudi 5.0 letter/points
    def test_grade_mapping(self):
        _reg, entry = self._graded_reg('G1', 97)
        self.assertEqual(entry.grade_letter, 'A+')
        self.assertEqual(entry.grade_point, 5.0)

    # FR-ASM-01 — assessment weights over 100% blocked
    def test_assessment_weight_limit(self):
        course = self.env['ums.course'].create({
            'code': 'AW', 'name_en': 'AW', 'name_ar': 'AW',
            'department_id': self.dept.id, 'credit_hours': 3, 'lecture_hours': 3})
        section = self.env['ums.section'].create({
            'course_id': course.id, 'term_id': self.term.id})
        self.env['ums.assessment.component'].create({
            'section_id': section.id, 'name': 'Midterm', 'weight': 60})
        with self.assertRaises(ValidationError):
            self.env['ums.assessment.component'].create({
                'section_id': section.id, 'name': 'Final', 'weight': 50})

    # FR-ASM-02 — approve updates registration state and grade
    def test_grade_posts_to_registration(self):
        reg, _entry = self._graded_reg('G2', 85)
        self.assertEqual(reg.state, 'completed')
        self.assertEqual(reg.grade_letter, 'B+')

    # FR-ASM-04 — CH-weighted GPA/CGPA
    def test_gpa_computation(self):
        self._graded_reg('GP1', 97)  # A+ 5.0, 3 CH
        self._graded_reg('GP2', 82)  # B   4.0, 3 CH
        gpa = self.env['ums.gpa.record'].search([
            ('student_id', '=', self.student.id), ('term_id', '=', self.term.id)])
        # (5.0*3 + 4.0*3) / 6 = 4.5
        self.assertEqual(gpa.cgpa, 4.5)

    # FR-ASM-05 — honors classification bands
    def test_classification(self):
        Gpa = self.env['ums.gpa.record']
        self.assertEqual(Gpa._classify(4.8)[0], 'mumtaz')
        self.assertEqual(Gpa._classify(4.0)[0], 'jayyid_jiddan')
        self.assertEqual(Gpa._classify(3.0)[0], 'jayyid')
        self.assertEqual(Gpa._classify(2.0)[0], 'maqbool')

    # FR-ASM-10 — failing grade marks registration failed
    def test_failing_grade(self):
        reg, entry = self._graded_reg('FAIL', 40)
        self.assertTrue(entry.is_fail)
        self.assertEqual(reg.state, 'failed')

    # FR-ASM-08/09 — degree audit and graduation eligibility
    def test_graduation_flow(self):
        # Build an active study plan of the two courses, then complete both.
        reg1, _ = self._graded_reg('DA1', 90)
        reg2, _ = self._graded_reg('DA2', 80)
        plan = self.env['ums.study.plan'].create({
            'program_id': self.program.id, 'version': 1})
        for reg in (reg1, reg2):
            self.env['ums.study.plan.line'].create({
                'study_plan_id': plan.id, 'course_id': reg.course_id.id,
                'level': 1, 'semester': '1'})
        plan.action_activate()
        self.student.study_plan_id = plan
        self.assertTrue(self.student.is_graduation_eligible())
        grad = self.env['ums.graduation'].create({
            'student_id': self.student.id, 'term_id': self.term.id})
        grad.action_check_eligibility()
        self.assertEqual(grad.state, 'eligible')
        grad.action_clear()
        grad.action_graduate()
        self.assertEqual(grad.state, 'graduated')
        self.assertEqual(self.student.status, 'graduated')

    # FR-ASM-09 — holds block graduation clearance
    def test_hold_blocks_graduation(self):
        grad = self.env['ums.graduation'].create({
            'student_id': self.student.id, 'term_id': self.term.id,
            'state': 'eligible'})
        self.env['ums.hold'].create({
            'student_id': self.student.id, 'hold_type': 'financial',
            'reason': 'Unpaid', 'blocks_transcript': True})
        with self.assertRaises(UserError):
            grad.action_clear()
