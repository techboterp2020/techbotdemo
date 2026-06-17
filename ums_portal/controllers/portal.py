from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class UmsPortal(CustomerPortal):
    """Expose the logged-in student's academic record on the Odoo portal
    (RFP unified portal)."""

    def _get_student(self):
        """Return the student tied to the current user.

        Falls back to a sample student for staff/admin so the page is populated
        during demos and back-office previews (a portal student always resolves
        to their own record and never hits the fallback).
        """
        partner = request.env.user.partner_id
        Student = request.env['ums.student'].sudo()
        student = Student.search([('partner_id', '=', partner.id)], limit=1)
        if not student and request.env.user.has_group(
                'ums_core.ums_group_academic_user'):
            student = Student.search([], limit=1)
        return student

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'registration_count' in counters:
            student = self._get_student()
            values['registration_count'] = len(student.registration_ids) \
                if student else 0
        return values

    @http.route(['/my/academics'], type='http', auth='user', website=True)
    def portal_my_academics(self, **kw):
        student = self._get_student()
        if not student:
            return request.redirect('/my')
        standing = student.standing_ids[:1]
        values = {
            'student': student,
            'registrations': student.registration_ids.filtered(
                lambda r: r.state in ('registered', 'confirmed', 'completed', 'failed')),
            'holds': student.hold_ids.filtered('active'),
            'cgpa': standing.cgpa if standing else 0.0,
            'is_preview': student.partner_id != request.env.user.partner_id,
            'page_name': 'academics',
        }
        return request.render('ums_portal.portal_my_academics', values)
