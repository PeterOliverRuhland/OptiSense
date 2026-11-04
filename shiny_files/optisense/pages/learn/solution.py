"""The worked solution of a step as a list of short lines, in the chosen language."""

import numpy as np

from optisense.i18n import fmt_num, norm_lang, t
from .engine import EPS, axis_cut, binding, boundaries, integrality, optimal_corners, side_answer, slack, violated
from .story import row_labels

OP_SIGN = {"<=": "≤", ">=": "≥", "=": "="}


def formula(a, lang):
    """a1·x1 + a2·x2 without zero terms and without a written 1 – like the lists on “Model & solution”."""
    parts = []
    for coef, var in zip(a, ("x1", "x2")):
        if abs(coef) < EPS:
            continue
        mag = abs(coef)
        term = var if abs(mag - 1) < EPS else f"{fmt_num(mag, lang)}·{var}"
        if not parts:
            parts.append(("−" if coef < 0 else "") + term)
        else:
            parts.append(("− " if coef < 0 else "+ ") + term)
    return " ".join(parts) if parts else "0"


def point(p, lang):
    return f"({fmt_num(p[0], lang)} | {fmt_num(p[1], lang)})"


def lines(ex, step, lang):
    m, sol = ex["model"], ex["solution"]
    labels = row_labels(ex, lang)
    tr = lambda key, **kw: t(lang, f"learn_sol_{key}", **kw)  # noqa: E731
    num = lambda v: fmt_num(v, lang)  # noqa: E731
    sid, out = step["id"], []
    if sid == "objective":
        vt = [t(lang, "integer_short" if k else "continuous_short") for k in integrality(m)]
        out.append(f"F = {formula(m['c'], lang)} → {m['sense']}")
        out.append(tr("range", vt1=vt[0], vt2=vt[1]))
    elif sid == "constraints":
        out += [f"{labels[i]}: {formula(r['a'], lang)} {OP_SIGN[r['op']]} {num(r['b'])}" for i, r in enumerate(m["rows"])]
        out.append(tr("scaled"))
    elif sid == "lines":
        # the table of axis intersections, like in the lecture
        for i, r in enumerate(m["rows"]):
            cuts = []
            for j in range(2):
                cut = axis_cut(r, j)
                cuts.append("–" if cut is None else f"{num(r['b'])} ÷ {num(r['a'][j])} = {num(cut)}")
            out.append(tr("line", label=labels[i], eq=f"{formula(r['a'], lang)} = {num(r['b'])}", p=cuts[0], q=cuts[1]))
        out.append(tr("line_none"))
    elif sid == "region":
        for i, (r, p) in enumerate(zip(m["rows"], ex["test_points"])):
            if r["op"] == "=":
                out.append(tr("side_eq", label=labels[i]))
                continue
            lhs = float(np.dot(r["a"], p))
            ok = side_answer(r, p) == "in"
            out.append(tr("side_in" if ok else "side_out", label=labels[i], p=point(p, lang),
                          check=f"{num(lhs)} {OP_SIGN[r['op']]} {num(r['b'])}"))
        for n, p in enumerate(ex["points"]):
            bad = violated(m, p)
            if not bad:
                out.append(tr("point_ok", n=n + 1, p=point(p, lang)))
            else:
                names = [labels[i] if isinstance(i, int) else t(lang, f"learn_sol_broken_{i}") for i in bad]
                out.append(tr("point_bad", n=n + 1, p=point(p, lang), names=", ".join(names)))
    elif sid == "corner":
        names = labels + [t(lang, "learn_axis_x1"), t(lang, "learn_axis_x2")]
        best = optimal_corners(m)
        out.append(tr("corner_move_" + m["sense"]))
        out.append(tr("corner", a=names[best[0][0]], b=names[best[0][1]]))
        if len(best) > 1:
            out.append(tr("corner_alt"))
    elif sid == "optimum":
        best = optimal_corners(m) if m["kind"] == "LP" else []
        if best:
            # the corner from the step before: two equations, solved together
            i, j, x = best[0]
            rows = boundaries(m)
            for k in (i, j):
                eq = f"{formula(rows[k]['a'], lang)} = {num(rows[k]['b'])}"
                out.append(f"{labels[k]}: {eq}" if k < len(labels) else eq)
            out.append(tr("opt_solve", p=point(x, lang)))
        else:
            x = sol["x"]
            out.append(tr("opt_point", p=point(x, lang)))
        out.append(tr("opt_value", calc=f"{num(m['c'][0])}·{num(x[0])} + {num(m['c'][1])}·{num(x[1])}", z=num(sol["z"])))
        if not best:
            out.append(tr("opt_int"))
        if len(best) != 1:
            out.append(tr("opt_alt"))
    elif sid == "slack":
        # the optimal point put into every constraint: what is used, what is left over
        x = sol["x"]
        for i, r in enumerate(m["rows"]):
            status = t(lang, "binding" if binding(r, x) else "non_binding")
            out.append(tr("slack", label=labels[i], lhs=num(float(np.dot(r["a"], x))), b=num(r["b"]), s=num(slack(r, x)), status=status))
        out.append(tr("slack_lines"))
    elif sid == "interpret":
        # in words, like the interpretation of the optimum solution in the lecture
        out.append(tr(f"interp_{m['sense']}", z=num(sol["z"])))
        out.append(tr("interp_x", x1=num(sol["x"][0]), x2=num(sol["x"][1])))
        for i, r in enumerate(m["rows"]):
            key = "interp_bind" if binding(r, sol["x"]) else "interp_left" if r["op"] == "<=" else "interp_over"
            out.append(tr(key, label=labels[i], s=num(slack(r, sol["x"]))))
        out.append(tr("round"))
    return out


def all_lines(ex, lang):
    lang = norm_lang(lang)
    return {s["id"]: lines(ex, s, lang) for s in ex["steps"]}
