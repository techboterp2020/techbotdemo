# UMS KSA Localization

Cross-cutting Saudi localization for the UMS suite (Odoo 19).

## Requirements covered

| Req ID | Capability |
|--------|------------|
| NFR-LOC-02 | Dual Hijri (Umm al-Qura) + Gregorian dates via `ums.hijri.mixin` and a converter |
| NFR-LOC-01 | Arabic-first base; Saudi working week (Sun–Thu) `resource.calendar` |
| FR-CAL-03 | Saudi weekend (Fri–Sat) default calendar |
| NFR-PRV-01 | PDPL consent records + data-subject requests; Data Protection Officer role |

## Hijri converter

`models/hijri.py` exposes `gregorian_to_hijri`, `format_hijri`, `format_dual`.
It uses the **`hijri_converter`** package (official Umm al-Qura data) when
installed, and falls back to the arithmetic Islamic calendar (±1 day) otherwise:

```bash
pip install hijri-converter   # recommended for production
```

Any model can inherit `ums.hijri.mixin` and add a computed Char field that calls
`self.hijri_date(rec.some_date)` or `self.dual_date(rec.some_date)`.

## PDPL

* `ums.consent` — consent per processing purpose, with lawful basis, expiry and a
  daily cron that expires stale consents.
* `ums.data.request` — access / correction / erasure / objection / portability
  requests, auto-numbered (`DSR/<year>/#####`) with a 30-day statutory due date.
