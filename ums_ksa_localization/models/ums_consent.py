from odoo import api, fields, models


class UmsConsent(models.Model):
    """Record of a data subject's consent for a processing purpose (PDPL —
    NFR-PRV-01)."""
    _name = 'ums.consent'
    _description = 'PDPL Consent Record'
    _inherit = ['mail.thread']
    _order = 'create_date desc'
    _rec_name = 'purpose'

    partner_id = fields.Many2one(
        'res.partner', string='Data Subject', required=True,
        ondelete='cascade', index=True, tracking=True,
    )
    purpose = fields.Char(string='Processing Purpose', required=True, tracking=True)
    lawful_basis = fields.Selection(
        selection=[
            ('consent', 'Consent'),
            ('contract', 'Contractual Necessity'),
            ('legal', 'Legal Obligation'),
            ('vital', 'Vital Interest'),
            ('public', 'Public Interest'),
            ('legitimate', 'Legitimate Interest'),
        ],
        string='Lawful Basis', required=True, default='consent', tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('given', 'Given'),
            ('withdrawn', 'Withdrawn'),
            ('expired', 'Expired'),
        ],
        string='Status', default='given', required=True, tracking=True,
    )
    consent_date = fields.Date(
        string='Consent Date', default=fields.Date.context_today, tracking=True)
    withdrawn_date = fields.Date(string='Withdrawn Date', tracking=True)
    expiry_date = fields.Date(string='Expiry Date')
    source = fields.Char(string='Captured Via', help='Portal form, paper, import, ...')
    notes = fields.Text(string='Notes')

    def action_withdraw(self):
        self.write({
            'state': 'withdrawn',
            'withdrawn_date': fields.Date.context_today(self),
        })

    @api.model
    def _cron_expire_consents(self):
        today = fields.Date.context_today(self)
        expired = self.search([
            ('state', '=', 'given'),
            ('expiry_date', '!=', False),
            ('expiry_date', '<', today),
        ])
        expired.write({'state': 'expired'})
