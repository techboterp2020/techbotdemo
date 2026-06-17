from odoo import fields, models


class UmsRoom(models.Model):
    """A teaching room / hall used for sections and exams (FR-CAL-04/05)."""
    _name = 'ums.room'
    _description = 'Room'
    _order = 'building, code'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True, copy=False)
    building = fields.Char(string='Building')
    capacity = fields.Integer(string='Capacity', required=True, default=30)
    exam_capacity = fields.Integer(
        string='Exam Capacity',
        help='Reduced seating capacity for invigilated exams.')
    room_type = fields.Selection(
        selection=[
            ('lecture', 'Lecture Hall'),
            ('lab', 'Laboratory'),
            ('seminar', 'Seminar Room'),
            ('exam', 'Exam Hall'),
        ],
        string='Type', default='lecture',
    )
    gender = fields.Selection(
        selection=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('mixed', 'Mixed'),
        ],
        string='Gender Designation', default='mixed',
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The room code must be unique.'),
    ]
