from odoo import models
from . import hijri


class UmsHijriMixin(models.AbstractModel):
    """Reusable helpers for dual Hijri/Gregorian display (NFR-LOC-02).

    Models that store Gregorian ``Date``/``Datetime`` fields inherit this mixin
    and expose computed Char fields by calling :meth:`hijri_date` /
    :meth:`dual_date`, so every academic and financial date can be rendered with
    its Hijri equivalent in the UI and on QWeb documents.

    Example::

        class AcademicTerm(models.Model):
            _name = 'ums.term'
            _inherit = ['ums.hijri.mixin']

            greg_start = fields.Date()
            hijri_start = fields.Char(compute='_compute_hijri', store=True)

            @api.depends('greg_start')
            def _compute_hijri(self):
                for rec in self:
                    rec.hijri_start = rec.hijri_date(rec.greg_start)
    """
    _name = 'ums.hijri.mixin'
    _description = 'UMS Hijri Date Mixin'

    def _hijri_lang(self):
        return 'ar' if (self.env.lang or '').startswith('ar') else 'en'

    def hijri_date(self, date_value, lang=None, with_label=True):
        """Return the Hijri string for a Gregorian date/datetime value."""
        if not date_value:
            return ''
        date_value = getattr(date_value, 'date', lambda: date_value)()
        return hijri.format_hijri(
            date_value, lang=lang or self._hijri_lang(), with_label=with_label)

    def dual_date(self, date_value, lang=None):
        """Return ``'<gregorian> (<hijri>)'`` for official documents."""
        if not date_value:
            return ''
        date_value = getattr(date_value, 'date', lambda: date_value)()
        return hijri.format_dual(date_value, lang=lang or self._hijri_lang())
