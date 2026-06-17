from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class UmsCollege(models.Model):
    """College / Faculty — second level of the hierarchy (FR-ACS-01)."""
    _name = 'ums.college'
    _description = 'College'
    _inherit = ['ums.bilingual.mixin', 'mail.thread']
    _order = 'name_en'

    code = fields.Char(string='Code', required=True, copy=False, tracking=True)
    institution_id = fields.Many2one(
        'ums.institution', string='Institution',
        required=True, ondelete='restrict', tracking=True, index=True,
    )
    dean_id = fields.Many2one('res.users', string='Dean', tracking=True)
    active = fields.Boolean(default=True)

    department_ids = fields.One2many('ums.department', 'college_id', string='Departments')
    department_count = fields.Integer(compute='_compute_counts', string='Departments')
    program_count = fields.Integer(compute='_compute_counts', string='Programs')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The college code must be unique.'),
    ]

    @api.depends('department_ids', 'department_ids.program_ids')
    def _compute_counts(self):
        for college in self:
            college.department_count = len(college.department_ids)
            college.program_count = len(college.department_ids.mapped('program_ids'))

    @api.ondelete(at_uninstall=False)
    def _unlink_guard_children(self):
        for college in self:
            if college.department_ids:
                raise UserError(_(
                    "You cannot delete college '%s' while it still has "
                    "departments. Archive it instead.", college.display_name))

    def action_view_departments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Departments'),
            'res_model': 'ums.department',
            'view_mode': 'list,form',
            'domain': [('college_id', '=', self.id)],
            'context': {'default_college_id': self.id},
        }
