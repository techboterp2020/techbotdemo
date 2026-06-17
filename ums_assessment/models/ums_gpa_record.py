from odoo import api, fields, models

# Honors classification bands on the Saudi 5.0 scale (FR-ASM-05), with
# bilingual labels.
HONORS_BANDS = [
    (4.50, 'mumtaz', 'Excellent', 'ممتاز'),
    (3.75, 'jayyid_jiddan', 'Very Good', 'جيد جداً'),
    (2.75, 'jayyid', 'Good', 'جيد'),
    (1.00, 'maqbool', 'Pass', 'مقبول'),
]


class UmsGpaRecord(models.Model):
    """Per-term GPA and cumulative CGPA, credit-hour weighted (FR-ASM-04/05)."""
    _name = 'ums.gpa.record'
    _description = 'GPA Record'
    _order = 'student_id, term_id'

    student_id = fields.Many2one(
        'ums.student', string='Student', required=True,
        ondelete='cascade', index=True,
    )
    term_id = fields.Many2one('ums.term', string='Term', required=True, index=True)
    term_gpa = fields.Float(string='Term GPA', digits=(3, 2))
    cgpa = fields.Float(string='CGPA', digits=(3, 2))
    term_credit_hours = fields.Integer(string='Term CH')
    cumulative_credit_hours = fields.Integer(string='Cumulative CH')
    classification = fields.Selection(
        selection=[
            ('mumtaz', 'Excellent (Mumtaz)'),
            ('jayyid_jiddan', 'Very Good (Jayyid Jiddan)'),
            ('jayyid', 'Good (Jayyid)'),
            ('maqbool', 'Pass (Maqbool)'),
        ],
        string='Classification',
    )
    classification_ar = fields.Char(string='Classification (Arabic)')

    _sql_constraints = [
        ('student_term_uniq', 'unique(student_id, term_id)',
         'A GPA record already exists for this student and term.'),
    ]

    @api.model
    def _classify(self, cgpa):
        """Return ``(code, en_label, ar_label)`` for a CGPA (FR-ASM-05)."""
        for threshold, code, en, ar in HONORS_BANDS:
            if cgpa >= threshold:
                return code, en, ar
        return 'maqbool', 'Pass', 'مقبول'

    @api.model
    def _weighted_gpa(self, entries):
        """CH-weighted GPA over approved, non-special grade entries."""
        total_ch = 0
        total_points = 0.0
        for entry in entries:
            if not entry.counts_in_gpa():
                continue
            total_ch += entry.credit_hours
            total_points += entry.grade_point * entry.credit_hours
        if not total_ch:
            return 0.0, 0
        return round(total_points / total_ch, 2), total_ch

    @api.model
    def recompute_for_student(self, student, term):
        """Recompute the term GPA and CGPA for a student (FR-ASM-04)."""
        Entry = self.env['ums.grade.entry']
        all_entries = Entry.search([('student_id', '=', student.id)])
        term_entries = all_entries.filtered(lambda e: e.term_id == term)

        term_gpa, term_ch = self._weighted_gpa(term_entries)
        cgpa, cum_ch = self._weighted_gpa(all_entries)
        code, _en, ar = self._classify(cgpa)

        vals = {
            'term_gpa': term_gpa,
            'cgpa': cgpa,
            'term_credit_hours': term_ch,
            'cumulative_credit_hours': cum_ch,
            'classification': code,
            'classification_ar': ar,
        }
        record = self.search([
            ('student_id', '=', student.id), ('term_id', '=', term.id)], limit=1)
        if record:
            record.write(vals)
        else:
            record = self.create({
                'student_id': student.id, 'term_id': term.id, **vals})

        # Feed academic standing in SIS (FR-SIS-06).
        self.env['ums.academic.standing'].recompute_for_term(student, term, cgpa)
        return record
