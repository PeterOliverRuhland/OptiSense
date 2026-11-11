"""The frame around the three pages: navbar, language switch, styles and scripts."""

from pathlib import Path

from shiny import ui

from ..i18n import LANGS, client_dictionary
from ..pages.guide import ui as guide
from ..pages.learn import ui as learn
from ..pages.work import ui as work

WWW = Path(__file__).resolve().parents[2] / "www"
PAGES = (work, learn, guide)   # order in the navbar


def asset(name):
    """URL of a file in www/ with its modification time, so browsers reload it after every change."""
    return f"{name}?v={int((WWW / name).stat().st_mtime)}"


language_switch = ui.nav_control(
    ui.div(
        ui.input_select("lang", None, LANGS, selected="en", selectize=False, width="auto"),
        class_="os-lang",
        **{"data-i18n-aria": "language", "aria-label": "Language"},
    )
)

app_ui = ui.page_navbar(
    *[page.panel for page in PAGES],
    ui.nav_spacer(),
    language_switch,
    title=ui.span("OptiSense", class_="os-brand"),
    id="page",
    window_title="OptiSense",
    header=ui.head_content(
        ui.tags.meta(name="viewport", content="width=device-width, initial-scale=1"),
        # tab icon: SVG for current browsers, .ico for every other (also asked for as /favicon.ico, e.g. by in-app
        # browsers); apple-touch-icon for Safari on iPhone, iPad and Mac; the manifest gives Chrome on Android and
        # Samsung Internet their home-screen icons (192/512 px)
        ui.tags.link(rel="icon", href=asset("favicon.ico"), sizes="32x32"),
        ui.tags.link(rel="icon", href=asset("favicon.svg"), type="image/svg+xml"),
        ui.tags.link(rel="apple-touch-icon", href=asset("apple-touch-icon.png")),
        ui.tags.link(rel="manifest", href=asset("manifest.json")),
        # optisense.css/.js: design tokens, navbar, shared components and the language switch
        ui.tags.link(rel="stylesheet", href=asset("optisense.css")),
        *[ui.tags.link(rel="stylesheet", href=asset(page.STYLESHEET)) for page in PAGES],
        ui.tags.script(f"window.OS_I18N = {client_dictionary()};"),
        ui.tags.script(src=asset("optisense.js")),
        *[ui.tags.script(src=asset(page.SCRIPT)) for page in PAGES],
    ),
    bg="#b0e2ff",
    fillable=["work", "learn"],
    lang="en",
)
