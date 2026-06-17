from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UmsTerm(models.Model):
    """An academic term/semester with dual Hijri/Gregorian dates (FR-CAL-01)."""
    _name = 'ums.term'
    _description = 'Academic Term'
    _inherit = ['ums.hijri.mixin']
    _order = 'date_start desc'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True, copy=False)
    academic_year_id = fields.Many2one(
        'ums.academic.year', string='Academic Year', required=True,
        ondelete='cascade', index=True,
    )
    term_type = fields.Selection(
        selection=[
            ('fall', 'Fall'),
            ('spring', 'Spring'),
            ('summer', 'Summer'),
        ],
        string='Type', required=True, default='fall',
    )
    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)
    hijri_start = fields.Char(string='Start (Hijri)', compute='_compute_hijri', store=True)
    hijri_end = fields.Char(string='End (Hijri)', compute='_compute_hijri', store=True)

    key_date_ids = fields.One2many('ums.key.date', 'term_id', string='Key Dates')
    section_ids = fields.One2many('ums.section', 'term_id', string='Sections')
    state = fields.Selection(
        selection=[
            ('planning', 'Planning'),
            ('registration', 'Registration Open'),
            ('in_progress', 'In Progress'),
            ('grading', 'Grading'),
            ('closed', 'Closed'),
        ],
        string='Status', default='planning', required=True, tracking=True,
    )
    is_current = fields.Boolean(string='Current Term')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The term code must be unique.'),
    ]

    @api.depends('date_start', 'date_end')
    def _compute_hijri(self):
        for term in self:
            term.hijri_start = term.hijri_date(term.date_start)
            term.hijri_end = term.hijri_date(term.date_end)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for term in self:
            if term.date_start and term.date_end and term.date_start >= term.date_end:
                raise ValidationError(_(
                    "Term '%s' must end after it starts.", term.name))

    @api.model
    def get_current_term(self):
        return self.search([('is_current', '=', True)], limit=1)

    def is_window_open(self, window_type):
        """True if today falls within the given key-date window for this term."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        window = self.key_date_ids.filtered(lambda k: k.date_type == window_type)[:1]
        if not window:
            return False
        start = window.date_start or window.date
        end = window.date_end or window.date
        return bool(start and end and start <= today <= end)
