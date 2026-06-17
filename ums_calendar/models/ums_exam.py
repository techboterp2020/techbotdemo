from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UmsExamSchedule(models.Model):
    """A scheduled final exam for a section, avoiding student/room clashes and
    allocating invigilators (FR-CAL-05)."""
    _name = 'ums.exam.schedule'
    _description = 'Exam Schedule'
    _inherit = ['ums.hijri.mixin', 'mail.thread']
    _order = 'exam_date, hour_from'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    section_id = fields.Many2one(
        'ums.section', string='Section', required=True,
        ondelete='cascade', index=True,
    )
    course_id = fields.Many2one(
        related='section_id.course_id', store=True, string='Course')
    term_id = fields.Many2one(
        related='section_id.term_id', store=True, string='Term', index=True)
    exam_type = fields.Selection(
        selection=[
            ('midterm', 'Midterm'),
            ('final', 'Final'),
            ('makeup', 'Make-up'),
        ],
        string='Exam Type', required=True, default='final',
    )
    exam_date = fields.Date(string='Date', required=True)
    hijri_display = fields.Char(
        string='Date (Hijri)', compute='_compute_hijri', store=True)
    hour_from = fields.Float(string='From', required=True, default=9.0)
    hour_to = fields.Float(string='To', required=True, default=11.0)
    room_id = fields.Many2one('ums.room', string='Room')
    invigilator_ids = fields.Many2many('res.users', string='Invigilators')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled'),
            ('done', 'Done'),
        ],
        string='Status', default='draft', required=True, tracking=True,
    )

    @api.depends('course_id.code', 'exam_type', 'exam_date')
    def _compute_name(self):
        for exam in self:
            exam.name = '%s %s %s' % (
                exam.course_id.code or '?',
                dict(self._fields['exam_type'].selection).get(exam.exam_type, ''),
                exam.exam_date or '')

    @api.depends('exam_date')
    def _compute_hijri(self):
        for exam in self:
            exam.hijri_display = exam.dual_date(exam.exam_date)

    @api.constrains('hour_from', 'hour_to')
    def _check_hours(self):
        for exam in self:
            if not (0 <= exam.hour_from < exam.hour_to <= 24):
                raise ValidationError(_(
                    "Exam '%s' hours must satisfy 0 ≤ from < to ≤ 24.", exam.name))

    @api.constrains('exam_date', 'hour_from', 'hour_to', 'room_id', 'state')
    def _check_room_clash(self):
        for exam in self:
            if exam.state == 'draft' or not exam.room_id:
                continue
            others = self.search([
                ('id', '!=', exam.id),
                ('room_id', '=', exam.room_id.id),
                ('exam_date', '=', exam.exam_date),
                ('state', '!=', 'draft'),
            ])
            for other in others:
                if exam.hour_from < other.hour_to and other.hour_from < exam.hour_to:
                    raise ValidationError(_(
                        "Room '%(room)s' is double-booked for exams '%(a)s' and "
                        "'%(b)s'.",
                        room=exam.room_id.display_name, a=exam.name, b=other.name))

    def get_student_clashes(self):
        """Return exams that clash for at least one shared student.

        Requires ums_sis (registrations). Returns an empty recordset when SIS is
        not installed.
        """
        self.ensure_one()
        reg_model = self.env.get('ums.registration')
        if reg_model is None:
            return self.env['ums.exam.schedule']
        my_students = reg_model.search([
            ('section_id', '=', self.section_id.id),
            ('state', 'in', ('registered', 'confirmed')),
        ]).mapped('student_id')
        if not my_students:
            return self.env['ums.exam.schedule']
        same_day = self.search([
            ('id', '!=', self.id),
            ('exam_date', '=', self.exam_date),
            ('state', '!=', 'draft'),
        ])
        clashing = self.env['ums.exam.schedule']
        for other in same_day:
            if not (self.hour_from < other.hour_to and other.hour_from < self.hour_to):
                continue
            other_students = reg_model.search([
                ('section_id', '=', other.section_id.id),
                ('state', 'in', ('registered', 'confirmed')),
            ]).mapped('student_id')
            if my_students & other_students:
                clashing |= other
        return clashing

    def action_schedule(self):
        for exam in self:
            clashes = exam.get_student_clashes()
            if clashes:
                raise ValidationError(_(
                    "Cannot schedule '%(exam)s': student clash with %(others)s.",
                    exam=exam.name,
                    others=', '.join(clashes.mapped('name'))))
            exam.state = 'scheduled'
