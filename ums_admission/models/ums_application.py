from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _


class UmsApplication(models.Model):
    """An admission application with a full committee-review state machine,
    composite scoring, document verification and SIS handover (FR-ADM-03/05/06/
    07/08/09)."""
    _name = 'ums.application'
    _description = 'Admission Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'composite_score desc, create_date desc'

    name = fields.Char(
        string='Application No.', required=True, copy=False, readonly=True,
        default=lambda self: _('New'))
    partner_name = fields.Char(string='Applicant Name', required=True, tracking=True)
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    national_id = fields.Char(string='National ID / Iqama', tracking=True)
    nafath_verified = fields.Boolean(string='Nafath Verified', tracking=True)
    gender = fields.Selection(
        selection=[('male', 'Male'), ('female', 'Female')],
        string='Gender', required=True, default='male',
    )

    program_id = fields.Many2one('ums.program', string='Program', required=True, tracking=True)
    intake_id = fields.Many2one('ums.intake', string='Intake', required=True, tracking=True)
    source_lead_id = fields.Many2one('ums.lead', string='Source Lead', readonly=True)

    # Entrance scores (FR-ADM-03)
    qiyas_score = fields.Float(string='Qiyas (Qudurat)', help='0–100')
    tahsili_score = fields.Float(string='Tahsili', help='0–100')
    hs_gpa = fields.Float(string='High-School GPA (%)', help='Normalised to 0–100')
    composite_score = fields.Float(
        string='Composite Score', compute='_compute_composite', store=True, tracking=True)
    rank = fields.Integer(string='Rank', readonly=True)

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('under_review', 'Under Review'),
            ('shortlisted', 'Shortlisted'),
            ('offer', 'Offer Issued'),
            ('accepted', 'Accepted'),
            ('enrolled', 'Enrolled'),
            ('rejected', 'Rejected'),
            ('waitlisted', 'Waitlisted'),
        ],
        string='Status', default='draft', required=True, tracking=True,
    )
    fee_paid = fields.Boolean(string='Application Fee Paid', tracking=True)
    document_ids = fields.One2many(
        'ums.application.document', 'application_id', string='Documents')
    documents_verified = fields.Boolean(
        string='All Documents Verified', compute='_compute_docs_verified', store=True)
    offer_date = fields.Date(string='Offer Date', readonly=True)
    acceptance_date = fields.Date(string='Acceptance Date', readonly=True)
    student_id = fields.Many2one('ums.student', string='Student', readonly=True, copy=False)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Application number must be unique.'),
    ]

    @api.depends('qiyas_score', 'tahsili_score', 'hs_gpa',
                 'program_id.weight_qiyas', 'program_id.weight_tahsili',
                 'program_id.weight_gpa')
    def _compute_composite(self):
        for app in self:
            program = app.program_id
            app.composite_score = (
                app.qiyas_score * (program.weight_qiyas or 0)
                + app.tahsili_score * (program.weight_tahsili or 0)
                + app.hs_gpa * (program.weight_gpa or 0))

    @api.depends('document_ids.state', 'document_ids.required')
    def _compute_docs_verified(self):
        for app in self:
            required = app.document_ids.filtered('required')
            app.documents_verified = bool(required) and all(
                d.state == 'verified' for d in required)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'ums.application') or _('New')
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # State machine (FR-ADM-06)
    # ------------------------------------------------------------------
    def action_submit(self):
        for app in self:
            if not app.fee_paid:
                raise UserError(_(
                    "Application '%s' cannot be submitted before the application "
                    "fee is paid.", app.name))
            app.state = 'submitted'

    def action_start_review(self):
        self.write({'state': 'under_review'})

    def action_shortlist(self):
        self.write({'state': 'shortlisted'})

    def action_issue_offer(self):
        for app in self:
            if not app.documents_verified:
                raise UserError(_(
                    "Verify all required documents before issuing an offer for "
                    "'%s'.", app.name))
            app._check_quota()
            app.write({
                'state': 'offer',
                'offer_date': fields.Date.context_today(app),
            })

    def action_accept_offer(self):
        for app in self:
            if app.state != 'offer':
                raise UserError(_("Only issued offers can be accepted."))
            app.write({
                'state': 'accepted',
                'acceptance_date': fields.Date.context_today(app),
            })

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_waitlist(self):
        self.write({'state': 'waitlisted'})

    def _check_quota(self):
        self.ensure_one()
        quota = self.intake_id.quota_ids.filtered(
            lambda q: q.program_id == self.program_id
            and q.gender in (self.gender, 'any'))[:1]
        if quota and quota.seats_available <= 0:
            raise ValidationError(_(
                "No seats available for program '%(p)s' (%(g)s) in this intake.",
                p=self.program_id.display_name, g=self.gender))

    # ------------------------------------------------------------------
    # Enrolment — SIS handover (FR-ADM-08)
    # ------------------------------------------------------------------
    def action_enroll(self):
        """Create the student record + partner and hand over to SIS."""
        students = self.env['ums.student']
        for app in self:
            if app.state != 'accepted':
                raise UserError(_(
                    "Only accepted applications can be enrolled (%s).", app.name))
            if app.student_id:
                raise UserError(_(
                    "Application '%s' is already enrolled.", app.name))
            student = students.create({
                'name': app.partner_name,
                'email': app.email,
                'phone': app.phone,
                'national_id': app.national_id,
                'gender': app.gender,
                'program_id': app.program_id.id,
                'admission_term_id': app.intake_id.term_id.id,
            })
            app.write({'state': 'enrolled', 'student_id': student.id})
        return True

    # ------------------------------------------------------------------
    # Ranking (FR-ADM-05)
    # ------------------------------------------------------------------
    @api.model
    def rank_intake(self, intake):
        """Recompute ranks within an intake by composite score (per program)."""
        for program in intake.quota_ids.mapped('program_id'):
            apps = self.search([
                ('intake_id', '=', intake.id),
                ('program_id', '=', program.id),
                ('state', 'not in', ('draft', 'rejected')),
            ], order='composite_score desc')
            for index, app in enumerate(apps, start=1):
                app.rank = index
