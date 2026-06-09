from odoo import fields, models


class TourBrand(models.Model):
    _name = 'oceanair.brand'
    _description = 'Group Brand / Business Unit'
    _order = 'sequence, name'

    name = fields.Char(string='Brand', required=True)
    code = fields.Char(string='Code')
    sequence = fields.Integer(default=10)
    segment = fields.Selection([
        ('travel', 'Travel & Tours'),
        ('desert', 'Desert Camps & Resorts'),
        ('fnb', 'Food & Beverage'),
        ('equestrian', 'Equestrian'),
        ('mobility', 'Mobility'),
    ], string='Segment', default='travel')
    active = fields.Boolean(default=True)
