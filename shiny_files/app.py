"""Entry point: `shiny run app.py` (from this folder) or `python app.py`."""

import os

from shiny import App

from optisense.server import server
from optisense.ui.layout import app_ui

app = App(app_ui, server, static_assets=os.path.join(os.path.dirname(__file__), "www"))
app.sanitize_errors = True   # show a general message instead of Python error details

if __name__ == "__main__":
    app.run()
