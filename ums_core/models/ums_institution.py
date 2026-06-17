from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class UmsInstitution(models.Model):
    """Top of the academic hierarchy: the university / legal entity (FR-ACS-01)."""
    _name = 'ums.institution'
    _description = 'Institution'
    _inherit = ['ums.bilingual.mixin', 'mail.thread']
    _order = 'name_en'

    code = fields.Char(string='Code', required=True, copy=False, tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
    vat = fields.Char(string='VAT Registration Number')
    active = fields.Boolean(default=True)

    college_ids = fields.One2many('ums.college', 'institution_id', string='Colleges')
    college_count = fields.Integer(compute='_compute_counts', string='Colleges')
    department_count = fields.Integer(compute='_compute_counts', string='Departments')
    program_count = fields.Integer(compute='_compute_counts', string='Programs')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The institution code must be unique.'),
    ]

    @api.depends('college_ids', 'college_ids.department_ids',
                 'college_ids.department_ids.program_ids')
    def _compute_counts(self):
        for institution in self:
            colleges = institution.college_ids
            departments = colleges.mapped('department_ids')
            institution.college_count = len(colleges)
            institution.department_count = len(departments)
            institution.program_count = len(departments.mapped('program_ids'))

    @api.ondelete(at_uninstall=False)
    def _unlink_guard_children(self):
        for institution in self:
            if institution.college_ids:
                raise UserError(_(
                    "You cannot delete institution '%s' while it still has "
                    "colleges. Archive it instead.", institution.display_name))

    def action_view_colleges(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Colleges'),
            'res_model': 'ums.college',
            'view_mode': 'list,form',
            'domain': [('institution_id', '=', self.id)],
            'context': {'default_institution_id': self.id},
        }
