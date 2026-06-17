from odoo import fields, models


class UmsAdvisingNote(models.Model):
    """Advisor note attached to a student (FR-SIS-04)."""
    _name = 'ums.advising.note'
    _description = 'Advising Note'
    _order = 'note_date desc'

    student_id = fields.Many2one(
        'ums.student', string='Student', required=True,
        ondelete='cascade', index=True,
    )
    advisor_id = fields.Many2one(
        'res.users', string='Advisor', default=lambda self: self.env.user)
    note_date = fields.Date(string='Date', default=fields.Date.context_today)
    subject = fields.Char(string='Subject', required=True)
    note = fields.Text(string='Note')
