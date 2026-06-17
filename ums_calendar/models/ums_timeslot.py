from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

DAY_SELECTION = [
    ('6', 'Sunday'),
    ('0', 'Monday'),
    ('1', 'Tuesday'),
    ('2', 'Wednesday'),
    ('3', 'Thursday'),
    ('4', 'Friday'),
    ('5', 'Saturday'),
]


class UmsTimeSlot(models.Model):
    """A weekly time slot (day + start/end hour) for timetabling (FR-CAL-04).

    Days follow Python's weekday numbering (0=Mon … 6=Sun); the Saudi week runs
    Sunday–Thursday.
    """
    _name = 'ums.timeslot'
    _description = 'Time Slot'
    _order = 'dayofweek, hour_from'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    dayofweek = fields.Selection(
        DAY_SELECTION, string='Day', required=True, default='6')
    hour_from = fields.Float(string='From', required=True)
    hour_to = fields.Float(string='To', required=True)

    @api.depends('dayofweek', 'hour_from', 'hour_to')
    def _compute_name(self):
        labels = dict(DAY_SELECTION)
        for slot in self:
            day = labels.get(slot.dayofweek, '')
            slot.name = '%s %02d:%02d–%02d:%02d' % (
                day, int(slot.hour_from), round((slot.hour_from % 1) * 60),
                int(slot.hour_to), round((slot.hour_to % 1) * 60))

    @api.constrains('hour_from', 'hour_to')
    def _check_hours(self):
        for slot in self:
            if not (0 <= slot.hour_from < slot.hour_to <= 24):
                raise ValidationError(_(
                    "Time slot hours must satisfy 0 ≤ from < to ≤ 24."))

    def overlaps(self, other):
        """True if this slot and ``other`` share a day and overlapping hours."""
        self.ensure_one()
        if self.dayofweek != other.dayofweek:
            return False
        return self.hour_from < other.hour_to and other.hour_from < self.hour_to
