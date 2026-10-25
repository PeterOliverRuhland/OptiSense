"""The three result tabs: solution, sensitivity, description."""

from htmltools import HTML, TagList, tags
from shiny import render

from optisense import core
from optisense.config import constraint_color
from optisense.i18n import t

from .. import plotting
from .html_utils import colored_name, con_swatch, con_text, fmt_html
from .solving import error_key


def register(ctx):
    tr, num = ctx.tr, ctx.num

    def table(headers, rows):
        head = tags.tr(*[tags.th(text, class_="num" if numeric else None) for text, numeric in headers])
        return tags.table(tags.thead(head), tags.tbody(*rows), class_="os-table")

    # ------------------------------------------------------------------ solution
    @render.ui
    def solution_view():
        sol, obj = ctx.solution(), ctx.active_objective()
        if not sol:
            return tags.p(tr("empty_solution"), class_="os-placeholder")
        if sol["status"] != "optimal":
            return tags.div(tr(error_key(sol["status"])), class_="os-alert", role="alert")
        cons = ctx.active_constraints()
        activity = core.constraint_activity(cons, sol["x1"], sol["x2"])
        rows = []
        for con, act in zip(cons, activity):
            tag = tags.span(tr("binding" if act["binding"] else "non_binding"),
                            class_="os-tag" + (" is-binding" if act["binding"] else ""))
            rows.append(tags.tr(
                tags.td(tags.div(con_swatch(con), con["name"]), tag, class_="os-cell-name"),
                tags.td(f"{num(act['lhs'])} {con['op']} {num(con['b'])}", class_="num"),
                tags.td(num(act["slack"]), class_="num")))
        binding = [con["name"] for con, act in zip(cons, activity) if act["binding"]]
        return TagList(
            tags.div(
                tags.div(tags.small(tr("optimal_value", name=obj["name"])), tags.b(num(sol["value"])), class_="os-kpi is-value"),
                tags.div(tags.small("x1"), tags.b(num(sol["x1"])), class_="os-kpi"),
                tags.div(tags.small("x2"), tags.b(num(sol["x2"])), class_="os-kpi"),
                class_="os-kpis",
            ),
            table([(tr("col_constraint"), False), (tr("col_lhs"), True), (tr("col_slack"), True)], rows),
            tags.p(tr("solution_sentence", x1=num(sol["x1"]), x2=num(sol["x2"]), name=obj["name"], value=num(sol["value"]))),
            tags.p(tr("binding_sentence", names=", ".join(binding))) if binding else None,
            tags.p(tr("problem_is", type=tr(f"type_{ctx.ptype()}")), class_="os-note"),
        )

    # ------------------------------------------------------------------ sensitivity
    @render.ui
    def sensitivity_view():
        sens = ctx.sensitivity()
        if not sens or not ctx.has_optimum():
            return tags.p(tr("empty_sensitivity"), class_="os-placeholder")
        sol, obj, cons = ctx.solution(), ctx.active_objective(), ctx.active_constraints()
        rows, sentences = [], []
        for con, sh in zip(cons, sens["shadow"]):
            name_cell = tags.td(con_swatch(con), con["name"])
            if sh is None:
                rows.append(tags.tr(name_cell, tags.td(tr("not_reported"), colspan="3")))
                continue
            rows.append(tags.tr(name_cell, tags.td(num(sh["price"]), class_="num"),
                                tags.td(num(sh["from"]), class_="num"), tags.td(num(sh["till"]), class_="num")))
            name_html = str(colored_name(con["name"], constraint_color(con["color_index"])))
            if sh["price"] == 0:
                sentences.append(HTML(fmt_html(tr("shadow_zero_sentence", name="{name}"), name=name_html)))
            else:
                sentences.append(HTML(fmt_html(tr("shadow_sentence", name="{name}", price=num(sh["price"]),
                                                  lo=num(sh["from"]), hi=num(sh["till"])), name=name_html)))
        lim = sens["limits"]
        lim_rows = []
        for var, coef in (("x1", obj["c1"]), ("x2", obj["c2"])):
            rng = lim.get(var)
            lim_rows.append(tags.tr(tags.td(var), tags.td(num(coef), class_="num"),
                                    tags.td(num(rng["from"]) if rng else tr("not_reported"), class_="num"),
                                    tags.td(num(rng["till"]) if rng else tr("not_reported"), class_="num")))
        limits_sentence = None
        if lim.get("x1") and lim.get("x2"):
            limits_sentence = tags.p(tr("limits_sentence", x1=num(sol["x1"]), x2=num(sol["x2"]),
                                        c1lo=num(lim["x1"]["from"]), c1hi=num(lim["x1"]["till"]),
                                        c2lo=num(lim["x2"]["from"]), c2hi=num(lim["x2"]["till"])))
        return TagList(
            tags.h4(tr("shadow_title")),
            table([(tr("col_constraint"), False), (tr("col_shadow"), True), (tr("col_from"), True), (tr("col_till"), True)], rows),
            *[tags.p(s) for s in sentences],
            tags.h4(tr("limits_title")),
            table([(tr("col_variable"), False), (tr("col_coef"), True), (tr("col_lower"), True), (tr("col_upper"), True)],
                  lim_rows),
            limits_sentence,
            tags.p(tr("integer_note"), class_="os-note") if ctx.ptype() != "LP" else None,
        )

    # ------------------------------------------------------------------ description
    @render.ui
    def description_view():
        obj, cons = ctx.active_objective(), ctx.active_constraints()
        if not obj or not cons:
            return tags.p(tr("empty_description"), class_="os-placeholder")
        sol = ctx.solution()
        opt = sol if ctx.has_optimum() else None
        xmax, ymax = core.plot_bounds(obj, cons, opt)
        level = core.dummy_level(obj, cons, xmax, ymax)

        def intercept_texts(a1, a2, b):
            i1, i2 = core.intercepts(a1, a2, b)
            none = tr("no_intercept")
            return (num(i1) if i1 is not None else none, num(i2) if i2 is not None else none)

        items = []
        i1, i2 = intercept_texts(obj["c1"], obj["c2"], level)
        dummy_name = str(colored_name(t(ctx.lang(), "plot_dummy", name=obj["name"]), plotting.DUMMY))
        direction = tr("dir_max" if obj["sense"] == "max" else "dir_min")
        items.append(tags.li(HTML(fmt_html(tr("desc_obj", name="{name}", level=num(level), i1=i1, i2=i2, dir=direction),
                                          name=dummy_name))))
        for con in cons:
            i1, i2 = intercept_texts(con["a1"], con["a2"], con["b"])
            name_html = str(colored_name(con["name"], constraint_color(con["color_index"])))
            key = "desc_con_h" if con["a1"] == 0 else ("desc_con_v" if con["a2"] == 0 else "desc_con")
            items.append(tags.li(HTML(fmt_html(tr(key, name="{name}", formula=con_text(con, ctx.lang()), i1=i1, i2=i2),
                                              name=name_html))))
        region = core.feasible_region(cons, ctx.var_types(), xmax, ymax)
        region_text = tr("desc_region") if ctx.ptype() == "LP" else tr("desc_region_int")
        if region.get("thinned"):
            region_text += " " + tr("desc_thinned")
        parts = [tags.h4(tr("desc_heading_functions")), tags.ul(*items), tags.p(region_text)]
        if opt:
            parts += [tags.h4(tr("desc_heading_solution")),
                      tags.p(tr("solution_sentence", x1=num(opt["x1"]), x2=num(opt["x2"]), name=obj["name"],
                                value=num(opt["value"])))]
        elif sol:
            parts.append(tags.div(tr(error_key(sol["status"])), class_="os-alert"))
        return tags.div(*parts, class_="os-desc")
