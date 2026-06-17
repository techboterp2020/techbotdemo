from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ums')
class TestLms(TransactionCase):

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
        course = cls.env['ums.course'].create({
            'code': 'C1', 'name_en': 'C1', 'name_ar': 'C1',
            'department_id': dept.id, 'credit_hours': 3, 'lecture_hours': 3})
        year = cls.env['ums.academic.year'].create({
            'name': 'AY', 'code': 'AY', 'date_start': date(2026, 9, 1),
            'date_end': date(2027, 6, 30)})
        cls.term = cls.env['ums.term'].create({
            'name': 'F', 'code': 'F', 'academic_year_id': year.id,
            'date_start': date(2026, 9, 1), 'date_end': date(2027, 1, 15),
            'state': 'in_progress'})
        cls.section = cls.env['ums.section'].create({
            'course_id': course.id, 'term_id': cls.term.id, 'state': 'open'})
        cls.student = cls.env['ums.student'].create({
            'name': 'S', 'national_id': '1234567890',
            'program_id': cls.program.id, 'gender': 'male'})
        cls.env['ums.registration'].create({
            'student_id': cls.student.id, 'section_id': cls.section.id,
            'state': 'registered'})

    # FR-LMS-01 — assignment lifecycle and submission grading
    def test_assignment_lifecycle(self):
        assignment = self.env['ums.assignment'].create({
            'name': 'HW1', 'section_id': self.section.id,
            'max_score': 100, 'due_date': '2026-12-01 23:59:00'})
        assignment.action_publish()
        self.assertEqual(assignment.state, 'published')
        sub = self.env['ums.assignment.submission'].create({
            'assignment_id': assignment.id, 'student_id': self.student.id})
        sub.action_submit()
        assignment.action_start_grading()
        with self.assertRaises(UserError):
            assignment.action_approve()  # ungraded submission present
        sub.score = 85
        sub.action_grade()
        assignment.action_approve()
        self.assertEqual(assignment.state, 'approved')

    # FR-LMS-02 — rubric scores sum into the submission score
    def test_rubric_grading(self):
        rubric = self.env['ums.rubric'].create({'name': 'R'})
        c1 = self.env['ums.rubric.criterion'].create({
            'rubric_id': rubric.id, 'name': 'Quality', 'max_points': 60})
        c2 = self.env['ums.rubric.criterion'].create({
            'rubric_id': rubric.id, 'name': 'Style', 'max_points': 40})
        self.assertEqual(rubric.max_score, 100)
        assignment = self.env['ums.assignment'].create({
            'name': 'HW2', 'section_id': self.section.id, 'rubric_id': rubric.id,
            'max_score': 100, 'due_date': '2026-12-01 23:59:00'})
        sub = self.env['ums.assignment.submission'].create({
            'assignment_id': assignment.id, 'student_id': self.student.id,
            'rubric_score_ids': [
                (0, 0, {'criterion_id': c1.id, 'points': 55}),
                (0, 0, {'criterion_id': c2.id, 'points': 30})]})
        sub.action_grade()
        self.assertEqual(sub.score, 85)

    # FR-LMS-02 — rubric points cannot exceed criterion max
    def test_rubric_overflow(self):
        rubric = self.env['ums.rubric'].create({'name': 'R2'})
        c1 = self.env['ums.rubric.criterion'].create({
            'rubric_id': rubric.id, 'name': 'X', 'max_points': 10})
        assignment = self.env['ums.assignment'].create({
            'name': 'HW3', 'section_id': self.section.id,
            'max_score': 100, 'due_date': '2026-12-01 23:59:00'})
        sub = self.env['ums.assignment.submission'].create({
            'assignment_id': assignment.id, 'student_id': self.student.id})
        with self.assertRaises(ValidationError):
            self.env['ums.submission.rubric.score'].create({
                'submission_id': sub.id, 'criterion_id': c1.id, 'points': 50})

    # FR-LMS-03 — absence threshold bars from final exam
    def test_attendance_bar(self):
        # 4 sessions, 2 absent -> 50% absence > 25% bar
        for i in range(4):
            session = self.env['ums.attendance.session'].create({
                'section_id': self.section.id,
                'session_date': date(2026, 10, i + 1)})
            self.env['ums.attendance.line'].create({
                'session_id': session.id, 'student_id': self.student.id,
                'status': 'absent' if i < 2 else 'present'})
        attended, absent = self.section.get_attendance_percent(self.student)
        self.assertEqual(absent, 50.0)
        self.assertTrue(self.section.is_barred_from_final(self.student))

    # FR-LMS-03 — roster bulk load
    def test_load_roster(self):
        session = self.env['ums.attendance.session'].create({
            'section_id': self.section.id, 'session_date': date(2026, 10, 10)})
        session.action_load_roster()
        self.assertEqual(len(session.line_ids), 1)
        self.assertEqual(session.line_ids.student_id, self.student)
