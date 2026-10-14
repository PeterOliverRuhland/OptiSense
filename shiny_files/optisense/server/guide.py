"""The guide tab and the contextual help dialogs behind the ? buttons."""

from htmltools import HTML, TagList, tags
from shiny import reactive, render, ui

from ..i18n import FIGURES, GUIDE_ORDER, guide, norm_lang

TOPICS = dict(GUIDE_ORDER)
# the ? of each step: dialog title and the guide sections it shows
HELP = {"steps": ("guide_steps", ["steps"]), "range": ("step2", ["range"]), "solve": ("step3", ["lp", "sens"])}


def register(ctx):
    input = ctx.input
    tr = ctx.tr

    def figure(topic):
        if topic not in FIGURES:
            return None
        name, caption_key = FIGURES[topic]
        caption = tr(caption_key)
        src = f"guide/{norm_lang(ctx.lang())}/{name}"
        return tags.figure(
            tags.a(tags.img(src=src, alt=caption, loading="lazy"), href=src, target="_blank", rel="noopener"),
            tags.figcaption(caption),
            class_="os-doc-figure",
        )

    @render.ui
    def guide_view():
        """All sections on one page; the navigation on the left scrolls to them."""
        sections = []
        for topic, label_key in GUIDE_ORDER:
            fig = figure(topic)
            sections.append(tags.section(
                tags.div(tags.h2(tr(label_key)), HTML(guide(ctx.lang(), topic)), class_="os-doc-text"),
                fig,
                id=f"guide-{topic}",
                class_="os-doc-section os-card" + (" has-figure" if fig is not None else ""),
            ))
        return TagList(*sections)

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
