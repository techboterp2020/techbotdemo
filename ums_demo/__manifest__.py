{
    'name': 'UMS Demo Data',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'Generates rich demo records across every UMS screen',
    'description': """
University Management System — Demo Data
========================================

Installing this module populates every UMS screen with 25+ realistic,
constraint-valid demo records via a post-install generator (ORM-based, so all
validations, sequences and computed fields behave exactly as in production).

Idempotent: re-installing/updating will not duplicate records.

For DEMO/UAT environments only — do not install in production.
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': [
        'ums_core',
        'ums_ksa_localization',
        'ums_calendar',
        'ums_sis',
        'ums_admission',
        'ums_iam',
        'ums_lms',
        'ums_finance',
        'ums_hr',
        'ums_assessment',
        'ums_credentials',
        'ums_bi',
        'ums_accreditation',
        'ums_lxp',
        'ums_portal',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
