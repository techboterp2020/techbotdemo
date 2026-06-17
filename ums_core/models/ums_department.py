from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class UmsDepartment(models.Model):
    """Academic department — owns programs and courses (FR-ACS-01)."""
    _name = 'ums.department'
    _description = 'Department'
    _inherit = ['ums.bilingual.mixin', 'mail.thread']
    _order = 'name_en'

    code = fields.Char(string='Code', required=True, copy=False, tracking=True)
    college_id = fields.Many2one(
        'ums.college', string='College',
        required=True, ondelete='restrict', tracking=True, index=True,
    )
    institution_id = fields.Many2one(
        'ums.institution', string='Institution',
        related='college_id.institution_id', store=True, index=True,
    )
    head_id = fields.Many2one('res.users', string='Department Head', tracking=True)
    active = fields.Boolean(default=True)

    program_ids = fields.One2many('ums.program', 'department_id', string='Programs')
    course_ids = fields.One2many('ums.course', 'department_id', string='Courses')
    program_count = fields.Integer(compute='_compute_counts', string='Programs')
    course_count = fields.Integer(compute='_compute_counts', string='Courses')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The department code must be unique.'),
    ]

    @api.depends('program_ids', 'course_ids')
    def _compute_counts(self):
        for department in self:
            department.program_count = len(department.program_ids)
            department.course_count = len(department.course_ids)

    @api.ondelete(at_uninstall=False)
    def _unlink_guard_children(self):
        for department in self:
            if department.program_ids or department.course_ids:
                raise UserError(_(
                    "You cannot delete department '%s' while it still has "
                    "programs or courses. Archive it instead.",
                    department.display_name))

    def action_view_programs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Programs'),
            'res_model': 'ums.program',
            'view_mode': 'list,form',
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id},
        }
