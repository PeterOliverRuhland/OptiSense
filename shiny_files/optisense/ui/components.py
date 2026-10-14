"""Small reusable UI pieces: translated text, help button, step card."""

from shiny import ui

from ..i18n import t


def tr(key, tag="span", **attrs):
    """Static text translated in the browser (see www/optisense.js). English is the fallback content."""
    return getattr(ui.tags, tag)(t("en", key), {"data-i18n": key}, **attrs)


def help_button(topic):
    return ui.tags.button("?", type="button", class_="os-help", **{"data-help": topic, "data-i18n-aria": "help",
                                                                    "aria-label": "Help"})


def step_card(number, title_key, help_topic, *body, extra=None):
    return ui.div(
        ui.div(
            ui.span(str(number), class_="os-num"),
            tr(title_key, class_="os-step-title"),
            extra,
            help_button(help_topic),
            class_="os-step-head",
        ),
        ui.div(*body, class_="os-step-body"),
        class_="os-card os-step",
        id=f"os-step-{number}",
    )


