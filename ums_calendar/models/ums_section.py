from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UmsSection(models.Model):
    """A course offering for a given term, with a timetable, room and
    instructor; clash detection prevents double-booking (FR-CAL-04)."""
    _name = 'ums.section'
    _description = 'Course Section'
    _inherit = ['mail.thread']
    _order = 'term_id, course_id, code'

    name = fields.Char(string='Section', compute='_compute_name', store=True)
    code = fields.Char(string='Section No.', required=True, default='01')
    course_id = fields.Many2one(
        'ums.course', string='Course', required=True,
        ondelete='restrict', index=True, tracking=True,
    )
    term_id = fields.Many2one(
        'ums.term', string='Term', required=True,
        ondelete='restrict', index=True, tracking=True,
    )
    instructor_id = fields.Many2one(
        'res.users', string='Instructor', tracking=True, index=True)
    room_id = fields.Many2one('ums.room', string='Room', tracking=True)
    timeslot_ids = fields.Many2many('ums.timeslot', string='Time Slots')

    capacity = fields.Integer(string='Capacity', required=True, default=30)
    enrolled_count = fields.Integer(
        string='Enrolled', compute='_compute_enrolled', store=False)
    seats_available = fields.Integer(
        string='Seats Available', compute='_compute_enrolled', store=False)
    gender = fields.Selection(
        selection=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('mixed', 'Mixed'),
        ],
        string='Gender', default='mixed',
    )
    credit_hours = fields.Integer(
        related='course_id.credit_hours', store=True, string='Credit Hours')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('open', 'Open'),
            ('closed', 'Closed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status', default='draft', required=True, tracking=True,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('course_term_code_uniq', 'unique(course_id, term_id, code)',
         'This section number already exists for the course in this term.'),
        ('capacity_positive', 'CHECK(capacity > 0)',
         'Capacity must be greater than zero.'),
    ]

    @api.depends('course_id.code', 'code', 'term_id.code')
    def _compute_name(self):
        for section in self:
            course = section.course_id.code or '?'
            term = section.term_id.code or '?'
            section.name = '%s-%s (%s)' % (course, section.code, term)

    def _compute_enrolled(self):
        # Overridden in ums_sis once registration exists; safe default here.
        reg_model = self.env.get('ums.registration')
        for section in self:
            count = 0
            if reg_model is not None:
                count = reg_model.search_count([
                    ('section_id', '=', section.id),
                    ('state', 'in', ('registered', 'confirmed')),
                ])
            section.enrolled_count = count
            section.seats_available = max(section.capacity - count, 0)

    @api.constrains('timeslot_ids', 'room_id', 'instructor_id', 'term_id', 'state')
    def _check_clashes(self):
        for section in self:
            if section.state == 'cancelled' or not section.timeslot_ids:
                continue
            section._check_room_clash()
            section._check_instructor_clash()

    def _conflicting_sections(self, field):
        """Other active sections in the same term sharing the given resource."""
        self.ensure_one()
        value = self[field]
        if not value:
            return self.env['ums.section']
        return self.search([
            ('id', '!=', self.id),
            ('term_id', '=', self.term_id.id),
            (field, '=', value.id),
            ('state', '!=', 'cancelled'),
        ])

    def _has_slot_overlap(self, other):
        for a in self.timeslot_ids:
            for b in other.timeslot_ids:
                if a.overlaps(b):
                    return True
        return False

    def _check_room_clash(self):
        for other in self._conflicting_sections('room_id'):
            if self._has_slot_overlap(other):
                raise ValidationError(_(
                    "Room '%(room)s' is double-booked: sections %(a)s and "
                    "%(b)s overlap in time.",
                    room=self.room_id.display_name,
                    a=self.name, b=other.name))

    def _check_instructor_clash(self):
        for other in self._conflicting_sections('instructor_id'):
            if self._has_slot_overlap(other):
                raise ValidationError(_(
                    "Instructor '%(inst)s' is double-booked: sections %(a)s "
                    "and %(b)s overlap in time.",
                    inst=self.instructor_id.display_name,
                    a=self.name, b=other.name))

    def action_open(self):
        self.write({'state': 'open'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
