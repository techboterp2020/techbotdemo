from odoo import api, fields, models
from odoo.tools.translate import _


class UmsDataRequest(models.Model):
    """A PDPL data-subject rights request: access, correction, erasure or
    objection (NFR-PRV-01)."""
    _name = 'ums.data.request'
    _description = 'PDPL Data Subject Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Reference', required=True, copy=False, readonly=True,
        default=lambda self: _('New'))
    partner_id = fields.Many2one(
        'res.partner', string='Data Subject', required=True,
        ondelete='restrict', index=True, tracking=True,
    )
    request_type = fields.Selection(
        selection=[
            ('access', 'Access'),
            ('correction', 'Correction'),
            ('erasure', 'Erasure'),
            ('objection', 'Objection to Processing'),
            ('portability', 'Data Portability'),
        ],
        string='Request Type', required=True, tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('submitted', 'Submitted'),
            ('in_review', 'In Review'),
            ('completed', 'Completed'),
            ('rejected', 'Rejected'),
        ],
        string='Status', default='submitted', required=True, tracking=True,
    )
    description = fields.Text(string='Request Details')
    response = fields.Text(string='Response / Resolution')
    request_date = fields.Date(
        string='Request Date', default=fields.Date.context_today)
    # PDPL: controllers must respond within a statutory window.
    due_date = fields.Date(
        string='Due Date', compute='_compute_due_date', store=True)
    handled_by = fields.Many2one('res.users', string='Handled By', tracking=True)

    @api.depends('request_date')
    def _compute_due_date(self):
        for req in self:
            if req.request_date:
                req.due_date = fields.Date.add(req.request_date, days=30)
            else:
                req.due_date = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'ums.data.request') or _('New')
        return super().create(vals_list)

    def action_start_review(self):
        self.write({'state': 'in_review', 'handled_by': self.env.user.id})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_reject(self):
        self.write({'state': 'rejected'})
