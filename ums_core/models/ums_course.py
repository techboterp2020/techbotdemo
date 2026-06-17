from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UmsCourse(models.Model):
    """Bilingual course catalog entry (FR-ACS-03)."""
    _name = 'ums.course'
    _description = 'Course'
    _inherit = ['ums.bilingual.mixin', 'mail.thread']
    _order = 'code'

    code = fields.Char(string='Course Code', required=True, copy=False, tracking=True)
    department_id = fields.Many2one(
        'ums.department', string='Owning Department',
        required=True, ondelete='restrict', tracking=True, index=True,
    )
    college_id = fields.Many2one(
        'ums.college', related='department_id.college_id',
        store=True, string='College', index=True,
    )

    credit_hours = fields.Integer(string='Credit Hours', required=True, tracking=True)
    lecture_hours = fields.Float(string='Lecture Hours', default=0.0)
    lab_hours = fields.Float(string='Lab Hours', default=0.0)
    tutorial_hours = fields.Float(string='Tutorial Hours', default=0.0)
    contact_hours = fields.Float(
        string='Contact Hours', compute='_compute_contact_hours', store=True,
        help='Total weekly contact hours (lecture + lab + tutorial).',
    )

    level = fields.Integer(
        string='Level', help='Academic level / year the course is normally taken at.')
    course_type = fields.Selection(
        selection=[
            ('university', 'University Requirement'),
            ('college', 'College Requirement'),
            ('major', 'Major / Core'),
            ('elective', 'Elective'),
            ('remedial', 'Remedial / Preparatory'),
        ],
        string='Course Type', required=True, default='major', tracking=True,
    )
    description = fields.Text(string='Description', translate=True)
    active = fields.Boolean(default=True)

    # FR-ACS-04 — prerequisites, co-requisites and equivalencies.
    prerequisite_ids = fields.One2many(
        'ums.course.prerequisite', 'course_id', string='Prerequisites')
    equivalent_course_ids = fields.Many2many(
        'ums.course', 'ums_course_equivalency_rel',
        'course_id', 'equivalent_id', string='Equivalent Courses',
    )
    learning_outcome_ids = fields.One2many(
        'ums.learning.outcome', 'course_id', string='Course Learning Outcomes',
        domain=[('outcome_type', '=', 'clo')],
    )

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The course code must be unique.'),
        ('credit_hours_positive', 'CHECK(credit_hours >= 0)',
         'Credit hours cannot be negative.'),
    ]

    @api.depends('lecture_hours', 'lab_hours', 'tutorial_hours')
    def _compute_contact_hours(self):
        for course in self:
            course.contact_hours = (
                course.lecture_hours + course.lab_hours + course.tutorial_hours)

    @api.constrains('equivalent_course_ids')
    def _check_equivalency_not_self(self):
        for course in self:
            if course in course.equivalent_course_ids:
                raise ValidationError(_(
                    "Course '%s' cannot be equivalent to itself.",
                    course.display_name))

    @api.constrains('credit_hours', 'contact_hours')
    def _check_hours_required(self):
        for course in self:
            if course.course_type != 'remedial' and course.credit_hours <= 0:
                raise ValidationError(_(
                    "Course '%s' must have at least one credit hour.",
                    course.display_name))
            if course.contact_hours <= 0:
                raise ValidationError(_(
                    "Course '%s' must define contact hours (lecture/lab/tutorial).",
                    course.display_name))

    def get_all_prerequisites(self):
        """Return the transitive set of prerequisite courses (excluding self)."""
        self.ensure_one()
        seen = self.env['ums.course']
        frontier = self.prerequisite_ids.filtered(
            lambda p: p.relation_type == 'prerequisite'
        ).mapped('prerequisite_course_id')
        while frontier:
            new = frontier - seen - self
            seen |= new
            frontier = new.mapped('prerequisite_ids').filtered(
                lambda p: p.relation_type == 'prerequisite'
            ).mapped('prerequisite_course_id')
        return seen
