{
    'name': 'UMS Teaching, Assignments, Attendance & LMS',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'Assignments, rubrics, attendance with thresholds and LMS integration',
    'description': """
University Management System — Teaching & LMS (FR-LMS-01 .. FR-LMS-05)
=====================================================================

* Assignment lifecycle: create / submit / grade / approve with reminders
  (FR-LMS-01).
* Rubric grading feeding continuous assessment (FR-LMS-02).
* Attendance capture (manual/bulk) with threshold rules that can bar a student
  from the final exam (FR-LMS-03).
* Attendance/absence notifications (FR-LMS-04).
* LMS integration connector with roster sync and grade pass-back; standards
  hooks for LTI 1.3, OneRoster, SCORM and xAPI (FR-LMS-05). Proctoring is out
  of scope per the commercial RFP.
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': [
        'ums_core',
        'ums_calendar',
        'ums_sis',
    ],
    'data': [
        'security/ums_lms_security.xml',
        'security/ir.model.access.csv',
        'views/ums_assignment_views.xml',
        'views/ums_rubric_views.xml',
        'views/ums_attendance_views.xml',
        'views/ums_lms_link_views.xml',
        'views/ums_menus.xml',
    ],
    'installable': True,
}
