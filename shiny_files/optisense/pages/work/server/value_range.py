"""Step 2: continuous or integer per variable."""

from htmltools import tags
from shiny import reactive, render


def register(ctx):
    input = ctx.input

    @reactive.effect
    def _from_input():
        # only the two known values; anything else the browser might send counts as continuous
        new = {v: "int" if input[f"vt_{v}"]() == "int" else "con" for v in ("x1", "x2")}
        with reactive.isolate():
            old = ctx.var_types()
        if new != old:
            ctx.var_types.set(new)
            ctx.problem_changed()

    @render.ui
    def problem_type():
        return tags.p(ctx.tr(f"type_{ctx.ptype()}"), class_="os-type")
