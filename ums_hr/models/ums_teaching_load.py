from odoo import api, fields, models


class UmsTeachingLoad(models.Model):
    """A faculty member's teaching load for a term, with workload vs policy
    (FR-FAC-02)."""
    _name = 'ums.teaching.load'
    _description = 'Teaching Load'
    _order = 'term_id desc, employee_id'

    employee_id = fields.Many2one(
        'hr.employee', string='Faculty', required=True,
        domain=[('is_faculty', '=', True)], index=True,
    )
    term_id = fields.Many2one('ums.term', string='Term', required=True, index=True)
    section_ids = fields.Many2many('ums.section', string='Sections')
    total_credit_hours = fields.Integer(
        string='Assigned CH', compute='_compute_load', store=True)
    max_load = fields.Integer(
        related='employee_id.max_teaching_load', string='Max CH')
    is_overloaded = fields.Boolean(
        string='Overloaded', compute='_compute_load', store=True)

    _sql_constraints = [
        ('employee_term_uniq', 'unique(employee_id, term_id)',
         'A teaching-load record already exists for this faculty and term.'),
    ]

    @api.depends('section_ids.credit_hours', 'employee_id.max_teaching_load')
    def _compute_load(self):
        for load in self:
            total = sum(load.section_ids.mapped('credit_hours'))
            load.total_credit_hours = total
            load.is_overloaded = total > (load.employee_id.max_teaching_load or 0)
