# OceanAir Tours — Odoo 19 Demo Module

A single, installable Odoo 19 Enterprise module that demonstrates OceanAir's
core operational workflow end-to-end:

> **Tour Booking → Supplier Costing → Margin/Profitability → One-click
> Invoicing → Vendor Bills**, with CRM and Accounting wired in.

This is the "hero" workflow to show live. The high-level mapping of *all* the
requirements in Munavvir's email (HR, Attendance, Payroll, WhatsApp,
Dashboards, etc.) to Odoo 19 native features is in
[`../DEMO_TALK_TRACK.md`](../DEMO_TALK_TRACK.md).

---

## Install

**On Odoo.sh (your setup):**
1. Copy the `oceanair_tours/` folder into your repository (e.g. under the
   addons path / repo root), commit and push to a dev/staging branch.
2. Odoo.sh rebuilds → the app appears in **Apps**.
3. Open **Apps → search "OceanAir" → Install**. It auto-installs its
   dependencies (`mail`, `account`, `crm`).

**On a local Odoo 19 / trial container:**
```bash
# drop oceanair_tours into your addons_path, then:
odoo-bin -u oceanair_tours -d <your_db>
# or just install it from the Apps menu.
```

Requires **Accounting** and **CRM** apps (pulled in automatically). A chart of
accounts must be configured on the company for invoicing to post — any fresh
Odoo 19 trial with a country set already has this.

Sample data (5 tour packages + 2 bookings + customer/suppliers) loads on
install so the demo looks populated immediately. They are normal records you
can delete afterwards.

---

## 3-minute live demo flow

1. **OceanAir Tours → Bookings** — show the list: Sales, Cost, **Margin** and
   **Margin %** totalled per row. Point out colour-coded statuses.
2. Open **Egypt Nile Cruise** booking (pre-loaded, *Confirmed*).
   - Show **Supplier Costs** tab: hotel / transport / guide lines, each with a
     supplier. Margin recalculates automatically (Sales 9,600 − Cost 5,400 =
     **4,200 margin, ~43.75%**).
3. Click **Create Customer Invoice** → a draft invoice opens in Accounting,
   pre-filled from the booking. *(Booking → Accounting, zero re-keying.)*
4. Back on the booking, click **Generate Vendor Bills** → draft supplier bills
   created and grouped per supplier. *(Supplier cost allocation.)*
5. Print **⚙ → Tour Booking / Costing Sheet** → branded PDF costing sheet.
6. **Reporting → Tour Profitability** → pivot & bar chart of margin by tour
   type. Drag dimensions to show ad-hoc analysis.
7. **CRM →** open any opportunity → **Create Tour Booking** button →
   pre-fills customer + links the opportunity. *(Lead → operations hand-off.)*

---

## What's inside

| Area | In this module |
|---|---|
| Tour catalog | `oceanair.tour.package` (City / Safari / Egypt / Croatia / Domes / Custom) |
| Operations | `oceanair.tour.booking` — full workflow, statusbar, chatter, activities |
| Costing | `oceanair.tour.cost.line` — supplier costs, auto margin |
| Accounting | One-click customer invoice + grouped vendor bills, cost-center (analytic) tagging |
| CRM | "Create Tour Booking" from an Opportunity |
| Reporting | List totals, Pivot, Bar graph, printable PDF costing sheet |
| Security | Tour Operations *User* / *Manager* roles |

Built for **Odoo 19** (uses `<list>` views, inline `invisible`/`readonly`
attributes, `<chatter/>`, `analytic_distribution`).
