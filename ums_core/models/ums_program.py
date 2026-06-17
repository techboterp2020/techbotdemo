from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _


class UmsProgram(models.Model):
    """Degree program — the spine admissions, registration and grading bind to
    (FR-ACS-02)."""
    _name = 'ums.program'
    _description = 'Program'
    _inherit = ['ums.bilingual.mixin', 'mail.thread']
    _order = 'name_en'

    code = fields.Char(string='Code', required=True, copy=False, tracking=True)
    department_id = fields.Many2one(
        'ums.department', string='Department',
        required=True, ondelete='restrict', tracking=True, index=True,
    )
    college_id = fields.Many2one(
        'ums.college', related='department_id.college_id',
        store=True, string='College', index=True,
    )
    institution_id = fields.Many2one(
        'ums.institution', related='department_id.institution_id',
        store=True, string='Institution', index=True,
    )

    degree_type = fields.Selection(
        selection=[
            ('diploma', 'Diploma'),
            ('associate', 'Associate'),
            ('bachelor', 'Bachelor'),
            ('higher_diploma', 'Higher Diploma'),
            ('master', 'Master'),
            ('phd', 'Doctorate (PhD)'),
        ],
        string='Degree Type', required=True, default='bachelor', tracking=True,
    )
    duration_years = fields.Float(
        string='Duration (Years)', required=True, default=4.0,
        help='Nominal program length in academic years.',
    )
    total_credit_hours = fields.Integer(
        string='Total Credit Hours', required=True, tracking=True,
        help='Total credit hours required to graduate from this program.',
    )
    language = fields.Selection(
        selection=[
            ('ar', 'Arabic'),
            ('en', 'English'),
            ('bilingual', 'Bilingual (AR/EN)'),
        ],
        string='Language of Instruction', required=True, default='ar',
    )
    grade_scheme_id = fields.Many2one(
        'ums.grade.scheme', string='Grading Scheme', tracking=True,
        help='Grading scheme applied to this program. Defaults to the Saudi 5.0 '
             'scheme (FR-ACS-07).',
    )
    active = fields.Boolean(default=True)

    study_plan_ids = fields.One2many('ums.study.plan', 'program_id', string='Study Plans')
    learning_outcome_ids = fields.One2many(
        'ums.learning.outcome', 'program_id', string='Program Learning Outcomes',
        domain=[('outcome_type', '=', 'plo')],
    )
    study_plan_count = fields.Integer(compute='_compute_counts', string='Study Plans')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The program code must be unique.'),
        ('total_ch_positive', 'CHECK(total_credit_hours > 0)',
         'Total credit hours must be greater than zero.'),
        ('duration_positive', 'CHECK(duration_years > 0)',
         'Duration must be greater than zero.'),
    ]

    @api.depends('study_plan_ids')
    def _compute_counts(self):
        for program in self:
            program.study_plan_count = len(program.study_plan_ids)

    @api.constrains('grade_scheme_id')
    def _check_grade_scheme(self):
        for program in self:
            scheme = program.grade_scheme_id
            if scheme and not scheme.active:
                raise ValidationError(_(
                    "The grading scheme '%s' is archived and cannot be assigned "
                    "to program '%s'.", scheme.display_name, program.display_name))

    @api.model_create_multi
    def create(self, vals_list):
        default_scheme = self.env.ref(
            'ums_core.grade_scheme_saudi_5', raise_if_not_found=False)
        for vals in vals_list:
            if not vals.get('grade_scheme_id') and default_scheme:
                vals['grade_scheme_id'] = default_scheme.id
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _unlink_guard_children(self):
        for program in self:
            if program.study_plan_ids:
                raise UserError(_(
                    "You cannot delete program '%s' while it still has study "
                    "plans. Archive it instead.", program.display_name))

    def action_view_study_plans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Study Plans'),
            'res_model': 'ums.study.plan',
            'view_mode': 'list,form',
            'domain': [('program_id', '=', self.id)],
            'context': {'default_program_id': self.id},
        }
