from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UmsCoursePrerequisite(models.Model):
    """A prerequisite / co-requisite relation between two courses (FR-ACS-04).

    Circular prerequisite chains are blocked at registration time and here at
    definition time.
    """
    _name = 'ums.course.prerequisite'
    _description = 'Course Prerequisite'
    _rec_name = 'prerequisite_course_id'

    course_id = fields.Many2one(
        'ums.course', string='Course', required=True,
        ondelete='cascade', index=True,
    )
    prerequisite_course_id = fields.Many2one(
        'ums.course', string='Required Course', required=True,
        ondelete='restrict', index=True,
    )
    relation_type = fields.Selection(
        selection=[
            ('prerequisite', 'Prerequisite (before)'),
            ('corequisite', 'Co-requisite (same term)'),
        ],
        string='Relation', required=True, default='prerequisite',
    )
    min_grade_point = fields.Float(
        string='Minimum Grade Point',
        help='Minimum grade point required in the prerequisite course '
             '(0 = pass only).',
    )

    _sql_constraints = [
        ('unique_relation',
         'unique(course_id, prerequisite_course_id, relation_type)',
         'This prerequisite relation already exists for the course.'),
    ]

    @api.constrains('course_id', 'prerequisite_course_id', 'relation_type')
    def _check_circular(self):
        for rel in self:
            if rel.course_id == rel.prerequisite_course_id:
                raise ValidationError(_(
                    "A course cannot be a prerequisite of itself (%s).",
                    rel.course_id.display_name))
            # Only hard prerequisites can form a blocking cycle.
            if rel.relation_type != 'prerequisite':
                continue
            # If the new required course (transitively) already requires this
            # course, adding the relation would create a cycle.
            chain = rel.prerequisite_course_id.get_all_prerequisites()
            if rel.course_id in chain:
                raise ValidationError(_(
                    "Circular prerequisite detected: '%s' already depends on "
                    "'%s'.",
                    rel.prerequisite_course_id.display_name,
                    rel.course_id.display_name))
