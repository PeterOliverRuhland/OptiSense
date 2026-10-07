"""The guide tab and the contextual help dialogs behind the ? buttons."""

from htmltools import HTML, TagList, tags
from shiny import reactive, render, ui

from ..i18n import GUIDE_ORDER, guide

TOPICS = dict(GUIDE_ORDER)


def register(ctx):
    input = ctx.input
    tr = ctx.tr

    @render.ui
    def guide_view():
        topic = input.guide_topic() if "guide_topic" in input else None
        topic = topic if topic in TOPICS else "steps"
        parts = [tags.h2(tr(TOPICS[topic])), HTML(guide(ctx.lang(), topic))]
        if topic == "example":
            parts.append(ui.input_action_button("guide_load_example", tr("load_example"), class_="os-btn os-btn-primary"))
        return TagList(*parts)

    @reactive.effect
    @reactive.event(input.help_topic)
    def _help():
        topic = input.help_topic()["topic"]
        if topic not in TOPICS:
            return
        ui.modal_show(ui.modal(
            tags.div(HTML(guide(ctx.lang(), topic)), class_="os-guide-body os-guide-body--modal"),
            title=tr(TOPICS[topic]),
            footer=ui.modal_button(tr("close"), class_="os-btn"),
            easy_close=True, size="l",
        ))
