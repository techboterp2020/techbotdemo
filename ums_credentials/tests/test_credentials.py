from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ums')
class TestCredentials(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        inst = cls.env['ums.institution'].create(
            {'code': 'I', 'name_en': 'I', 'name_ar': 'I'})
        college = cls.env['ums.college'].create(
            {'code': 'C', 'name_en': 'C', 'name_ar': 'C', 'institution_id': inst.id})
        dept = cls.env['ums.department'].create(
            {'code': 'D', 'name_en': 'D', 'name_ar': 'D', 'college_id': college.id})
        program = cls.env['ums.program'].create({
            'code': 'P', 'name_en': 'P', 'name_ar': 'P',
            'department_id': dept.id, 'degree_type': 'bachelor',
            'total_credit_hours': 120})
        cls.student = cls.env['ums.student'].create({
            'name': 'Grad', 'national_id': '1234567890',
            'program_id': program.id, 'gender': 'male'})

    def test_issue_and_verify(self):
        cred = self.env['ums.credential'].create({
            'name': 'BSc Certificate', 'credential_type': 'degree',
            'student_id': self.student.id})
        self.assertTrue(cred.serial.startswith('CRED/'))
        self.assertTrue(cred.verification_token)
        # Not valid until issued.
        self.assertFalse(self.env['ums.credential'].verify(cred.verification_token)['valid'])
        cred.action_issue()
        result = self.env['ums.credential'].verify(cred.verification_token)
        self.assertTrue(result['valid'])
        self.assertEqual(result['recipient'], 'Grad')
        # Revocation invalidates.
        cred.action_revoke()
        self.assertFalse(self.env['ums.credential'].verify(cred.serial)['valid'])

    def test_open_badge_export(self):
        cred = self.env['ums.credential'].create({
            'name': 'Badge', 'credential_type': 'badge',
            'student_id': self.student.id})
        badge = cred.to_open_badge()
        self.assertIn('OpenBadgeCredential', badge['type'])
        self.assertEqual(badge['credentialSubject']['name'], 'Grad')
