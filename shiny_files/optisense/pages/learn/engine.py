"""Exercises with two variables: model check, generation, reference solution and grading.

No Shiny code and no texts. Questions are identified by keys (c0, a1_0, line0_1_0 …); the browser
(www/learn.js) labels them in the chosen language, story.py and solution.py write the texts that
depend on the numbers. Expected answers never leave the server.

Every generated task is solved with SciPy before it is used. LP sensitivity uses the normal cone
and an optimal basis; integer tasks are re-solved instead (a shadow price does not apply there).
"""

import copy
import itertools
import math
import random
import re
from fractions import Fraction

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

EPS = 1e-7
KINDS = ("LP", "ILP", "MILP1", "MILP2")
INTEGRALITY = {"LP": (0, 0), "ILP": (1, 1), "MILP1": (1, 0), "MILP2": (0, 1)}
OPS = ("<=", ">=", "=")
TOPICS = ("gastro", "production", "farming", "events", "transport", "advertising")
MIN_TOPICS = ("gastro", "farming", "transport", "advertising")   # contexts that also make sense as cost minimisation
WEIGHTS = {"model": 25, "lines": 15, "region": 10, "intersection": 15, "optimum": 25, "sensitivity": 20,
           "interpret": 5, "simplex": 10}
OPTIONS = {"mode": ("practice", "exam"), "form": ("text", "math"), "method": ("both", "graph", "calc"),
           "difficulty": ("easy", "medium", "hard"), "kind": ("LP", "ILP", "MILP")}
MAX_ROWS = 8


class LearnError(ValueError):
    """A problem the learner can fix. `key` names a text in texts.py (without the learn_ prefix)."""

    def __init__(self, key, **params):
        super().__init__(key)
        self.key, self.params = key, params


# ---------------------------------------------------------------------------------------------- numbers
INFINITY = {"inf", "+inf", "∞", "+∞", "infinity", "unendlich"}


def number(value, lang="en"):
    """A learner's number: decimal comma or point, fractions like 3/4, ∞. German reads 1.500 as 1500,
    English reads 1,500 as 1500."""
    if isinstance(value, bool):
        raise LearnError("err_number")
    if isinstance(value, (int, float)):
        out = float(value)
    else:
        s = str(value).strip().replace("−", "-").replace(" ", "").replace(" ", "")
        low = s.lower()
        if low in INFINITY:
            return math.inf
        if low.startswith("-") and low[1:] in INFINITY:
            return -math.inf
        if lang == "de" and re.fullmatch(r"-?[1-9]\d{0,2}(\.\d{3})+(,\d*)?", s):
            s = s.replace(".", "")
        elif lang != "de" and re.fullmatch(r"-?[1-9]\d{0,2}(,\d{3})+(\.\d*)?", s):
            s = s.replace(",", "")
        s = s.replace(",", ".")
        try:
            out = float(Fraction(s))
        except (ValueError, ZeroDivisionError):
            raise LearnError("err_number") from None
    if math.isnan(out):
        raise LearnError("err_number")
    return out


NONE_WORDS = {"-", "–", "—", "--", "keiner", "keine", "kein", "none", "no", "n/a"}


def is_none(value):
    """“No axis intersection” – the line is parallel to that axis."""
    return str(value).strip().lower() in NONE_WORDS


def axis_cut(r, j):
    """Where the boundary line of row r meets axis j (j = 0: x1-axis, j = 1: x2-axis); None if parallel."""
    return r["b"] / r["a"][j] if abs(r["a"][j]) > EPS else None


def close(answer, expected, lang="en"):
    try:
        a = number(answer, lang)
    except LearnError:
        return False
    if math.isinf(expected):
        return a == expected
    return bool(math.isfinite(a) and abs(a - expected) <= max(0.005, abs(expected) * 1e-4))


def nice_ceil(value):
    """Smallest 'round' axis maximum ≥ value (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 7, 8 × 10^k)."""
    if value <= 0:
        return 1.0
    p = 10 ** math.floor(math.log10(value))
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 7, 8, 10):
        if m * p >= value - 1e-9:
            return float(m * p)
    return float(10 * p)


# ---------------------------------------------------------------------------------------------- model
def validate(raw):
    """{c: [c1, c2], sense, kind, rows: [{a: [a1, a2], op, b, name?}]} with numbers checked."""
    try:
        m = copy.deepcopy(raw)
        m["c"] = [number(v) for v in m["c"]]
        m["sense"] = str(m["sense"]).lower()
        if len(m["c"]) != 2 or m["sense"] not in ("min", "max") or m["kind"] not in KINDS:
            raise LearnError("err_model")
        if not 1 <= len(m["rows"]) <= MAX_ROWS:
            raise LearnError("err_rows", n=MAX_ROWS)
        for r in m["rows"]:
            r["a"] = [number(v) for v in r["a"]]
            r["b"] = number(r["b"])
            r["op"] = {"≤": "<=", "≥": ">="}.get(r["op"], r["op"])
            if len(r["a"]) != 2 or r["op"] not in OPS:
                raise LearnError("err_model")
            if np.linalg.norm(r["a"]) < EPS:
                raise LearnError("err_row_zero")
        values = m["c"] + [v for r in m["rows"] for v in r["a"] + [r["b"]]]
        if not all(math.isfinite(v) and abs(v) <= 1e6 for v in values):
            raise LearnError("err_too_large")
        if np.linalg.norm(m["c"]) < EPS:
            raise LearnError("err_obj_zero")
        return m
    except (KeyError, TypeError, IndexError):
        raise LearnError("err_model") from None


def integrality(m):
    return INTEGRALITY[m["kind"]]


def kind_of(int1, int2):
    return {(0, 0): "LP", (1, 1): "ILP", (1, 0): "MILP1", (0, 1): "MILP2"}[(int(int1), int(int2))]


def solve(m):
    A = np.array([r["a"] for r in m["rows"]], dtype=float)
    lo = [r["b"] if r["op"] in (">=", "=") else -np.inf for r in m["rows"]]
    hi = [r["b"] if r["op"] in ("<=", "=") else np.inf for r in m["rows"]]
    sign = 1 if m["sense"] == "min" else -1
    args = dict(integrality=integrality(m), bounds=Bounds([0, 0], [np.inf, np.inf]), constraints=LinearConstraint(A, lo, hi))
    res = milp(sign * np.array(m["c"]), options={"time_limit": 5}, **args)
    if res.status == 4:  # HiGHS may report "unbounded or infeasible" with presolve on
        res = milp(sign * np.array(m["c"]), options={"time_limit": 5, "presolve": False}, **args)
    if res.status != 0:
        return {"status": {2: "infeasible", 3: "unbounded"}.get(res.status, "error")}
    x = np.array(res.x)
    x = np.where(np.abs(x - np.round(x)) < 1e-7, np.round(x), x)   # 299.9999999 → 300
    return {"status": "optimal", "x": x.tolist(), "z": float(np.dot(m["c"], x))}


def satisfies(r, x, tol=1e-6):
    v = float(np.dot(r["a"], x)) - r["b"]
    t = tol * max(1, abs(r["b"]))
    return v <= t if r["op"] == "<=" else v >= -t if r["op"] == ">=" else abs(v) <= t


def violated(m, x, integer=True):
    """Indices of the violated rows; 'neg' for x < 0, 'int' for a broken integer condition."""
    x = np.array(x, dtype=float)
    out = [i for i, r in enumerate(m["rows"]) if not satisfies(r, x)]
    if min(x) < -EPS:
        out.append("neg")
    if integer and any(k and abs(v - round(v)) > 1e-6 for k, v in zip(integrality(m), x)):
        out.append("int")
    return out


def feasible(m, x, integer=True):
    x = np.array(x, dtype=float)
    return x.shape == (2,) and bool(np.isfinite(x).all()) and not violated(m, x, integer)


def boundaries(m):
    """The constraint rows plus the two axes (x1 = 0 is the x2-axis, x2 = 0 the x1-axis)."""
    return m["rows"] + [{"a": [1, 0], "b": 0, "op": ">="}, {"a": [0, 1], "b": 0, "op": ">="}]


def vertices(m):
    out = []
    for r, s in itertools.combinations(boundaries(m), 2):
        B = np.array([r["a"], s["a"]], dtype=float)
        if abs(np.linalg.det(B)) < EPS:
            continue
        x = np.linalg.solve(B, [r["b"], s["b"]])
        if feasible(m, x, False) and not any(np.linalg.norm(x - y) < EPS for y in out):
            out.append(x)
    return out


def rays(m):
    """Extreme recession directions of the feasible region in the nonnegative orthant."""
    out = []
    for r in boundaries(m):
        a, b = r["a"]
        for d in (np.array([b, -a], float), np.array([-b, a], float)):
            norm = np.linalg.norm(d)
            if norm < EPS or min(d) < -EPS:
                continue
            d /= norm
            ok = all(np.dot(s["a"], d) <= EPS if s["op"] == "<=" else np.dot(s["a"], d) >= -EPS if s["op"] == ">="
                     else abs(np.dot(s["a"], d)) < EPS for s in m["rows"])
            if ok:
                out.append(d)
    return out


def sensitivity(m, x):
    x = np.array(x)
    c = np.array(m["c"])
    sign = 1 if m["sense"] == "max" else -1
    result = {"slacks": [abs(float(np.dot(r["a"], x) - r["b"])) for r in m["rows"]], "shadow": None, "rhs": None,
              "ranges": None}
    if m["kind"] != "LP":
        return result
    ds = [v - x for v in vertices(m)] + rays(m)
    ranges = []
    for j in range(2):
        low, high = -math.inf, math.inf
        for d in ds:
            a = sign * d[j]
            rhs = -sign * c[1 - j] * d[1 - j]
            if a > EPS:
                high = min(high, rhs / a)
            elif a < -EPS:
                low = max(low, rhs / a)
        ranges.append([low, high])
    result["ranges"] = ranges
    rows = boundaries(m)
    active = [i for i, r in enumerate(rows) if abs(np.dot(r["a"], x) - r["b"]) < 1e-5]
    for pair in itertools.combinations(active, 2):
        B = np.array([rows[i]["a"] for i in pair], float)
        if abs(np.linalg.det(B)) < EPS:
            continue
        dual = np.linalg.solve(B.T, c)
        if any((rows[i]["op"] == "<=" and sign * v < -EPS) or (rows[i]["op"] == ">=" and sign * v > EPS)
               for i, v in zip(pair, dual)):
            continue
        shadow = [0.0] * len(m["rows"])
        intervals = []
        for i, v in zip(pair, dual):
            if i < len(shadow):
                shadow[i] = float(v)
        for k, r in enumerate(m["rows"]):
            velocity = np.linalg.solve(B, [1.0 if i == k else 0.0 for i in pair])
            low, high = -math.inf, math.inf
            for i, s in enumerate(rows):
                factor = 1 if s["op"] == "<=" else -1
                t = float(np.dot(s["a"], velocity)) - (1 if i == k else 0)
                residual = s["b"] - float(np.dot(s["a"], x))
                conditions = [(t, residual), (-t, -residual)] if s["op"] == "=" else [(factor * t, factor * residual)]
                for a, b in conditions:
                    if a > EPS:
                        high = min(high, b / a)
                    elif a < -EPS:
                        low = max(low, b / a)
            intervals.append([r["b"] + low, r["b"] + high])
        result.update(shadow=shadow, rhs=intervals)
        break
    return result


def simplex_trace(m):
    """Tableaus of the primal simplex (most negative objective entry, smallest ratio, ties: first)."""
    n = len(m["rows"])
    T = np.zeros((n + 1, n + 3))
    T[0, :2] = -np.array(m["c"])
    for i, r in enumerate(m["rows"]):
        T[i + 1, :2] = r["a"]
        T[i + 1, i + 2] = 1
        T[i + 1, -1] = r["b"]
    trace = []
    for _ in range(12):
        col = int(np.argmin(T[0, :-1]))
        if T[0, col] >= -EPS:
            break
        candidates = [(T[i, -1] / T[i, col], i) for i in range(1, n + 1) if T[i, col] > EPS]
        if not candidates:
            break
        _, row = min(candidates)
        old = T.copy()
        pivot = T[row, col]
        T[row] /= pivot
        for i in range(n + 1):
            if i != row:
                T[i] -= T[i, col] * T[row]
        T[np.abs(T) < 1e-12] = 0
        trace.append({"tableau": old.tolist(), "enter": col, "leave": row, "pivot": float(pivot), "next_z": float(T[0, -1])})
    return trace


# ---------------------------------------------------------------------------------------------- generator
def generate(options):
    rng = random.Random(options.get("seed"))
    difficulty, kind = options["difficulty"], options["kind"]
    topic = options.get("topic") if options.get("topic") in TOPICS else rng.choice(TOPICS)
    for _ in range(150):
        a, b, d, e = rng.randint(1, 3), rng.randint(3, 6), rng.randint(3, 6), rng.randint(1, 3)
        if a * e == b * d:
            continue
        target = [rng.randint(3, 9) + rng.choice([0, 0.5]), rng.randint(3, 9) + rng.choice([0, 0.5])]
        c = [rng.randint(3, 12), rng.randint(3, 12)]
        sense = "min" if difficulty == "hard" and topic in MIN_TOPICS and rng.random() < 0.45 else "max"
        op = ">=" if sense == "min" else "<="
        rows = [{"a": [a, b], "b": a * target[0] + b * target[1], "op": op, "role": "r1"},
                {"a": [d, e], "b": d * target[0] + e * target[1], "op": op, "role": "r2"}]
        if difficulty != "easy":
            rows.append({"a": [1, 1], "b": math.ceil(sum(target)) + rng.randint(3, 8), "op": "<=", "role": "total"})
        if difficulty == "hard" and sense == "max" and rng.random() < 0.2:
            rows[-1]["op"] = "="
            rows[-1]["b"] = round(sum(target))
        if difficulty == "hard" and sense == "max" and rng.random() < 0.35:
            rows.append({"a": [1, 0], "b": rng.randint(1, 3), "op": ">=", "role": "least"})
        m = validate({"c": c, "rows": rows, "sense": sense, "kind": kind})
        sol = solve(m)
        if sol["status"] == "optimal" and min(sol["x"]) > EPS:
            return m, {"source": "generated", "topic": topic}, sol
    raise LearnError("err_generate")


# ---------------------------------------------------------------------------------------------- exercise
def normalize_options(raw, rng=random):
    """The learner's choices from the start page, reduced to known values ('MILP' picks one of the two)."""
    raw = raw if isinstance(raw, dict) else {}
    opts = {k: raw.get(k) if raw.get(k) in allowed else allowed[0] for k, allowed in OPTIONS.items()}
    if opts["kind"] == "MILP":
        opts["kind"] = rng.choice(["MILP1", "MILP2"])
    opts["topic"] = raw.get("topic") if raw.get("topic") in TOPICS else "random"
    opts["sensitivity"] = bool(raw.get("sensitivity", False))
    opts["simplex"] = bool(raw.get("simplex", False))
    return opts


def question(key, expected, choices=None):
    q = {"key": key, "expected": expected}
    if choices is not None:
        q["choices"] = [str(c) for c in choices]
    return q


def axis_extent(m, sol):
    """A 'round' axis maximum per axis that shows all corners and the relevant axis intercepts."""
    pts = [list(v) for v in vertices(m)] + [sol["x"]]
    out = []
    for j in range(2):
        base = max([1.0] + [abs(float(p[j])) for p in pts])
        reach = base
        for r in m["rows"]:
            if abs(r["a"][j]) > EPS:
                cut = r["b"] / r["a"][j]
                if 0 < cut <= 1.5 * base:
                    reach = max(reach, cut)
        out.append(nice_ceil(reach * 1.08))
    return out


def check_points(m, ext, sol):
    """Points for 'feasible or not?': the origin, a point inside, one far out and a non-optimal corner."""
    ints = integrality(m)

    def rnd(p):
        return [float(round(v)) if k else round(v * 2) / 2 for v, k in zip(p, ints)]

    vs = vertices(m)
    pts = [[0.0, 0.0]]
    if vs:
        pts.append(rnd(np.mean(vs, axis=0)))
    pts.append(rnd([ext[0] * 0.7, ext[1] * 0.7]))
    corners = [v for v in vs if np.linalg.norm(v - np.array(sol["x"])) > 1e-6 and np.linalg.norm(v) > 1e-6]
    corners.sort(key=lambda v: sum(abs(c * 2 - round(c * 2)) > 1e-9 for c in v))   # prefer corners like (6,5 | 0)
    if corners:
        pts.append([round(float(v), 4) for v in corners[0]])
    out = []
    for p in pts:
        if not any(abs(p[0] - q[0]) < 1e-9 and abs(p[1] - q[1]) < 1e-9 for q in out):
            out.append(p)
    return out


def side_test_point(r, ext):
    """A test point not on the boundary line: the origin if possible."""
    qx, qy = nice_ceil(ext[0] / 4), nice_ceil(ext[1] / 4)
    for p in ([0.0, 0.0], [qx, 0.0], [0.0, qy], [qx, qy]):
        if abs(float(np.dot(r["a"], p)) - r["b"]) > 1e-6 * max(1, abs(r["b"])):
            return p
    return [qx, qy]


def side_answer(r, p):
    if r["op"] == "=":
        return "line"
    return "in" if satisfies(r, p) else "out"


def simplex_possible(m, form, tutorial=False):
    return ((form != "text" or tutorial) and m["kind"] == "LP" and m["sense"] == "max"
            and all(r["op"] == "<=" and r["b"] >= 0 for r in m["rows"]))


def make_exercise(options, custom=None, info=None, points=None):
    """options: mode, form, method, difficulty, kind (LP/ILP/MILP1/MILP2), topic, sensitivity, simplex, seed.
    custom: a model to use instead of a generated one; info describes where the exercise comes from."""
    options = dict(options)
    tutorial = bool(info and info.get("source") == "tutorial")
    if custom is not None:
        m = validate(custom)
        sol = solve(m)
        info = info or {"source": "own"}
        if not tutorial:
            options["form"] = "math"
    else:
        m, info, sol = generate(options)
    if sol["status"] != "optimal":
        raise LearnError({"infeasible": "err_infeasible", "unbounded": "err_unbounded"}.get(sol["status"], "err_solver"))
    options["kind"] = m["kind"]
    sen = sensitivity(m, sol["x"])
    ext = axis_extent(m, sol)
    ints = integrality(m)
    method = options.get("method", "both")
    steps = []

    def add(sid, qs, **extra):
        steps.append({"id": sid, "questions": qs, **extra})

    if options.get("form") == "text":
        qs = [question("sense", m["sense"], ("max", "min")),
              question("vt0", "int" if ints[0] else "con", ("con", "int")),
              question("vt1", "int" if ints[1] else "con", ("con", "int")),
              question("c0", m["c"][0]), question("c1", m["c"][1])]
        for i, r in enumerate(m["rows"]):
            qs += [question(f"a{i}_0", r["a"][0]), question(f"a{i}_1", r["a"][1]),
                   question(f"op{i}", r["op"], OPS), question(f"b{i}", r["b"])]
        add("model", qs)
    test_points = [side_test_point(r, ext) for r in m["rows"]]
    region_points = points or check_points(m, ext, sol)
    if method in ("graph", "both"):
        add("lines", [question(f"ax{i}_{j}", axis_cut(r, j)) for i, r in enumerate(m["rows"]) for j in range(2)])
        qs = [question(f"side{i}", side_answer(r, p), ("in", "out", "line")) for i, (r, p) in enumerate(zip(m["rows"], test_points))]
        qs += [question(f"p{n}", "yes" if feasible(m, p) else "no", ("yes", "no")) for n, p in enumerate(region_points)]
        add("region", qs)
    if method in ("calc", "both"):
        idx = [str(i) for i in range(len(boundaries(m)))]
        add("intersection", [question("boundary1", None, idx), question("boundary2", None, idx),
                             question("crossx", None), question("crossy", None)])
    add("optimum", [question("x", sol["x"][0]), question("y", sol["x"][1]), question("z", sol["z"])])
    qs = [question(f"slack{i}", sen["slacks"][i]) for i in range(len(m["rows"]))]
    if options.get("sensitivity", True):
        if m["kind"] == "LP" and sen["shadow"] is not None:
            active = sum(v < EPS for v in sen["slacks"]) + sum(v < EPS for v in sol["x"])
            # one optimal basis only: non-degenerate and without equations, so the answers are unambiguous
            if active == 2 and not any(r["op"] == "=" for r in m["rows"]):
                qs += [question(f"shadow{i}", sen["shadow"][i]) for i in range(len(m["rows"]))]
                qs += [question(f"range{j}_{k}", sen["ranges"][j][k]) for j in range(2) for k in range(2)]
        elif m["kind"] != "LP":
            changed = copy.deepcopy(m)
            changed["rows"][0]["b"] += 1
            new = solve(changed)
            if new["status"] == "optimal":
                qs.append(question("idelta", new["z"] - sol["z"]))
    add("sensitivity", qs)
    add("interpret", [question("meaning", m["sense"], ("max", "min")), question("round", "no", ("yes", "no"))])
    if options.get("simplex") and simplex_possible(m, options.get("form"), tutorial):
        trace = simplex_trace(m)
        if trace:
            cols = [str(j + 1) for j in range(len(m["rows"]) + 2)]
            rows = [str(i + 1) for i in range(len(m["rows"]))]
            qs = []
            for i, t in enumerate(trace):
                qs += [question(f"enter{i}", str(t["enter"] + 1), cols), question(f"leave{i}", str(t["leave"]), rows),
                       question(f"pivot{i}", t["pivot"]), question(f"nextz{i}", t["next_z"])]
            add("simplex", qs, tableaus=[t["tableau"] for t in trace])
    total = sum(WEIGHTS[s["id"]] for s in steps)
    for s in steps:
        s["points"] = round(WEIGHTS[s["id"]] / total * 100)
    steps[-1]["points"] = 100 - sum(s["points"] for s in steps[:-1])
    return {"model": m, "solution": sol, "sen": sen, "options": options, "info": info, "steps": steps,
            "extent": ext, "points": region_points, "test_points": test_points}


def step_by_id(ex, sid):
    return next((s for s in ex["steps"] if s["id"] == sid), None)


# ---------------------------------------------------------------------------------------------- grading
def grade_step(ex, step, answers, all_answers=None, lang="en"):
    """{step, points, max, correct, checks: {key: bool}} for the learner's answers to one step."""
    m = ex["model"]
    answers = answers or {}
    checks = {}
    for q in step["questions"]:
        e, a = q["expected"], answers.get(q["key"], "")
        checks[q["key"]] = (str(a) == str(e)) if isinstance(e, str) else close(a, e, lang) if isinstance(e, (int, float)) else False

    def num(key, source=answers):
        return number(source.get(key, ""), lang)

    sid = step["id"]
    if sid == "model":
        # a constraint may be scaled as a whole (×2, ×−1 with the comparison turned round)
        for i, r in enumerate(m["rows"]):
            try:
                vals = [num(f"a{i}_0"), num(f"a{i}_1"), num(f"b{i}")]
            except LearnError:
                continue
            target = r["a"] + [r["b"]]
            idx = max(range(3), key=lambda j: abs(target[j]))
            factor = vals[idx] / target[idx]
            op = r["op"] if factor > 0 else {"<=": ">=", ">=": "<=", "=": "="}[r["op"]]
            ok = abs(factor) > EPS and answers.get(f"op{i}") == op and all(close(v, factor * t) for v, t in zip(vals, target))
            for key in (f"a{i}_0", f"a{i}_1", f"b{i}", f"op{i}"):
                checks[key] = ok
    elif sid == "lines":
        # axis intersections: a number, or “–” where the line is parallel to the axis
        for i, r in enumerate(m["rows"]):
            for j in range(2):
                key, cut, a = f"ax{i}_{j}", axis_cut(r, j), answers.get(f"ax{i}_{j}", "")
                checks[key] = is_none(a) if cut is None else (not is_none(a) and close(a, cut, lang))
    elif sid == "intersection":
        try:
            i, j = int(answers.get("boundary1", "-1")), int(answers.get("boundary2", "-1"))
        except (TypeError, ValueError):
            i = j = -1
        rows = boundaries(m)
        if i != j and 0 <= i < len(rows) and 0 <= j < len(rows):
            B = np.array([rows[i]["a"], rows[j]["a"]], dtype=float)
            valid = abs(np.linalg.det(B)) > EPS
            checks["boundary1"] = checks["boundary2"] = bool(valid)
            if valid:
                p = np.linalg.solve(B, [rows[i]["b"], rows[j]["b"]])
                checks["crossx"] = close(answers.get("crossx"), p[0], lang)
                checks["crossy"] = close(answers.get("crossy"), p[1], lang)
    elif sid == "optimum":
        try:
            p = [num("x"), num("y")]
            ok = feasible(m, p) and close(float(np.dot(m["c"], p)), ex["solution"]["z"])
        except LearnError:
            ok = False
        checks["x"] = checks["y"] = bool(ok)   # any optimal point counts (alternative optima)
    elif sid == "sensitivity" and all_answers:
        try:
            oa = all_answers.get("optimum", {})
            p = [num("x", oa), num("y", oa)]
            if feasible(m, p) and close(float(np.dot(m["c"], p)), ex["solution"]["z"]):
                for i, r in enumerate(m["rows"]):
                    checks[f"slack{i}"] = close(answers.get(f"slack{i}"), abs(np.dot(r["a"], p) - r["b"]), lang)
        except LearnError:
            pass
    count = sum(bool(v) for v in checks.values())
    points = round(step["points"] * count / max(1, len(checks)), 2)
    return {"step": sid, "points": points, "max": step["points"], "correct": count == len(checks), "checks": checks}


def hint_id(key):
    """Which hint text explains a question (www/learn.js: learn_hint_<id>)."""
    for pattern, hid in ((r"sense", "sense"), (r"vt\d", "vt"), (r"c\d", "c"), (r"(a\d+_\d|op\d+|b\d+)", "row"),
                         (r"ax\d+_\d", "line"), (r"side\d+", "side"), (r"p\d+", "point"), (r"boundary\d", "boundary"),
                         (r"cross[xy]", "cross"), (r"[xy]", "opt"), (r"z", "z"), (r"slack\d+", "slack"),
                         (r"shadow\d+", "shadow"), (r"range\d_\d", "range"), (r"idelta", "idelta"), (r"meaning", "meaning"),
                         (r"round", "round"), (r"enter\d+", "enter"), (r"leave\d+", "leave"), (r"pivot\d+", "pivot"),
                         (r"nextz\d+", "nextz")):
        if re.fullmatch(pattern, key):
            return hid
    return "general"


def hints_for(step, grade):
    """Hint ids for the questions that are still wrong or empty, in the order of the questions."""
    out = []
    for q in step["questions"]:
        if not grade["checks"].get(q["key"]):
            hid = hint_id(q["key"])
            if hid not in out:
                out.append(hid)
    return out


def public_steps(ex):
    """The steps without expected answers."""
    out = []
    for s in ex["steps"]:
        item = {"id": s["id"], "points": s["points"],
                "questions": [{k: v for k, v in q.items() if k != "expected"} for q in s["questions"]]}
        if "tableaus" in s:
            item["tableaus"] = s["tableaus"]
        out.append(item)
    return out
