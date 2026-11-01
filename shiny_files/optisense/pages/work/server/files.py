"""Import & export of .lp files, the textbook example and resetting everything."""

from htmltools import TagList, tags
from shiny import reactive, render, ui

import math
import os

from optisense import core
from optisense.config import EXAMPLE_NAMES, MAX_CONSTRAINTS, MAX_IMPORT_BYTES, MAX_NAME_LENGTH, MAX_VALUE
from .html_utils import safe_filename


def upload_path(session, files):
    """Server path of the first file this session really uploaded, or None.

    The browser can overwrite the value of a file input, "datapath" included, so the path is only
    trusted if it is a file in this session's upload folder (an internal of shiny 1.2.1)."""
    manager = getattr(session.root_scope(), "_file_upload_manager", None)
    basedir = getattr(manager, "_basedir", None)
    info = files[0] if isinstance(files, (list, tuple)) and files else None
    path = info.get("datapath") if isinstance(info, dict) else None
    if not isinstance(basedir, str) or not isinstance(path, str):
        return None
    try:
        base, real = os.path.realpath(basedir), os.path.realpath(path)
        if real != base and os.path.commonpath([base, real]) == base and os.path.isfile(real):
            return real
    except (OSError, ValueError):
        pass
    return None


def register(ctx):
    input = ctx.input
    tr = ctx.tr
    pending_confirm = reactive.value(None)   # "reset" | "example"

    # ------------------------------------------------------------------ import / export
    @reactive.effect
    @reactive.event(input.btn_import_export)
    def _io_dialog():
        export_part = [tags.p(tr("export_text"))]
        if ctx.can_optimize():
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

    @render.download(filename=lambda: f"{safe_filename(input.lp_name(), 'optisense-problem')}.lp")
    def dl_lp():
        if ctx.can_optimize():
            yield core.to_lp_file(ctx.active_objective(), ctx.active_constraints(), ctx.var_types()).encode()

    @reactive.effect
    @reactive.event(input.btn_do_import)
    def _import():
        path = upload_path(ctx.session, input.lp_upload())
        if path is None:
            ctx.notify("n_import_none", "error")
            return
        try:
            if os.path.getsize(path) > MAX_IMPORT_BYTES:
                ctx.notify("n_import_too_large", "error", kb=MAX_IMPORT_BYTES // 1000)
                return
            with open(path, encoding="utf-8", errors="replace") as fh:
                obj, cons, var_types = core.parse_lp_file(fh.read(MAX_IMPORT_BYTES + 1))
        except OSError:
            ctx.notify("n_import_unreadable", "error")
            return
        except core.LPParseError as exc:
            # only the line number, never text from the file
            if exc.line is not None:
                ctx.notify("n_import_failed", "error", line=exc.line)
            elif exc.reason == core.lp_format.MISSING_PARTS:
                ctx.notify("n_import_incomplete", "error")
            else:
                ctx.notify("n_import_unreadable", "error")
            return
        if len(cons) > MAX_CONSTRAINTS:
            ctx.notify("n_import_too_many", "error", n=MAX_CONSTRAINTS)
            return
        values = [obj["c1"], obj["c2"]] + [v for c in cons for v in (c["a1"], c["a2"], c["b"])]
        if any(v < 0 for v in values):
            ctx.notify("n_import_negative", "error")
            return
        if not all(math.isfinite(v) and v <= MAX_VALUE for v in values):
            ctx.notify("n_import_too_big", "error")
            return
        for con in cons:
            con["name"] = (con.get("name") or "")[:MAX_NAME_LENGTH] or None
        ctx.load_problem(obj, cons, var_types)
        ui.modal_remove()
        ctx.notify("n_imported")

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
        names = EXAMPLE_NAMES[ctx.lang()]
        ctx.load_problem({"name": "F", "c1": 10, "c2": 20, "sense": "max"},
                         [{"name": names[0], "a1": 6, "a2": 9, "op": "≤", "b": 720},
                          {"name": names[1], "a1": 0, "a2": 1, "op": "≤", "b": 60}],
                         {"x1": "con", "x2": "con"})
        ctx.notify("n_example")
        ui.update_navs("page", selected="work")

    def example_request():
        if ctx.objectives() or ctx.constraints():
            confirm("example", "load_example", "example_replace", "load_example")
        else:
            load_example()

    @reactive.effect
    @reactive.event(input.btn_example)
    def _example():
        example_request()

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
        elif kind == "reset":
            ctx.objectives.set([])
            ctx.constraints.set([])
            ctx.set_var_types({"x1": "con", "x2": "con"})
            ctx.notify("n_reset", "warning")
