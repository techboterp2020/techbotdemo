{
    'name': 'UMS Assessment, Grading & Transcripts',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'Assessment components, grade entry, GPA/CGPA, transcripts and graduation',
    'description': """
University Management System — Assessment & Grading (FR-ASM-01 .. FR-ASM-09)
===========================================================================

* Configurable assessment components with weights summing to 100% (FR-ASM-01).
* Faculty grade entry with draft/submit/approve and audit (FR-ASM-02/10).
* Marks → letter → points mapping per scheme (Saudi 5.0, F=1.0) (FR-ASM-03).
* Term GPA and cumulative CGPA, credit-hour weighted (FR-ASM-04).
* Honors classification with bilingual labels (FR-ASM-05).
* Official bilingual transcript with verification QR (FR-ASM-07).
* Degree audit vs study plan and graduation eligibility (FR-ASM-08/09).
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': [
        'ums_core',
        'ums_calendar',
        'ums_sis',
        'ums_ksa_localization',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/ums_grade_entry_views.xml',
        'views/ums_gpa_record_views.xml',
        'views/ums_graduation_views.xml',
        'reports/transcript_report.xml',
        'views/ums_menus.xml',
    ],
    'installable': True,
}
