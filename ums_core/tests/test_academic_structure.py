from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ums')
class TestAcademicStructure(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.institution = cls.env['ums.institution'].create({
            'code': 'TST', 'name_en': 'Test University', 'name_ar': 'جامعة اختبار',
        })
        cls.college = cls.env['ums.college'].create({
            'code': 'TENG', 'name_en': 'Engineering', 'name_ar': 'الهندسة',
            'institution_id': cls.institution.id,
        })
        cls.department = cls.env['ums.department'].create({
            'code': 'TCS', 'name_en': 'Computer Science', 'name_ar': 'الحاسب',
            'college_id': cls.college.id,
        })
        cls.program = cls.env['ums.program'].create({
            'code': 'TBSCS', 'name_en': 'BSc CS', 'name_ar': 'بكالوريوس',
            'department_id': cls.department.id,
            'degree_type': 'bachelor', 'total_credit_hours': 6,
        })

    def _course(self, code, ch=3):
        return self.env['ums.course'].create({
            'code': code, 'name_en': code, 'name_ar': code,
            'department_id': self.department.id,
            'credit_hours': ch, 'lecture_hours': ch,
        })

    # FR-ACS-01 — hierarchy roll-up counts
    def test_rollup_counts(self):
        self.assertEqual(self.institution.college_count, 1)
        self.assertEqual(self.institution.department_count, 1)
        self.assertEqual(self.institution.program_count, 1)
        self.assertEqual(self.college.department_count, 1)
        self.assertEqual(self.college.program_count, 1)

    # FR-ACS-01 — deletion guarded by dependencies
    def test_delete_guard(self):
        with self.assertRaises(UserError):
            self.institution.unlink()
        with self.assertRaises(UserError):
            self.college.unlink()

    # FR-ACS-02 — duplicate program code blocked
    def test_program_unique_code(self):
        with self.assertRaises(Exception):
            self.env['ums.program'].create({
                'code': 'TBSCS', 'name_en': 'Dup', 'name_ar': 'مكرر',
                'department_id': self.department.id,
                'degree_type': 'bachelor', 'total_credit_hours': 6,
            })

    # FR-ACS-02 — default Saudi 5.0 scheme auto-assigned
    def test_program_default_scheme(self):
        scheme = self.env.ref('ums_core.grade_scheme_saudi_5')
        self.assertEqual(self.program.grade_scheme_id, scheme)

    # FR-ACS-03 — contact hours computed
    def test_course_contact_hours(self):
        course = self._course('TST101')
        course.lab_hours = 2
        self.assertEqual(course.contact_hours, 5)  # 3 lecture + 2 lab

    # FR-ACS-04 — circular prerequisite blocked
    def test_circular_prerequisite(self):
        a = self._course('A100')
        b = self._course('B100')
        self.env['ums.course.prerequisite'].create({
            'course_id': b.id, 'prerequisite_course_id': a.id,
        })
        # Now making A require B would create a cycle.
        with self.assertRaises(ValidationError):
            self.env['ums.course.prerequisite'].create({
                'course_id': a.id, 'prerequisite_course_id': b.id,
            })

    # FR-ACS-04 — transitive prerequisite resolution
    def test_transitive_prerequisites(self):
        a = self._course('A200')
        b = self._course('B200')
        c = self._course('C200')
        self.env['ums.course.prerequisite'].create(
            {'course_id': b.id, 'prerequisite_course_id': a.id})
        self.env['ums.course.prerequisite'].create(
            {'course_id': c.id, 'prerequisite_course_id': b.id})
        self.assertEqual(c.get_all_prerequisites(), a | b)

    # FR-ACS-05 — study plan must total program CH before activation
    def test_study_plan_total_validation(self):
        plan = self.env['ums.study.plan'].create({
            'program_id': self.program.id, 'version': 1,
        })
        c1 = self._course('P100', ch=3)
        self.env['ums.study.plan.line'].create({
            'study_plan_id': plan.id, 'course_id': c1.id, 'level': 1, 'semester': '1',
        })
        # 3 CH != program total 6 -> activation blocked
        with self.assertRaises(ValidationError):
            plan.action_activate()
        c2 = self._course('P200', ch=3)
        self.env['ums.study.plan.line'].create({
            'study_plan_id': plan.id, 'course_id': c2.id, 'level': 1, 'semester': '1',
        })
        plan.action_activate()
        self.assertEqual(plan.state, 'active')
        self.assertEqual(plan.total_ch, 6)

    # FR-ACS-05 — duplicate course in a plan blocked
    def test_study_plan_no_duplicate_course(self):
        plan = self.env['ums.study.plan'].create({
            'program_id': self.program.id, 'version': 2,
        })
        c1 = self._course('D100', ch=3)
        with self.assertRaises(ValidationError):
            self.env['ums.study.plan.line'].create([
                {'study_plan_id': plan.id, 'course_id': c1.id,
                 'level': 1, 'semester': '1'},
                {'study_plan_id': plan.id, 'course_id': c1.id,
                 'level': 2, 'semester': '1'},
            ])

    # FR-ACS-06 — only CLOs map to PLOs
    def test_clo_plo_mapping(self):
        course = self._course('LO100')
        plo = self.env['ums.learning.outcome'].create({
            'code': 'PLO1', 'name': 'Apply CS principles',
            'outcome_type': 'plo', 'program_id': self.program.id,
        })
        clo = self.env['ums.learning.outcome'].create({
            'code': 'CLO1', 'name': 'Write programs',
            'outcome_type': 'clo', 'course_id': course.id,
            'mapped_plo_ids': [(4, plo.id)],
        })
        self.assertIn(plo, clo.mapped_plo_ids)
        with self.assertRaises(ValidationError):
            plo.mapped_plo_ids = [(4, plo.id)]

    # FR-ACS-07 — Saudi 5.0 mark -> letter/point mapping
    def test_grade_scheme_mapping(self):
        scheme = self.env.ref('ums_core.grade_scheme_saudi_5')
        self.assertEqual(scheme.grade_for_mark(97), ('A+', 5.0, False))
        self.assertEqual(scheme.grade_for_mark(82), ('B', 4.0, False))
        letter, point, is_fail = scheme.grade_for_mark(40)
        self.assertEqual((letter, point), ('F', 1.0))
        self.assertTrue(is_fail)

    # FR-ACS-07 — out-of-range mark fails loudly
    def test_grade_scheme_no_band(self):
        scheme = self.env.ref('ums_core.grade_scheme_saudi_5')
        with self.assertRaises(ValidationError):
            scheme.grade_for_mark(150)
