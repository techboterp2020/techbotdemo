{
    'name': 'UMS Analytics & KPI Dashboards',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'Academic KPIs and advanced analytics dashboards',
    'description': """
University Management System — Analytics & KPIs (FR-BI-01/02, RFP Phase 2)
=========================================================================

Role-based dashboards and academic KPIs (enrollment, retention, graduation
rate, GPA distribution, student/faculty ratio) computed from operational data.
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': ['ums_core', 'ums_sis', 'ums_assessment'],
    'data': [
        'security/ir.model.access.csv',
        'views/ums_kpi_views.xml',
        'views/ums_menus.xml',
    ],
    'installable': True,
}
