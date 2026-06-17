{
    'name': 'UMS Public Website & Online Application',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'Branded university website, programs catalog and online apply form',
    'description': """
University Management System — Public Website
=============================================

A branded, bilingual public website for the university:

* Modern homepage with hero, live stats, featured programs and admissions CTA.
* Programs catalog driven by the academic structure (ums.program).
* Online "Apply Now" form that captures enquiries straight into the Admissions
  CRM (ums.lead) for the recruitment funnel.
* Links to the student self-service portal.

Built on Odoo 19 ``website``.
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'ums_core',
        'ums_admission',
    ],
    'data': [
        'views/templates.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ums_website/static/src/css/ums_website.css',
        ],
    },
    'installable': True,
    'application': True,
}
