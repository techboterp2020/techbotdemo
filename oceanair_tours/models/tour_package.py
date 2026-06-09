from odoo import api, fields, models, _


class TourPackage(models.Model):
    _name = 'oceanair.tour.package'
    _description = 'Tour Package'
    _order = 'name'

    name = fields.Char(string='Package Name', required=True)
    code = fields.Char(string='Reference')
    tour_type = fields.Selection([
        ('city', 'City Tour'),
        ('safari', 'Safari Tour'),
        ('egypt', 'Egypt Tour'),
        ('croatia', 'Croatia Tour'),
        ('domes', 'Domes / Stay'),
        ('custom', 'Custom Package'),
    ], string='Tour Type', default='city', required=True)
    destination = fields.Char(string='Destination')
    duration_days = fields.Integer(string='Duration (Days)', default=1)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id)
    default_price = fields.Monetary(
        string='Selling Price / Pax', currency_field='currency_id')
    description = fields.Html(string='Itinerary / Description')
    active = fields.Boolean(default=True)
    booking_count = fields.Integer(
        string='Bookings', compute='_compute_booking_count')

    def _compute_booking_count(self):
        Booking = self.env['oceanair.tour.booking']
        for rec in self:
            rec.booking_count = Booking.search_count(
                [('package_id', '=', rec.id)])

    def action_view_bookings(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bookings'),
            'res_model': 'oceanair.tour.booking',
            'view_mode': 'list,form,pivot,graph',
            'domain': [('package_id', '=', self.id)],
            'context': {'default_package_id': self.id},
        }
