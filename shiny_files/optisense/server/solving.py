"""Step 3: button states, linear optimization and sensitivity analysis."""

import subprocess

from htmltools import TagList, tags
from shiny import reactive, render, ui

from .. import core

ERROR_KEYS = {"infeasible": "infeasible", "unbounded": "unbounded"}


def error_key(status):
    return ERROR_KEYS.get(status, "solver_error")


def register(ctx):
    input, session = ctx.input, ctx.session

    @reactive.effect
    async def _button_states():
        can_opt, solved = ctx.can_optimize(), ctx.has_optimum()
        ui.update_action_button("btn_opt", disabled=not can_opt)
        ui.update_action_button("btn_sens", disabled=not solved)
        ui.update_action_button("btn_png", disabled=not can_opt)
        await session.send_custom_message("os-step-state", {"1": can_opt, "2": can_opt, "3": solved})

    @render.ui
    def solve_hint():
        hints = []
        if ctx.active_objective() is None:
            hints.append(ctx.tr("need_objective"))
        if not ctx.active_constraints():
            hints.append(ctx.tr("need_constraint"))
        if not hints and not ctx.has_optimum():
            hints.append(ctx.tr("need_optimum"))
        return TagList(*[tags.p(h, class_="os-hint") for h in hints]) if hints else None

    @reactive.effect
    @reactive.event(input.btn_opt)
    def _optimize():
        if not ctx.can_optimize():
            return
        result = core.solve(ctx.active_objective(), ctx.active_constraints(), ctx.var_types())
        ctx.solution.set(result)
        ctx.sensitivity.set(None)
        if result["status"] == "optimal":
            ctx.notify("n_optimized")
            ui.update_navs("results_tabs", selected="solution")
        else:
            ctx.notify(error_key(result["status"]), "error")

    @reactive.effect
    @reactive.event(input.btn_sens)
    def _sensitivity():
        if not (ctx.can_optimize() and ctx.has_optimum()):
            return
        try:
            result = core.run_sensitivity(ctx.active_objective(), ctx.active_constraints(), ctx.var_types())
        except subprocess.TimeoutExpired:
            ctx.notify("n_lpsolve_timeout", "error")
            return
        except (OSError, ValueError):
            ctx.notify("n_lpsolve_missing", "error")
            return
        ctx.sensitivity.set(result)
        ctx.notify("n_sens_done")
        ui.update_navs("results_tabs", selected="sensitivity")
