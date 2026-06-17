from odoo import api, fields, models
from odoo.tools.translate import _


class UmsStudent(models.Model):
    """Student finance: tuition computation, balance and financial holds
    (FR-FIN-02/08)."""
    _inherit = 'ums.student'

    student_type = fields.Selection(
        selection=[
            ('regular', 'Regular'),
            ('transfer', 'Transfer'),
            ('international', 'International'),
            ('sponsored', 'Sponsored'),
        ],
        string='Student Type', default='regular', required=True,
    )
    invoice_ids = fields.One2many(
        'account.move', 'ums_student_id', string='Invoices',
        domain=[('move_type', '=', 'out_invoice')])
    outstanding_balance = fields.Monetary(
        string='Outstanding Balance', compute='_compute_balance')
    currency_id = fields.Many2one(
        'res.currency', compute='_compute_balance')

    @api.depends('invoice_ids.amount_residual', 'invoice_ids.state')
    def _compute_balance(self):
        for student in self:
            student.currency_id = student.company_id.currency_id \
                or self.env.company.currency_id
            posted = student.invoice_ids.filtered(lambda m: m.state == 'posted')
            student.outstanding_balance = sum(posted.mapped('amount_residual'))

    def compute_term_tuition(self, term):
        """Tuition for the student's active registrations in a term (FR-FIN-02)."""
        self.ensure_one()
        regs = self.registration_ids.filtered(
            lambda r: r.term_id == term
            and r.state in ('registered', 'confirmed'))
        credit_hours = sum(regs.mapped('credit_hours'))
        structure = self.env['ums.fee.structure'].find_for(
            self.program_id, level=self.level, student_type=self.student_type)
        if not structure:
            return 0.0
        return structure.compute_tuition(credit_hours)

    def sync_financial_hold(self):
        """Place/clear a financial hold based on outstanding balance (FR-FIN-08)."""
        Hold = self.env['ums.hold']
        for student in self:
            existing = student.hold_ids.filtered(
                lambda h: h.hold_type == 'financial' and h.active)
            if student.outstanding_balance > 0 and not existing:
                Hold.create({
                    'student_id': student.id,
                    'hold_type': 'financial',
                    'reason': _('Outstanding balance'),
                    'blocks_registration': True,
                    'blocks_transcript': True,
                })
            elif student.outstanding_balance <= 0 and existing:
                existing.action_clear()
