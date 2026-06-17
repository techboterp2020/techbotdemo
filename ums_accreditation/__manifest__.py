{
    'name': 'UMS Accreditation & Quality Assurance',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'NCAAA/ETEC accreditation KPI packs and program/course QA reports',
    'description': """
University Management System — Accreditation & QA (FR-BI-03, RFP Phase 2)
========================================================================

Structured accreditation and quality-assurance reporting aligned with NCAAA /
ETEC: program/course reports, CLO→PLO coverage, and KPI packs for institutional
reviews and audit preparation.
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': ['ums_core', 'ums_assessment'],
    'data': [
        'security/ir.model.access.csv',
        'views/ums_accreditation_views.xml',
        'views/ums_menus.xml',
    ],
    'installable': True,
}
