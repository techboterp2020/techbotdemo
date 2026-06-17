from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UmsKeyDate(models.Model):
    """A key calendar date/window that drives registration and exam windows and
    is published on the portal (FR-CAL-02)."""
    _name = 'ums.key.date'
    _description = 'Academic Key Date'
    _inherit = ['ums.hijri.mixin']
    _order = 'date_start, date'

    name = fields.Char(string='Name', required=True)
    term_id = fields.Many2one(
        'ums.term', string='Term', required=True, ondelete='cascade', index=True)
    date_type = fields.Selection(
        selection=[
            ('registration', 'Registration'),
            ('add_drop', 'Add / Drop'),
            ('withdraw', 'Withdrawal'),
            ('exam', 'Final Exams'),
            ('results', 'Results Publication'),
            ('graduation', 'Graduation'),
            ('holiday', 'Holiday'),
            ('other', 'Other'),
        ],
        string='Type', required=True, default='other',
    )
    # A key date may be a single day (date) or a window (date_start..date_end).
    date = fields.Date(string='Date')
    date_start = fields.Date(string='From')
    date_end = fields.Date(string='To')
    hijri_display = fields.Char(
        string='Hijri', compute='_compute_hijri', store=True)
    show_on_portal = fields.Boolean(string='Show on Portal', default=True)

    @api.depends('date', 'date_start', 'date_end')
    def _compute_hijri(self):
        for kd in self:
            if kd.date_start and kd.date_end:
                kd.hijri_display = '%s — %s' % (
                    kd.hijri_date(kd.date_start), kd.hijri_date(kd.date_end))
            else:
                kd.hijri_display = kd.hijri_date(kd.date or kd.date_start)

    @api.constrains('date', 'date_start', 'date_end')
    def _check_dates(self):
        for kd in self:
            if not kd.date and not kd.date_start:
                raise ValidationError(_(
                    "Key date '%s' needs either a single date or a start date.",
                    kd.name))
            if kd.date_start and kd.date_end and kd.date_start > kd.date_end:
                raise ValidationError(_(
                    "Key date '%s' window must end on/after it starts.", kd.name))
