"""Step 2: continuous or integer per variable."""

from htmltools import tags
from shiny import reactive, render


def register(ctx):
    input = ctx.input

    @reactive.effect
    def _from_input():
        new = {"x1": input.vt_x1(), "x2": input.vt_x2()}
        with reactive.isolate():
            old = ctx.var_types()
        if new != old:
            ctx.var_types.set(new)
            ctx.problem_changed()

    @render.text
    def status_step2():
        return ctx.ptype()

    @render.ui
    def problem_type():
        return tags.p(ctx.tr(f"type_{ctx.ptype()}"), class_="os-type")
