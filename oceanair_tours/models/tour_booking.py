from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TourBooking(models.Model):
    _name = 'oceanair.tour.booking'
    _description = 'Tour Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc, id desc'

    name = fields.Char(
        string='Booking Reference', required=True, copy=False,
        readonly=True, default='New')
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True, tracking=True)
    package_id = fields.Many2one(
        'oceanair.tour.package', string='Tour Package', tracking=True)
    tour_type = fields.Selection(
        related='package_id.tour_type', string='Tour Type', store=True)
    sales_agent_id = fields.Many2one(
        'res.users', string='Sales Agent',
        default=lambda self: self.env.user, tracking=True)
    date_from = fields.Date(
        string='Travel From', default=fields.Date.context_today, tracking=True)
    date_to = fields.Date(string='Travel To', tracking=True)
    pax_adults = fields.Integer(string='Adults', default=1)
    pax_children = fields.Integer(string='Children', default=0)
    pax_total = fields.Integer(
        string='Total Pax', compute='_compute_pax_total', store=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)
    unit_price = fields.Monetary(
        string='Price / Pax', currency_field='currency_id')
    cost_line_ids = fields.One2many(
        'oceanair.tour.cost.line', 'booking_id', string='Supplier Costs')

    amount_sale = fields.Monetary(
        string='Total Sales', compute='_compute_amounts',
        store=True, currency_field='currency_id')
    amount_cost = fields.Monetary(
        string='Total Cost', compute='_compute_amounts',
        store=True, currency_field='currency_id')
    margin = fields.Monetary(
        string='Margin', compute='_compute_amounts',
        store=True, currency_field='currency_id')
    margin_pct = fields.Float(
        string='Margin (%)', compute='_compute_amounts', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('done', 'Completed'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    invoice_id = fields.Many2one(
        'account.move', string='Customer Invoice', readonly=True, copy=False)
    invoice_count = fields.Integer(
        string='Invoice', compute='_compute_counts')
    vendor_bill_ids = fields.Many2many(
        'account.move', 'oceanair_booking_bill_rel', 'booking_id', 'move_id',
        string='Vendor Bills', copy=False)
    vendor_bill_count = fields.Integer(
        string='Vendor Bills', compute='_compute_counts')
    lead_id = fields.Many2one(
        'crm.lead', string='Source Opportunity', copy=False)
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Cost Center')
    notes = fields.Html(string='Internal Notes')

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('pax_adults', 'pax_children')
    def _compute_pax_total(self):
        for rec in self:
            rec.pax_total = (rec.pax_adults or 0) + (rec.pax_children or 0)

    @api.depends('unit_price', 'pax_total', 'cost_line_ids.subtotal')
    def _compute_amounts(self):
        for rec in self:
            rec.amount_sale = rec.unit_price * rec.pax_total
            rec.amount_cost = sum(rec.cost_line_ids.mapped('subtotal'))
            rec.margin = rec.amount_sale - rec.amount_cost
            rec.margin_pct = (
                (rec.margin / rec.amount_sale) * 100.0
                if rec.amount_sale else 0.0)

    @api.depends('invoice_id', 'vendor_bill_ids')
    def _compute_counts(self):
        for rec in self:
            rec.invoice_count = 1 if rec.invoice_id else 0
            rec.vendor_bill_count = len(rec.vendor_bill_ids)

    # ------------------------------------------------------------------
    # Onchange / Create
    # ------------------------------------------------------------------
    @api.onchange('package_id')
    def _onchange_package_id(self):
        if self.package_id:
            self.unit_price = self.package_id.default_price
            if self.package_id.duration_days and self.date_from:
                self.date_to = fields.Date.add(
                    self.date_from, days=self.package_id.duration_days)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'oceanair.tour.booking') or 'New'
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_set_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_done(self):
        self.write({'state': 'done'})

    # ------------------------------------------------------------------
    # Invoicing
    # ------------------------------------------------------------------
    def _prepare_invoice_line(self):
        self.ensure_one()
        product = self.env.ref(
            'oceanair_tours.product_tour_service', raise_if_not_found=False)
        line = {
            'name': self.package_id.name or self.name or _('Tour Package'),
            'quantity': self.pax_total or 1,
            'price_unit': self.unit_price,
        }
        if product:
            line['product_id'] = product.id
        if self.analytic_account_id:
            line['analytic_distribution'] = {
                str(self.analytic_account_id.id): 100}
        return line

    def action_create_invoice(self):
        self.ensure_one()
        if self.invoice_id:
            raise UserError(
                _('A customer invoice already exists for this booking.'))
        if not self.partner_id:
            raise UserError(_('Please set a customer before invoicing.'))
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_origin': self.name,
            'invoice_line_ids': [(0, 0, self._prepare_invoice_line())],
        })
        self.invoice_id = move.id
        self.state = 'invoiced'
        return self._open_move(move)

    def action_create_vendor_bills(self):
        self.ensure_one()
        product = self.env.ref(
            'oceanair_tours.product_tour_service', raise_if_not_found=False)
        Move = self.env['account.move']
        created = self.env['account.move']
        grouped = {}
        for line in self.cost_line_ids:
            if not line.vendor_id:
                continue
            grouped.setdefault(line.vendor_id, []).append(line)
        if not grouped:
            raise UserError(
                _('Add at least one supplier cost line with a Supplier '
                  'set to generate vendor bills.'))
        for vendor, lines in grouped.items():
            inv_lines = []
            for line in lines:
                vals = {
                    'name': line.name,
                    'quantity': line.quantity,
                    'price_unit': line.unit_cost,
                }
                if product:
                    vals['product_id'] = product.id
                if self.analytic_account_id:
                    vals['analytic_distribution'] = {
                        str(self.analytic_account_id.id): 100}
                inv_lines.append((0, 0, vals))
            bill = Move.create({
                'move_type': 'in_invoice',
                'partner_id': vendor.id,
                'invoice_origin': self.name,
                'invoice_line_ids': inv_lines,
            })
            created |= bill
        self.vendor_bill_ids = [(4, m.id) for m in created]
        return self.action_view_vendor_bills()

    # ------------------------------------------------------------------
    # Smart buttons
    # ------------------------------------------------------------------
    def _open_move(self, move):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': move.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            return False
        return self._open_move(self.invoice_id)

    def action_view_vendor_bills(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Bills'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.vendor_bill_ids.ids)],
        }
