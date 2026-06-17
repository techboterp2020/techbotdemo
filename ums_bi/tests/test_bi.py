from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ums')
class TestBi(TransactionCase):

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
        cls.env['ums.student'].create({
            'name': 'A', 'national_id': '1111111111',
            'program_id': cls.program.id, 'gender': 'male', 'status': 'active'})
        cls.env['ums.student'].create({
            'name': 'B', 'national_id': '2222222222',
            'program_id': cls.program.id, 'gender': 'male', 'status': 'graduated'})

    def test_compute_kpis(self):
        kpis = self.env['ums.kpi'].compute_kpis(self.program)
        self.assertEqual(kpis['enrollment'], 1)
        self.assertEqual(kpis['graduates'], 1)
        self.assertEqual(kpis['graduation_rate'], 50.0)

    def test_snapshot(self):
        created = self.env['ums.kpi'].snapshot(self.program)
        self.assertTrue(created)
        codes = set(created.mapped('code'))
        self.assertIn('enrollment', codes)
        self.assertIn('graduation_rate', codes)
