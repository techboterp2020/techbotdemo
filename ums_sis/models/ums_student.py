from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UmsStudent(models.Model):
    """Master student record (FR-SIS-01). Delegates personal data to res.partner
    so a student is also a contact/finance party keyed on National ID."""
    _name = 'ums.student'
    _description = 'Student'
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'university_id'

    partner_id = fields.Many2one(
        'res.partner', string='Related Partner', required=True,
        ondelete='restrict', auto_join=True, index=True,
    )
    university_id = fields.Char(
        string='University ID', copy=False, readonly=True,
        default=lambda self: _('New'), tracking=True,
    )
    program_id = fields.Many2one(
        'ums.program', string='Program', required=True, tracking=True, index=True)
    study_plan_id = fields.Many2one(
        'ums.study.plan', string='Study Plan', tracking=True,
        domain="[('program_id', '=', program_id), ('state', '=', 'active')]")
    college_id = fields.Many2one(
        related='program_id.college_id', store=True, string='College', index=True)
    department_id = fields.Many2one(
        related='program_id.department_id', store=True, string='Department', index=True)
    advisor_id = fields.Many2one(
        'res.users', string='Academic Advisor', tracking=True, index=True)
    admission_term_id = fields.Many2one('ums.term', string='Admission Term')
    level = fields.Integer(string='Current Level', default=1, tracking=True)
    gender = fields.Selection(
        selection=[('male', 'Male'), ('female', 'Female')],
        string='Gender', required=True, default='male', tracking=True,
    )
    status = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('leave', 'On Leave'),
            ('suspended', 'Suspended'),
            ('withdrawn', 'Withdrawn'),
            ('graduated', 'Graduated'),
            ('dismissed', 'Dismissed'),
        ],
        string='Status', default='active', required=True, tracking=True,
    )

    registration_ids = fields.One2many(
        'ums.registration', 'student_id', string='Registrations')
    hold_ids = fields.One2many('ums.hold', 'student_id', string='Holds')
    advising_note_ids = fields.One2many(
        'ums.advising.note', 'student_id', string='Advising Notes')
    standing_ids = fields.One2many(
        'ums.academic.standing', 'student_id', string='Academic Standing')
    status_history_ids = fields.One2many(
        'ums.student.status.history', 'student_id', string='Status History')

    active_hold_count = fields.Integer(
        string='Active Holds', compute='_compute_active_holds')
    has_blocking_hold = fields.Boolean(compute='_compute_active_holds')
    completed_credit_hours = fields.Integer(
        string='Completed CH', compute='_compute_credit_hours')

    _sql_constraints = [
        ('university_id_uniq', 'unique(university_id)',
         'The University ID must be unique.'),
    ]

    @api.depends('hold_ids.active', 'hold_ids.blocks_registration')
    def _compute_active_holds(self):
        for student in self:
            active = student.hold_ids.filtered('active')
            student.active_hold_count = len(active)
            student.has_blocking_hold = any(active.mapped('blocks_registration'))

    @api.depends('registration_ids.state', 'registration_ids.credit_hours')
    def _compute_credit_hours(self):
        for student in self:
            student.completed_credit_hours = sum(
                student.registration_ids.filtered(
                    lambda r: r.state == 'completed').mapped('credit_hours'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('university_id', _('New')) == _('New'):
                vals['university_id'] = self.env['ir.sequence'].next_by_code(
                    'ums.student') or _('New')
            vals['is_ums_student'] = True
            vals['is_company'] = False
        students = super().create(vals_list)
        for student in students:
            student._log_status_change(False, student.status, _('Initial record'))
        return students

    def write(self, vals):
        if 'status' in vals:
            for student in self:
                if student.status != vals['status']:
                    student._log_status_change(
                        student.status, vals['status'],
                        vals.pop('status_change_reason', _('Status updated')))
        return super().write(vals)

    def _log_status_change(self, old_status, new_status, reason):
        self.ensure_one()
        self.env['ums.student.status.history'].create({
            'student_id': self.id,
            'old_status': old_status or False,
            'new_status': new_status,
            'reason': reason,
            'effective_date': fields.Date.context_today(self),
            'changed_by': self.env.user.id,
        })

    def change_status(self, new_status, reason):
        """Public API to transition status with an audited reason (FR-SIS-07)."""
        self.write({'status': new_status, 'status_change_reason': reason})

    def action_view_registrations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Registrations'),
            'res_model': 'ums.registration',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def get_enrollment_letter_data(self):
        """Data for the bilingual enrollment verification letter (FR-SIS-09)."""
        self.ensure_one()
        term = self.env['ums.term'].get_current_term()
        return {
            'student': self,
            'term': term,
            'active_registrations': self.registration_ids.filtered(
                lambda r: r.term_id == term and r.state in ('registered', 'confirmed')),
        }
