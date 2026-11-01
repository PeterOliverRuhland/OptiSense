"""The graphical solution and its PNG download."""

from htmltools import TagList, tags
from shiny import reactive, render, ui

from .. import plotting
from .html_utils import safe_filename

DPI_CHOICES = ("72", "150", "300", "600")


def register(ctx):
    input = ctx.input
    tr = ctx.tr

    @reactive.calc
    def plot_scale():
        # sent by www/work.js: root font size / 16, grows on large screens
        try:
            return float(input.ui_scale())
        except Exception:  # noqa: BLE001 - not sent yet
            return 1.0

    def make_figure(figsize=None, scale=None, compact=False):
        return plotting.draw(ctx.active_objective(), ctx.active_constraints(), ctx.var_types(), ctx.solution(),
                             ctx.lang(), figsize=figsize, scale=plot_scale() if scale is None else scale, compact=compact)

    @render.plot(alt="Graphical solution")
    def plot():
        try:   # sent by www/work.js: true on smartphones
            phone = bool(input.ui_phone())
        except Exception:  # noqa: BLE001 - not sent yet
            phone = False
        return make_figure(compact=phone)

    @reactive.effect
    @reactive.event(input.btn_png)
    def _png_dialog():
        ui.modal_show(ui.modal(
            ui.input_text("png_name", tr("file_name"), "optisense-graph"),
            ui.input_select("png_dpi", tr("dpi"), {d: d for d in DPI_CHOICES}, selected="150"),
            tags.p(tr("dpi_hint"), class_="os-hint"),
            title=tr("png_title"),
            footer=TagList(ui.modal_button(tr("close"), class_="os-btn"),
                           ui.download_button("dl_png", tr("download_png"), class_="btn-primary")),
            easy_close=True,
        ))

    @render.download(filename=lambda: f"{safe_filename(input.png_name(), 'optisense-graph')}.png")
    def dl_png():
        dpi = str(input.png_dpi()) if str(input.png_dpi()) in DPI_CHOICES else "150"   # the browser may send anything
        # fixed size, independent of the screen; no local name, so png_bytes can free the figure at once
        yield plotting.png_bytes(make_figure(figsize=(8, 7), scale=1.0), int(dpi))
