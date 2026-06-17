{
    'name': 'UMS KSA Localization',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'Hijri dual dates, Arabic-first bilingual base, Saudi week and PDPL',
    'description': """
University Management System — KSA Localization
===============================================

Cross-cutting Saudi localization for the UMS suite:

* Dual Hijri (Umm al-Qura) + Gregorian dates everywhere via a reusable mixin
  and a date utility (NFR-LOC-02).
* Arabic-first bilingual foundation and Saudi working week (Sunday–Thursday)
  resource calendar (NFR-LOC-01 / FR-CAL-03).
* PDPL compliance base: consent capture and data-subject requests
  (access / correction / erasure) with a Data Protection Officer role
  (NFR-PRV-01).

The Hijri converter prefers the ``hijri_converter`` package (official
Umm al-Qura data) when installed and falls back to the arithmetic
(tabular) Islamic calendar otherwise.
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': [
        'ums_core',
        'resource',
    ],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        'security/ums_pdpl_security.xml',
        'security/ir.model.access.csv',
        'data/ums_sequence_data.xml',
        'data/resource_calendar_data.xml',
        'views/ums_consent_views.xml',
        'views/ums_data_request_views.xml',
        'views/ums_menus.xml',
    ],
    'installable': True,
}
