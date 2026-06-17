from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ums')
class TestCalendar(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.year = cls.env['ums.academic.year'].create({
            'name': '2026/2027', 'code': 'AY2627',
            'date_start': date(2026, 9, 1), 'date_end': date(2027, 6, 30),
        })
        cls.term = cls.env['ums.term'].create({
            'name': 'Fall 2026', 'code': 'F26',
            'academic_year_id': cls.year.id, 'term_type': 'fall',
            'date_start': date(2026, 9, 1), 'date_end': date(2027, 1, 15),
        })
        college = cls.env['ums.college'].create({
            'code': 'C', 'name_en': 'C', 'name_ar': 'C',
            'institution_id': cls.env['ums.institution'].create({
                'code': 'I', 'name_en': 'I', 'name_ar': 'I'}).id})
        dept = cls.env['ums.department'].create({
            'code': 'D', 'name_en': 'D', 'name_ar': 'D', 'college_id': college.id})
        cls.course1 = cls.env['ums.course'].create({
            'code': 'C1', 'name_en': 'C1', 'name_ar': 'C1',
            'department_id': dept.id, 'credit_hours': 3, 'lecture_hours': 3})
        cls.course2 = cls.env['ums.course'].create({
            'code': 'C2', 'name_en': 'C2', 'name_ar': 'C2',
            'department_id': dept.id, 'credit_hours': 3, 'lecture_hours': 3})
        cls.room = cls.env['ums.room'].create({
            'code': 'R1', 'name': 'Room 1', 'capacity': 30})
        cls.slot = cls.env['ums.timeslot'].create({
            'dayofweek': '6', 'hour_from': 8.0, 'hour_to': 10.0})  # Sun 8-10

    # FR-CAL-01 — dual Hijri dates computed
    def test_term_hijri(self):
        self.assertTrue(self.term.hijri_start)
        self.assertTrue(self.term.hijri_start.endswith('AH'))

    # FR-CAL-01 — term must end after it starts
    def test_term_date_validation(self):
        with self.assertRaises(ValidationError):
            self.env['ums.term'].create({
                'name': 'Bad', 'code': 'BAD',
                'academic_year_id': self.year.id,
                'date_start': date(2027, 1, 1), 'date_end': date(2026, 12, 1)})

    # FR-CAL-04 — timeslot overlap detection
    def test_timeslot_overlap(self):
        other = self.env['ums.timeslot'].create({
            'dayofweek': '6', 'hour_from': 9.0, 'hour_to': 11.0})
        self.assertTrue(self.slot.overlaps(other))
        non = self.env['ums.timeslot'].create({
            'dayofweek': '0', 'hour_from': 8.0, 'hour_to': 10.0})
        self.assertFalse(self.slot.overlaps(non))

    # FR-CAL-04 — room double-booking blocked
    def test_room_clash(self):
        self.env['ums.section'].create({
            'course_id': self.course1.id, 'term_id': self.term.id,
            'room_id': self.room.id, 'timeslot_ids': [(6, 0, [self.slot.id])],
            'state': 'open'})
        with self.assertRaises(ValidationError):
            self.env['ums.section'].create({
                'course_id': self.course2.id, 'term_id': self.term.id,
                'room_id': self.room.id, 'timeslot_ids': [(6, 0, [self.slot.id])],
                'state': 'open'})

    # FR-CAL-04 — instructor double-booking blocked
    def test_instructor_clash(self):
        instructor = self.env['res.users'].create({
            'name': 'Prof', 'login': 'prof_clash_test'})
        self.env['ums.section'].create({
            'course_id': self.course1.id, 'term_id': self.term.id,
            'instructor_id': instructor.id,
            'timeslot_ids': [(6, 0, [self.slot.id])], 'state': 'open'})
        with self.assertRaises(ValidationError):
            self.env['ums.section'].create({
                'course_id': self.course2.id, 'term_id': self.term.id,
                'instructor_id': instructor.id,
                'timeslot_ids': [(6, 0, [self.slot.id])], 'state': 'open'})

    # FR-CAL-04 — non-overlapping slots do not clash
    def test_no_clash_different_time(self):
        late = self.env['ums.timeslot'].create({
            'dayofweek': '6', 'hour_from': 10.0, 'hour_to': 12.0})
        self.env['ums.section'].create({
            'course_id': self.course1.id, 'term_id': self.term.id,
            'room_id': self.room.id, 'timeslot_ids': [(6, 0, [self.slot.id])],
            'state': 'open'})
        # Same room, later slot -> allowed
        section = self.env['ums.section'].create({
            'course_id': self.course2.id, 'term_id': self.term.id,
            'room_id': self.room.id, 'timeslot_ids': [(6, 0, [late.id])],
            'state': 'open'})
        self.assertEqual(section.state, 'open')

    # FR-CAL-02 — key date window query
    def test_window_open(self):
        self.env['ums.key.date'].create({
            'term_id': self.term.id, 'name': 'Reg',
            'date_type': 'registration',
            'date_start': date(2026, 8, 1), 'date_end': date(2099, 1, 1)})
        self.assertTrue(self.term.is_window_open('registration'))
        self.assertFalse(self.term.is_window_open('withdraw'))
