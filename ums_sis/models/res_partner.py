import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class ResPartner(models.Model):
    """National ID / Iqama is the natural identity key linking applicant →
    student → employee → finance (Data Model §7)."""
    _inherit = 'res.partner'

    national_id = fields.Char(string='National ID / Iqama', copy=False, index=True)
    is_ums_student = fields.Boolean(string='Is Student', default=False)

    _sql_constraints = [
        ('national_id_uniq', 'unique(national_id)',
         'The National ID / Iqama must be unique.'),
    ]

    @api.constrains('national_id')
    def _check_national_id(self):
        for partner in self:
            nid = partner.national_id
            if nid and not re.fullmatch(r'\d{10}', nid.strip()):
                raise ValidationError(_(
                    "National ID / Iqama '%s' must be exactly 10 digits.", nid))
