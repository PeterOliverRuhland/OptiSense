"""The graphical solution and its PNG download."""

import io

from htmltools import TagList, tags
from shiny import reactive, render, ui

from .. import plotting
from .html_utils import safe_filename


def register(ctx):
    input = ctx.input
    tr = ctx.tr

    def make_figure(figsize=None, scale=None):
        return plotting.draw(ctx.active_objective(), ctx.active_constraints(), ctx.var_types(), ctx.solution(),
                             ctx.lang(), figsize=figsize, scale=ctx.plot_scale() if scale is None else scale)

    @render.plot(alt="Graphical solution")
    def plot():
        return make_figure()

    @reactive.effect
    @reactive.event(input.btn_png)
    def _png_dialog():
        ui.modal_show(ui.modal(
            ui.input_text("png_name", tr("file_name"), "optisense-graph"),
            ui.input_select("png_dpi", tr("dpi"), {"72": "72", "150": "150", "300": "300", "600": "600"}, selected="150"),
            tags.p(tr("dpi_hint"), class_="os-hint"),
            title=tr("png_title"),
            footer=TagList(ui.modal_button(tr("close"), class_="os-btn"),
                           ui.download_button("dl_png", tr("download_png"), class_="btn-primary")),
            easy_close=True,
        ))

    @render.download(filename=lambda: f"{safe_filename(input.png_name(), 'optisense-graph')}.png")
    def dl_png():
        fig = make_figure(figsize=(8, 7), scale=1.0)   # fixed size, independent of the screen
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=int(input.png_dpi() or 150), bbox_inches="tight")
        buf.seek(0)
        yield buf.read()
