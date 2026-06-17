from odoo import fields, models


class UmsSection(models.Model):
    """Link registrations back to the section defined in ums_calendar so seat
    counts and rosters resolve (FR-CAL-04 / FR-SIS-02)."""
    _inherit = 'ums.section'

    registration_ids = fields.One2many(
        'ums.registration', 'section_id', string='Registrations')
