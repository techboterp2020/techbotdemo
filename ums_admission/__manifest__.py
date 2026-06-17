{
    'name': 'UMS Student CRM — Recruitment & Admissions',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'Lead capture, applications, admissions workflow, offers and SIS handover',
    'description': """
University Management System — Student CRM (Recruitment & Admissions)
=====================================================================

Covers the full pre-enrolment lifecycle (FR-ADM-01 .. FR-ADM-10 and the
commercial Student CRM scope):

* Multi-channel lead / enquiry capture (FR-ADM-01).
* Configurable application forms per program/intake (FR-ADM-02).
* Qiyas (Qudurat) + Tahsili + HS GPA weighted composite score (FR-ADM-03).
* Rule-based eligibility and ranked shortlist with seat/gender quotas (FR-ADM-05).
* Committee review workflow with full status lifecycle (FR-ADM-06).
* Document verification workflow with checklist (FR-ADM-07).
* Auto-generate University ID + student record on enrolment — SIS handover
  (FR-ADM-08).
* Offer issuance and acceptance tracking (FR-ADM-09).
* Recruitment-funnel reporting.

Communication is via Odoo mail/SMS; Nafath/identity and payment hooks are
provided for downstream integration.
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': [
        'ums_core',
        'ums_calendar',
        'ums_sis',
        'mail',
    ],
    'data': [
        'security/ums_admission_security.xml',
        'security/ir.model.access.csv',
        'data/ums_sequence_data.xml',
        'views/ums_lead_views.xml',
        'views/ums_intake_views.xml',
        'views/ums_application_views.xml',
        'views/ums_menus.xml',
    ],
    'installable': True,
}
