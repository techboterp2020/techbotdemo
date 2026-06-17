from odoo import api, fields, models


class UmsPathway(models.Model):
    """A curated learning pathway — an ordered set of steps a learner follows
    (RFP Phase 2 LXP)."""
    _name = 'ums.pathway'
    _description = 'Learning Pathway'
    _order = 'name'

    name = fields.Char(string='Title', required=True)
    description = fields.Text(string='Description')
    program_id = fields.Many2one('ums.program', string='Program')
    level = fields.Integer(string='Target Level')
    step_ids = fields.One2many('ums.pathway.step', 'pathway_id', string='Steps')
    step_count = fields.Integer(compute='_compute_step_count')
    active = fields.Boolean(default=True)

    @api.depends('step_ids')
    def _compute_step_count(self):
        for pathway in self:
            pathway.step_count = len(pathway.step_ids)

    def recommended_for(self, student):
        """Return pathways matching a student's program/level (personalization)."""
        return self.search([
            '|', ('program_id', '=', student.program_id.id), ('program_id', '=', False),
            '|', ('level', '=', student.level), ('level', '=', 0),
        ])


class UmsPathwayStep(models.Model):
    _name = 'ums.pathway.step'
    _description = 'Learning Pathway Step'
    _order = 'pathway_id, sequence'

    pathway_id = fields.Many2one(
        'ums.pathway', string='Pathway', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Step', required=True)
    course_id = fields.Many2one('ums.course', string='Linked Course')
    content_url = fields.Char(string='Content URL')
    estimated_hours = fields.Float(string='Estimated Hours')
