from odoo import api, fields, models


class UmsFeeStructure(models.Model):
    """Fee structure for a program/level/student-type with per-credit-hour
    tuition and fixed fees (FR-FIN-01)."""
    _name = 'ums.fee.structure'
    _description = 'Fee Structure'
    _order = 'program_id, level'

    name = fields.Char(string='Name', required=True)
    program_id = fields.Many2one('ums.program', string='Program', required=True, index=True)
    level = fields.Integer(string='Level', help='0 = applies to all levels.')
    student_type = fields.Selection(
        selection=[
            ('regular', 'Regular'),
            ('transfer', 'Transfer'),
            ('international', 'International'),
            ('sponsored', 'Sponsored'),
        ],
        string='Student Type', default='regular', required=True,
    )
    per_ch_rate = fields.Monetary(string='Per Credit-Hour Rate', required=True)
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id)
    item_ids = fields.One2many('ums.fee.item', 'structure_id', string='Fixed Fees')
    active = fields.Boolean(default=True)

    @api.model
    def find_for(self, program, level=None, student_type='regular'):
        """Return the best-matching fee structure for a student context."""
        domain = [('program_id', '=', program.id),
                  ('student_type', '=', student_type)]
        structures = self.search(domain)
        if level:
            level_match = structures.filtered(lambda s: s.level == level)
            if level_match:
                return level_match[:1]
        return structures.filtered(lambda s: not s.level)[:1] or structures[:1]

    def compute_tuition(self, credit_hours):
        """Tuition for a given CH = per-CH rate × CH + fixed fees."""
        self.ensure_one()
        fixed = sum(self.item_ids.mapped('amount'))
        return self.per_ch_rate * credit_hours + fixed


class UmsFeeItem(models.Model):
    """A fixed fee line within a fee structure (registration, lab, ...)."""
    _name = 'ums.fee.item'
    _description = 'Fee Item'

    structure_id = fields.Many2one(
        'ums.fee.structure', string='Structure', required=True, ondelete='cascade')
    name = fields.Char(string='Fee', required=True)
    amount = fields.Monetary(string='Amount', required=True)
    currency_id = fields.Many2one(related='structure_id.currency_id')
    is_vat_exempt = fields.Boolean(
        string='VAT Exempt', default=True,
        help='Tuition is typically VAT-exempt in KSA; toggle per item (FR-FIN-04).')
