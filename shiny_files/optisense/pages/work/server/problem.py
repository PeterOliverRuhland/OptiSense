"""Step 1: the list of objective functions and constraints, the switches and the edit dialogs."""

from htmltools import HTML, TagList, tags
from shiny import reactive, render, req, ui

import math

from optisense.config import DEFAULT_NAMES, MAX_CONSTRAINTS, MAX_NAME_LENGTH, MAX_OBJECTIVES, MAX_VALUE

from .. import plotting
from .html_utils import con_swatch, con_text, esc, formula, swatch


def register(ctx):
    input = ctx.input
    tr = ctx.tr
    editing = reactive.value(None)       # ("obj"|"con", id or None) while a dialog is open
    modal_errors = reactive.value([])

    # ------------------------------------------------------------------ list
    def heading(key, kind, count, limit):
        add = None
        if count < limit:
            label = tr("add_objective" if kind == "obj" else "add_constraint")
            add = tags.button(tr("add_new"), type="button", class_="os-add", title=label,
                              **{"data-add": kind, "aria-label": label})
        return tags.div(tags.span(tr(key)), add, class_="os-list-label")

    def row(kind, item, mark, text):
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
            class_="os-row" + ("" if item["active"] else " is-off"),
            role="button", tabindex="0", title=label,
            **{"aria-label": label, "data-kind": kind, "data-id": str(item["id"])},
        )

    @render.ui
    def problem_list():
        objs, cons = ctx.objectives(), ctx.constraints()
        rows = [heading("objective_function", "obj", len(objs), MAX_OBJECTIVES)]
        if not objs:
            rows.append(tags.div(tr("no_objective"), class_="os-empty"))
        for obj in objs:
            text = HTML(f"<b>{esc(obj['name'])}</b> = {esc(formula(obj['c1'], obj['c2'], ctx.lang()))} → {obj['sense']}")
            rows.append(row("obj", obj, swatch(plotting.OPTIMIZED), text))
        rows.append(heading("constraints", "con", len(cons), MAX_CONSTRAINTS))
        if not cons:
            rows.append(tags.div(tr("no_constraints"), class_="os-empty"))
        for con in cons:
            rows.append(row("con", con, con_swatch(con), HTML(f"<b>{esc(con['name'])}:</b> {esc(con_text(con, ctx.lang()))}")))
        return tags.div(*rows, class_="os-list")

    @reactive.effect
    @reactive.event(input.row_toggle)
    def _toggle():
        ev = input.row_toggle()
        item_id, on = ev["id"], bool(ev["on"])
        if ev["kind"] == "obj":
            # only one objective function can be active
            objs = [dict(o) for o in ctx.objectives()]
            for o in objs:
                if o["id"] == item_id:
                    o["active"] = on
                elif on:
                    o["active"] = False
            ctx.objectives.set(objs)
        else:
            ctx.constraints.set([dict(c, active=on) if c["id"] == item_id else c for c in ctx.constraints()])
        ctx.problem_changed()

    # ------------------------------------------------------------------ dialogs
    def items_of(kind):
        return ctx.objectives() if kind == "obj" else ctx.constraints()

    def find(kind, item_id):
        return next((i for i in items_of(kind) if i["id"] == item_id), None)

    def unique_name(base, items):
        names = {i["name"] for i in items}
        if base not in names:
            return base
        k = 2
        while f"{base}_{k}" in names:
            k += 1
        return f"{base}_{k}"

    def numeric(input_id, label_key, value):
        return ui.input_numeric(input_id, tr(label_key), value, min=0, step=0.01)

    def show_dialog(kind, item=None):
        editing.set((kind, item["id"] if item else None))
        modal_errors.set([])
        lc = ctx.lang()
        if kind == "obj":
            name = item["name"] if item else unique_name(DEFAULT_NAMES["objective"][lc], ctx.objectives())
            body = [
                ui.input_text("f_name", tr("name"), name),
                ui.div(numeric("f_a1", "coef_c1", item["c1"] if item else 1),
                       numeric("f_a2", "coef_c2", item["c2"] if item else 1), class_="os-form-grid"),
                ui.input_radio_buttons("f_sense", tr("sense"), {"max": tr("maximize"), "min": tr("minimize")},
                                       selected=item["sense"] if item else "max", inline=True),
            ]
            title = tr("edit_objective" if item else "new_objective")
        else:
            default = DEFAULT_NAMES["constraint"][lc].format(n=len(ctx.constraints()) + 1)
            name = item["name"] if item else unique_name(default, ctx.constraints())
            body = [
                ui.input_text("f_name", tr("name"), name),
                ui.div(numeric("f_a1", "coef_a1", item["a1"] if item else 1),
                       numeric("f_a2", "coef_a2", item["a2"] if item else 1), class_="os-form-grid"),
                ui.div(ui.input_select("f_op", tr("operator"), {"≤": "≤", "≥": "≥", "=": "="},
                                       selected=item["op"] if item else "≤"),
                       numeric("f_b", "rhs_b", item["b"] if item else 10), class_="os-form-grid"),
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

    def close_dialog():
        editing.set(None)
        ui.modal_remove()

    @render.ui
    def m_preview():
        ed = editing()
        req(ed)
        a1, a2 = input.f_a1(), input.f_a2()
        if not isinstance(a1, (int, float)) or not isinstance(a2, (int, float)):
            return None
        name = (input.f_name() or "").strip() or "…"
        if ed[0] == "obj":
            text = f"{name} = {formula(a1, a2, ctx.lang())} → {input.f_sense()}"
        else:
            b = input.f_b()
            text = f"{name}: {formula(a1, a2, ctx.lang())} {input.f_op()} {ctx.num(b) if isinstance(b, (int, float)) else '…'}"
        return tags.div(tags.small(tr("preview")), text, class_="os-preview")

    @render.ui
    def m_errors():
        errs = modal_errors()
        if not errs:
            return None
        return tags.div(tags.ul(*[tags.li(e) for e in errs]), class_="os-errors", role="alert")

    @reactive.effect
    @reactive.event(input.add_click)
    def _add():
        kind = input.add_click()["kind"]
        limit = MAX_OBJECTIVES if kind == "obj" else MAX_CONSTRAINTS
        if len(items_of(kind)) < limit:
            show_dialog(kind)

    @reactive.effect
    @reactive.event(input.row_click)
    def _edit():
        ev = input.row_click()
        item = find(ev["kind"], ev["id"])
        if item:
            show_dialog(ev["kind"], item)

    @reactive.effect
    @reactive.event(input.m_cancel)
    def _cancel():
        close_dialog()

    def validate(kind, item_id):
        errs, values = [], {}
        name = str(input.f_name() or "").strip()[:MAX_NAME_LENGTH]
        if not name:
            errs.append(tr("err_name"))
        elif any(i["name"] == name and i["id"] != item_id for i in items_of(kind)):
            errs.append(tr("err_name_taken"))
        labels = ("coef_c1", "coef_c2") if kind == "obj" else ("coef_a1", "coef_a2")
        fields = [("f_a1", labels[0]), ("f_a2", labels[1])] + ([("f_b", "rhs_b")] if kind == "con" else [])
        for fid, key in fields:
            v = input[fid]()
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v < 0:
                errs.append(tr("err_number", field=tr(key)))
            elif v > MAX_VALUE:
                errs.append(tr("err_number_large", field=tr(key)))
            else:
                values[fid] = float(v)
        # choices the browser sends are checked too: it could send anything
        if kind == "obj" and input.f_sense() not in ("max", "min"):
            errs.append(tr("err_choice", field=tr("sense")))
        if kind == "con" and input.f_op() not in ("≤", "≥", "="):
            errs.append(tr("err_choice", field=tr("operator")))
        if values.get("f_a1") == 0 and values.get("f_a2") == 0:
            errs.append(tr("err_both_zero"))
        return name, values, errs

    @reactive.effect
    @reactive.event(input.m_save)
    def _save():
        ed = editing()
        if not ed:
            return
        kind, item_id = ed
        name, values, errs = validate(kind, item_id)
        if errs:
            modal_errors.set(errs)
            return
        limit = MAX_OBJECTIVES if kind == "obj" else MAX_CONSTRAINTS
        if item_id is None and len(items_of(kind)) >= limit:
            close_dialog()
            return
        if kind == "obj":
            data = {"name": name, "c1": values["f_a1"], "c2": values["f_a2"], "sense": input.f_sense()}
            objs = [dict(o) for o in ctx.objectives()]
            if item_id is None:
                for o in objs:              # the new objective becomes the active one
                    o["active"] = False
                objs.append(dict(data, id=ctx.next_id(), active=True))
                ctx.notify("n_obj_added")
            else:
                objs = [dict(o, **data) if o["id"] == item_id else o for o in objs]
                ctx.notify("n_saved")
            ctx.objectives.set(objs)
        else:
            data = {"name": name, "a1": values["f_a1"], "a2": values["f_a2"], "op": input.f_op(), "b": values["f_b"]}
            cons = list(ctx.constraints())
            if item_id is None:
                used = {c["color_index"] for c in cons}
                color_index = next(i for i in range(len(cons) + 1) if i not in used)
                cons.append(dict(data, id=ctx.next_id(), active=True, color_index=color_index))
                ctx.notify("n_con_added")
            else:
                cons = [dict(c, **data) if c["id"] == item_id else c for c in cons]
                ctx.notify("n_saved")
            ctx.constraints.set(cons)
        ctx.problem_changed()
        close_dialog()

    @reactive.effect
    @reactive.event(input.m_delete)
    def _delete():
        ed = editing()
        if not ed or ed[1] is None:
            return
        kind, item_id = ed
        item = find(kind, item_id)
        if kind == "obj":
            objs = [o for o in ctx.objectives() if o["id"] != item_id]
            if item and item["active"] and objs:
                objs[-1] = dict(objs[-1], active=True)
            ctx.objectives.set(objs)
        else:
            ctx.constraints.set([c for c in ctx.constraints() if c["id"] != item_id])
        ctx.problem_changed()
        close_dialog()
        if item:
            ctx.notify("n_deleted", name=item["name"])
