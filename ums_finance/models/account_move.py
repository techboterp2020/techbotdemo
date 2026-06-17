import uuid

from odoo import api, fields, models


class AccountMove(models.Model):
    """ZATCA Phase-2 e-invoice fields (FR-FIN-03/04).

    UUID, previous-invoice hash chain, cryptographic stamp/CSID and an embedded
    QR are stored here. Generation of the signed UBL 2.1 XML and Fatoora
    clearance is handled by ``l10n_sa`` + the Fatoora connector in production;
    this module provides the data model and a deterministic local QR payload.
    """
    _inherit = 'account.move'

    is_student_invoice = fields.Boolean(string='Student Invoice')
    ums_student_id = fields.Many2one('ums.student', string='Student', index=True)

    zatca_uuid = fields.Char(string='ZATCA UUID', copy=False, readonly=True)
    zatca_previous_hash = fields.Char(string='Previous Invoice Hash', copy=False, readonly=True)
    zatca_invoice_hash = fields.Char(string='Invoice Hash', copy=False, readonly=True)
    zatca_qr = fields.Char(string='ZATCA QR Payload', copy=False, readonly=True)
    zatca_state = fields.Selection(
        selection=[
            ('none', 'Not Submitted'),
            ('reported', 'Reported (B2C)'),
            ('cleared', 'Cleared (B2B)'),
            ('rejected', 'Rejected'),
        ],
        string='ZATCA Status', default='none', copy=False,
    )

    def _prepare_zatca_fields(self):
        """Assign UUID + hash chain for the invoice (called on posting)."""
        for move in self:
            if move.zatca_uuid:
                continue
            previous = self.search([
                ('company_id', '=', move.company_id.id),
                ('zatca_invoice_hash', '!=', False),
                ('id', '!=', move.id),
            ], order='id desc', limit=1)
            move.zatca_uuid = str(uuid.uuid4())
            move.zatca_previous_hash = previous.zatca_invoice_hash or '0'
            # Deterministic local hash placeholder (production: signed UBL hash).
            move.zatca_invoice_hash = '%s-%s' % (move.zatca_uuid[:8], move.id)
            move.zatca_qr = self._build_zatca_qr_payload()

    def _build_zatca_qr_payload(self):
        self.ensure_one()
        company = self.company_id
        parts = [
            company.name or '',
            company.vat or '',
            (self.invoice_date and self.invoice_date.isoformat()) or '',
            '%.2f' % (self.amount_total or 0.0),
            '%.2f' % (self.amount_tax or 0.0),
        ]
        return '|'.join(parts)

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        posted.filtered('is_student_invoice')._prepare_zatca_fields()
        return posted
