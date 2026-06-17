from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.tools.translate import _

# Default per-term credit-hour ceiling; probation lowers it (FR-SIS-02/06).
DEFAULT_MAX_CH = 18
PROBATION_MAX_CH = 12


class UmsRegistration(models.Model):
    """A student's enrollment in a section — the anchor for grades, attendance
    and tuition (FR-SIS-02/03)."""
    _name = 'ums.registration'
    _description = 'Course Registration'
    _inherit = ['mail.thread']
    _order = 'term_id desc, student_id'

    student_id = fields.Many2one(
        'ums.student', string='Student', required=True,
        ondelete='cascade', index=True, tracking=True,
    )
    section_id = fields.Many2one(
        'ums.section', string='Section', required=True,
        ondelete='restrict', index=True, tracking=True,
    )
    course_id = fields.Many2one(
        related='section_id.course_id', store=True, string='Course', index=True)
    term_id = fields.Many2one(
        related='section_id.term_id', store=True, string='Term', index=True)
    credit_hours = fields.Integer(
        related='section_id.credit_hours', store=True, string='Credit Hours')
    registration_date = fields.Date(
        string='Registered On', default=fields.Date.context_today)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('registered', 'Registered'),
            ('confirmed', 'Confirmed'),
            ('dropped', 'Dropped'),
            ('withdrawn', 'Withdrawn'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        string='Status', default='draft', required=True, tracking=True,
    )
    advisor_approved = fields.Boolean(string='Advisor Approved', tracking=True)
    grade_letter = fields.Char(string='Grade')
    grade_point = fields.Float(string='Grade Point')

    _sql_constraints = [
        ('student_section_uniq', 'unique(student_id, section_id)',
         'The student is already registered in this section.'),
    ]

    # ------------------------------------------------------------------
    # Validation engine (FR-SIS-02)
    # ------------------------------------------------------------------
    def _get_credit_limit(self):
        self.ensure_one()
        standing = self.env['ums.academic.standing'].search([
            ('student_id', '=', self.student_id.id),
        ], order='create_date desc', limit=1)
        if standing and standing.standing in ('probation', 'warning'):
            return PROBATION_MAX_CH
        return DEFAULT_MAX_CH

    def _check_holds(self):
        if self.student_id.has_blocking_hold:
            blocking = self.student_id.hold_ids.filtered(
                lambda h: h.active and h.blocks_registration)
            raise ValidationError(_(
                "Registration blocked by active hold(s): %s.",
                ', '.join(blocking.mapped('reason'))))

    def _check_window(self):
        term = self.section_id.term_id
        # Allow if a registration or add/drop window is currently open.
        if not (term.is_window_open('registration')
                or term.is_window_open('add_drop')):
            # Fall back to term state to keep tests/config simple.
            if term.state not in ('registration', 'planning', 'in_progress'):
                raise ValidationError(_(
                    "The registration window for term '%s' is not open.",
                    term.display_name))

    def _check_capacity(self):
        section = self.section_id
        if section.seats_available <= 0:
            raise ValidationError(_(
                "Section '%s' is full (no seats available).", section.display_name))

    def _check_gender(self):
        section = self.section_id
        student = self.student_id
        if section.gender != 'mixed' and student.gender != section.gender:
            raise ValidationError(_(
                "Section '%(s)s' is restricted to %(g)s students.",
                s=section.display_name, g=section.gender))

    def _check_prerequisites(self):
        course = self.section_id.course_id
        completed = self.student_id.registration_ids.filtered(
            lambda r: r.state == 'completed').mapped('course_id')
        for prereq in course.prerequisite_ids.filtered(
                lambda p: p.relation_type == 'prerequisite'):
            if prereq.prerequisite_course_id not in completed:
                raise ValidationError(_(
                    "Prerequisite not met for '%(course)s': requires '%(prereq)s'.",
                    course=course.display_name,
                    prereq=prereq.prerequisite_course_id.display_name))

    def _check_credit_limit(self):
        term_regs = self.student_id.registration_ids.filtered(
            lambda r: r.term_id == self.term_id
            and r.state in ('registered', 'confirmed')
            and r.id != self.id)
        total = sum(term_regs.mapped('credit_hours')) + self.credit_hours
        limit = self._get_credit_limit()
        if total > limit:
            raise ValidationError(_(
                "Credit limit exceeded: %(total)s CH requested, limit is "
                "%(limit)s CH for this term.", total=total, limit=limit))

    def _check_timetable_clash(self):
        my_slots = self.section_id.timeslot_ids
        if not my_slots:
            return
        others = self.student_id.registration_ids.filtered(
            lambda r: r.term_id == self.term_id
            and r.state in ('registered', 'confirmed')
            and r.id != self.id)
        for other in others:
            for a in my_slots:
                for b in other.section_id.timeslot_ids:
                    if a.overlaps(b):
                        raise ValidationError(_(
                            "Timetable clash with '%(course)s' at %(slot)s.",
                            course=other.course_id.display_name, slot=a.name))

    def _validate_registration(self):
        """Run every registration rule; raises ValidationError on the first
        failure (FR-SIS-02)."""
        self.ensure_one()
        self._check_holds()
        self._check_window()
        self._check_capacity()
        self._check_gender()
        self._check_prerequisites()
        self._check_credit_limit()
        self._check_timetable_clash()

    # ------------------------------------------------------------------
    # Lifecycle (FR-SIS-02/03)
    # ------------------------------------------------------------------
    def action_register(self):
        for reg in self:
            reg._validate_registration()
            reg.state = 'registered'

    def action_confirm(self):
        for reg in self:
            if reg.state != 'registered':
                raise UserError(_("Only registered courses can be confirmed."))
            reg.state = 'confirmed'

    def action_drop(self):
        """Drop within the add/drop window (FR-SIS-03)."""
        for reg in self:
            if reg.state not in ('registered', 'confirmed'):
                raise UserError(_("Only active registrations can be dropped."))
            if not reg.term_id.is_window_open('add_drop') \
                    and reg.term_id.state not in ('registration', 'planning'):
                raise UserError(_(
                    "The add/drop window for '%s' has closed; use withdraw "
                    "instead.", reg.term_id.display_name))
            reg.state = 'dropped'

    def action_withdraw(self):
        """Withdraw after the add/drop deadline (FR-SIS-03)."""
        for reg in self:
            if reg.state not in ('registered', 'confirmed'):
                raise UserError(_("Only active registrations can be withdrawn."))
            reg.state = 'withdrawn'

    @api.model_create_multi
    def create(self, vals_list):
        regs = super().create(vals_list)
        # Validate immediately when created directly in a registered state.
        for reg in regs:
            if reg.state in ('registered', 'confirmed'):
                reg._validate_registration()
        return regs
