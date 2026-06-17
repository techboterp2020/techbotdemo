from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ums')
class TestLxp(TransactionCase):

    def test_recommended_for(self):
        inst = self.env['ums.institution'].create(
            {'code': 'I', 'name_en': 'I', 'name_ar': 'I'})
        college = self.env['ums.college'].create(
            {'code': 'C', 'name_en': 'C', 'name_ar': 'C', 'institution_id': inst.id})
        dept = self.env['ums.department'].create(
            {'code': 'D', 'name_en': 'D', 'name_ar': 'D', 'college_id': college.id})
        program = self.env['ums.program'].create({
            'code': 'P', 'name_en': 'P', 'name_ar': 'P',
            'department_id': dept.id, 'degree_type': 'bachelor',
            'total_credit_hours': 120})
        student = self.env['ums.student'].create({
            'name': 'S', 'national_id': '1234567890',
            'program_id': program.id, 'gender': 'male', 'level': 1})
        pathway = self.env['ums.pathway'].create({
            'name': 'Intro Path', 'program_id': program.id, 'level': 1})
        recommended = self.env['ums.pathway'].recommended_for(student)
        self.assertIn(pathway, recommended)
