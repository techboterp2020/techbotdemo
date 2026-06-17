from odoo import api, fields, models


class UmsKpi(models.Model):
    """A computed academic KPI snapshot (FR-BI-02).

    KPIs are recomputed on demand from operational data; storing snapshots lets
    dashboards trend values over time.
    """
    _name = 'ums.kpi'
    _description = 'Academic KPI'
    _order = 'snapshot_date desc, code'

    name = fields.Char(string='KPI', required=True)
    code = fields.Char(string='Code', required=True)
    value = fields.Float(string='Value')
    unit = fields.Selection(
        selection=[('count', 'Count'), ('percent', 'Percent'), ('ratio', 'Ratio')],
        string='Unit', default='count')
    snapshot_date = fields.Date(
        string='As Of', default=fields.Date.context_today)
    program_id = fields.Many2one('ums.program', string='Program')

    @api.model
    def compute_kpis(self, program=None):
        """Compute the core academic KPIs and return them as a dict.

        enrollment, graduates, graduation_rate, avg_cgpa, student_faculty_ratio.
        """
        Student = self.env['ums.student']
        base = [('program_id', '=', program.id)] if program else []
        enrolled = Student.search_count(base + [('status', '=', 'active')])
        graduated = Student.search_count(base + [('status', '=', 'graduated')])
        total = Student.search_count(base) or 1

        gpa_records = self.env['ums.gpa.record'].search(
            [('student_id.program_id', '=', program.id)] if program else [])
        avg_cgpa = (sum(gpa_records.mapped('cgpa')) / len(gpa_records)) \
            if gpa_records else 0.0

        faculty = self.env['hr.employee'].search_count([('is_faculty', '=', True)]) \
            if 'hr.employee' in self.env else 0

        return {
            'enrollment': enrolled,
            'graduates': graduated,
            'graduation_rate': round(graduated / total * 100, 2),
            'avg_cgpa': round(avg_cgpa, 2),
            'student_faculty_ratio': round(enrolled / faculty, 2) if faculty else 0.0,
        }

    @api.model
    def snapshot(self, program=None):
        """Persist the current KPI values as dated snapshots."""
        kpis = self.compute_kpis(program)
        unit = {'graduation_rate': 'percent', 'avg_cgpa': 'ratio',
                'student_faculty_ratio': 'ratio'}
        created = self.env['ums.kpi']
        for code, value in kpis.items():
            created |= self.create({
                'name': code.replace('_', ' ').title(),
                'code': code, 'value': value,
                'unit': unit.get(code, 'count'),
                'program_id': program.id if program else False,
            })
        return created
