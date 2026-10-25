"""The ? buttons of the steps: a dialog with the matching sections of the guide (pages/guide/content.py)."""

from htmltools import HTML, tags
from shiny import reactive, ui

from optisense.i18n import guide
from optisense.pages.guide.content import GUIDE_ORDER

TOPICS = dict(GUIDE_ORDER)
# the ? of each step: dialog title and the guide sections it shows
HELP = {"steps": ("guide_steps", ["steps"]), "range": ("step2", ["range"]), "solve": ("step3", ["lp", "sens"])}


def register(ctx):
    input = ctx.input
    tr = ctx.tr

    @reactive.effect
    @reactive.event(input.help_topic)
    def _help():
        topic = input.help_topic()["topic"]
        if topic not in HELP:
            return
        title_key, sections = HELP[topic]
        parts = []
        for section in sections:
            if len(sections) > 1:
                parts.append(tags.h2(tr(TOPICS[section])))
            parts.append(HTML(guide(ctx.lang(), section)))
        ui.modal_show(ui.modal(
            tags.div(*parts, class_="os-guide-body os-guide-body--modal"),
            title=tr(title_key),
            footer=ui.modal_button(tr("close"), class_="os-btn"),
            easy_close=True, size="l",
        ))
