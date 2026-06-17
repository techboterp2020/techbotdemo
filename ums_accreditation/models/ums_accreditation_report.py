from odoo import api, fields, models


class UmsAccreditationReport(models.Model):
    """An NCAAA/ETEC accreditation report for a program (FR-BI-03)."""
    _name = 'ums.accreditation.report'
    _description = 'Accreditation Report'
    _order = 'create_date desc'

    name = fields.Char(string='Title', required=True)
    program_id = fields.Many2one('ums.program', string='Program', required=True)
    report_type = fields.Selection(
        selection=[
            ('program', 'Program Report'),
            ('course', 'Course Report'),
            ('kpi_pack', 'KPI Pack'),
            ('self_study', 'Self-Study'),
        ],
        string='Type', required=True, default='program',
    )
    period = fields.Char(string='Academic Period')
    plo_count = fields.Integer(string='PLOs', compute='_compute_coverage')
    clo_mapped_count = fields.Integer(string='Mapped CLOs', compute='_compute_coverage')
    coverage_percent = fields.Float(
        string='PLO Coverage (%)', compute='_compute_coverage')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
        ],
        string='Status', default='draft', required=True,
    )

    @api.depends('program_id')
    def _compute_coverage(self):
        for report in self:
            plos = report.program_id.learning_outcome_ids.filtered(
                lambda o: o.outcome_type == 'plo')
            courses = report.program_id.study_plan_ids.mapped(
                'line_ids.course_id')
            clos = courses.mapped('learning_outcome_ids').filtered(
                lambda o: o.outcome_type == 'clo')
            mapped_plos = clos.mapped('mapped_plo_ids')
            report.plo_count = len(plos)
            report.clo_mapped_count = len(clos.filtered(lambda c: c.mapped_plo_ids))
            report.coverage_percent = round(
                len(mapped_plos & plos) / len(plos) * 100, 2) if plos else 0.0

    def get_kpi_pack(self):
        """Assemble the accreditation KPI pack for the program."""
        self.ensure_one()
        kpi_model = self.env.get('ums.kpi')
        kpis = kpi_model.compute_kpis(self.program_id) if kpi_model is not None else {}
        return {
            'program': self.program_id.display_name,
            'period': self.period,
            'plo_coverage': self.coverage_percent,
            'kpis': kpis,
        }
