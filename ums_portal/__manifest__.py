{
    'name': 'UMS Unified Portal',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'Single self-service portal for students, faculty and staff',
    'description': """
University Management System — Unified Portal (RFP Phase 2)
==========================================================

A centralized self-service access point. Students see their registrations,
grades, holds and financial balance through the Odoo portal. A native mobile
app is out of scope per the commercial RFP (the portal is responsive).
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': ['portal', 'ums_sis', 'ums_lms'],
    'data': [
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ums_portal/static/src/css/ums_portal.css',
        ],
    },
    'installable': True,
}
