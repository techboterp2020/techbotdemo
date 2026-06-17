from odoo import api, fields, models

# CGPA thresholds on the Saudi 5.0 scale (FR-SIS-06). Configurable per
# institution bylaws; these are sensible defaults.
GOOD_STANDING_MIN = 2.0
WARNING_MIN = 1.0


class UmsAcademicStanding(models.Model):
    """A student's academic standing computed at term close (FR-SIS-06)."""
    _name = 'ums.academic.standing'
    _description = 'Academic Standing'
    _order = 'create_date desc'

    student_id = fields.Many2one(
        'ums.student', string='Student', required=True,
        ondelete='cascade', index=True,
    )
    term_id = fields.Many2one('ums.term', string='Term', required=True, index=True)
    cgpa = fields.Float(string='CGPA', digits=(3, 2))
    standing = fields.Selection(
        selection=[
            ('good', 'Good Standing'),
            ('warning', 'Academic Warning'),
            ('probation', 'Probation'),
            ('dismissal', 'Subject to Dismissal'),
        ],
        string='Standing', required=True, default='good',
    )
    note = fields.Char(string='Note')

    _sql_constraints = [
        ('student_term_uniq', 'unique(student_id, term_id)',
         'Standing already computed for this student and term.'),
    ]

    @api.model
    def compute_standing(self, cgpa):
        """Map a CGPA (Saudi 5.0) to a standing band (FR-SIS-06)."""
        if cgpa >= GOOD_STANDING_MIN:
            return 'good'
        if cgpa >= WARNING_MIN:
            return 'warning'
        return 'probation'

    @api.model
    def recompute_for_term(self, student, term, cgpa):
        """Create/update the standing record for a student/term."""
        standing = self.compute_standing(cgpa)
        existing = self.search([
            ('student_id', '=', student.id), ('term_id', '=', term.id)], limit=1)
        vals = {'cgpa': cgpa, 'standing': standing}
        if existing:
            existing.write(vals)
            return existing
        return self.create({
            'student_id': student.id, 'term_id': term.id, **vals})
