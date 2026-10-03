"""Core logic of OptiSense: problem model, solving, feasible region, LP file I/O and
sensitivity analysis via lp_solve. Contains no Shiny code, so it can be tested on its own."""

import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

import numpy as np
from scipy.optimize import LinearConstraint, milp

EPS = 1e-9
OPS = ("≤", "≥", "=")


# ---------------------------------------------------------------------------
# Problem type
# ---------------------------------------------------------------------------

def problem_type(var_types):
    """var_types = {"x1": "con"|"int", "x2": "con"|"int"} -> "LP" | "ILP" | "MILP"."""
    ints = [v for v in ("x1", "x2") if var_types.get(v) == "int"]
    if not ints:
        return "LP"
    if len(ints) == 2:
        return "ILP"
    return "MILP"


def integrality(var_types):
    return [1 if var_types.get("x1") == "int" else 0, 1 if var_types.get("x2") == "int" else 0]


# ---------------------------------------------------------------------------
# Solving
# ---------------------------------------------------------------------------

def solve(objective, constraints, var_types):
    """Solve with scipy.optimize.milp.

    Returns dict(status="optimal"|"infeasible"|"unbounded"|"error", value, x1, x2).
    """
    c = np.array([objective["c1"], objective["c2"]], dtype=float)
    if objective["sense"] == "max":
        c = -c
    A, lb, ub = [], [], []
    for con in constraints:
        A.append([con["a1"], con["a2"]])
        if con["op"] == "≤":
            lb.append(-np.inf)
            ub.append(con["b"])
        elif con["op"] == "≥":
            lb.append(con["b"])
            ub.append(np.inf)
        else:
            lb.append(con["b"])
            ub.append(con["b"])
    kwargs = {"integrality": integrality(var_types)}
    if A:
        kwargs["constraints"] = LinearConstraint(np.array(A, dtype=float), np.array(lb), np.array(ub))
    try:
        res = milp(c, **kwargs)
    except Exception:  # noqa: BLE001 - surface any solver problem as a message
        return {"status": "error"}
    if res.status == 0 and res.x is not None:
        value = float(-res.fun if objective["sense"] == "max" else res.fun)
        x1, x2 = (float(v) for v in res.x)
        return {"status": "optimal", "value": _clean(value), "x1": _clean(x1), "x2": _clean(x2)}
    if res.status == 2:
        return {"status": "infeasible"}
    if res.status == 3:
        return {"status": "unbounded"}
    if res.status == 4 and any(kwargs["integrality"]):
        # HiGHS cannot tell "unbounded" from "infeasible" for integer problems; the LP relaxation can
        relaxed = solve(objective, constraints, {"x1": "con", "x2": "con"})
        if relaxed["status"] in ("unbounded", "infeasible"):
            return {"status": relaxed["status"]}
    return {"status": "error"}


def _clean(v, digits=9):
    v = round(v, digits)
    return 0.0 if v == 0 else v


def constraint_activity(constraints, x1, x2):
    """Left-hand side, slack and binding status of each constraint at (x1, x2)."""
    rows = []
    for con in constraints:
        lhs = _clean(con["a1"] * x1 + con["a2"] * x2)
        slack = _clean(abs(con["b"] - lhs))
        rows.append({"lhs": lhs, "slack": slack, "binding": slack <= 1e-7 * max(1.0, abs(con["b"]))})
    return rows


# ---------------------------------------------------------------------------
# Geometry for the graph
# ---------------------------------------------------------------------------

def intercepts(a1, a2, b):
    """Where a1*x1 + a2*x2 = b meets the axes (None where it never does)."""
    return (b / a1 if a1 else None, b / a2 if a2 else None)


def plot_bounds(objective, constraints, solution=None):
    """Axis limits: 10 % above the largest axis intercept or solution coordinate."""
    xs, ys = [0.0], [0.0]
    for con in constraints:
        i1, i2 = intercepts(con["a1"], con["a2"], con["b"])
        if i1 is not None:
            xs.append(i1)
        if i2 is not None:
            ys.append(i2)
    if solution and solution.get("status") == "optimal":
        xs.append(solution["x1"])
        ys.append(solution["x2"])
    xmax, ymax = max(xs), max(ys)
    # a constraint parallel to an axis gives only one intercept; mirror the other axis then
    if xmax <= 0:
        xmax = ymax or 10
    if ymax <= 0:
        ymax = xmax or 10
    return _nice_ceil(xmax * 1.1), _nice_ceil(ymax * 1.1)


def _nice_ceil(v):
    if v <= 0:
        return 10.0
    mag = 10 ** math.floor(math.log10(v))
    for step in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if step * mag >= v - EPS:
            return float(step * mag)
    return float(v)


def _clip(poly, a1, a2, b, keep_le):
    """Sutherland–Hodgman: keep the part of poly with a1*x+a2*y <= b (or >= b)."""
    def inside(p):
        v = a1 * p[0] + a2 * p[1] - b
        return v <= EPS if keep_le else v >= -EPS

    def cross(p, q):
        vp = a1 * p[0] + a2 * p[1] - b
        vq = a1 * q[0] + a2 * q[1] - b
        t = vp / (vp - vq)
        return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))

    out = []
    n = len(poly)
    for i in range(n):
        cur, prev = poly[i], poly[i - 1]
        if inside(cur):
            if not inside(prev):
                out.append(cross(prev, cur))
            out.append(cur)
        elif inside(prev):
            out.append(cross(prev, cur))
    return out


def feasible_polygon(constraints, xmax, ymax):
    """Continuous feasible region inside [0, xmax] x [0, ymax] as a list of vertices."""
    poly = [(0.0, 0.0), (xmax, 0.0), (xmax, ymax), (0.0, ymax)]
    for con in constraints:
        if con["op"] in ("≤", "="):
            poly = _clip(poly, con["a1"], con["a2"], con["b"], True)
        if con["op"] in ("≥", "="):
            poly = _clip(poly, con["a1"], con["a2"], con["b"], False)
        if not poly:
            return []
    return poly


def is_feasible(constraints, x1, x2, tol=1e-7):
    for con in constraints:
        lhs = con["a1"] * x1 + con["a2"] * x2
        scale = tol * max(1.0, abs(con["b"]))
        if con["op"] == "≤" and lhs > con["b"] + scale:
            return False
        if con["op"] == "≥" and lhs < con["b"] - scale:
            return False
        if con["op"] == "=" and abs(lhs - con["b"]) > scale:
            return False
    return True


def x2_interval(constraints, x1, ymax):
    """Feasible x2 values for a fixed x1 as (lo, hi) or None."""
    lo, hi = 0.0, ymax
    for con in constraints:
        rest = con["b"] - con["a1"] * x1
        if abs(con["a2"]) < EPS:
            if not is_feasible([con], x1, 0.0):
                return None
            continue
        bound = rest / con["a2"]
        if con["op"] == "≤":
            hi = min(hi, bound)
        elif con["op"] == "≥":
            lo = max(lo, bound)
        else:
            lo, hi = max(lo, bound), min(hi, bound)
    return (lo, hi) if hi >= lo - EPS else None


def x1_interval(constraints, x2, xmax):
    swapped = [dict(con, a1=con["a2"], a2=con["a1"]) for con in constraints]
    return x2_interval(swapped, x2, xmax)


def feasible_region(constraints, var_types, xmax, ymax, max_points=6000):
    """Return the feasible region in the form the graph needs.

    {"kind": "polygon", "points": [...]}                     LP
    {"kind": "points", "points": [...], "thinned": bool}      ILP
    {"kind": "vsegments"|"hsegments", "segments": [...], ...} MILP
    """
    t = problem_type(var_types)
    if t == "LP":
        return {"kind": "polygon", "points": feasible_polygon(constraints, xmax, ymax)}

    def steps(limit):
        n = int(math.floor(limit)) + 1
        stride = max(1, math.ceil(n / 400))
        return list(range(0, n, stride)), stride > 1

    if t == "ILP":
        xs, thin_x = steps(xmax)
        ys, thin_y = steps(ymax)
        if len(xs) * len(ys) > max_points * 20:
            stride = math.ceil(math.sqrt(len(xs) * len(ys) / (max_points * 20)))
            xs, ys, thin_x = xs[::stride], ys[::stride], True
        pts = [(x, y) for x in xs for y in ys if is_feasible(constraints, x, y)]
        return {"kind": "points", "points": pts, "thinned": thin_x or thin_y}

    if var_types.get("x1") == "int":
        xs, thinned = steps(xmax)
        segs = []
        for x in xs:
            iv = x2_interval(constraints, x, ymax)
            if iv:
                segs.append((x, iv[0], iv[1]))
        return {"kind": "vsegments", "segments": segs, "thinned": thinned}

    ys, thinned = steps(ymax)
    segs = []
    for y in ys:
        iv = x1_interval(constraints, y, xmax)
        if iv:
            segs.append((y, iv[0], iv[1]))
    return {"kind": "hsegments", "segments": segs, "thinned": thinned}


def line_in_box(a1, a2, b, xmax, ymax):
    """Segment of a1*x1 + a2*x2 = b inside [0, xmax] x [0, ymax], or None."""
    pts = []
    if abs(a2) > EPS:
        for x in (0.0, xmax):
            y = (b - a1 * x) / a2
            if -EPS <= y <= ymax + EPS:
                pts.append((x, y))
    if abs(a1) > EPS:
        for y in (0.0, ymax):
            x = (b - a2 * y) / a1
            if -EPS <= x <= xmax + EPS:
                pts.append((x, y))
    uniq = []
    for p in pts:
        if all(abs(p[0] - q[0]) > 1e-9 or abs(p[1] - q[1]) > 1e-9 for q in uniq):
            uniq.append(p)
    if len(uniq) < 2:
        return None
    uniq.sort()
    return uniq[0], uniq[-1]


def dummy_level(objective, constraints, xmax, ymax):
    """Objective value for the dashed 'dummy' iso-line: halfway across the feasible region."""
    poly = feasible_polygon(constraints, xmax, ymax) if constraints else []
    if not poly:
        poly = [(0, 0), (xmax, ymax)]
    vals = [objective["c1"] * x + objective["c2"] * y for x, y in poly]
    lo, hi = min(vals), max(vals)
    level = lo + 0.5 * (hi - lo)
    if level <= EPS:
        level = 0.25 * (objective["c1"] * xmax + objective["c2"] * ymax)
    return level


def perpendicular_foot(a1, a2, level, x0, y0):
    """Foot of the perpendicular from (x0, y0) onto a1*x + a2*y = level."""
    d = a1 * a1 + a2 * a2
    if d < EPS:
        return None
    k = (a1 * x0 + a2 * y0 - level) / d
    return x0 - k * a1, y0 - k * a2


# ---------------------------------------------------------------------------
# LP file format
# ---------------------------------------------------------------------------

def _fmt_coef(v):
    return f"{v:g}"


def to_lp_file(objective, constraints, var_types):
    lines = [f"{objective['sense']}: {_fmt_coef(objective['c1'])} x1 + {_fmt_coef(objective['c2'])} x2;"]
    for i, con in enumerate(constraints, start=1):
        sym = {"≤": "<=", "≥": ">=", "=": "="}[con["op"]]
        label = _lp_label(con["name"], i)
        lines.append(f"{label}: {_fmt_coef(con['a1'])} x1 + {_fmt_coef(con['a2'])} x2 {sym} {_fmt_coef(con['b'])};")
    lines += ["x1 >= 0;", "x2 >= 0;"]
    ints = [v for v in ("x1", "x2") if var_types.get(v) == "int"]
    if ints:
        lines.append(f"int {','.join(ints)};")
    return "\n".join(lines) + "\n"


def _lp_label(name, i):
    label = re.sub(r"[^A-Za-z0-9_]", "_", name or "")
    if not label or not label[0].isalpha():
        label = f"R{i}"
    return label


class LPParseError(ValueError):
    pass


_TERM = re.compile(r"([+-]?)\s*(\d*\.?\d+(?:[eE][+-]?\d+)?)?\s*\*?\s*(x[12])\b")


def _parse_expr(expr):
    expr = expr.strip()
    coef = {"x1": 0.0, "x2": 0.0}
    rest = _TERM.sub("", expr).replace("+", "").replace(" ", "")
    if rest:
        raise LPParseError(expr)
    for sign, num, var in _TERM.findall(expr):
        val = float(num) if num else 1.0
        coef[var] += -val if sign == "-" else val
    return coef


def parse_lp_file(text):
    """Parse the LP format OptiSense writes (and simple hand-written files like it)."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    statements = [s.strip() for s in text.split(";") if s.strip()]
    objective, constraints = None, []
    var_types = {"x1": "con", "x2": "con"}
    for st in statements:
        low = st.lower()
        m = re.match(r"^(max|maximi[sz]e|min|minimi[sz]e)\s*:(.*)$", low, flags=re.S)
        if m:
            coef = _parse_expr(m.group(2))
            objective = {"c1": coef["x1"], "c2": coef["x2"], "sense": "max" if m.group(1).startswith("max") else "min"}
            continue
        m = re.match(r"^int\s+(.*)$", low)
        if m:
            for var in re.split(r"[\s,]+", m.group(1).strip()):
                if var in ("x1", "x2"):
                    var_types[var] = "int"
                elif var:
                    raise LPParseError(st)
            continue
        name = None
        m = re.match(r"^-?([A-Za-z_][A-Za-z0-9_\[\].]*)\s*:(.*)$", st, flags=re.S)
        if m:
            name, st = m.group(1), m.group(2)
        m = re.match(r"^(.*?)(<=|>=|=<|=>|<|>|=)(.*)$", st, flags=re.S)
        if not m:
            raise LPParseError(st)
        left, op, right = m.group(1), m.group(2), m.group(3)
        op = {"<=": "≤", "=<": "≤", "<": "≤", ">=": "≥", "=>": "≥", ">": "≥", "=": "="}[op]
        coef = _parse_expr(left)
        try:
            b = float(right.strip())
        except ValueError as exc:
            raise LPParseError(st) from exc
        # plain non-negativity bounds are implied
        if name is None and b == 0 and op == "≥" and sum(1 for v in coef.values() if v) == 1 and max(coef.values()) == 1:
            continue
        constraints.append({"name": name, "a1": coef["x1"], "a2": coef["x2"], "op": op, "b": b})
    if objective is None or not constraints:
        raise LPParseError("missing objective or constraints")
    return objective, constraints, var_types


# ---------------------------------------------------------------------------
# Sensitivity analysis with lp_solve
# ---------------------------------------------------------------------------

def find_lp_solve():
    exe = os.environ.get("LP_SOLVE_BIN") or shutil.which("lp_solve")
    if exe:
        return exe
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_dir = os.path.join(base, "lp_solve_5.5", "lp_solve", "bin")
    if sys.platform.startswith("linux"):
        return os.path.join(bin_dir, "linux", "lp_solve")
    if sys.platform == "darwin":
        return os.path.join(bin_dir, "mac", "lp_solve")
    if sys.platform.startswith("win"):
        return os.path.join(bin_dir, "windows64", "lp_solve.exe")
    return None


def _num(token):
    v = float(token)
    if v <= -1e29:
        return -math.inf
    if v >= 1e29:
        return math.inf
    return _clean(v)


def run_sensitivity(objective, constraints, var_types, timeout=30):
    """Run lp_solve -S4 and return shadow prices and objective-coefficient limits.

    Rows are named R1..Rn in the order of `constraints`.
    Raises FileNotFoundError / OSError if lp_solve cannot start, subprocess.TimeoutExpired on timeout.
    """
    exe = find_lp_solve()
    if not exe:
        raise FileNotFoundError("lp_solve")
    lines = [f"{objective['sense']}: {_fmt_coef(objective['c1'])} x1 + {_fmt_coef(objective['c2'])} x2;"]
    for i, con in enumerate(constraints, start=1):
        sym = {"≤": "<=", "≥": ">=", "=": "="}[con["op"]]
        lines.append(f"R{i}: {_fmt_coef(con['a1'])} x1 + {_fmt_coef(con['a2'])} x2 {sym} {_fmt_coef(con['b'])};")
    lines += ["x1 >= 0;", "x2 >= 0;"]
    ints = [v for v in ("x1", "x2") if var_types.get(v) == "int"]
    if ints:
        lines.append(f"int {','.join(ints)};")
    path = os.path.join(tempfile.gettempdir(), f"optisense_{uuid.uuid4().hex}.lp")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    try:
        out = subprocess.run([exe, "-S4", path], capture_output=True, text=True, timeout=timeout).stdout
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    return parse_sensitivity(out, len(constraints))


def parse_sensitivity(output, n_constraints):
    shadow = {}
    limits = {}
    section = None
    for raw in output.splitlines():
        line = raw.strip()
        if line.startswith("Objective function limits"):
            section = "limits"
            continue
        if line.startswith("Dual value"):
            section = "dual"
            continue
        if not line or line.startswith("From") or line.startswith("Dual values"):
            continue
        parts = line.split()
        if section == "limits" and parts[0] in ("x1", "x2") and len(parts) >= 4:
            limits[parts[0]] = {"from": _num(parts[1]), "till": _num(parts[2])}
        elif section == "dual" and len(parts) >= 4 and re.fullmatch(r"R\d+", parts[0]):
            idx = int(parts[0][1:]) - 1
            shadow[idx] = {"price": _num(parts[1]), "from": _num(parts[2]), "till": _num(parts[3])}
    if "Dual value" not in output:
        raise ValueError("unexpected lp_solve output")
    return {
        "shadow": [shadow.get(i) for i in range(n_constraints)],
        "limits": {v: limits.get(v) for v in ("x1", "x2")},
    }
