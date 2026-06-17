from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UmsLearningOutcome(models.Model):
    """Course (CLO) or Program (PLO) learning outcome, with CLO→PLO mapping for
    accreditation (FR-ACS-06)."""
    _name = 'ums.learning.outcome'
    _description = 'Learning Outcome'
    _order = 'outcome_type, code'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Statement', required=True, translate=True)
    outcome_type = fields.Selection(
        selection=[
            ('clo', 'Course Learning Outcome'),
            ('plo', 'Program Learning Outcome'),
        ],
        string='Type', required=True, default='clo',
    )
    course_id = fields.Many2one(
        'ums.course', string='Course', ondelete='cascade', index=True)
    program_id = fields.Many2one(
        'ums.program', string='Program', ondelete='cascade', index=True)

    # CLO → PLO mapping matrix (exportable for accreditation).
    mapped_plo_ids = fields.Many2many(
        'ums.learning.outcome', 'ums_clo_plo_rel', 'clo_id', 'plo_id',
        string='Mapped Program Outcomes',
        domain=[('outcome_type', '=', 'plo')],
    )

    @api.constrains('outcome_type', 'course_id', 'program_id')
    def _check_owner(self):
        for outcome in self:
            if outcome.outcome_type == 'clo' and not outcome.course_id:
                raise ValidationError(_(
                    "A Course Learning Outcome must be linked to a course."))
            if outcome.outcome_type == 'plo' and not outcome.program_id:
                raise ValidationError(_(
                    "A Program Learning Outcome must be linked to a program."))

    @api.constrains('outcome_type', 'mapped_plo_ids')
    def _check_mapping_only_for_clo(self):
        for outcome in self:
            if outcome.outcome_type == 'plo' and outcome.mapped_plo_ids:
                raise ValidationError(_(
                    "Only Course Learning Outcomes can be mapped to Program "
                    "Learning Outcomes."))
