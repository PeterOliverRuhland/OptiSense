"""Geometry for the graph: axis bounds, feasible region, lines and the dummy objective line."""

import math

from .model import EPS, problem_type


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

