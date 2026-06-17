from odoo import fields, models


class HrEmployee(models.Model):
    """Faculty profile fields on the standard employee (FR-FAC-01)."""
    _inherit = 'hr.employee'

    is_faculty = fields.Boolean(string='Is Faculty')
    academic_rank = fields.Selection(
        selection=[
            ('lecturer', 'Lecturer'),
            ('assistant', 'Assistant Professor'),
            ('associate', 'Associate Professor'),
            ('professor', 'Professor'),
            ('teaching_assistant', 'Teaching Assistant'),
        ],
        string='Academic Rank',
    )
    qualifications = fields.Text(string='Qualifications')
    specialisation = fields.Char(string='Specialisation')
    ums_department_id = fields.Many2one('ums.department', string='Academic Department')
    max_teaching_load = fields.Integer(
        string='Max Teaching Load (CH)', default=12,
        help='Maximum credit hours per term per workload policy (FR-FAC-02).')
