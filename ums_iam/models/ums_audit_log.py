from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class UmsAuditLog(models.Model):
    """Append-only audit log for sensitive academic/financial/admin actions
    (NFR-SEC-03). Records cannot be modified or deleted through the ORM."""
    _name = 'ums.audit.log'
    _description = 'Audit Log'
    _order = 'create_date desc'

    name = fields.Char(string='Action', required=True)
    user_id = fields.Many2one(
        'res.users', string='User', required=True,
        default=lambda self: self.env.user, index=True,
    )
    category = fields.Selection(
        selection=[
            ('grade', 'Grade Change'),
            ('finance', 'Financial Transaction'),
            ('admission', 'Admission Decision'),
            ('config', 'Configuration Change'),
            ('access', 'Access / Login'),
            ('data', 'Data Subject / PDPL'),
        ],
        string='Category', required=True, index=True,
    )
    model_name = fields.Char(string='Model', index=True)
    res_id = fields.Integer(string='Record ID')
    description = fields.Text(string='Details')
    log_date = fields.Datetime(
        string='Timestamp', default=fields.Datetime.now, index=True)

    @api.model
    def log_action(self, name, category, record=None, description=None):
        """Convenience helper for other modules to append an audit entry."""
        vals = {'name': name, 'category': category, 'description': description}
        if record is not None and record:
            vals['model_name'] = record._name
            vals['res_id'] = record.id
        return self.sudo().create(vals)

    def write(self, vals):
        raise UserError(_("Audit log entries are immutable and cannot be edited."))

    def unlink(self):
        raise UserError(_("Audit log entries are immutable and cannot be deleted."))
