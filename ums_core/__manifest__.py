{
    'name': 'UMS Core — Academic Structure & Catalog',
    'version': '19.0.1.0.0',
    'category': 'Education/University',
    'summary': 'Institution hierarchy, programs, study plans, courses and grading schemes',
    'description': """
University Management System — Core (KSA)
=========================================

Foundation module for the University Management System built on Odoo 19.
Implements the Academic Structure & Catalog (FR-ACS-01 .. FR-ACS-07):

* Institution > College > Department > Program hierarchy with roll-up counts
  and deletion guards (FR-ACS-01).
* Programs with degree type, duration, total credit hours and language of
  instruction; unique code enforced (FR-ACS-02).
* Bilingual (Arabic/English) course catalog with credit & contact hours,
  level and type; unique code (FR-ACS-03).
* Course prerequisites, co-requisites and equivalencies with circular
  dependency protection (FR-ACS-04).
* Versioned study plans mapping courses to levels/semesters with required vs
  elective credit validation (FR-ACS-05).
* Course/Program Learning Outcome (CLO/PLO) mapping (FR-ACS-06).
* Grading schemes per program (Saudi 5.0 default, F=1.0; 4.0 configurable),
  credit-hour weighted (FR-ACS-07).

This module establishes the security-group skeleton that downstream UMS
modules (admissions, SIS, finance, ...) extend.
""",
    'author': 'UMS Implementation Team',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'security/ums_security.xml',
        'security/ir.model.access.csv',
        'data/ums_grade_scheme_data.xml',
        'views/ums_institution_views.xml',
        'views/ums_college_views.xml',
        'views/ums_department_views.xml',
        'views/ums_program_views.xml',
        'views/ums_course_views.xml',
        'views/ums_study_plan_views.xml',
        'views/ums_learning_outcome_views.xml',
        'views/ums_grade_scheme_views.xml',
        'views/ums_menus.xml',
    ],
    'demo': [
        'demo/ums_demo.xml',
    ],
    'application': True,
    'installable': True,
}
