from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

MIN_GRADUATION_CGPA = 2.0


class UmsStudent(models.Model):
    """Degree audit vs study plan (FR-ASM-08)."""
    _inherit = 'ums.student'

    def get_degree_audit(self):
        """Return ``{done, remaining, in_progress, required_ch, completed_ch}``
        comparing completed courses to the active study plan."""
        self.ensure_one()
        plan = self.study_plan_id or self.program_id.study_plan_ids.filtered(
            lambda p: p.state == 'active')[:1]
        required_courses = plan.line_ids.mapped('course_id')
        completed = self.registration_ids.filtered(
            lambda r: r.state == 'completed').mapped('course_id')
        in_progress = self.registration_ids.filtered(
            lambda r: r.state in ('registered', 'confirmed')).mapped('course_id')
        remaining = required_courses - completed - in_progress
        return {
            'done': completed & required_courses,
            'in_progress': in_progress & required_courses,
            'remaining': remaining,
            'required_ch': self.program_id.total_credit_hours,
            'completed_ch': sum((completed & required_courses).mapped('credit_hours')),
        }

    def is_graduation_eligible(self):
        """True if the student has met all graduation requirements (FR-ASM-08)."""
        self.ensure_one()
        audit = self.get_degree_audit()
        if audit['remaining']:
            return False
        if audit['completed_ch'] < audit['required_ch']:
            return False
        gpa = self.env['ums.gpa.record'].search(
            [('student_id', '=', self.id)], order='term_id desc', limit=1)
        if gpa and gpa.cgpa < MIN_GRADUATION_CGPA:
            return False
        return True


class UmsGraduation(models.Model):
    """Graduation processing, clearance and certificate (FR-ASM-09)."""
    _name = 'ums.graduation'
    _description = 'Graduation'
    _inherit = ['ums.hijri.mixin', 'mail.thread']
    _order = 'graduation_date desc'

    student_id = fields.Many2one(
        'ums.student', string='Student', required=True, index=True)
    program_id = fields.Many2one(
        related='student_id.program_id', store=True, string='Program')
    term_id = fields.Many2one('ums.term', string='Graduation Term', required=True)
    graduation_date = fields.Date(string='Graduation Date')
    hijri_graduation = fields.Char(
        string='Graduation Date (Hijri)', compute='_compute_hijri', store=True)
    final_cgpa = fields.Float(string='Final CGPA', digits=(3, 2))
    classification = fields.Char(string='Classification')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('eligible', 'Eligible'),
            ('cleared', 'Cleared'),
            ('graduated', 'Graduated'),
        ],
        string='Status', default='draft', required=True, tracking=True,
    )

    @api.depends('graduation_date')
    def _compute_hijri(self):
        for grad in self:
            grad.hijri_graduation = grad.hijri_date(grad.graduation_date)

    def action_check_eligibility(self):
        for grad in self:
            if not grad.student_id.is_graduation_eligible():
                raise UserError(_(
                    "Student '%s' does not yet meet graduation requirements.",
                    grad.student_id.display_name))
            gpa = self.env['ums.gpa.record'].search(
                [('student_id', '=', grad.student_id.id)],
                order='term_id desc', limit=1)
            grad.write({
                'state': 'eligible',
                'final_cgpa': gpa.cgpa if gpa else 0.0,
                'classification': dict(gpa._fields['classification'].selection).get(
                    gpa.classification) if gpa else False,
            })

    def action_clear(self):
        for grad in self:
            blocking = grad.student_id.hold_ids.filtered(
                lambda h: h.active and h.blocks_transcript)
            if blocking:
                raise UserError(_(
                    "Cannot clear '%s': active holds must be resolved first.",
                    grad.student_id.display_name))
            grad.state = 'cleared'

    def action_graduate(self):
        for grad in self:
            if grad.state != 'cleared':
                raise UserError(_("Clearance is required before graduation."))
            grad.write({
                'state': 'graduated',
                'graduation_date': grad.graduation_date
                or fields.Date.context_today(grad),
            })
            grad.student_id.change_status('graduated', _('Graduated'))
