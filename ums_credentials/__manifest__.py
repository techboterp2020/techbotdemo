{
    'name': 'UMS Digital Credentials',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'Issue and verify digital credentials / Open Badges (no blockchain)',
    'description': """
University Management System — Digital Credentials (RFP Phase 2)
===============================================================

Issue, manage and verify academic credentials, certificates and badges in a
secure digital format with a QR/serial verification service. Aligned with the
OBv3 / Open Badges direction. Blockchain certificates are explicitly out of
scope per the commercial RFP.
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': ['ums_core', 'ums_sis'],
    'data': [
        'security/ir.model.access.csv',
        'data/ums_sequence_data.xml',
        'views/ums_credential_views.xml',
        'views/ums_menus.xml',
    ],
    'installable': True,
}
