from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class UmsPortal(CustomerPortal):
    """Expose the logged-in student's academic record on the Odoo portal
    (RFP unified portal)."""

    def _get_student(self):
        partner = request.env.user.partner_id
        return request.env['ums.student'].sudo().search(
            [('partner_id', '=', partner.id)], limit=1)

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        student = self._get_student()
        if 'registration_count' in counters:
            values['registration_count'] = len(student.registration_ids) \
                if student else 0
        return values

    @http.route(['/my/academics'], type='http', auth='user', website=True)
    def portal_my_academics(self, **kw):
        student = self._get_student()
        if not student:
            return request.redirect('/my')
        values = {
            'student': student,
            'registrations': student.registration_ids.filtered(
                lambda r: r.state in ('registered', 'confirmed', 'completed', 'failed')),
            'holds': student.hold_ids.filtered('active'),
            'page_name': 'academics',
        }
        return request.render('ums_portal.portal_my_academics', values)
