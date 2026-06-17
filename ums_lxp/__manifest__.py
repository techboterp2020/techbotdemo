{
    'name': 'UMS Learning Experience Platform',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'Personalized learning pathways and curated content',
    'description': """
University Management System — LXP (RFP Phase 2)
===============================================

Enhances the digital learning journey with personalized learning pathways,
curated content access and learner engagement tools. AI-powered tutoring and
early-warning systems are out of scope per the commercial RFP.
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': ['ums_core', 'ums_sis'],
    'data': [
        'security/ir.model.access.csv',
        'views/ums_pathway_views.xml',
        'views/ums_menus.xml',
    ],
    'installable': True,
}
