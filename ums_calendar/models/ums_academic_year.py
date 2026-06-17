from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UmsAcademicYear(models.Model):
    """An academic year grouping its terms (FR-CAL-01)."""
    _name = 'ums.academic.year'
    _description = 'Academic Year'
    _inherit = ['ums.hijri.mixin']
    _order = 'date_start desc'

    name = fields.Char(string='Name', required=True, help='e.g. 2026/2027')
    code = fields.Char(string='Code', required=True, copy=False)
    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)
    hijri_start = fields.Char(string='Start (Hijri)', compute='_compute_hijri', store=True)
    hijri_end = fields.Char(string='End (Hijri)', compute='_compute_hijri', store=True)
    term_ids = fields.One2many('ums.term', 'academic_year_id', string='Terms')
    is_current = fields.Boolean(string='Current Year')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The academic year code must be unique.'),
    ]

    @api.depends('date_start', 'date_end')
    def _compute_hijri(self):
        for year in self:
            year.hijri_start = year.hijri_date(year.date_start)
            year.hijri_end = year.hijri_date(year.date_end)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for year in self:
            if year.date_start and year.date_end and year.date_start >= year.date_end:
                raise ValidationError(_(
                    "Academic year '%s' must end after it starts.", year.name))
