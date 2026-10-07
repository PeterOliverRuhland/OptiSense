"""Small HTML helpers for server-built content."""

import re


def esc(text):
    """Escape text for use inside HTML."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def fmt_html(template, **html_parts):
    """Insert already-escaped HTML (e.g. a coloured name) into an escaped, translated sentence."""
    out = esc(template)
    for key, value in html_parts.items():
        out = out.replace("{" + key + "}", value)
    return out


def safe_filename(name, default):
    name = re.sub(r"[^\w\- .]", "_", (name or "").strip())[:80].strip(" .")
    return name or default
