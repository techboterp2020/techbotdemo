from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UmsStudyPlan(models.Model):
    """A versioned curriculum mapping courses to levels/semesters (FR-ACS-05)."""
    _name = 'ums.study.plan'
    _description = 'Study Plan'
    _inherit = ['mail.thread']
    _order = 'program_id, version desc'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    program_id = fields.Many2one(
        'ums.program', string='Program', required=True,
        ondelete='restrict', tracking=True, index=True,
    )
    version = fields.Integer(string='Version', required=True, default=1, tracking=True)
    effective_term = fields.Char(
        string='Effective From (Term)',
        help='Catalog term this study-plan version takes effect from.')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('archived', 'Archived'),
        ],
        string='Status', default='draft', required=True, tracking=True,
    )
    active = fields.Boolean(default=True)

    line_ids = fields.One2many('ums.study.plan.line', 'study_plan_id', string='Courses')

    required_ch = fields.Integer(
        string='Required Credit Hours', compute='_compute_credit_hours', store=True)
    elective_ch = fields.Integer(
        string='Elective Credit Hours', compute='_compute_credit_hours', store=True)
    total_ch = fields.Integer(
        string='Total Credit Hours', compute='_compute_credit_hours', store=True)
    program_total_ch = fields.Integer(
        related='program_id.total_credit_hours', string='Program Total CH')

    _sql_constraints = [
        ('program_version_uniq', 'unique(program_id, version)',
         'A study plan version already exists for this program.'),
        ('version_positive', 'CHECK(version > 0)', 'Version must be positive.'),
    ]

    @api.depends('program_id', 'program_id.name', 'version')
    def _compute_name(self):
        for plan in self:
            program = plan.program_id.display_name or _('Plan')
            plan.name = _('%(program)s — v%(version)s',
                          program=program, version=plan.version)

    @api.depends('line_ids.credit_hours', 'line_ids.is_elective')
    def _compute_credit_hours(self):
        for plan in self:
            required = sum(
                line.credit_hours for line in plan.line_ids if not line.is_elective)
            elective = sum(
                line.credit_hours for line in plan.line_ids if line.is_elective)
            plan.required_ch = required
            plan.elective_ch = elective
            plan.total_ch = required + elective

    @api.constrains('state', 'total_ch', 'program_id')
    def _check_total_credit_hours(self):
        for plan in self:
            if plan.state != 'active':
                continue
            program_total = plan.program_id.total_credit_hours
            if plan.total_ch != program_total:
                raise ValidationError(_(
                    "Study plan '%(plan)s' totals %(total)s credit hours but the "
                    "program requires %(required)s. Adjust the plan before "
                    "activating it.",
                    plan=plan.name, total=plan.total_ch, required=program_total))

    @api.constrains('program_id', 'line_ids')
    def _check_no_duplicate_course(self):
        for plan in self:
            courses = plan.line_ids.mapped('course_id')
            if len(courses) != len(plan.line_ids):
                raise ValidationError(_(
                    "Study plan '%s' lists the same course more than once.",
                    plan.name))

    def action_activate(self):
        for plan in self:
            plan._check_total_credit_hours()
            # Only one active plan per program; supersede the others.
            siblings = plan.program_id.study_plan_ids.filtered(
                lambda p: p.id != plan.id and p.state == 'active')
            siblings.write({'state': 'archived'})
            plan.state = 'active'

    def action_archive_plan(self):
        self.write({'state': 'archived'})

    def action_set_draft(self):
        self.write({'state': 'draft'})

    def action_new_version(self):
        """Clone this plan into a new draft version for revision."""
        self.ensure_one()
        new_version = max(self.program_id.study_plan_ids.mapped('version')) + 1
        copy = self.copy({'version': new_version, 'state': 'draft'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ums.study.plan',
            'res_id': copy.id,
            'view_mode': 'form',
            'target': 'current',
        }


class UmsStudyPlanLine(models.Model):
    """One course slot in a study plan, placed at a level/semester (FR-ACS-05)."""
    _name = 'ums.study.plan.line'
    _description = 'Study Plan Line'
    _order = 'level, semester, sequence'

    study_plan_id = fields.Many2one(
        'ums.study.plan', string='Study Plan', required=True,
        ondelete='cascade', index=True,
    )
    program_id = fields.Many2one(
        related='study_plan_id.program_id', store=True, string='Program')
    sequence = fields.Integer(default=10)
    course_id = fields.Many2one(
        'ums.course', string='Course', required=True, ondelete='restrict')
    credit_hours = fields.Integer(
        related='course_id.credit_hours', store=True, string='Credit Hours')
    level = fields.Integer(string='Level', required=True, default=1)
    semester = fields.Selection(
        selection=[
            ('1', 'Semester 1'),
            ('2', 'Semester 2'),
            ('3', 'Summer'),
        ],
        string='Semester', required=True, default='1',
    )
    is_elective = fields.Boolean(string='Elective', default=False)
