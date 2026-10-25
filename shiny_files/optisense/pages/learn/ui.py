"""Layout of “Learn & practise”: one empty panel; www/learn.js draws the page, server.py answers it."""

from shiny import ui

from optisense.ui.components import tr

STYLESHEET, SCRIPT = "learn.css", "learn.js"

panel = ui.nav_panel(
    tr("tab_learn"),
    ui.div(id="os-learn", class_="os-learn html-fill-item"),
    value="learn",
)
