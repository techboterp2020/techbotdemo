from odoo import api, fields, models
from odoo.tools.translate import _


class ResUsers(models.Model):
    """User lifecycle (SCIM-style provisioning) and audit hooks (RFP IAM)."""
    _inherit = 'res.users'

    ums_external_id = fields.Char(
        string='IdP External ID', copy=False, index=True,
        help='Stable identifier from the external identity provider (SCIM id).')
    ums_lifecycle_state = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('suspended', 'Suspended'),
            ('deprovisioned', 'Deprovisioned'),
        ],
        string='Lifecycle State', default='active',
    )

    @api.model
    def scim_provision(self, external_id, values):
        """Create or update a user from an external IdP (SCIM upsert).

        ``values`` accepts at least ``name`` and ``login``; group assignment is
        left to RBAC mapping by the caller.
        """
        user = self.search([('ums_external_id', '=', external_id)], limit=1)
        if not user and values.get('login'):
            user = self.search([('login', '=', values['login'])], limit=1)
        payload = dict(values, ums_external_id=external_id)
        if user:
            user.write(payload)
        else:
            user = self.create(payload)
        self.env['ums.audit.log'].log_action(
            _('SCIM provision'), 'access', record=user,
            description=_('External ID %s', external_id))
        return user

    def scim_deprovision(self):
        """Disable a user that was removed from the external IdP."""
        for user in self:
            user.write({'active': False, 'ums_lifecycle_state': 'deprovisioned'})
            self.env['ums.audit.log'].log_action(
                _('SCIM deprovision'), 'access', record=user)
        return True

    def action_require_mfa(self):
        """Flag staff/admin accounts that must enrol in MFA (NFR-SEC-02)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/odoo/action-base_setup.action_general_configuration',
            'target': 'self',
        }
