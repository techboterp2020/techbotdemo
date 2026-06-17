from odoo import api, fields, models


class UmsRubric(models.Model):
    """A grading rubric whose criteria feed continuous assessment (FR-LMS-02)."""
    _name = 'ums.rubric'
    _description = 'Grading Rubric'

    name = fields.Char(string='Name', required=True)
    criterion_ids = fields.One2many(
        'ums.rubric.criterion', 'rubric_id', string='Criteria')
    max_score = fields.Float(string='Maximum Score', compute='_compute_max', store=True)

    @api.depends('criterion_ids.max_points')
    def _compute_max(self):
        for rubric in self:
            rubric.max_score = sum(rubric.criterion_ids.mapped('max_points'))


class UmsRubricCriterion(models.Model):
    _name = 'ums.rubric.criterion'
    _description = 'Rubric Criterion'
    _order = 'sequence, id'

    rubric_id = fields.Many2one(
        'ums.rubric', string='Rubric', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Criterion', required=True)
    max_points = fields.Float(string='Max Points', required=True, default=10.0)
