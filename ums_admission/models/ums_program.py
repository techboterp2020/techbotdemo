from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UmsProgram(models.Model):
    """Per-program admission weights for the composite entrance score
    (FR-ADM-03). Weights must sum to 1.0."""
    _inherit = 'ums.program'

    weight_qiyas = fields.Float(string='Qiyas (Qudurat) Weight', default=0.30)
    weight_tahsili = fields.Float(string='Tahsili Weight', default=0.30)
    weight_gpa = fields.Float(string='High-School GPA Weight', default=0.40)

    @api.constrains('weight_qiyas', 'weight_tahsili', 'weight_gpa')
    def _check_weights(self):
        for program in self:
            total = program.weight_qiyas + program.weight_tahsili + program.weight_gpa
            if abs(total - 1.0) > 0.001:
                raise ValidationError(_(
                    "Admission weights for program '%(p)s' must sum to 1.0 "
                    "(currently %(t).2f).", p=program.display_name, t=total))
