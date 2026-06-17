from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _


class UmsAssignment(models.Model):
    """An assignment with a create→submit→grade→approve lifecycle (FR-LMS-01)."""
    _name = 'ums.assignment'
    _description = 'Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date desc'

    name = fields.Char(string='Title', required=True, tracking=True)
    section_id = fields.Many2one(
        'ums.section', string='Section', required=True,
        ondelete='cascade', index=True, tracking=True,
    )
    course_id = fields.Many2one(related='section_id.course_id', store=True, string='Course')
    instructor_id = fields.Many2one(
        related='section_id.instructor_id', store=True, string='Instructor')
    description = fields.Html(string='Instructions')
    max_score = fields.Float(string='Maximum Score', required=True, default=100.0)
    weight = fields.Float(
        string='Weight (%)', help='Contribution to continuous assessment.')
    rubric_id = fields.Many2one('ums.rubric', string='Rubric')
    assigned_date = fields.Date(string='Assigned', default=fields.Date.context_today)
    due_date = fields.Datetime(string='Due', tracking=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('published', 'Published'),
            ('grading', 'Grading'),
            ('approved', 'Approved'),
        ],
        string='Status', default='draft', required=True, tracking=True,
    )
    submission_ids = fields.One2many(
        'ums.assignment.submission', 'assignment_id', string='Submissions')
    submission_count = fields.Integer(compute='_compute_counts')
    graded_count = fields.Integer(compute='_compute_counts')

    @api.depends('submission_ids.state')
    def _compute_counts(self):
        for a in self:
            a.submission_count = len(a.submission_ids)
            a.graded_count = len(a.submission_ids.filtered(
                lambda s: s.state in ('graded', 'approved')))

    def action_publish(self):
        for a in self:
            if not a.due_date:
                raise UserError(_("Set a due date before publishing '%s'.", a.name))
            a.state = 'published'

    def action_start_grading(self):
        self.write({'state': 'grading'})

    def action_approve(self):
        for a in self:
            ungraded = a.submission_ids.filtered(
                lambda s: s.state == 'submitted')
            if ungraded:
                raise UserError(_(
                    "All submissions must be graded before approving '%s'.", a.name))
            a.state = 'approved'


class UmsAssignmentSubmission(models.Model):
    """A student's submission to an assignment (FR-LMS-01/02)."""
    _name = 'ums.assignment.submission'
    _description = 'Assignment Submission'
    _order = 'submitted_date desc'

    assignment_id = fields.Many2one(
        'ums.assignment', string='Assignment', required=True,
        ondelete='cascade', index=True,
    )
    student_id = fields.Many2one(
        'ums.student', string='Student', required=True, ondelete='cascade', index=True)
    submitted_date = fields.Datetime(string='Submitted On')
    is_late = fields.Boolean(string='Late', compute='_compute_late', store=True)
    content = fields.Text(string='Submission')
    attachment = fields.Binary(string='File', attachment=True)
    filename = fields.Char(string='Filename')
    score = fields.Float(string='Score')
    rubric_score_ids = fields.One2many(
        'ums.submission.rubric.score', 'submission_id', string='Rubric Scores')
    feedback = fields.Text(string='Feedback')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('graded', 'Graded'),
            ('approved', 'Approved'),
        ],
        string='Status', default='draft', required=True,
    )

    _sql_constraints = [
        ('assignment_student_uniq', 'unique(assignment_id, student_id)',
         'The student already has a submission for this assignment.'),
    ]

    @api.depends('submitted_date', 'assignment_id.due_date')
    def _compute_late(self):
        for sub in self:
            due = sub.assignment_id.due_date
            sub.is_late = bool(sub.submitted_date and due and sub.submitted_date > due)

    @api.constrains('score')
    def _check_score(self):
        for sub in self:
            if sub.score < 0 or sub.score > sub.assignment_id.max_score:
                raise ValidationError(_(
                    "Score must be between 0 and %s.", sub.assignment_id.max_score))

    def action_submit(self):
        self.write({
            'state': 'submitted',
            'submitted_date': fields.Datetime.now(),
        })

    def action_grade(self):
        for sub in self:
            if sub.rubric_score_ids:
                sub.score = sum(sub.rubric_score_ids.mapped('points'))
            sub.state = 'graded'


class UmsSubmissionRubricScore(models.Model):
    _name = 'ums.submission.rubric.score'
    _description = 'Submission Rubric Score'

    submission_id = fields.Many2one(
        'ums.assignment.submission', string='Submission', required=True,
        ondelete='cascade',
    )
    criterion_id = fields.Many2one(
        'ums.rubric.criterion', string='Criterion', required=True)
    points = fields.Float(string='Points')

    @api.constrains('points', 'criterion_id')
    def _check_points(self):
        for line in self:
            if line.points < 0 or line.points > line.criterion_id.max_points:
                raise ValidationError(_(
                    "Points for '%(c)s' must be between 0 and %(m)s.",
                    c=line.criterion_id.name, m=line.criterion_id.max_points))
