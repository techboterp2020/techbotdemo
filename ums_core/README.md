# UMS Core — Academic Structure & Catalog

Foundation module of the **University Management System (KSA)** built on **Odoo 19**.
It is the dependency root every other UMS module binds to.

## Requirements covered

| Req ID | Capability |
|--------|------------|
| FR-ACS-01 | Institution → College → Department → Program hierarchy, roll-up counts, deletion guards |
| FR-ACS-02 | Programs: degree type, duration, total credit hours, language; unique code |
| FR-ACS-03 | Bilingual (AR/EN) course catalog with credit & contact hours, level, type; unique code |
| FR-ACS-04 | Prerequisites, co-requisites, equivalencies; circular-dependency protection |
| FR-ACS-05 | Versioned study plans; required vs elective CH validated to program total |
| FR-ACS-06 | CLO / PLO learning outcomes with CLO→PLO mapping matrix |
| FR-ACS-07 | Grading schemes (Saudi 5.0 default, F=1.0; 4.0 configurable), mark→letter→point |

## Models

`ums.institution`, `ums.college`, `ums.department`, `ums.program`, `ums.course`,
`ums.course.prerequisite`, `ums.study.plan` (+ `.line`), `ums.learning.outcome`,
`ums.grade.scheme` (+ `.line`), and the `ums.bilingual.mixin` abstract base.

## Security groups (skeleton, extended by downstream modules)

`ums_group_academic_user` ⊂ `ums_group_dept_head` ⊂ `ums_group_registrar` ⊂ `ums_group_admin`.

## Install & test

```bash
# add this repo's addons/ folder to addons_path
odoo -d ums --addons-path=.../addons -i ums_core
# run the test suite
odoo -d ums --addons-path=.../addons -i ums_core --test-enable --test-tags ums --stop-after-init
```

The default **Saudi 5.0** grade scheme is loaded on install and auto-assigned to new
programs. Demo data installs a small Engineering / Computer Science structure.
