from odoo import fields, models


class UmsApplicationDocument(models.Model):
    """An uploaded application document with a verification workflow (FR-ADM-07)."""
    _name = 'ums.application.document'
    _description = 'Application Document'

    application_id = fields.Many2one(
        'ums.application', string='Application', required=True,
        ondelete='cascade', index=True,
    )
    name = fields.Char(string='Document', required=True)
    doc_type = fields.Selection(
        selection=[
            ('national_id', 'National ID / Iqama'),
            ('hs_certificate', 'High-School Certificate'),
            ('transcript', 'Transcript'),
            ('qiyas', 'Qiyas Result'),
            ('photo', 'Photograph'),
            ('other', 'Other'),
        ],
        string='Type', required=True, default='other',
    )
    required = fields.Boolean(string='Required', default=True)
    attachment = fields.Binary(string='File', attachment=True)
    filename = fields.Char(string='Filename')
    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('verified', 'Verified'),
            ('rejected', 'Rejected'),
        ],
        string='Status', default='pending', required=True,
    )
    authenticity_flag = fields.Boolean(
        string='Authenticity Concern',
        help='Flag raised when a document appears altered or unverifiable.')
    verified_by = fields.Many2one('res.users', string='Verified By')
    note = fields.Char(string='Note')

    def action_verify(self):
        self.write({'state': 'verified', 'verified_by': self.env.user.id})

    def action_reject(self):
        self.write({'state': 'rejected', 'verified_by': self.env.user.id})
