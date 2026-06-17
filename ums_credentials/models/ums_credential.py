import uuid

from odoo import api, fields, models
from odoo.tools.translate import _


class UmsCredential(models.Model):
    """A verifiable digital credential / badge issued to a student (RFP Phase 2).

    Each credential carries a unique serial and verification token (QR/serial
    lookup). Open Badges (OBv3) assertion JSON can be generated from these
    fields; no blockchain is used.
    """
    _name = 'ums.credential'
    _description = 'Digital Credential'
    _inherit = ['mail.thread']
    _order = 'issue_date desc'

    name = fields.Char(string='Title', required=True, tracking=True)
    serial = fields.Char(
        string='Serial', copy=False, readonly=True,
        default=lambda self: _('New'), index=True)
    verification_token = fields.Char(
        string='Verification Token', copy=False, readonly=True, index=True)
    credential_type = fields.Selection(
        selection=[
            ('degree', 'Degree Certificate'),
            ('badge', 'Open Badge'),
            ('course', 'Course Certificate'),
            ('award', 'Award'),
        ],
        string='Type', required=True, default='badge',
    )
    student_id = fields.Many2one(
        'ums.student', string='Recipient', required=True, ondelete='cascade', index=True)
    program_id = fields.Many2one('ums.program', string='Program')
    description = fields.Text(string='Description')
    issue_date = fields.Date(string='Issued On', default=fields.Date.context_today)
    expiry_date = fields.Date(string='Expires On')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('issued', 'Issued'),
            ('revoked', 'Revoked'),
        ],
        string='Status', default='draft', required=True, tracking=True,
    )

    _sql_constraints = [
        ('serial_uniq', 'unique(serial)', 'The credential serial must be unique.'),
        ('token_uniq', 'unique(verification_token)',
         'The verification token must be unique.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('serial', _('New')) == _('New'):
                vals['serial'] = self.env['ir.sequence'].next_by_code(
                    'ums.credential') or _('New')
            if not vals.get('verification_token'):
                vals['verification_token'] = uuid.uuid4().hex
        return super().create(vals_list)

    def action_issue(self):
        self.write({'state': 'issued'})

    def action_revoke(self):
        self.write({'state': 'revoked'})

    @api.model
    def verify(self, token):
        """Public verification by token/serial (QR resolves here)."""
        credential = self.sudo().search([
            '|', ('verification_token', '=', token), ('serial', '=', token),
        ], limit=1)
        if not credential or credential.state != 'issued':
            return {'valid': False}
        return {
            'valid': True,
            'name': credential.name,
            'recipient': credential.student_id.name,
            'serial': credential.serial,
            'issued': credential.issue_date,
        }

    def to_open_badge(self):
        """Minimal OBv3-style assertion dict for export/interoperability."""
        self.ensure_one()
        return {
            'type': ['VerifiableCredential', 'OpenBadgeCredential'],
            'id': 'urn:uuid:%s' % self.verification_token,
            'name': self.name,
            'issuanceDate': self.issue_date and self.issue_date.isoformat(),
            'credentialSubject': {
                'type': ['AchievementSubject'],
                'name': self.student_id.name,
            },
        }
