from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ums')
class TestIam(TransactionCase):

    # NFR-SEC-03 — audit log is immutable
    def test_audit_log_immutable(self):
        log = self.env['ums.audit.log'].log_action(
            'Test action', 'config', description='unit test')
        self.assertTrue(log)
        with self.assertRaises(UserError):
            log.name = 'changed'
        with self.assertRaises(UserError):
            log.unlink()

    # RFP IAM — SCIM provisioning upserts users and logs the action
    def test_scim_provision_and_deprovision(self):
        Users = self.env['res.users']
        user = Users.scim_provision('ext-123', {
            'name': 'External User', 'login': 'ext_user_iam_test'})
        self.assertEqual(user.ums_external_id, 'ext-123')
        self.assertEqual(user.ums_lifecycle_state, 'active')

        # Upsert again with the same external id updates rather than duplicates.
        again = Users.scim_provision('ext-123', {'name': 'Renamed User'})
        self.assertEqual(again, user)
        self.assertEqual(user.name, 'Renamed User')

        user.scim_deprovision()
        self.assertFalse(user.active)
        self.assertEqual(user.ums_lifecycle_state, 'deprovisioned')

        logs = self.env['ums.audit.log'].search([
            ('category', '=', 'access'),
            ('res_id', '=', user.id),
            ('model_name', '=', 'res.users')])
        self.assertTrue(logs)
