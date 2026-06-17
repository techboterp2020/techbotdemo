from odoo import api, fields, models


class UmsBilingualMixin(models.AbstractModel):
    """Shared Arabic-first bilingual naming for catalog entities.

    Stores an Arabic (primary) and English (secondary) name and exposes a
    computed ``name`` used as the record display name. Both names print on
    official documents (NFR-LOC-01).
    """
    _name = 'ums.bilingual.mixin'
    _description = 'UMS Bilingual Naming Mixin'

    name_ar = fields.Char(string='Name (Arabic)', required=True, translate=False)
    name_en = fields.Char(string='Name (English)', required=True, translate=False)
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        index=True,
    )

    @api.depends('name_ar', 'name_en')
    def _compute_name(self):
        # English is used as the technical display label for back-office search;
        # the Arabic name is always available and printed alongside it.
        for record in self:
            record.name = record.name_en or record.name_ar or ''

    @api.depends('name_ar', 'name_en')
    def _compute_display_name(self):
        for record in self:
            parts = [p for p in (record.name_en, record.name_ar) if p]
            record.display_name = ' / '.join(parts) or record._description
