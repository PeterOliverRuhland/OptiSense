"""Layout of “Learn & practise”: one empty panel; www/learn.js draws the page, server.py answers it."""

import json

from shiny import ui

from optisense.ui.components import tr

from .engine import task_list

STYLESHEET, SCRIPT = "learn.css", "learn.js"

panel = ui.nav_panel(
    tr("tab_learn"),
    # the practice tasks of every level and variable type, so the start page can list them (ids only, no numbers)
    ui.tags.script(f"window.OS_LEARN_TASKS = {json.dumps(task_list())};"),
    ui.div(id="os-learn", class_="os-learn html-fill-item"),
    value="learn",
)
