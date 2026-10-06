import io
import subprocess

from htmltools import HTML, TagList, tags
from shiny import reactive, render, req, ui

import lp_core
import plotting
from i18n import DEFAULT_NAMES, EXAMPLE_NAMES, GUIDE_ORDER, fmt_num, guide, norm_lang, t


def server(input, output, session):
    # ------------------------------------------------------------------ state
    # objectives: [{id, name, c1, c2, sense, active}]
    # constraints: [{id, name, a1, a2, op, b, active, color_index}]
    objectives = reactive.value([])
    constraints = reactive.value([])
    var_types = reactive.value({"x1": "con", "x2": "con"})
    solution = reactive.value(None)      # result of lp_core.solve for the current problem
    sensitivity = reactive.value(None)   # result of lp_core.run_sensitivity
    editing = reactive.value(None)       # ("obj"|"con", id or None) while a modal is open
    modal_errors = reactive.value([])
    pending_confirm = reactive.value(None)  # "reset" | "example"
    counter = {"id": 0}

    def next_id():
        counter["id"] += 1
        return counter["id"]

    @reactive.calc
    def lang():
        return norm_lang(input.lang())

    def tr(key, **kw):
        return t(lang(), key, **kw)

    def num(v):
        return fmt_num(v, lang())

    def notify(key, kind="message", **kw):
        # errors stay until closed; everything else disappears after 4 s
        # one shared id: a new message replaces the previous one instead of stacking
        ui.notification_show(tr(key, **kw), type=kind, duration=None if kind == "error" else 3, id="os-status")

    def problem_changed():
        solution.set(None)
        sensitivity.set(None)

    @reactive.calc
    def active_objective():
        for obj in objectives():
            if obj["active"]:
                return obj
        return None

    @reactive.calc
    def active_constraints():
        return [c for c in constraints() if c["active"]]

    @reactive.calc
    def ptype():
        return lp_core.problem_type(var_types())

    # ------------------------------------------------------------------ formatting helpers
    def formula(a1, a2, lang_code=None):
        lc = lang_code or lang()
        parts = []
        for coef, var in ((a1, "x1"), (a2, "x2")):
            if coef == 0:
                continue
            c = "" if coef == 1 else f"{fmt_num(coef, lc)}·"
            parts.append(f"{c}{var}")
        return " + ".join(parts) if parts else "0"

    def obj_text(obj):
        return f"{obj['name']} = {formula(obj['c1'], obj['c2'])} → {obj['sense']}"

    def con_text(con):
        return f"{formula(con['a1'], con['a2'])} {con['op']} {num(con['b'])}"

    def swatch(color, dashed=False, style=""):
        cls = "os-swatch is-dashed" if dashed else "os-swatch"
        return tags.span(class_=cls, style=f"background:{color};color:{color};{style}", **{"aria-hidden": "true"})

    def con_swatch(con):
        color, line = plotting.constraint_style(con["color_index"])
        return swatch(color, dashed=(line != "-"))

    def colored_name(name, color):
        return tags.span(name, class_="os-name", style=f"color:{color}")

    # ------------------------------------------------------------------ step 1: list
    @render.ui
    def problem_list():
        lc = lang()
        rows = [tags.div(tr("objective_function"), class_="os-list-label")]
        objs = objectives()
        if not objs:
            rows.append(tags.div(tr("no_objective"), class_="os-empty"))
        for obj in objs:
            rows.append(_row("obj", obj, swatch(plotting.OPTIMIZED),
                             HTML(f"<b>{_esc(obj['name'])}</b> = {formula(obj['c1'], obj['c2'], lc)} → {obj['sense']}")))
        rows.append(tags.div(tr("constraints"), class_="os-list-label"))
        cons = constraints()
        if not cons:
            rows.append(tags.div(tr("no_constraints"), class_="os-empty"))
        for con in cons:
            rows.append(_row("con", con, con_swatch(con),
                             HTML(f"<b>{_esc(con['name'])}:</b> {_esc(con_text(con))}")))
        return tags.div(*rows, class_="os-list")

    def _row(kind, item, mark, text):
        label = tr("edit_item", name=item["name"])
        return tags.div(
            mark,
            tags.span(text, class_="os-formula"),
            tags.label(
                tags.input(type="checkbox", checked=True if item["active"] else None,
                           **{"data-toggle-kind": kind, "data-id": str(item["id"]), "aria-label": tr("toggle_active")}),
                tags.span(),
                class_="os-switch", title=tr("toggle_active"),
            ),
            tags.span("›", class_="os-chev", **{"aria-hidden": "true"}),
            class_="os-row" + ("" if item["active"] else " is-off"),
            role="button", tabindex="0", title=label, **{"aria-label": label, "data-kind": kind, "data-id": str(item["id"])},
        )

    @render.text
    def status_step1():
        n = (1 if active_objective() else 0) + len(active_constraints())
        return tr("n_functions", n=n)

    @reactive.effect
    @reactive.event(input.row_toggle)
    def _toggle():
        ev = input.row_toggle()
        kind, item_id, on = ev["kind"], ev["id"], bool(ev["on"])
        if kind == "obj":
            objs = [dict(o) for o in objectives()]
            for o in objs:
                if o["id"] == item_id:
                    o["active"] = on
                elif on:
                    o["active"] = False
            objectives.set(objs)
        else:
            constraints.set([dict(c, active=on) if c["id"] == item_id else c for c in constraints()])
        problem_changed()

    # ------------------------------------------------------------------ modals for functions
    def _find(kind, item_id):
        items = objectives() if kind == "obj" else constraints()
        return next((i for i in items if i["id"] == item_id), None)

    def _numeric(input_id, label_key, value):
        return ui.input_numeric(input_id, tr(label_key), value, min=0, step=0.01)

    def show_function_modal(kind, item=None):
        editing.set((kind, item["id"] if item else None))
        modal_errors.set([])
        lc = lang()
        if kind == "obj":
            default_name = DEFAULT_NAMES["objective"][lc]
            body = [
                ui.input_text("f_name", tr("name"), item["name"] if item else _unique_name(default_name, objectives())),
                ui.div(_numeric("f_a1", "coef_c1", item["c1"] if item else 1),
                       _numeric("f_a2", "coef_c2", item["c2"] if item else 1), class_="os-form-grid"),
                ui.input_radio_buttons("f_sense", tr("sense"), {"max": tr("maximize"), "min": tr("minimize")},
                                       selected=item["sense"] if item else "max", inline=True),
            ]
            title = tr("edit_objective" if item else "new_objective")
        else:
            n = len(constraints()) + 1
            default_name = DEFAULT_NAMES["constraint"][lc].format(n=n)
            body = [
                ui.input_text("f_name", tr("name"), item["name"] if item else _unique_name(default_name, constraints())),
                ui.div(_numeric("f_a1", "coef_a1", item["a1"] if item else 1),
                       _numeric("f_a2", "coef_a2", item["a2"] if item else 1), class_="os-form-grid"),
                ui.div(ui.input_select("f_op", tr("operator"), {"≤": "≤", "≥": "≥", "=": "="},
                                       selected=item["op"] if item else "≤"),
                       _numeric("f_b", "rhs_b", item["b"] if item else 10), class_="os-form-grid"),
            ]
            title = tr("edit_constraint" if item else "new_constraint")
        footer = [ui.input_action_button("m_cancel", tr("cancel"), class_="os-btn")]
        if item:
            footer.insert(0, ui.input_action_button("m_delete", tr("delete"), class_="os-btn os-btn-danger"))
        footer.append(ui.input_action_button("m_save", tr("save"), class_="btn-primary"))
        ui.modal_show(ui.modal(
            *body,
            tags.p(tr("nonneg_inputs"), class_="os-hint"),
            ui.output_ui("m_preview"),
            ui.output_ui("m_errors"),
            title=title, footer=TagList(*footer), easy_close=False, size="m",
        ))

    def _unique_name(base, items, exclude_id=None):
        names = {i["name"] for i in items if i["id"] != exclude_id}
        if base not in names:
            return base
        k = 2
        while f"{base}_{k}" in names:
            k += 1
        return f"{base}_{k}"

    @render.ui
    def m_preview():
        ed = editing()
        req(ed)
        a1, a2 = input.f_a1(), input.f_a2()
        if not isinstance(a1, (int, float)) or not isinstance(a2, (int, float)):
            return None
        name = (input.f_name() or "").strip() or "…"
        if ed[0] == "obj":
            text = f"{name} = {formula(a1, a2)} → {input.f_sense()}"
        else:
            b = input.f_b()
            text = f"{name}: {formula(a1, a2)} {input.f_op()} {num(b) if isinstance(b, (int, float)) else '…'}"
        return tags.div(tags.small(tr("preview")), text, class_="os-preview")

    @render.ui
    def m_errors():
        errs = modal_errors()
        if not errs:
            return None
        return tags.div(tags.ul(*[tags.li(e) for e in errs]), class_="os-errors", role="alert")

    @reactive.effect
    @reactive.event(input.btn_add_obj)
    def _add_obj():
        show_function_modal("obj")

    @reactive.effect
    @reactive.event(input.btn_add_con)
    def _add_con():
        show_function_modal("con")

    @reactive.effect
    @reactive.event(input.row_click)
    def _edit_row():
        ev = input.row_click()
        item = _find(ev["kind"], ev["id"])
        if item:
            show_function_modal(ev["kind"], item)

    @reactive.effect
    @reactive.event(input.m_cancel)
    def _cancel():
        editing.set(None)
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.m_save)
    def _save():
        ed = editing()
        if not ed:
            return
        kind, item_id = ed
        items = objectives() if kind == "obj" else constraints()
        errs = []
        name = (input.f_name() or "").strip()
        if not name:
            errs.append(tr("err_name"))
        elif any(i["name"] == name and i["id"] != item_id for i in items):
            errs.append(tr("err_name_taken"))
        labels = ("coef_c1", "coef_c2") if kind == "obj" else ("coef_a1", "coef_a2")
        fields = [("f_a1", labels[0]), ("f_a2", labels[1])] + ([("f_b", "rhs_b")] if kind == "con" else [])
        values = {}
        for fid, key in fields:
            v = input[fid]()
            if not isinstance(v, (int, float)) or v < 0:
                errs.append(tr("err_number", field=tr(key)))
            else:
                values[fid] = float(v)
        if "f_a1" in values and "f_a2" in values and values["f_a1"] == 0 and values["f_a2"] == 0:
            errs.append(tr("err_both_zero"))
        if errs:
            modal_errors.set(errs)
            return
        if kind == "obj":
            data = {"name": name, "c1": values["f_a1"], "c2": values["f_a2"], "sense": input.f_sense()}
            objs = [dict(o) for o in objectives()]
            if item_id is None:
                for o in objs:
                    o["active"] = False
                objs.append(dict(data, id=next_id(), active=True))
                notify("n_obj_added")
            else:
                objs = [dict(o, **data) if o["id"] == item_id else o for o in objs]
                notify("n_saved")
            objectives.set(objs)
        else:
            data = {"name": name, "a1": values["f_a1"], "a2": values["f_a2"], "op": input.f_op(), "b": values["f_b"]}
            cons = list(constraints())
            if item_id is None:
                used = {c["color_index"] for c in cons}
                color_index = next(i for i in range(len(cons) + 1) if i not in used)
                cons.append(dict(data, id=next_id(), active=True, color_index=color_index))
                notify("n_con_added")
            else:
                cons = [dict(c, **data) if c["id"] == item_id else c for c in cons]
                notify("n_saved")
            constraints.set(cons)
        problem_changed()
        editing.set(None)
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.m_delete)
    def _delete():
        ed = editing()
        if not ed or ed[1] is None:
            return
        kind, item_id = ed
        item = _find(kind, item_id)
        if kind == "obj":
            objs = [o for o in objectives() if o["id"] != item_id]
            if item and item["active"] and objs and not any(o["active"] for o in objs):
                objs[-1] = dict(objs[-1], active=True)
            objectives.set(objs)
        else:
            constraints.set([c for c in constraints() if c["id"] != item_id])
        problem_changed()
        editing.set(None)
        ui.modal_remove()
        if item:
            notify("n_deleted", name=item["name"])

    # ------------------------------------------------------------------ step 2: value range
    @reactive.effect
    def _var_types_from_input():
        new = {"x1": input.vt_x1(), "x2": input.vt_x2()}
        with reactive.isolate():
            old = var_types()
        if new != old:
            var_types.set(new)
            problem_changed()

    @render.text
    def status_step2():
        return ptype()

    @render.ui
    def problem_type():
        bounds = []
        for v in ("x1", "x2"):
            bounds.append(f"{v} ∈ ℕ0" if var_types()[v] == "int" else f"{v} ≥ 0")
        return tags.p(tags.b(tr(f"type_{ptype()}")), " · ", "; ".join(bounds), class_="os-type")

    # ------------------------------------------------------------------ step 3: solve
    @reactive.effect
    async def _button_states():
        can_opt = active_objective() is not None and bool(active_constraints())
        sol = solution()
        ui.update_action_button("btn_opt", disabled=not can_opt)
        ui.update_action_button("btn_sens", disabled=not (sol and sol.get("status") == "optimal"))
        ui.update_action_button("btn_png", disabled=not can_opt)
        await session.send_custom_message("os-step-state", {
            "1": can_opt,
            "2": can_opt,
            "3": bool(sol and sol.get("status") == "optimal"),
        })

    @render.ui
    def solve_hint():
        hints = []
        if active_objective() is None:
            hints.append(tr("need_objective"))
        if not active_constraints():
            hints.append(tr("need_constraint"))
        sol = solution()
        if not hints and not (sol and sol.get("status") == "optimal"):
            hints.append(tr("need_optimum"))
        if not hints:
            return None
        return TagList(*[tags.p(h, class_="os-hint") for h in hints])

    @render.text
    def status_step3():
        if sensitivity():
            return tr("status_analysed")
        sol = solution()
        if sol and sol.get("status") == "optimal":
            return tr("status_solved")
        if active_objective() and active_constraints():
            return tr("status_ready")
        return tr("status_open")

    @reactive.effect
    @reactive.event(input.btn_opt)
    def _optimize():
        obj, cons = active_objective(), active_constraints()
        if not obj or not cons:
            return
        result = lp_core.solve(obj, cons, var_types())
        solution.set(result)
        sensitivity.set(None)
        if result["status"] == "optimal":
            notify("n_optimized")
            ui.update_navs("results_tabs", selected="solution")
        else:
            notify({"infeasible": "infeasible", "unbounded": "unbounded"}.get(result["status"], "solver_error"), "error")

    @reactive.effect
    @reactive.event(input.btn_sens)
    def _sensitivity():
        obj, cons, sol = active_objective(), active_constraints(), solution()
        if not (obj and cons and sol and sol.get("status") == "optimal"):
            return
        try:
            result = lp_core.run_sensitivity(obj, cons, var_types())
        except subprocess.TimeoutExpired:
            notify("n_lpsolve_timeout", "error")
            return
        except (OSError, ValueError):
            notify("n_lpsolve_missing", "error")
            return
        sensitivity.set(result)
        notify("n_sens_done")
        ui.update_navs("results_tabs", selected="sensitivity")

    # ------------------------------------------------------------------ graph
    def make_figure(figsize=None):
        obj = active_objective()
        cons = active_constraints()
        return plotting.draw(obj, cons, var_types(), solution(), lang(), figsize=figsize)

    @render.plot(alt="Graphical solution")
    def plot():
        return make_figure()

    # ------------------------------------------------------------------ results: solution
    @render.ui
    def solution_view():
        sol = solution()
        obj = active_objective()
        if not sol:
            return tags.p(tr("empty_solution"), class_="os-placeholder")
        if sol["status"] != "optimal":
            key = {"infeasible": "infeasible", "unbounded": "unbounded"}.get(sol["status"], "solver_error")
            return tags.div(tr(key), class_="os-alert", role="alert")
        cons = active_constraints()
        activity = lp_core.constraint_activity(cons, sol["x1"], sol["x2"])
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
            tags.table(
                tags.thead(tags.tr(tags.th(tr("col_constraint")),
                                   tags.th(tr("col_lhs"), class_="num"), tags.th(tr("col_slack"), class_="num"))),
                tags.tbody(*rows), class_="os-table"),
            tags.p(tr("solution_sentence", x1=num(sol["x1"]), x2=num(sol["x2"]), name=obj["name"], value=num(sol["value"]))),
            tags.p(tr("binding_sentence", names=", ".join(binding))) if binding else None,
            tags.p(tr("problem_is", type=tr(f"type_{ptype()}")), class_="os-note"),
        )

    # ------------------------------------------------------------------ results: sensitivity
    @render.ui
    def sensitivity_view():
        sens = sensitivity()
        sol = solution()
        if not sens or not sol or sol.get("status") != "optimal":
            return tags.p(tr("empty_sensitivity"), class_="os-placeholder")
        obj = active_objective()
        cons = active_constraints()
        rows, sentences = [], []
        for con, sh in zip(cons, sens["shadow"]):
            color = plotting.constraint_color(con["color_index"])
            if sh is None:
                rows.append(tags.tr(tags.td(con_swatch(con), con["name"]), tags.td(tr("not_reported"), colspan="3")))
                continue
            rows.append(tags.tr(tags.td(con_swatch(con), con["name"]), tags.td(num(sh["price"]), class_="num"),
                                tags.td(num(sh["from"]), class_="num"), tags.td(num(sh["till"]), class_="num")))
            name_html = str(colored_name(con["name"], color))
            if sh["price"] == 0:
                sentences.append(HTML(_fmt_html(tr("shadow_zero_sentence", name="{name}"), name=name_html)))
            else:
                sentences.append(HTML(_fmt_html(tr("shadow_sentence", name="{name}", price=num(sh["price"]),
                                                   lo=num(sh["from"]), hi=num(sh["till"])), name=name_html)))
        lim = sens["limits"]
        lim_rows = []
        for var, coef in (("x1", obj["c1"]), ("x2", obj["c2"])):
            L = lim.get(var)
            lim_rows.append(tags.tr(tags.td(var), tags.td(num(coef), class_="num"),
                                    tags.td(num(L["from"]) if L else tr("not_reported"), class_="num"),
                                    tags.td(num(L["till"]) if L else tr("not_reported"), class_="num")))
        limits_sentence = None
        if lim.get("x1") and lim.get("x2"):
            limits_sentence = tags.p(tr("limits_sentence", x1=num(sol["x1"]), x2=num(sol["x2"]),
                                        c1lo=num(lim["x1"]["from"]), c1hi=num(lim["x1"]["till"]),
                                        c2lo=num(lim["x2"]["from"]), c2hi=num(lim["x2"]["till"])))
        return TagList(
            tags.h4(tr("shadow_title")),
            tags.table(
                tags.thead(tags.tr(tags.th(tr("col_constraint")), tags.th(tr("col_shadow"), class_="num"),
                                   tags.th(tr("col_from"), class_="num"), tags.th(tr("col_till"), class_="num"))),
                tags.tbody(*rows), class_="os-table"),
            *[tags.p(s) for s in sentences],
            tags.h4(tr("limits_title")),
            tags.table(
                tags.thead(tags.tr(tags.th(tr("col_variable")), tags.th(tr("col_coef"), class_="num"),
                                   tags.th(tr("col_lower"), class_="num"), tags.th(tr("col_upper"), class_="num"))),
                tags.tbody(*lim_rows), class_="os-table"),
            limits_sentence,
            tags.p(tr("integer_note"), class_="os-note") if ptype() != "LP" else None,
        )

    # ------------------------------------------------------------------ results: description
    @render.ui
    def description_view():
        obj = active_objective()
        cons = active_constraints()
        if not obj or not cons:
            return tags.p(tr("empty_description"), class_="os-placeholder")
        sol = solution()
        opt = sol if sol and sol.get("status") == "optimal" else None
        xmax, ymax = lp_core.plot_bounds(obj, cons, opt)
        level = lp_core.dummy_level(obj, cons, xmax, ymax)

        def icpt(a1, a2, b):
            i1, i2 = lp_core.intercepts(a1, a2, b)
            return (num(i1) if i1 is not None else tr("no_intercept"), num(i2) if i2 is not None else tr("no_intercept"))

        items = []
        i1, i2 = icpt(obj["c1"], obj["c2"], level)
        dummy_name = str(colored_name(t(lang(), "plot_dummy", name=obj["name"]), plotting.DUMMY))
        items.append(tags.li(HTML(_fmt_html(tr("desc_obj", name="{name}", level=num(level), i1=i1, i2=i2,
                                                  dir=tr("dir_max" if obj["sense"] == "max" else "dir_min")),
                                           name=dummy_name))))
        for con in cons:
            i1, i2 = icpt(con["a1"], con["a2"], con["b"])
            name_html = str(colored_name(con["name"], plotting.constraint_color(con["color_index"])))
            key = "desc_con_h" if con["a1"] == 0 else ("desc_con_v" if con["a2"] == 0 else "desc_con")
            items.append(tags.li(HTML(_fmt_html(tr(key, name="{name}", formula=con_text(con), i1=i1, i2=i2),
                                               name=name_html))))
        region = lp_core.feasible_region(cons, var_types(), xmax, ymax)
        region_text = tr("desc_region") if ptype() == "LP" else tr("desc_region_int")
        if region.get("thinned"):
            region_text += " " + tr("desc_thinned")
        parts = [tags.h4(tr("desc_heading_functions")), tags.ul(*items), tags.p(region_text)]
        if opt:
            parts += [tags.h4(tr("desc_heading_solution")),
                      tags.p(tr("solution_sentence", x1=num(opt["x1"]), x2=num(opt["x2"]), name=obj["name"],
                                value=num(opt["value"])))]
        elif sol:
            key = {"infeasible": "infeasible", "unbounded": "unbounded"}.get(sol["status"], "solver_error")
            parts.append(tags.div(tr(key), class_="os-alert"))
        return tags.div(*parts, class_="os-desc")

    # ------------------------------------------------------------------ PNG
    @reactive.effect
    @reactive.event(input.btn_png)
    def _png_modal():
        ui.modal_show(ui.modal(
            ui.input_text("png_name", tr("file_name"), "optisense-graph"),
            ui.input_select("png_dpi", tr("dpi"), {"72": "72", "150": "150", "300": "300", "600": "600"}, selected="150"),
            tags.p(tr("dpi_hint"), class_="os-hint"),
            title=tr("png_title"),
            footer=TagList(ui.modal_button(tr("close"), class_="os-btn"),
                           ui.download_button("dl_png", tr("download_png"), class_="btn-primary")),
            easy_close=True,
        ))

    @render.download(filename=lambda: f"{_safe_filename(input.png_name(), 'optisense-graph')}.png")
    def dl_png():
        fig = make_figure(figsize=(8, 7))
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=int(input.png_dpi() or 150), bbox_inches="tight")
        buf.seek(0)
        yield buf.read()

    # ------------------------------------------------------------------ import / export
    @reactive.effect
    @reactive.event(input.btn_import_export)
    def _io_modal():
        can_export = active_objective() is not None and bool(active_constraints())
        export_part = [tags.p(tr("export_text"))]
        if can_export:
            export_part += [ui.input_text("lp_name", tr("file_name"), "optisense-problem"),
                            ui.download_button("dl_lp", tr("download_lp"), class_="btn-primary")]
        else:
            export_part.append(tags.p(tr("export_needs"), class_="os-hint"))
        ui.modal_show(ui.modal(
            tags.div(tags.h5(tr("export_title")), *export_part, class_="os-modal-section"),
            tags.div(tags.h5(tr("import_title")), tags.p(tr("import_text")),
                     ui.input_file("lp_upload", tr("choose_file"), accept=[".lp", ".txt"]),
                     ui.input_action_button("btn_do_import", tr("import_btn"), class_="os-btn"),
                     class_="os-modal-section"),
            title=tr("import_export"),
            footer=ui.modal_button(tr("close"), class_="os-btn"),
            easy_close=True,
        ))

    @render.download(filename=lambda: f"{_safe_filename(input.lp_name(), 'optisense-problem')}.lp")
    def dl_lp():
        obj, cons = active_objective(), active_constraints()
        if not obj or not cons:
            return
        yield lp_core.to_lp_file(obj, cons, var_types()).encode()

    @reactive.effect
    @reactive.event(input.btn_do_import)
    def _import():
        files = input.lp_upload()
        if not files:
            notify("n_import_none", "error")
            return
        try:
            with open(files[0]["datapath"], encoding="utf-8", errors="replace") as fh:
                obj, cons, vt = lp_core.parse_lp_file(fh.read())
        except lp_core.LPParseError as exc:
            notify("n_import_failed", "error", line=str(exc)[:80])
            return
        values = [obj["c1"], obj["c2"]] + [v for c in cons for v in (c["a1"], c["a2"], c["b"])]
        if any(v < 0 for v in values):
            notify("n_import_negative", "error")
            return
        load_problem(obj, cons, vt)
        ui.modal_remove()
        notify("n_imported")

    def load_problem(obj, cons, vt):
        lc = lang()
        objectives.set([dict(id=next_id(), name=obj.get("name") or "F", c1=obj["c1"], c2=obj["c2"],
                             sense=obj["sense"], active=True)])
        new_cons, names = [], set()
        for i, con in enumerate(cons):
            name = con.get("name") or DEFAULT_NAMES["constraint"][lc].format(n=i + 1)
            if name in names:
                name = f"{name}_{i + 1}"
            names.add(name)
            new_cons.append(dict(id=next_id(), name=name, a1=con["a1"], a2=con["a2"], op=con["op"], b=con["b"],
                                 active=True, color_index=i))
        constraints.set(new_cons)
        var_types.set(dict(vt))
        ui.update_radio_buttons("vt_x1", selected=vt["x1"])
        ui.update_radio_buttons("vt_x2", selected=vt["x2"])
        problem_changed()

    # ------------------------------------------------------------------ example & reset (with confirmation)
    def confirm(kind, title_key, text_key, button_key):
        pending_confirm.set(kind)
        ui.modal_show(ui.modal(
            tags.p(tr(text_key)),
            title=tr(title_key),
            footer=TagList(ui.modal_button(tr("cancel"), class_="os-btn"),
                           ui.input_action_button("btn_confirm", tr(button_key), class_="btn-primary")),
            easy_close=True,
        ))

    def load_example():
        names = EXAMPLE_NAMES[lang()]
        load_problem({"name": "F", "c1": 10, "c2": 20, "sense": "max"},
                     [{"name": names[0], "a1": 1, "a2": 1, "op": "≤", "b": 100},
                      {"name": names[1], "a1": 6, "a2": 9, "op": "≤", "b": 720},
                      {"name": names[2], "a1": 0, "a2": 1, "op": "≤", "b": 60}],
                     {"x1": "con", "x2": "con"})
        notify("n_example")

    @reactive.effect
    @reactive.event(input.guide_load_example)
    def _example_from_guide():
        _example_request()

    @reactive.effect
    @reactive.event(input.btn_example)
    def _example():
        _example_request()

    def _example_request():
        if objectives() or constraints():
            confirm("example", "load_example", "example_replace", "load_example")
        else:
            load_example()
            ui.update_navs("page", selected="work")

    @reactive.effect
    @reactive.event(input.btn_reset)
    def _reset():
        confirm("reset", "reset_title", "reset_text", "reset_btn")

    @reactive.effect
    @reactive.event(input.btn_confirm)
    def _confirmed():
        kind = pending_confirm()
        pending_confirm.set(None)
        ui.modal_remove()
        if kind == "example":
            load_example()
            ui.update_navs("page", selected="work")
        elif kind == "reset":
            objectives.set([])
            constraints.set([])
            var_types.set({"x1": "con", "x2": "con"})
            ui.update_radio_buttons("vt_x1", selected="con")
            ui.update_radio_buttons("vt_x2", selected="con")
            problem_changed()
            notify("n_reset", "warning")

    # ------------------------------------------------------------------ guide and contextual help
    def guide_content(topic, with_heading=True):
        label_key = dict(GUIDE_ORDER)[topic]
        parts = [tags.h2(tr(label_key))] if with_heading else []
        parts.append(HTML(guide(lang(), topic)))
        if topic == "example":
            parts.append(ui.input_action_button("guide_load_example", tr("load_example"), class_="os-btn os-btn-primary"))
        return TagList(*parts)

    @render.ui
    def guide_view():
        topic = input.guide_topic() if "guide_topic" in input else None
        if topic not in dict(GUIDE_ORDER):
            topic = "steps"
        return guide_content(topic)

    @reactive.effect
    @reactive.event(input.help_topic)
    def _help():
        topic = input.help_topic()["topic"]
        if topic not in dict(GUIDE_ORDER):
            return
        ui.modal_show(ui.modal(
            tags.div(HTML(guide(lang(), topic)), class_="os-guide-body", style="padding:0;background:none"),
            title=tr(dict(GUIDE_ORDER)[topic]),
            footer=ui.modal_button(tr("close"), class_="os-btn"),
            easy_close=True, size="l",
        ))


def _esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _fmt_html(template, **html_parts):
    """Insert already-escaped HTML into an escaped translated sentence."""
    out = _esc(template)
    for key, value in html_parts.items():
        out = out.replace("{" + key + "}", value)
    return out


def _safe_filename(name, default):
    import re
    name = re.sub(r"[^\w\- .]", "_", (name or "").strip())[:80].strip(" .")
    return name or default
