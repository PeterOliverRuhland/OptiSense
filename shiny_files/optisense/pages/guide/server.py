"""The guide: all sections in the chosen language, each with its figure from www/guide/<lang>/."""

from htmltools import HTML, TagList, tags
from shiny import render

from optisense.i18n import guide, norm_lang

from .content import FIGURES, GUIDE_ORDER


def register(ctx):
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
