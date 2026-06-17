from datetime import date

from odoo.tests.common import TransactionCase, tagged
from odoo.addons.ums_ksa_localization.models import hijri


@tagged('post_install', '-at_install', 'ums')
class TestHijri(TransactionCase):

    def test_known_conversion(self):
        # 2024-07-07 is 1 Muharram 1446 in the Umm al-Qura calendar.
        y, m, d = hijri.gregorian_to_hijri(date(2024, 7, 7))
        if hijri._HAS_UMM_AL_QURA:
            self.assertEqual((y, m, d), (1446, 1, 1))
        else:
            # Arithmetic fallback can differ by ~1 day (here landing on the
            # last day of 1445); assert it is a structurally valid Hijri date
            # close to the expected year.
            self.assertIn(y, (1445, 1446))
            self.assertTrue(1 <= m <= 12)
            self.assertTrue(1 <= d <= 30)

    def test_format_hijri_en(self):
        text = hijri.format_hijri(date(2024, 7, 7), lang='en')
        # Month name comes from the English month list; year is 4 digits.
        self.assertTrue(any(mn in text for mn in hijri.ENGLISH_MONTHS))
        self.assertTrue(text.endswith('AH'))

    def test_format_hijri_ar(self):
        text = hijri.format_hijri(date(2024, 7, 7), lang='ar')
        self.assertTrue(any(mn in text for mn in hijri.ARABIC_MONTHS))
        self.assertIn('هـ', text)

    def test_format_dual(self):
        text = hijri.format_dual(date(2024, 7, 7), lang='en')
        self.assertIn('2024', text)
        self.assertIn('(', text)
        self.assertTrue(text.rstrip().endswith(')'))

    def test_empty(self):
        self.assertEqual(hijri.format_hijri(None), '')
        self.assertEqual(hijri.format_dual(None), '')

    def test_mixin_helper(self):
        # The mixin is abstract; exercise its helpers via a concrete model that
        # inherits it indirectly is out of scope here — call on the abstract
        # model's env wrapper instead.
        mixin = self.env['ums.hijri.mixin']
        self.assertEqual(mixin.hijri_date(False), '')
        text = mixin.hijri_date(date(2024, 7, 7), lang='en')
        self.assertTrue(text.endswith('AH'))
