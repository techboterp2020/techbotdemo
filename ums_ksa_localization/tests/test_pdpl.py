from datetime import date

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ums')
class TestPdpl(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Subject'})

    def test_consent_withdraw(self):
        consent = self.env['ums.consent'].create({
            'partner_id': self.partner.id,
            'purpose': 'Admissions processing',
            'lawful_basis': 'consent',
        })
        self.assertEqual(consent.state, 'given')
        consent.action_withdraw()
        self.assertEqual(consent.state, 'withdrawn')
        self.assertTrue(consent.withdrawn_date)

    def test_consent_expiry_cron(self):
        consent = self.env['ums.consent'].create({
            'partner_id': self.partner.id,
            'purpose': 'Marketing',
            'expiry_date': date(2000, 1, 1),
        })
        self.env['ums.consent']._cron_expire_consents()
        self.assertEqual(consent.state, 'expired')

    def test_data_request_sequence_and_due_date(self):
        req = self.env['ums.data.request'].create({
            'partner_id': self.partner.id,
            'request_type': 'access',
        })
        self.assertNotEqual(req.name, 'New')
        self.assertTrue(req.name.startswith('DSR/'))
        self.assertTrue(req.due_date)
        # Due date is 30 days after the request date.
        self.assertEqual((req.due_date - req.request_date).days, 30)

    def test_data_request_workflow(self):
        req = self.env['ums.data.request'].create({
            'partner_id': self.partner.id,
            'request_type': 'erasure',
        })
        req.action_start_review()
        self.assertEqual(req.state, 'in_review')
        self.assertEqual(req.handled_by, self.env.user)
        req.action_complete()
        self.assertEqual(req.state, 'completed')
