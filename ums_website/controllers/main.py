from odoo import http
from odoo.http import request


class UmsWebsite(http.Controller):
    """Public university website + online application capture."""

    def _stats(self):
        env = request.env
        return {
            'program_count': env['ums.program'].sudo().search_count([]),
            'college_count': env['ums.college'].sudo().search_count([]),
            'course_count': env['ums.course'].sudo().search_count([]),
            'student_count': env['ums.student'].sudo().search_count(
                [('status', '=', 'active')]) if 'ums.student' in env else 0,
        }

    @http.route(['/university'], type='http', auth='public', website=True, sitemap=True)
    def university_home(self, **kw):
        programs = request.env['ums.program'].sudo().search([], limit=6)
        values = dict(self._stats(), programs=programs)
        return request.render('ums_website.home', values)

    @http.route(['/university/programs'], type='http', auth='public',
                website=True, sitemap=True)
    def university_programs(self, college=None, **kw):
        domain = []
        if college:
            domain.append(('college_id', '=', int(college)))
        programs = request.env['ums.program'].sudo().search(domain)
        colleges = request.env['ums.college'].sudo().search([])
        return request.render('ums_website.programs', {
            'programs': programs, 'colleges': colleges,
            'active_college': int(college) if college else False})

    @http.route(['/university/apply'], type='http', auth='public',
                website=True, sitemap=True)
    def university_apply(self, program=None, **kw):
        programs = request.env['ums.program'].sudo().search([])
        return request.render('ums_website.apply', {
            'programs': programs,
            'selected_program': int(program) if program else False,
            'error': kw.get('error')})

    @http.route(['/university/apply/submit'], type='http', auth='public',
                website=True, methods=['POST'], csrf=True)
    def university_apply_submit(self, **post):
        name = (post.get('name') or '').strip()
        email = (post.get('email') or '').strip()
        if not name or not email:
            return request.redirect('/university/apply?error=1')
        program_id = False
        if post.get('program_id'):
            try:
                program_id = int(post['program_id'])
            except (ValueError, TypeError):
                program_id = False
        request.env['ums.lead'].sudo().create({
            'name': name,
            'email': email,
            'phone': (post.get('phone') or '').strip(),
            'national_id': (post.get('national_id') or '').strip(),
            'program_id': program_id,
            'source': 'website',
            'stage': 'new',
        })
        return request.render('ums_website.apply_thanks', {'name': name})
