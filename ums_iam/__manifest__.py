{
    'name': 'UMS Identity & Access Management',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'SSO, MFA, user lifecycle/SCIM, immutable audit log and access reporting',
    'description': """
University Management System — Identity & Access Management (RFP #5 / NFR-SEC)
=============================================================================

* Single Sign-On via OAuth2/OIDC (Nafath) and SAML 2.0 hooks — builds on
  Odoo ``auth_oauth``; a Nafath provider template is seeded.
* Mandatory multi-factor authentication for staff/admin (``auth_totp``).
* Role-based access control (extends the UMS group model).
* User lifecycle management with a SCIM-style provisioning API.
* Immutable audit log for sensitive actions + access reporting (NFR-SEC-03).
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': [
        'ums_core',
        'auth_totp',
        'auth_oauth',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/auth_oauth_provider_data.xml',
        'views/ums_audit_log_views.xml',
        'views/res_users_views.xml',
        'views/ums_menus.xml',
    ],
    'installable': True,
}
