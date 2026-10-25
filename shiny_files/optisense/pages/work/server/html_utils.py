"""Small HTML helpers for the content of “Model & solution”."""

import re

from htmltools import tags

from optisense.config import constraint_style
from optisense.i18n import fmt_num


def esc(text):
    """Escape text for use inside HTML."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def fmt_html(template, **html_parts):
    """Insert already-escaped HTML (e.g. a coloured name) into an escaped, translated sentence."""
    out = esc(template)
    for key, value in html_parts.items():
        out = out.replace("{" + key + "}", value)
    return out


def formula(a1, a2, lang):
    """a1·x1 + a2·x2 without zero terms and without a written 1."""
    parts = []
    for coef, var in ((a1, "x1"), (a2, "x2")):
        if coef == 0:
            continue
        parts.append(f"{'' if coef == 1 else fmt_num(coef, lang) + '·'}{var}")
    return " + ".join(parts) if parts else "0"


def con_text(con, lang):
    return f"{formula(con['a1'], con['a2'], lang)} {con['op']} {fmt_num(con['b'], lang)}"


def swatch(color, dashed=False):
    cls = "os-swatch is-dashed" if dashed else "os-swatch"
    return tags.span(class_=cls, style=f"background:{color};color:{color}", **{"aria-hidden": "true"})


def con_swatch(con):
    color, line = constraint_style(con["color_index"])
    return swatch(color, dashed=(line != "-"))


def colored_name(name, color):
    return tags.span(name, class_="os-name", style=f"color:{color}")


def safe_filename(name, default):
    name = re.sub(r"[^\w\- .]", "_", (name or "").strip())[:80].strip(" .")
    return name or default
