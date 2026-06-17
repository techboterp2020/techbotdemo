from odoo import fields, models


class UmsRegistration(models.Model):
    """Link a registration to its grade entry (FR-ASM-02)."""
    _inherit = 'ums.registration'

    grade_entry_id = fields.One2many(
        'ums.grade.entry', 'registration_id', string='Grade Entry')

    def action_create_grade_entry(self):
        """Create a draft grade entry for grading this registration."""
        entries = self.env['ums.grade.entry']
        for reg in self:
            if not reg.grade_entry_id:
                entries |= self.env['ums.grade.entry'].create({
                    'registration_id': reg.id})
        return entries
