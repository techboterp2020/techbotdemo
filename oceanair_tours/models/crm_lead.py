from odoo import models, _


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def action_create_tour_booking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Tour Booking'),
            'res_model': 'oceanair.tour.booking',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_sales_agent_id': (self.user_id.id
                                           or self.env.user.id),
                'default_lead_id': self.id,
            },
        }
