"""All user-facing text of OptiSense in English (source) and German.

Each page keeps its own texts (pages/work/texts.py, pages/guide/texts.py and content.py, pages/learn/texts.py);
texts used on more than one page are in common.py. This module joins them and translates.

Rules: every string has a key; whole sentences with {placeholders}; mathematical notation
(x1, x2, c1, a1, b, ≤ ≥ =, ℕ0) is never translated.
"""

import json

from ..pages.guide.content import GUIDE
from ..pages.guide.texts import TEXT as GUIDE_TEXT
from ..pages.learn.texts import LEARN
from ..pages.work.texts import TEXT as WORK_TEXT
from .common import TEXT as COMMON_TEXT

# one dictionary for all short texts; the keys of the learning page start with learn_
TEXT = {**COMMON_TEXT, **WORK_TEXT, **GUIDE_TEXT, **LEARN}

LANGS = {"en": "English", "de": "Deutsch"}
DEFAULT_LANG = "en"


def norm_lang(lang):
    return lang if lang in LANGS else DEFAULT_LANG


def t(lang, key, **kwargs):
    entry = TEXT.get(key)
    if entry is None:
        return key
    text = entry.get(norm_lang(lang)) or entry[DEFAULT_LANG]
    return text.format(**kwargs) if kwargs else text


def guide(lang, topic):
    return GUIDE[topic].get(norm_lang(lang)) or GUIDE[topic][DEFAULT_LANG]


def fmt_num(value, lang, digits=4):
    """Number for display: up to `digits` decimals, trailing zeros removed, locale separators.
    German uses 1.500,5; English uses 1,500.5."""
    if value is None:
        return "–"
    if value == float("inf"):
        return "∞"
    if value == float("-inf"):
        return "−∞"
    v = round(float(value), digits)
    if v == 0:
        v = 0.0
    s = f"{v:,.{digits}f}".rstrip("0").rstrip(".")
    if norm_lang(lang) == "de":
        s = s.replace(",", "\u0000").replace(".", ",").replace("\u0000", ".")
    return s.replace("-", "−")


def client_dictionary():
    """The short texts as {lang: {key: text}} for the browser-side translator."""
    out = {code: {} for code in LANGS}
    for key, entry in TEXT.items():
        for code in LANGS:
            out[code][key] = entry.get(code) or entry[DEFAULT_LANG]
    return json.dumps(out, ensure_ascii=False)
