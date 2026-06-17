from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _


class UmsGradeEntry(models.Model):
    """Faculty grade entry for a registration with draft/submit/approve and an
    audited grade-change history (FR-ASM-02/03/10)."""
    _name = 'ums.grade.entry'
    _description = 'Grade Entry'
    _inherit = ['mail.thread']
    _order = 'term_id desc, student_id'

    registration_id = fields.Many2one(
        'ums.registration', string='Registration', required=True,
        ondelete='cascade', index=True,
    )
    student_id = fields.Many2one(
        related='registration_id.student_id', store=True, string='Student', index=True)
    section_id = fields.Many2one(
        related='registration_id.section_id', store=True, string='Section')
    course_id = fields.Many2one(
        related='registration_id.course_id', store=True, string='Course')
    term_id = fields.Many2one(
        related='registration_id.term_id', store=True, string='Term', index=True)
    credit_hours = fields.Integer(
        related='registration_id.credit_hours', store=True, string='CH')

    total_mark = fields.Float(string='Total Mark', tracking=True)
    grade_letter = fields.Char(string='Letter', compute='_compute_grade', store=True)
    grade_point = fields.Float(string='Grade Point', compute='_compute_grade', store=True)
    is_fail = fields.Boolean(compute='_compute_grade', store=True)
    special_grade = fields.Selection(
        selection=[
            ('ic', 'Incomplete (IC)'),
            ('w', 'Withdrawn (W)'),
            ('ip', 'In Progress (IP)'),
        ],
        string='Special Grade', help='Overrides the numeric grade where set.')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
        ],
        string='Status', default='draft', required=True, tracking=True,
    )

    _sql_constraints = [
        ('registration_uniq', 'unique(registration_id)',
         'A grade entry already exists for this registration.'),
    ]

    @api.depends('total_mark', 'special_grade', 'student_id.program_id.grade_scheme_id')
    def _compute_grade(self):
        for entry in self:
            if entry.special_grade or entry.total_mark is False:
                entry.grade_letter = (entry.special_grade or '').upper() or False
                entry.grade_point = 0.0
                entry.is_fail = False
                continue
            scheme = entry.student_id.program_id.grade_scheme_id
            if not scheme:
                entry.grade_letter = False
                entry.grade_point = 0.0
                entry.is_fail = False
                continue
            letter, point, is_fail = scheme.grade_for_mark(entry.total_mark)
            entry.grade_letter = letter
            entry.grade_point = point
            entry.is_fail = is_fail

    @api.constrains('total_mark')
    def _check_mark_range(self):
        for entry in self:
            if entry.total_mark and not (0 <= entry.total_mark <= 100):
                raise ValidationError(_("Total mark must be between 0 and 100."))

    def action_submit(self):
        for entry in self:
            if entry.special_grade != 'ip' and entry.total_mark is False:
                raise UserError(_("Enter a mark before submitting."))
            entry.state = 'submitted'

    def action_approve(self):
        """Post the grade: update registration and recompute GPA (FR-ASM-04)."""
        for entry in self:
            if entry.state != 'submitted':
                raise UserError(_("Only submitted grades can be approved."))
            entry.state = 'approved'
            reg = entry.registration_id
            if entry.special_grade == 'w':
                reg.write({'state': 'withdrawn'})
            elif entry.special_grade in ('ic', 'ip'):
                reg.write({'grade_letter': entry.grade_letter})
            else:
                reg.write({
                    'state': 'failed' if entry.is_fail else 'completed',
                    'grade_letter': entry.grade_letter,
                    'grade_point': entry.grade_point,
                })
            self.env['ums.gpa.record'].recompute_for_student(
                entry.student_id, entry.term_id)

    def action_reset_draft(self):
        """Post-submission grade change requires returning to draft (FR-ASM-10)."""
        self.write({'state': 'draft'})

    def counts_in_gpa(self):
        """True if this entry contributes to GPA (graded, non-special)."""
        self.ensure_one()
        return bool(
            self.state == 'approved' and not self.special_grade
            and self.grade_letter)
