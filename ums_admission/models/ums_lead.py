from odoo import api, fields, models
from odoo.tools.translate import _


class UmsLead(models.Model):
    """A recruitment lead / enquiry captured from any channel (FR-ADM-01).

    Leads form the top of the recruitment funnel and convert into applications.
    """
    _name = 'ums.lead'
    _description = 'Admission Lead / Enquiry'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Prospect Name', required=True, tracking=True)
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    national_id = fields.Char(string='National ID / Iqama')
    program_id = fields.Many2one('ums.program', string='Program of Interest')
    intake_id = fields.Many2one('ums.intake', string='Intake')
    source = fields.Selection(
        selection=[
            ('website', 'Website'),
            ('phone', 'Phone'),
            ('email', 'Email'),
            ('walk_in', 'Walk-in'),
            ('event', 'Event / Fair'),
            ('social', 'Social Media'),
            ('referral', 'Referral'),
            ('agent', 'Agent'),
        ],
        string='Source', default='website', tracking=True,
    )
    stage = fields.Selection(
        selection=[
            ('new', 'New'),
            ('contacted', 'Contacted'),
            ('qualified', 'Qualified'),
            ('applied', 'Applied'),
            ('lost', 'Lost'),
        ],
        string='Funnel Stage', default='new', required=True, tracking=True,
    )
    application_id = fields.Many2one(
        'ums.application', string='Application', readonly=True, copy=False)
    salesperson_id = fields.Many2one(
        'res.users', string='Owner', default=lambda self: self.env.user)

    def action_convert_to_application(self):
        """Convert a qualified lead into an application (funnel → app)."""
        self.ensure_one()
        application = self.env['ums.application'].create({
            'partner_name': self.name,
            'email': self.email,
            'phone': self.phone,
            'national_id': self.national_id,
            'program_id': self.program_id.id,
            'intake_id': self.intake_id.id,
            'gender': 'male',
            'source_lead_id': self.id,
        })
        self.write({'stage': 'applied', 'application_id': application.id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ums.application',
            'res_id': application.id,
            'view_mode': 'form',
        }

    @api.model
    def get_funnel_summary(self):
        """Lead counts per funnel stage for recruitment reporting."""
        data = self.read_group([], ['stage'], ['stage'])
        return {d['stage']: d['stage_count'] for d in data}
