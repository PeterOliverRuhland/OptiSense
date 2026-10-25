"""Layout of the guide: sticky contents list on the left, the sections (server.py) on the right."""

from shiny import ui

from optisense.ui.components import tr

from .content import GUIDE_ORDER

STYLESHEET, SCRIPT = "guide.css", "guide.js"

panel = ui.nav_panel(
    tr("tab_guide"),
    ui.div(
        ui.tags.nav(
            tr("guide_contents", tag="div", class_="os-guide-nav-title"),
            *[ui.tags.a(tr(label_key), href=f"#guide-{topic}", class_="os-guide-tab", **{"data-guide": topic})
              for topic, label_key in GUIDE_ORDER],
            class_="os-guide-nav os-card",
            **{"data-i18n-aria": "guide_contents", "aria-label": "Contents"},
        ),
        ui.div(ui.output_ui("guide_view"), class_="os-doc"),
        class_="os-guide",
    ),
    value="guide",
)
