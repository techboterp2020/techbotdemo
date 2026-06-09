from odoo import api, fields, models


class TourCostLine(models.Model):
    _name = 'oceanair.tour.cost.line'
    _description = 'Tour Supplier Cost Line'

    booking_id = fields.Many2one(
        'oceanair.tour.booking', string='Booking',
        required=True, ondelete='cascade')
    name = fields.Char(string='Description', required=True)
    cost_type = fields.Selection([
        ('hotel', 'Hotel / Accommodation'),
        ('transport', 'Transport / Transfer'),
        ('guide', 'Guide / Excursion'),
        ('tickets', 'Tickets / Entrance'),
        ('visa', 'Visa'),
        ('meals', 'Meals'),
        ('other', 'Other'),
    ], string='Cost Type', default='hotel', required=True)
    vendor_id = fields.Many2one('res.partner', string='Supplier')
    quantity = fields.Float(string='Qty', default=1.0)
    unit_cost = fields.Monetary(
        string='Unit Cost', currency_field='currency_id')
    subtotal = fields.Monetary(
        string='Subtotal', compute='_compute_subtotal',
        store=True, currency_field='currency_id')
    currency_id = fields.Many2one(
        related='booking_id.currency_id', string='Currency', store=True)

    @api.depends('quantity', 'unit_cost')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_cost
