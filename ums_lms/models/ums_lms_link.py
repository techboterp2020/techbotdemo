from odoo import fields, models


class UmsLmsLink(models.Model):
    """Configuration for an external LMS integration (FR-LMS-05).

    Abstracts the connector so endpoints/credentials are configuration, not
    code. Standards hooks: LTI 1.3/Advantage, OneRoster, SCORM, xAPI. Proctoring
    is explicitly out of scope per the commercial RFP.
    """
    _name = 'ums.lms.link'
    _description = 'LMS Integration Link'

    name = fields.Char(string='Name', required=True)
    lms_type = fields.Selection(
        selection=[
            ('moodle', 'Moodle'),
            ('canvas', 'Canvas'),
            ('blackboard', 'Blackboard'),
            ('odoo_elearning', 'Odoo eLearning'),
            ('other', 'Other'),
        ],
        string='LMS', required=True, default='moodle',
    )
    base_url = fields.Char(string='Base URL')
    # Interoperability standards supported by this connector.
    standard = fields.Selection(
        selection=[
            ('lti13', 'LTI 1.3 / Advantage'),
            ('oneroster', 'OneRoster'),
            ('scorm', 'SCORM'),
            ('xapi', 'xAPI'),
            ('rest', 'REST / JSON'),
        ],
        string='Primary Standard', default='lti13',
    )
    client_id = fields.Char(string='Client ID')
    deployment_id = fields.Char(string='LTI Deployment ID')
    sync_roster = fields.Boolean(string='Sync Rosters', default=True)
    sync_grades = fields.Boolean(string='Grade Pass-back', default=True)
    active = fields.Boolean(default=True)

    def action_sync_roster(self):
        """Placeholder for roster push to the LMS (integration point).

        Real implementations enqueue an outbound, retried, logged call per the
        integration architecture (Section 8). Returns the count that would sync.
        """
        self.ensure_one()
        sections = self.env['ums.section'].search([('state', '=', 'open')])
        return {'sections': len(sections),
                'students': sum(len(s.registration_ids) for s in sections)}
