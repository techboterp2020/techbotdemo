from odoo import fields, models


class UmsStudentStatusHistory(models.Model):
    """Audited record of every student status transition (FR-SIS-07)."""
    _name = 'ums.student.status.history'
    _description = 'Student Status History'
    _order = 'effective_date desc, id desc'

    student_id = fields.Many2one(
        'ums.student', string='Student', required=True,
        ondelete='cascade', index=True,
    )
    old_status = fields.Char(string='From Status')
    new_status = fields.Char(string='To Status', required=True)
    reason = fields.Char(string='Reason')
    effective_date = fields.Date(
        string='Effective Date', default=fields.Date.context_today)
    changed_by = fields.Many2one(
        'res.users', string='Changed By', default=lambda self: self.env.user)
