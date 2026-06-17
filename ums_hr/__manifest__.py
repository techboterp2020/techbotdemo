{
    'name': 'UMS Faculty & HR',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'Faculty profiles on hr.employee and teaching-load management',
    'description': """
University Management System — Faculty & HR (FR-FAC-01/02, FR-HR-*)
==================================================================

* Faculty profile extending hr.employee: rank, qualifications, specialisation
  (FR-FAC-01).
* Teaching-load assignment and workload calculation vs policy (FR-FAC-02).

Employee lifecycle, contracts and Saudi payroll (GOSI/WPS) are delivered with
Odoo HR/Payroll (``hr`` + ``l10n_sa_hr_payroll``) and configured during
implementation.
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': [
        'ums_core',
        'ums_calendar',
        'hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/ums_teaching_load_views.xml',
        'views/ums_menus.xml',
    ],
    'installable': True,
}
