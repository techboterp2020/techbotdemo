{
    'name': 'UMS Student Information System & Registration',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'Student records, registration, holds, academic standing and status lifecycle',
    'description': """
University Management System — SIS & Registration (FR-SIS-01 .. FR-SIS-09)
==========================================================================

* Master student record on res.partner: national ID, program, study plan,
  advisor, status (FR-SIS-01).
* Self-service registration with prerequisite, credit-limit, clash, capacity
  and hold checks (FR-SIS-02).
* Add/Drop/Withdraw with deadline enforcement (FR-SIS-03).
* Advisor approval and advising notes (FR-SIS-04).
* Holds (financial/academic/disciplinary/library) blocking actions (FR-SIS-05).
* Academic standing computation per term (FR-SIS-06).
* Student status lifecycle with audited history (FR-SIS-07).
* Re-admission & major change with credit re-mapping (FR-SIS-08).
* Enrollment verification letters (FR-SIS-09).

Also provides the rules-based progression logic and accreditation data export
required by the commercial SIS scope.
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': [
        'ums_core',
        'ums_calendar',
        'ums_ksa_localization',
    ],
    'data': [
        'security/ums_sis_security.xml',
        'security/ir.model.access.csv',
        'security/ums_sis_record_rules.xml',
        'data/ums_sequence_data.xml',
        'views/ums_student_views.xml',
        'views/ums_registration_views.xml',
        'views/ums_hold_views.xml',
        'views/ums_advising_views.xml',
        'views/ums_standing_views.xml',
        'views/ums_menus.xml',
    ],
    'installable': True,
}
