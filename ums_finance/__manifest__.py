{
    'name': 'UMS Finance, Fees & ZATCA E-Invoicing',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'Fee structures, credit-hour tuition, ZATCA Phase-2 fields and financial holds',
    'description': """
University Management System — Finance & ZATCA (FR-FIN-01 .. FR-FIN-08)
======================================================================

* Fee structures by program/level/student-type with per-credit-hour tuition
  (FR-FIN-01).
* Automatic tuition computation on registration and recompute on add/drop
  (FR-FIN-02).
* ZATCA Phase-2 e-invoice fields on account.move: UUID, previous-invoice hash,
  cryptographic stamp/CSID and embedded QR (FR-FIN-03/04).
* Student financial statement/ledger; unpaid balances raise a financial hold
  that feeds SIS (FR-FIN-08).

Builds on Odoo Accounting (``account``). For production ZATCA clearance pair
with ``l10n_sa`` and the Fatoora connector.
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': [
        'ums_core',
        'ums_sis',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/ums_fee_structure_views.xml',
        'views/account_move_views.xml',
        'views/ums_student_views.xml',
        'views/ums_menus.xml',
    ],
    'installable': True,
}
