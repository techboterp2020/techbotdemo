"""Hijri (Islamic) calendar conversion utilities.

Prefers the ``hijri_converter`` package (official Umm al-Qura tabular data,
1343–1500 AH) when it is installed; otherwise falls back to the well-known
arithmetic (tabular civil) Islamic calendar, which can differ from the
official Umm al-Qura calendar by ±1 day. For production transcripts and
certificates install ``hijri_converter`` so dates match the Umm al-Qura
calendar exactly.
"""
import logging

_logger = logging.getLogger(__name__)

try:
    from hijri_converter import Gregorian, Hijri  # type: ignore
    _HAS_UMM_AL_QURA = True
except Exception:  # pragma: no cover - depends on optional package
    _HAS_UMM_AL_QURA = False

ARABIC_MONTHS = [
    'محرم', 'صفر', 'ربيع الأول', 'ربيع الآخر', 'جمادى الأولى', 'جمادى الآخرة',
    'رجب', 'شعبان', 'رمضان', 'شوال', 'ذو القعدة', 'ذو الحجة',
]
ENGLISH_MONTHS = [
    'Muharram', 'Safar', "Rabi' al-Awwal", "Rabi' al-Thani",
    'Jumada al-Ula', 'Jumada al-Akhirah', 'Rajab', "Sha'ban",
    'Ramadan', 'Shawwal', "Dhu al-Qa'dah", 'Dhu al-Hijjah',
]


def _gregorian_to_jd(y, m, d):
    a = (14 - m) // 12
    y2 = y + 4800 - a
    m2 = m + 12 * a - 3
    return (d + (153 * m2 + 2) // 5 + 365 * y2 + y2 // 4
            - y2 // 100 + y2 // 400 - 32045)


def _arithmetic_g2h(y, m, d):
    """Arithmetic (tabular) Gregorian -> Hijri fallback."""
    jd = _gregorian_to_jd(y, m, d)
    l = jd - 1948440 + 10632
    n = (l - 1) // 10631
    l = l - 10631 * n + 354
    j = ((10985 - l) // 5316) * ((50 * l) // 17719) + (l // 5670) * ((43 * l) // 15238)
    l = l - ((30 - j) // 15) * ((17719 * j) // 50) - (j // 16) * ((15238 * j) // 43) + 29
    hm = (24 * l) // 709
    hd = l - (709 * hm) // 24
    hy = 30 * n + j - 30
    return int(hy), int(hm), int(hd)


def gregorian_to_hijri(date):
    """Return an ``(year, month, day)`` Hijri tuple for a ``datetime.date``."""
    if _HAS_UMM_AL_QURA:
        try:
            h = Gregorian(date.year, date.month, date.day).to_hijri()
            return h.year, h.month, h.day
        except Exception:  # outside Umm al-Qura coverage -> fallback
            _logger.debug("Umm al-Qura out of range for %s, using arithmetic", date)
    return _arithmetic_g2h(date.year, date.month, date.day)


def format_hijri(date, lang='en', with_label=True):
    """Format ``date`` as a Hijri string, e.g. ``'15 Ramadan 1447 AH'``."""
    if not date:
        return ''
    y, m, d = gregorian_to_hijri(date)
    months = ARABIC_MONTHS if lang == 'ar' else ENGLISH_MONTHS
    month_name = months[m - 1] if 1 <= m <= 12 else str(m)
    if lang == 'ar':
        text = f'{d} {month_name} {y}'
        return f'{text} هـ' if with_label else text
    text = f'{d} {month_name} {y}'
    return f'{text} AH' if with_label else text


def format_dual(date, lang='en'):
    """Return ``'<gregorian> (<hijri>)'`` for official documents."""
    if not date:
        return ''
    greg = date.strftime('%d %b %Y')
    return f'{greg} ({format_hijri(date, lang=lang)})'
