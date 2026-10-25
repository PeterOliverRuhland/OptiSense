"""The worked solution of a step as a list of short lines, in the chosen language."""

import itertools

import numpy as np

from optisense.i18n import fmt_num, norm_lang, t
from .engine import EPS, axis_cut, boundaries, feasible, integrality, side_answer, solve, violated
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
    if sid == "model":
        vt = [t(lang, "integer_short" if k else "continuous_short") for k in integrality(m)]
        out.append(f"F = {formula(m['c'], lang)} → {m['sense']}")
        out.append(tr("range", vt1=vt[0], vt2=vt[1]))
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
    elif sid == "intersection":
        rows = boundaries(m)
        names = labels + ["x1 = 0", "x2 = 0"]
        for i, j in itertools.combinations(range(len(rows)), 2):
            B = np.array([rows[i]["a"], rows[j]["a"]], dtype=float)
            if abs(np.linalg.det(B)) < EPS:
                continue
            p = np.linalg.solve(B, [rows[i]["b"], rows[j]["b"]])
            if feasible(m, p, False):
                out.append(tr("cross", a=names[i], b=names[j], p=point(p, lang), z=num(float(np.dot(m["c"], p)))))
        out.append(tr("cross_any"))
        if m["kind"] != "LP":
            out.append(tr("cross_int"))
    elif sid == "optimum":
        x = sol["x"]
        out.append(tr("opt_point", p=point(x, lang)))
        out.append(tr("opt_value", calc=f"{num(m['c'][0])}·{num(x[0])} + {num(m['c'][1])}·{num(x[1])}", z=num(sol["z"])))
        if m["kind"] == "LP":
            corners = []
            for i, j in itertools.combinations(range(len(boundaries(m))), 2):
                rows = boundaries(m)
                B = np.array([rows[i]["a"], rows[j]["a"]], dtype=float)
                if abs(np.linalg.det(B)) < EPS:
                    continue
                p = np.linalg.solve(B, [rows[i]["b"], rows[j]["b"]])
                if feasible(m, p, False) and not any(np.linalg.norm(p - c) < 1e-6 for c, _ in corners):
                    corners.append((p, float(np.dot(m["c"], p))))
            if len(corners) > 1:
                out.append(tr("opt_corners", list="; ".join(f"{point(p, lang)}: {num(z)}" for p, z in corners)))
        else:
            out.append(tr("opt_int"))
        out.append(tr("opt_alt"))
    elif sid == "sensitivity":
        sen, x = ex["sen"], sol["x"]
        keys = {q["key"] for q in step["questions"]}
        for i, r in enumerate(m["rows"]):
            lhs = float(np.dot(r["a"], x))
            status = t(lang, "binding" if sen["slacks"][i] < 1e-6 else "non_binding")
            out.append(tr("slack", label=labels[i], lhs=num(lhs), b=num(r["b"]), s=num(sen["slacks"][i]), status=status))
        if "shadow0" in keys:
            for i, p in enumerate(sen["shadow"]):
                lo, hi = sen["rhs"][i]
                out.append(tr("shadow", label=labels[i], p=num(p), lo=num(lo), hi=num(hi)))
        if "range0_0" in keys:
            for j, (lo, hi) in enumerate(sen["ranges"]):
                out.append(tr("range_c", j=j + 1, lo=num(lo), hi=num(hi)))
        if "idelta" in keys:
            changed = {**m, "rows": [dict(r) for r in m["rows"]]}
            changed["rows"][0]["b"] += 1
            new = solve(changed)
            out.append(tr("idelta", label=labels[0], z=num(new["z"]), d=num(new["z"] - sol["z"])))
    elif sid == "interpret":
        # in words, like the interpretation of the optimum solution in the lecture
        out.append(tr(f"interp_{m['sense']}", z=num(sol["z"])))
        out.append(tr("interp_x", x1=num(sol["x"][0]), x2=num(sol["x"][1])))
        for i, (r, s) in enumerate(zip(m["rows"], ex["sen"]["slacks"])):
            key = "interp_bind" if s < 1e-6 else "interp_left" if r["op"] == "<=" else "interp_over"
            out.append(tr(key, label=labels[i], s=num(s)))
        out.append(tr("round"))
    elif sid == "simplex":
        n_rows = len(m["rows"])
        cols = ["x1", "x2"] + [f"s{i + 1}" for i in range(n_rows)]
        expected = {q["key"]: q["expected"] for q in step["questions"]}
        for i in range(len(step["tableaus"])):
            out.append(tr("simplex", n=i + 1, col=cols[int(expected[f"enter{i}"]) - 1],
                          row=labels[int(expected[f"leave{i}"]) - 1], p=num(expected[f"pivot{i}"]), z=num(expected[f"nextz{i}"])))
    return out


def all_lines(ex, lang):
    lang = norm_lang(lang)
    return {s["id"]: lines(ex, s, lang) for s in ex["steps"]}
