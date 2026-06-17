from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ums')
class TestRegistration(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        inst = cls.env['ums.institution'].create(
            {'code': 'I', 'name_en': 'I', 'name_ar': 'I'})
        college = cls.env['ums.college'].create(
            {'code': 'C', 'name_en': 'C', 'name_ar': 'C', 'institution_id': inst.id})
        cls.dept = cls.env['ums.department'].create(
            {'code': 'D', 'name_en': 'D', 'name_ar': 'D', 'college_id': college.id})
        cls.program = cls.env['ums.program'].create({
            'code': 'P', 'name_en': 'P', 'name_ar': 'P',
            'department_id': cls.dept.id, 'degree_type': 'bachelor',
            'total_credit_hours': 120})
        year = cls.env['ums.academic.year'].create({
            'name': 'AY', 'code': 'AY', 'date_start': date(2026, 9, 1),
            'date_end': date(2027, 6, 30)})
        cls.term = cls.env['ums.term'].create({
            'name': 'Fall', 'code': 'F', 'academic_year_id': year.id,
            'date_start': date(2026, 9, 1), 'date_end': date(2027, 1, 15),
            'state': 'registration'})
        cls.student = cls.env['ums.student'].create({
            'name': 'Ali Student', 'national_id': '1234567890',
            'program_id': cls.program.id, 'gender': 'male'})

    def _course(self, code, ch=3):
        return self.env['ums.course'].create({
            'code': code, 'name_en': code, 'name_ar': code,
            'department_id': self.dept.id, 'credit_hours': ch, 'lecture_hours': ch})

    def _section(self, course, slots=None, **kw):
        vals = {'course_id': course.id, 'term_id': self.term.id,
                'state': 'open', 'capacity': kw.pop('capacity', 30)}
        if slots:
            vals['timeslot_ids'] = [(6, 0, [s.id for s in slots])]
        vals.update(kw)
        return self.env['ums.section'].create(vals)

    # FR-SIS-01 — university ID auto-assigned, national id validated
    def test_student_creation(self):
        self.assertNotEqual(self.student.university_id, 'New')
        self.assertTrue(self.student.is_ums_student)
        self.assertEqual(len(self.student.status_history_ids), 1)

    def test_national_id_validation(self):
        with self.assertRaises(ValidationError):
            self.env['ums.student'].create({
                'name': 'Bad', 'national_id': '123',
                'program_id': self.program.id, 'gender': 'male'})

    # FR-SIS-02 — happy path registration
    def test_register_ok(self):
        section = self._section(self._course('OK1'))
        reg = self.env['ums.registration'].create({
            'student_id': self.student.id, 'section_id': section.id})
        reg.action_register()
        self.assertEqual(reg.state, 'registered')

    # FR-SIS-05 — blocking hold prevents registration
    def test_hold_blocks(self):
        self.env['ums.hold'].create({
            'student_id': self.student.id, 'hold_type': 'financial',
            'reason': 'Unpaid fees', 'blocks_registration': True})
        section = self._section(self._course('H1'))
        reg = self.env['ums.registration'].create({
            'student_id': self.student.id, 'section_id': section.id})
        with self.assertRaises(ValidationError):
            reg.action_register()

    # FR-SIS-02 — prerequisite enforcement
    def test_prerequisite_enforced(self):
        cs101 = self._course('CS101')
        cs201 = self._course('CS201')
        self.env['ums.course.prerequisite'].create({
            'course_id': cs201.id, 'prerequisite_course_id': cs101.id})
        section = self._section(cs201)
        reg = self.env['ums.registration'].create({
            'student_id': self.student.id, 'section_id': section.id})
        with self.assertRaises(ValidationError):
            reg.action_register()

    # FR-SIS-02 — credit-limit enforcement
    def test_credit_limit(self):
        # Register 18 CH (6 x 3), then a 19th-21st CH course should fail.
        for i in range(6):
            sec = self._section(self._course('L%s' % i))
            self.env['ums.registration'].create({
                'student_id': self.student.id, 'section_id': sec.id,
                'state': 'registered'})
        extra = self._section(self._course('LX'))
        reg = self.env['ums.registration'].create({
            'student_id': self.student.id, 'section_id': extra.id})
        with self.assertRaises(ValidationError):
            reg.action_register()

    # FR-SIS-02 — capacity enforcement
    def test_capacity_full(self):
        section = self._section(self._course('CAP'), capacity=1)
        other = self.env['ums.student'].create({
            'name': 'Other', 'national_id': '2234567890',
            'program_id': self.program.id, 'gender': 'male'})
        self.env['ums.registration'].create({
            'student_id': other.id, 'section_id': section.id,
            'state': 'registered'})
        reg = self.env['ums.registration'].create({
            'student_id': self.student.id, 'section_id': section.id})
        with self.assertRaises(ValidationError):
            reg.action_register()

    # FR-SIS-02 — timetable clash enforcement
    def test_timetable_clash(self):
        slot = self.env['ums.timeslot'].create({
            'dayofweek': '6', 'hour_from': 8.0, 'hour_to': 10.0})
        s1 = self._section(self._course('T1'), slots=[slot])
        s2 = self._section(self._course('T2'), slots=[slot])
        self.env['ums.registration'].create({
            'student_id': self.student.id, 'section_id': s1.id,
            'state': 'registered'})
        reg = self.env['ums.registration'].create({
            'student_id': self.student.id, 'section_id': s2.id})
        with self.assertRaises(ValidationError):
            reg.action_register()

    # FR-SIS-07 — status change is audited
    def test_status_change_audited(self):
        self.student.change_status('graduated', 'Completed degree')
        self.assertEqual(self.student.status, 'graduated')
        last = self.student.status_history_ids.sorted('id')[-1]
        self.assertEqual(last.new_status, 'graduated')
        self.assertEqual(last.reason, 'Completed degree')

    # FR-SIS-06 — standing computation bands
    def test_standing_bands(self):
        Standing = self.env['ums.academic.standing']
        self.assertEqual(Standing.compute_standing(3.5), 'good')
        self.assertEqual(Standing.compute_standing(1.5), 'warning')
        self.assertEqual(Standing.compute_standing(0.8), 'probation')
