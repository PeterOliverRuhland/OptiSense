"""Import & export of .lp files, the textbook example and resetting everything."""

from htmltools import TagList, tags
from shiny import reactive, render, ui

from .. import core
from ..config import EXAMPLE_NAMES
from .html_utils import safe_filename


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
        files = input.lp_upload()
        if not files:
            ctx.notify("n_import_none", "error")
            return
        try:
            with open(files[0]["datapath"], encoding="utf-8", errors="replace") as fh:
                obj, cons, var_types = core.parse_lp_file(fh.read())
        except core.LPParseError as exc:
            ctx.notify("n_import_failed", "error", line=str(exc)[:80])
            return
        values = [obj["c1"], obj["c2"]] + [v for c in cons for v in (c["a1"], c["a2"], c["b"])]
        if any(v < 0 for v in values):
            ctx.notify("n_import_negative", "error")
            return
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
    @reactive.event(input.guide_load_example)
    def _example_from_guide():
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
