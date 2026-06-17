from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UmsAssessmentComponent(models.Model):
    """A weighted assessment component of a section; weights sum to 100%
    (FR-ASM-01)."""
    _name = 'ums.assessment.component'
    _description = 'Assessment Component'
    _order = 'section_id, sequence'

    section_id = fields.Many2one(
        'ums.section', string='Section', required=True,
        ondelete='cascade', index=True,
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Component', required=True)
    component_type = fields.Selection(
        selection=[
            ('quiz', 'Quiz'),
            ('assignment', 'Assignment'),
            ('midterm', 'Midterm'),
            ('project', 'Project'),
            ('participation', 'Participation'),
            ('final', 'Final Exam'),
        ],
        string='Type', default='quiz', required=True,
    )
    weight = fields.Float(string='Weight (%)', required=True)
    max_mark = fields.Float(string='Max Mark', default=100.0)

    @api.constrains('section_id', 'weight')
    def _check_weights(self):
        for section in self.mapped('section_id'):
            total = sum(section.assessment_component_ids.mapped('weight'))
            # Allow partial configuration but block totals over 100%.
            if total > 100.0001:
                raise ValidationError(_(
                    "Assessment weights for section '%(s)s' sum to %(t)s%%, "
                    "which exceeds 100%%.", s=section.display_name, t=total))


class UmsSection(models.Model):
    _inherit = 'ums.section'

    assessment_component_ids = fields.One2many(
        'ums.assessment.component', 'section_id', string='Assessment Components')
    assessment_weight_total = fields.Float(
        string='Weights Total (%)', compute='_compute_weight_total')

    @api.depends('assessment_component_ids.weight')
    def _compute_weight_total(self):
        for section in self:
            section.assessment_weight_total = sum(
                section.assessment_component_ids.mapped('weight'))
