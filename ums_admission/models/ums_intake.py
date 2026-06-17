from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UmsIntake(models.Model):
    """An admission intake (e.g. Fall 2026) with per-program seat & gender
    quotas (FR-ADM-02/05)."""
    _name = 'ums.intake'
    _description = 'Admission Intake'
    _order = 'date_open desc'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True, copy=False)
    term_id = fields.Many2one('ums.term', string='Entry Term', required=True)
    date_open = fields.Date(string='Opens On', required=True)
    date_close = fields.Date(string='Closes On', required=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('open', 'Open'),
            ('closed', 'Closed'),
        ],
        string='Status', default='draft', required=True,
    )
    quota_ids = fields.One2many('ums.seat.quota', 'intake_id', string='Seat Quotas')
    application_fee = fields.Monetary(string='Application Fee')
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The intake code must be unique.'),
    ]

    @api.constrains('date_open', 'date_close')
    def _check_dates(self):
        for intake in self:
            if intake.date_open and intake.date_close \
                    and intake.date_open > intake.date_close:
                raise ValidationError(_(
                    "Intake '%s' must close on/after it opens.", intake.name))

    def is_open(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        return (self.state == 'open'
                and self.date_open <= today <= self.date_close)


class UmsSeatQuota(models.Model):
    """Seat capacity per program (and gender) for an intake (FR-ADM-05)."""
    _name = 'ums.seat.quota'
    _description = 'Seat Quota'

    intake_id = fields.Many2one(
        'ums.intake', string='Intake', required=True, ondelete='cascade')
    program_id = fields.Many2one('ums.program', string='Program', required=True)
    gender = fields.Selection(
        selection=[('male', 'Male'), ('female', 'Female'), ('any', 'Any')],
        string='Gender', default='any', required=True,
    )
    seats = fields.Integer(string='Seats', required=True, default=0)
    seats_filled = fields.Integer(
        string='Filled', compute='_compute_seats_filled')
    seats_available = fields.Integer(
        string='Available', compute='_compute_seats_filled')

    def _compute_seats_filled(self):
        Application = self.env['ums.application']
        for quota in self:
            domain = [
                ('intake_id', '=', quota.intake_id.id),
                ('program_id', '=', quota.program_id.id),
                ('state', 'in', ('accepted', 'enrolled')),
            ]
            if quota.gender != 'any':
                domain.append(('gender', '=', quota.gender))
            filled = Application.search_count(domain)
            quota.seats_filled = filled
            quota.seats_available = max(quota.seats - filled, 0)
