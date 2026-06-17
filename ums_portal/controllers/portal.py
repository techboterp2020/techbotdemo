from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class UmsPortal(CustomerPortal):
    """Student and faculty self-service dashboards on the Odoo portal."""

    def _get_student(self):
        partner = request.env.user.partner_id
        Student = request.env['ums.student'].sudo()
        student = Student.search([('partner_id', '=', partner.id)], limit=1)
        if not student and not request.env.user.share:
            student = Student.search([], limit=1)
        return student

    def _get_sections(self):
        Section = request.env['ums.section'].sudo()
        sections = Section.search([('instructor_id', '=', request.env.user.id)])
        is_preview = False
        if not sections and not request.env.user.share:
            sections = Section.search([], limit=12)
            is_preview = True
        return sections, is_preview

    @staticmethod
    def _attendance_stats(lines):
        present = len(lines.filtered(lambda l: l.status in ('present', 'late')))
        absent = len(lines.filtered(lambda l: l.status == 'absent'))
        total = present + absent
        deg = round(present / total * 360) if total else 0
        pct = round(present / total * 100) if total else 0
        return {'present': present, 'absent': absent, 'total': total,
                'deg': deg, 'pct': pct}

    # ---------------------------------------------------------------- student
    @http.route(['/my/academics'], type='http', auth='user', website=True)
    def portal_my_academics(self, **kw):
        student = self._get_student()
        if not student:
            return request.redirect('/my')
        standing = student.standing_ids[:1]
        att_lines = request.env['ums.attendance.line'].sudo().search(
            [('student_id', '=', student.id)])
        registrations = student.registration_ids.filtered(
            lambda r: r.state in ('registered', 'confirmed', 'completed', 'failed'))
        values = {
            'student': student,
            'registrations': registrations,
            'holds': student.hold_ids.filtered('active'),
            'cgpa': standing.cgpa if standing else 0.0,
            'completed_ch': student.completed_credit_hours,
            'attendance': self._attendance_stats(att_lines),
            'is_preview': student.partner_id != request.env.user.partner_id,
            'page_name': 'academics',
        }
        return request.render('ums_portal.portal_my_academics', values)

    # ---------------------------------------------------------------- faculty
    @http.route(['/my/teaching'], type='http', auth='user', website=True)
    def portal_my_teaching(self, **kw):
        sections, is_preview = self._get_sections()
        att_lines = request.env['ums.attendance.line'].sudo().search(
            [('section_id', 'in', sections.ids)])
        assignment_count = request.env['ums.assignment'].sudo().search_count(
            [('section_id', 'in', sections.ids)])
        values = {
            'sections': sections,
            'total_students': sum(s.enrolled_count for s in sections),
            'assignment_count': assignment_count,
            'attendance': self._attendance_stats(att_lines),
            'user_name': request.env.user.name,
            'is_preview': is_preview,
            'page_name': 'teaching',
        }
        return request.render('ums_portal.portal_my_teaching', values)
