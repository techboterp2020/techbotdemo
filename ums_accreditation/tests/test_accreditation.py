from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ums')
class TestAccreditation(TransactionCase):

    def test_plo_coverage(self):
        inst = self.env['ums.institution'].create(
            {'code': 'I', 'name_en': 'I', 'name_ar': 'I'})
        college = self.env['ums.college'].create(
            {'code': 'C', 'name_en': 'C', 'name_ar': 'C', 'institution_id': inst.id})
        dept = self.env['ums.department'].create(
            {'code': 'D', 'name_en': 'D', 'name_ar': 'D', 'college_id': college.id})
        program = self.env['ums.program'].create({
            'code': 'P', 'name_en': 'P', 'name_ar': 'P',
            'department_id': dept.id, 'degree_type': 'bachelor',
            'total_credit_hours': 3})
        course = self.env['ums.course'].create({
            'code': 'C1', 'name_en': 'C1', 'name_ar': 'C1',
            'department_id': dept.id, 'credit_hours': 3, 'lecture_hours': 3})
        plan = self.env['ums.study.plan'].create({
            'program_id': program.id, 'version': 1})
        self.env['ums.study.plan.line'].create({
            'study_plan_id': plan.id, 'course_id': course.id,
            'level': 1, 'semester': '1'})
        plan.action_activate()
        plo = self.env['ums.learning.outcome'].create({
            'code': 'PLO1', 'name': 'Outcome', 'outcome_type': 'plo',
            'program_id': program.id})
        self.env['ums.learning.outcome'].create({
            'code': 'CLO1', 'name': 'C', 'outcome_type': 'clo',
            'course_id': course.id, 'mapped_plo_ids': [(4, plo.id)]})
        report = self.env['ums.accreditation.report'].create({
            'name': 'R', 'program_id': program.id, 'report_type': 'program'})
        self.assertEqual(report.plo_count, 1)
        self.assertEqual(report.coverage_percent, 100.0)
