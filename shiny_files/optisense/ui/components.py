"""UI helper shared by the pages: static text that the browser translates."""

from shiny import ui

from ..i18n import t


def tr(key, tag="span", **attrs):
    """Static text translated in the browser (see www/optisense.js). English is the fallback content."""
    return getattr(ui.tags, tag)(t("en", key), {"data-i18n": key}, **attrs)
