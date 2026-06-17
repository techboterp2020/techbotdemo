from odoo import api, fields, models
from odoo.tools.translate import _

# Default absence threshold (%) beyond which a student is barred from the final
# exam — configurable per institutional regulation (FR-LMS-03).
DEFAULT_ABSENCE_BAR_PERCENT = 25.0


class UmsAttendanceSession(models.Model):
    """One class meeting whose attendance is recorded (FR-LMS-03)."""
    _name = 'ums.attendance.session'
    _description = 'Attendance Session'
    _order = 'session_date desc'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    section_id = fields.Many2one(
        'ums.section', string='Section', required=True,
        ondelete='cascade', index=True,
    )
    session_date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)
    hour_from = fields.Float(string='From')
    hour_to = fields.Float(string='To')
    line_ids = fields.One2many(
        'ums.attendance.line', 'session_id', string='Attendance')
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('done', 'Recorded')],
        string='Status', default='draft', required=True,
    )

    @api.depends('section_id.name', 'session_date')
    def _compute_name(self):
        for s in self:
            s.name = '%s — %s' % (s.section_id.name or '?', s.session_date or '')

    def action_load_roster(self):
        """Populate attendance lines from the section roster (bulk capture)."""
        self.ensure_one()
        existing = self.line_ids.mapped('student_id')
        regs = self.section_id.registration_ids.filtered(
            lambda r: r.state in ('registered', 'confirmed'))
        for reg in regs:
            if reg.student_id not in existing:
                self.env['ums.attendance.line'].create({
                    'session_id': self.id,
                    'student_id': reg.student_id.id,
                    'status': 'present',
                })

    def action_mark_done(self):
        self.write({'state': 'done'})


class UmsAttendanceLine(models.Model):
    """A single student's attendance for a session (FR-LMS-03)."""
    _name = 'ums.attendance.line'
    _description = 'Attendance Line'

    session_id = fields.Many2one(
        'ums.attendance.session', string='Session', required=True,
        ondelete='cascade', index=True,
    )
    section_id = fields.Many2one(
        related='session_id.section_id', store=True, string='Section', index=True)
    student_id = fields.Many2one(
        'ums.student', string='Student', required=True, ondelete='cascade', index=True)
    status = fields.Selection(
        selection=[
            ('present', 'Present'),
            ('absent', 'Absent'),
            ('late', 'Late'),
            ('excused', 'Excused'),
        ],
        string='Status', default='present', required=True,
    )

    _sql_constraints = [
        ('session_student_uniq', 'unique(session_id, student_id)',
         'Attendance already recorded for this student in the session.'),
    ]


class UmsSection(models.Model):
    """Attendance roll-up and final-exam bar per student (FR-LMS-03)."""
    _inherit = 'ums.section'

    absence_bar_percent = fields.Float(
        string='Absence Bar (%)', default=DEFAULT_ABSENCE_BAR_PERCENT,
        help='Absence percentage beyond which a student is barred from the '
             'final exam.')

    def get_attendance_percent(self, student):
        """Return ``(attended_pct, absent_pct)`` for a student in this section."""
        self.ensure_one()
        lines = self.env['ums.attendance.line'].search([
            ('section_id', '=', self.id),
            ('student_id', '=', student.id),
        ])
        total = len(lines)
        if not total:
            return 100.0, 0.0
        absent = len(lines.filtered(lambda l: l.status == 'absent'))
        absent_pct = (absent / total) * 100.0
        return 100.0 - absent_pct, absent_pct

    def is_barred_from_final(self, student):
        """True if the student's absence exceeds the section bar (FR-LMS-03)."""
        self.ensure_one()
        _attended, absent_pct = self.get_attendance_percent(student)
        return absent_pct > (self.absence_bar_percent or DEFAULT_ABSENCE_BAR_PERCENT)
