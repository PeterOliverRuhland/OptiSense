"""Per-session state and helpers shared by all server parts.

objectives:  [{id, name, c1, c2, sense, active}]          (at most MAX_OBJECTIVES, one active)
constraints: [{id, name, a1, a2, op, b, active, color_index}]  (at most MAX_CONSTRAINTS)
"""

from htmltools import tags
from shiny import reactive, ui

from .. import core, plotting
from ..config import DEFAULT_NAMES
from ..i18n import fmt_num, norm_lang, t


class AppContext:
    def __init__(self, input, session):
        self.input = input
        self.session = session
        self.objectives = reactive.value([])
        self.constraints = reactive.value([])
        self.var_types = reactive.value({"x1": "con", "x2": "con"})
        self.solution = reactive.value(None)      # result of core.solve for the current problem
        self.sensitivity = reactive.value(None)   # result of core.run_sensitivity
        self._next_id = 0

        @reactive.calc
        def lang():
            return norm_lang(input.lang())

        @reactive.calc
        def active_objective():
            return next((o for o in self.objectives() if o["active"]), None)

        @reactive.calc
        def active_constraints():
            return [c for c in self.constraints() if c["active"]]

        @reactive.calc
        def ptype():
            return core.problem_type(self.var_types())

        @reactive.calc
        def plot_scale():
            # sent by www/optisense.js: root font size / 16, grows on large screens
            try:
                return float(input.ui_scale())
            except Exception:  # noqa: BLE001 - not sent yet
                return 1.0

        self.lang = lang
        self.active_objective = active_objective
        self.active_constraints = active_constraints
        self.ptype = ptype
        self.plot_scale = plot_scale

    # ------------------------------------------------------------------ ids and state changes
    def next_id(self):
        self._next_id += 1
        return self._next_id

    def problem_changed(self):
        """Any change to the problem makes old results invalid."""
        self.solution.set(None)
        self.sensitivity.set(None)

    def has_optimum(self):
        sol = self.solution()
        return bool(sol and sol.get("status") == "optimal")

    def can_optimize(self):
        return self.active_objective() is not None and bool(self.active_constraints())

    def load_problem(self, obj, cons, var_types):
        """Replace the whole problem (example, import)."""
        lc = self.lang()
        self.objectives.set([dict(id=self.next_id(), name=obj.get("name") or "F", c1=obj["c1"], c2=obj["c2"],
                                  sense=obj["sense"], active=True)])
        new_cons, names = [], set()
        for i, con in enumerate(cons):
            name = con.get("name") or DEFAULT_NAMES["constraint"][lc].format(n=i + 1)
            if name in names:
                name = f"{name}_{i + 1}"
            names.add(name)
            new_cons.append(dict(id=self.next_id(), name=name, a1=con["a1"], a2=con["a2"], op=con["op"], b=con["b"],
                                 active=True, color_index=i))
        self.constraints.set(new_cons)
        self.set_var_types(var_types)

    def set_var_types(self, var_types):
        self.var_types.set(dict(var_types))
        ui.update_radio_buttons("vt_x1", selected=var_types["x1"])
        ui.update_radio_buttons("vt_x2", selected=var_types["x2"])
        self.problem_changed()

    # ------------------------------------------------------------------ text
    def tr(self, key, **kw):
        return t(self.lang(), key, **kw)

    def num(self, value):
        return fmt_num(value, self.lang())

    def notify(self, key, kind="message", **kw):
        """Errors stay until closed; other messages disappear after 3 s. One shared id, so a new
        message replaces the previous one instead of stacking."""
        ui.notification_show(self.tr(key, **kw), type=kind, duration=None if kind == "error" else 3, id="os-status")

    def formula(self, a1, a2):
        parts = []
        for coef, var in ((a1, "x1"), (a2, "x2")):
            if coef == 0:
                continue
            parts.append(f"{'' if coef == 1 else fmt_num(coef, self.lang()) + '·'}{var}")
        return " + ".join(parts) if parts else "0"

    def con_text(self, con):
        return f"{self.formula(con['a1'], con['a2'])} {con['op']} {self.num(con['b'])}"

    # ------------------------------------------------------------------ small visual pieces
    @staticmethod
    def swatch(color, dashed=False):
        cls = "os-swatch is-dashed" if dashed else "os-swatch"
        return tags.span(class_=cls, style=f"background:{color};color:{color}", **{"aria-hidden": "true"})

    def con_swatch(self, con):
        color, line = plotting.constraint_style(con["color_index"])
        return self.swatch(color, dashed=(line != "-"))

    @staticmethod
    def colored_name(name, color):
        return tags.span(name, class_="os-name", style=f"color:{color}")
