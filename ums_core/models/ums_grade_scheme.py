from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UmsGradeScheme(models.Model):
    """A grading scheme: marks → letter → grade point (FR-ACS-07).

    Defaults to the Saudi 5.0 scale (F=1.0); a 4.0 scale is configurable per
    program.
    """
    _name = 'ums.grade.scheme'
    _description = 'Grade Scheme'
    _inherit = ['ums.bilingual.mixin']
    _order = 'name_en'

    code = fields.Char(string='Code', required=True, copy=False)
    scale = fields.Selection(
        selection=[
            ('5', 'Saudi 5.0'),
            ('4', '4.0'),
        ],
        string='Scale', required=True, default='5',
    )
    max_points = fields.Float(
        string='Maximum Grade Point', compute='_compute_max_points', store=True)
    active = fields.Boolean(default=True)

    line_ids = fields.One2many('ums.grade.scheme.line', 'scheme_id', string='Bands')
    program_ids = fields.One2many('ums.program', 'grade_scheme_id', string='Programs')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The grade scheme code must be unique.'),
    ]

    @api.depends('scale')
    def _compute_max_points(self):
        for scheme in self:
            scheme.max_points = 5.0 if scheme.scale == '5' else 4.0

    @api.constrains('line_ids')
    def _check_bands(self):
        for scheme in self:
            lines = scheme.line_ids.sorted('min_mark')
            for line in lines:
                if line.min_mark > line.max_mark:
                    raise ValidationError(_(
                        "Band '%s' has a minimum mark greater than its maximum.",
                        line.letter))
                if line.grade_point > scheme.max_points:
                    raise ValidationError(_(
                        "Band '%(letter)s' grade point %(gp)s exceeds the scheme "
                        "maximum of %(max)s.",
                        letter=line.letter, gp=line.grade_point,
                        max=scheme.max_points))
            # Detect overlapping mark ranges.
            for prev, curr in zip(lines, lines[1:]):
                if curr.min_mark <= prev.max_mark:
                    raise ValidationError(_(
                        "Grade bands '%(a)s' and '%(b)s' overlap on marks.",
                        a=prev.letter, b=curr.letter))

    def grade_for_mark(self, mark):
        """Return ``(letter, grade_point, is_fail)`` for a numeric ``mark``.

        Raises if no band matches so a misconfigured scheme fails loudly rather
        than silently producing a wrong transcript.
        """
        self.ensure_one()
        for line in self.line_ids:
            if line.min_mark <= mark <= line.max_mark:
                return line.letter, line.grade_point, line.is_fail
        raise ValidationError(_(
            "No grade band in scheme '%(scheme)s' matches the mark %(mark)s.",
            scheme=self.display_name, mark=mark))


class UmsGradeSchemeLine(models.Model):
    """One mark band of a grading scheme."""
    _name = 'ums.grade.scheme.line'
    _description = 'Grade Scheme Band'
    _order = 'scheme_id, min_mark desc'

    scheme_id = fields.Many2one(
        'ums.grade.scheme', string='Scheme', required=True,
        ondelete='cascade', index=True,
    )
    letter = fields.Char(string='Letter', required=True)
    letter_ar = fields.Char(string='Letter (Arabic)')
    min_mark = fields.Float(string='Min Mark', required=True)
    max_mark = fields.Float(string='Max Mark', required=True)
    grade_point = fields.Float(string='Grade Point', required=True)
    is_fail = fields.Boolean(string='Failing', default=False)

    _sql_constraints = [
        ('marks_order', 'CHECK(min_mark <= max_mark)',
         'Minimum mark must not exceed the maximum mark.'),
    ]
