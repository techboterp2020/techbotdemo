from odoo import api, fields, models


class UmsHold(models.Model):
    """A hold that blocks registration/transcript until cleared (FR-SIS-05)."""
    _name = 'ums.hold'
    _description = 'Student Hold'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    student_id = fields.Many2one(
        'ums.student', string='Student', required=True,
        ondelete='cascade', index=True, tracking=True,
    )
    hold_type = fields.Selection(
        selection=[
            ('financial', 'Financial'),
            ('academic', 'Academic'),
            ('disciplinary', 'Disciplinary'),
            ('library', 'Library'),
            ('admin', 'Administrative'),
        ],
        string='Type', required=True, tracking=True,
    )
    reason = fields.Char(string='Reason', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    blocks_registration = fields.Boolean(string='Blocks Registration', default=True)
    blocks_transcript = fields.Boolean(string='Blocks Transcript', default=True)
    placed_by = fields.Many2one(
        'res.users', string='Placed By', default=lambda self: self.env.user)
    placed_date = fields.Date(
        string='Placed On', default=fields.Date.context_today)
    cleared_by = fields.Many2one('res.users', string='Cleared By')
    cleared_date = fields.Date(string='Cleared On')

    def action_clear(self):
        for hold in self:
            hold.write({
                'active': False,
                'cleared_by': self.env.user.id,
                'cleared_date': fields.Date.context_today(self),
            })
