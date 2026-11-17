"""Step 2: continuous or integer per variable."""

from htmltools import tags
from shiny import reactive, render

from .. import example


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
    def types_story():
        """The example only: what x1 and x2 are and why they are integer, above the two rows."""
        key = example.types_note(ctx.objectives(), ctx.var_types())
        return tags.p(ctx.tr(key), class_="os-story") if key else None

    @render.ui
    def problem_type():
        return tags.p(ctx.tr(f"type_{ctx.ptype()}"), class_="os-type")
