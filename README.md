# University Management System (KSA) — Odoo 19 Enterprise

A modular University Management System for a Saudi higher-education institution,
built as a suite of custom Odoo 19 add-ons. Implements the UMS FSD/TSD
requirements matrix and the commercial RFP/quotation scope.

## Modules & install order

| # | Module | Scope | Key requirements |
|---|--------|-------|------------------|
| 1 | `ums_core` | Academic structure & catalog | FR-ACS-01..07 |
| 2 | `ums_ksa_localization` | Hijri dates, bilingual base, Saudi week, PDPL | NFR-LOC-01/02, NFR-PRV-01 |
| 3 | `ums_calendar` | Academic years/terms, key dates, timetabling, exams | FR-CAL-01..05 |
| 4 | `ums_sis` | Students, registration, holds, standing, status | FR-SIS-01..09 |
| 5 | `ums_admission` | Student CRM: leads, applications, offers, SIS handover | FR-ADM-01..10 |
| 6 | `ums_iam` | SSO, MFA, SCIM lifecycle, immutable audit log | NFR-SEC, RFP #5 |
| 7 | `ums_lms` | Assignments, rubrics, attendance, LMS integration | FR-LMS-01..05 |
| 8 | `ums_finance` | Fee structures, CH tuition, ZATCA Phase-2, holds | FR-FIN-01..08 |
| 9 | `ums_hr` | Faculty profiles, teaching load | FR-FAC-01/02 |
| 10 | `ums_assessment` | Grade entry, GPA/CGPA, honors, transcripts, graduation | FR-ASM-01..10 |
| 11 | `ums_credentials` | Digital credentials / Open Badges (QR verify) | RFP Phase 2 |
| 12 | `ums_bi` | Academic KPIs and dashboards | FR-BI-01/02 |
| 13 | `ums_accreditation` | NCAAA/ETEC KPI packs, CLO→PLO coverage | FR-BI-03 |
| 14 | `ums_lxp` | Personalized learning pathways | RFP Phase 2 |
| 15 | `ums_portal` | Unified self-service portal | RFP Phase 2 |

Install order (topological):

```
ums_core → ums_ksa_localization → ums_calendar → ums_sis → ums_assessment →
ums_accreditation → ums_admission → ums_bi → ums_credentials → ums_finance →
ums_hr → ums_iam → ums_lms → ums_lxp → ums_portal
```

## Install & test

```bash
odoo -d ums \
  --addons-path=/Users/muhammadsalmanalikhan/Downloads/Techbot-Projects-data/school-module/addons \
  -i ums_core,ums_ksa_localization,ums_calendar,ums_sis,ums_admission,ums_iam,\
ums_lms,ums_finance,ums_hr,ums_assessment,ums_credentials,ums_bi,\
ums_accreditation,ums_lxp,ums_portal \
  --test-enable --test-tags ums --stop-after-init
```

For exact Umm al-Qura Hijri dates in production: `pip install hijri-converter`.
For ZATCA Fatoora clearance: add `l10n_sa` + the Fatoora connector.

## Demo data

Installing **`ums_demo`** populates every screen with 25+ realistic,
constraint-valid records (institutions, programs, 30 courses, 25 students with
registrations/grades/GPA, 25 applications, leads, sections, assignments,
attendance, fee structures, credentials, KPIs, PDPL records, audit log, …). It
runs through the ORM via a post-install hook, so all validations and computed
fields behave exactly as in production. It is **idempotent** and for
**demo/UAT only**.

```bash
# installs the whole suite + demo data in one go
odoo -d ums \
  --addons-path=/Users/muhammadsalmanalikhan/Downloads/Techbot-Projects-data/school-module/addons \
  -i ums_demo
```

To wipe and reseed: drop the DB (or uninstall `ums_demo`) and re-install.

## KSA compliance built in
- **Bilingual** (Arabic-first) naming on catalog entities; bilingual transcripts.
- **Dual Hijri/Gregorian** dates via `ums.hijri.mixin`.
- **Saudi 5.0 GPA** (F=1.0) default scheme with honors (Mumtaz/Jayyid Jiddan/…).
- **PDPL**: consent records + data-subject requests + DPO role.
- **ZATCA Phase-2** invoice fields (UUID, hash chain, QR) on `account.move`.
- **Saudi week** (Sun–Thu) resource calendar; Nafath OIDC SSO provider template.

## Explicitly out of scope (per RFP)
AI tutoring / early-warning · blockchain certificates · native mobile app ·
proctoring tools.

## Status
All 15 modules are statically validated (Python compile, XML well-formedness,
ACL/CSV consistency, manifest data-file references, dependency graph). Each
module ships unit tests tagged `ums`. The tests have **not** been executed here
(no Odoo 19 runtime on the build machine) — run the command above in your Odoo
instance to execute them.
