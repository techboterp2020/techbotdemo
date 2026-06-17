{
    'name': 'UMS Academic Calendar & Scheduling',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'Academic years, terms, key dates, timetabling and exam scheduling',
    'description': """
University Management System — Academic Calendar (FR-CAL-01 .. FR-CAL-05)
=========================================================================

* Academic years & terms with dual Hijri/Gregorian dates (FR-CAL-01).
* Key dates (registration / add-drop / withdraw / exam / results / grad) that
  drive windows and display on the portal (FR-CAL-02).
* Saudi weekend (Fri–Sat) and holiday calendar (FR-CAL-03).
* Section timetabling with room/instructor/slot and clash detection (FR-CAL-04).
* Exam scheduling avoiding student clashes with invigilators (FR-CAL-05).
""",
    'author': 'UMS Implementation Team',
    'license': 'LGPL-3',
    'depends': [
        'ums_core',
        'ums_ksa_localization',
        'resource',
    ],
    'data': [
        'security/ums_calendar_security.xml',
        'security/ir.model.access.csv',
        'views/ums_academic_year_views.xml',
        'views/ums_term_views.xml',
        'views/ums_key_date_views.xml',
        'views/ums_room_views.xml',
        'views/ums_timeslot_views.xml',
        'views/ums_section_views.xml',
        'views/ums_exam_views.xml',
        'views/ums_menus.xml',
    ],
    'installable': True,
}
