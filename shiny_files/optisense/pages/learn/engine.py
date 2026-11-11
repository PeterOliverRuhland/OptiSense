"""Exercises with two variables: model check, generation, reference solution and grading.

No Shiny code and no texts. Questions are identified by keys (c0, a1_0, line0_1_0 …); the browser
(www/learn.js) labels them in the chosen language, story.py and solution.py write the texts that
depend on the numbers. Expected answers never leave the server.

Every generated task is solved with SciPy before it is used. After the optimum the learner determines the
slack of every constraint and whether it is binding – the interpretation used in the lecture.
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
WEIGHTS = {"objective": 10, "constraints": 15, "lines": 15, "region": 10, "corner": 15, "optimum": 25,
           "slack": 15, "interpret": 5}
# generated tasks: continuous, integer or mixed (MILP: x1 or x2 integer, chosen at random)
OPTIONS = {"mode": ("practice", "exam"), "form": ("text", "math"), "difficulty": ("easy", "medium"), "kind": ("LP", "ILP", "MILP")}
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


def meet(r, s):
    """Where the boundaries of two rows meet, or None if they are parallel."""
    B = np.array([r["a"], s["a"]], dtype=float)
    if abs(np.linalg.det(B)) < EPS:
        return None
    return np.linalg.solve(B, [r["b"], s["b"]])


def corners(m):
    """The corners of the continuous feasible region as (i, j, point): the first two boundaries that meet there."""
    rows, out = boundaries(m), []
    for i, j in itertools.combinations(range(len(rows)), 2):
        x = meet(rows[i], rows[j])
        if x is not None and feasible(m, x, False) and not any(np.linalg.norm(x - y) < EPS for _, _, y in out):
            out.append((i, j, x))
    return out


def vertices(m):
    return [x for _, _, x in corners(m)]


def optimal_corners(m):
    """The corners with the best objective value (several if a side of the region is parallel to the objective line)."""
    cs = corners(m)
    if not cs:
        return []
    sign = 1 if m["sense"] == "max" else -1
    best = max(sign * float(np.dot(m["c"], x)) for _, _, x in cs)
    return [c for c in cs if sign * float(np.dot(m["c"], c[2])) >= best - 1e-9 * max(1, abs(best))]


def chosen_corner(m, b1, b2):
    """The point where the two boundaries chosen by the learner meet (indices as sent by the browser), or None."""
    try:
        i, j = int(b1), int(b2)
    except (TypeError, ValueError):
        return None
    rows = boundaries(m)
    if i == j or not (0 <= i < len(rows) and 0 <= j < len(rows)):
        return None
    return meet(rows[i], rows[j])


def slack(r, x):
    """What is left over of a constraint at the point x (the surplus for ≥)."""
    return abs(float(np.dot(r["a"], x)) - r["b"])


def binding(r, x):
    return slack(r, x) < 1e-6 * max(1, abs(r["b"]))


# ---------------------------------------------------------------------------------------------- generator
def generate(options):
    rng = random.Random(options.get("seed"))
    difficulty = options["difficulty"]
    kind = rng.choice(("MILP1", "MILP2")) if options["kind"] == "MILP" else options["kind"]
    topic = options.get("topic") if options.get("topic") in TOPICS else rng.choice(TOPICS)
    for _ in range(150):
        a, b, d, e = rng.randint(1, 3), rng.randint(3, 6), rng.randint(3, 6), rng.randint(1, 3)
        if a * e == b * d:
            continue
        target = [rng.randint(3, 9) + rng.choice([0, 0.5]), rng.randint(3, 9) + rng.choice([0, 0.5])]
        c = [rng.randint(3, 12), rng.randint(3, 12)]
        sense = "min" if difficulty == "medium" and topic in MIN_TOPICS and rng.random() < 0.45 else "max"
        op = ">=" if sense == "min" else "<="
        rows = [{"a": [a, b], "b": a * target[0] + b * target[1], "op": op, "role": "r1"},
                {"a": [d, e], "b": d * target[0] + e * target[1], "op": op, "role": "r2"}]
        if difficulty == "medium":
            rows.append({"a": [1, 1], "b": math.ceil(sum(target)) + rng.randint(3, 8), "op": "<=", "role": "total"})
        m = validate({"c": c, "rows": rows, "sense": sense, "kind": kind})
        sol = solve(m)
        if sol["status"] != "optimal" or min(sol["x"]) <= EPS:
            continue
        # with integer variables the integrality has to matter: the LP optimum itself must not be allowed
        if kind != "LP" and feasible(m, solve({**m, "kind": "LP"})["x"]):
            continue
        return m, {"source": "generated", "topic": topic}, sol
    raise LearnError("err_generate")


# ---------------------------------------------------------------------------------------------- exercise
def normalize_options(raw):
    """The learner's choices from the start page, reduced to known values."""
    raw = raw if isinstance(raw, dict) else {}
    opts = {k: raw.get(k) if raw.get(k) in allowed else allowed[0] for k, allowed in OPTIONS.items()}
    opts["topic"] = raw.get("topic") if raw.get("topic") in TOPICS else "random"
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
    # only corners like (6,5 | 0): a rounded one such as (0 | 9,6667) lies just outside the region it is a corner of
    corners = [v for v in vs if np.linalg.norm(v - np.array(sol["x"])) > 1e-6 and np.linalg.norm(v) > 1e-6
               and all(abs(c * 2 - round(c * 2)) < 1e-9 for c in v)]
    if corners:
        pts.append([round(float(c) * 2) / 2 for c in corners[0]])
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


def make_exercise(options, custom=None, info=None, points=None):
    """options: mode, form, difficulty, kind (LP/ILP/MILP1/MILP2), topic, seed.
    custom: a model to use instead of a generated one; info describes where the exercise comes from."""
    options = dict(options)
    if custom is not None:
        m = validate(custom)
        sol = solve(m)
        info = info or {"source": "own"}
        if info["source"] != "tutorial":
            options["form"] = "math"
    else:
        m, info, sol = generate(options)
    if sol["status"] != "optimal":
        raise LearnError({"infeasible": "err_infeasible", "unbounded": "err_unbounded"}.get(sol["status"], "err_solver"))
    options["kind"] = m["kind"]
    ext = axis_extent(m, sol)
    ints = integrality(m)
    steps = []

    def add(sid, qs):
        steps.append({"id": sid, "questions": qs})

    if options.get("form") == "text":
        # the model in two steps, each with its own check and hints: objective and value range, then the constraints
        add("objective", [question("sense", m["sense"], ("max", "min")),
                          question("vt0", "int" if ints[0] else "con", ("con", "int")),
                          question("vt1", "int" if ints[1] else "con", ("con", "int")),
                          question("c0", m["c"][0]), question("c1", m["c"][1])])
        qs = []
        for i, r in enumerate(m["rows"]):
            qs += [question(f"a{i}_0", r["a"][0]), question(f"a{i}_1", r["a"][1]),
                   question(f"op{i}", r["op"], OPS), question(f"b{i}", r["b"])]
        add("constraints", qs)
    test_points = [side_test_point(r, ext) for r in m["rows"]]
    region_points = points or check_points(m, ext, sol)
    add("lines", [question(f"ax{i}_{j}", axis_cut(r, j)) for i, r in enumerate(m["rows"]) for j in range(2)])
    qs = [question(f"side{i}", side_answer(r, p), ("in", "out", "line")) for i, (r, p) in enumerate(zip(m["rows"], test_points))]
    qs += [question(f"p{n}", "yes" if feasible(m, p) else "no", ("yes", "no")) for n, p in enumerate(region_points)]
    add("region", qs)
    if m["kind"] == "LP":
        # first find the optimal corner with the objective line, then calculate it; integer optima lie on lattice points
        idx = [str(i) for i in range(len(boundaries(m)))]
        add("corner", [question("boundary1", None, idx), question("boundary2", None, idx)])
    add("optimum", [question("x", sol["x"][0]), question("y", sol["x"][1]), question("z", sol["z"])])
    # what is left over at the optimum, and which constraints are used up (binding)
    qs = []
    for i, r in enumerate(m["rows"]):
        qs += [question(f"slack{i}", slack(r, sol["x"])), question(f"bind{i}", "yes" if binding(r, sol["x"]) else "no", ("yes", "no"))]
    add("slack", qs)
    add("interpret", [question("meaning", m["sense"], ("max", "min")), question("round", "no", ("yes", "no"))])
    total = sum(WEIGHTS[s["id"]] for s in steps)
    for s in steps:
        s["points"] = round(WEIGHTS[s["id"]] / total * 100)
    steps[-1]["points"] = 100 - sum(s["points"] for s in steps[:-1])
    return {"model": m, "solution": sol, "options": options, "info": info, "steps": steps,
            "extent": ext, "points": region_points, "test_points": test_points}


def step_by_id(ex, sid):
    return next((s for s in ex["steps"] if s["id"] == sid), None)


def unfilled_before(ex, step, answers):
    """Ids of the steps before `step` that still have an empty field. “Solution” is only given once they are
    filled in: the region cannot be solved without a model. Whether the entries are right does not matter."""
    out = []
    for s in ex["steps"]:
        if s["id"] == step["id"]:
            break
        mine = (answers or {}).get(s["id"], {})
        if any(str(mine.get(q["key"], "")).strip() == "" for q in s["questions"]):
            out.append(s["id"])
    return out


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
    if sid == "constraints":
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
    elif sid == "corner":
        # two lines that meet at an optimal corner (with several optimal corners, each counts)
        p = chosen_corner(m, answers.get("boundary1"), answers.get("boundary2"))
        ok = p is not None and feasible(m, p, False) and close(float(np.dot(m["c"], p)), ex["solution"]["z"])
        checks["boundary1"] = checks["boundary2"] = bool(ok)
    elif sid == "optimum":
        try:
            p = [num("x"), num("y")]
            ok = feasible(m, p) and close(float(np.dot(m["c"], p)), ex["solution"]["z"])
        except LearnError:
            ok = False
        checks["x"] = checks["y"] = bool(ok)   # any optimal point counts (alternative optima)
    elif sid == "slack" and all_answers:
        # at the learner's optimum, if it is one (with several optimal points each counts)
        try:
            oa = all_answers.get("optimum", {})
            p = [num("x", oa), num("y", oa)]
            if feasible(m, p) and close(float(np.dot(m["c"], p)), ex["solution"]["z"]):
                for i, r in enumerate(m["rows"]):
                    checks[f"slack{i}"] = close(answers.get(f"slack{i}"), slack(r, p), lang)
                    checks[f"bind{i}"] = answers.get(f"bind{i}") == ("yes" if binding(r, p) else "no")
        except LearnError:
            pass
    count = sum(bool(v) for v in checks.values())
    points = round(step["points"] * count / max(1, len(checks)), 2)
    return {"step": sid, "points": points, "max": step["points"], "correct": count == len(checks), "checks": checks}


def solution_values(ex, step, all_answers=None, lang="en"):
    """The answers of a step as the learner would enter them – “Solution” fills them into the fields.
    Where grading accepts several answers, the values follow the learner (the optimum at their optimal corner,
    slack at their optimal point)."""
    m, sol = ex["model"], ex["solution"]
    sid = step["id"]
    out = {q["key"]: q["expected"] for q in step["questions"]}
    if sid == "lines":
        out = {k: "–" if v is None else v for k, v in out.items()}
    elif sid == "corner":
        best = optimal_corners(m)
        out = {"boundary1": str(best[0][0]), "boundary2": str(best[0][1])} if best else {}
    elif sid == "optimum" and step_by_id(ex, "corner"):
        ca = (all_answers or {}).get("corner", {})
        p = chosen_corner(m, ca.get("boundary1"), ca.get("boundary2"))
        if p is not None and feasible(m, p, False) and close(float(np.dot(m["c"], p)), sol["z"]):
            out.update(x=float(p[0]), y=float(p[1]))
    elif sid == "slack":
        x = sol["x"]
        try:
            oa = (all_answers or {}).get("optimum", {})
            p = [number(oa.get("x", ""), lang), number(oa.get("y", ""), lang)]
            if feasible(m, p) and close(float(np.dot(m["c"], p)), sol["z"]):
                x = p
        except LearnError:
            pass
        for i, r in enumerate(m["rows"]):
            out[f"slack{i}"] = slack(r, x)
            out[f"bind{i}"] = "yes" if binding(r, x) else "no"
    return {k: v for k, v in out.items() if v is not None}


def hint_id(key):
    """Which hint text explains a question (www/learn.js: learn_hint_<id>)."""
    for pattern, hid in ((r"sense", "sense"), (r"vt\d", "vt"), (r"c\d", "c"), (r"(a\d+_\d|op\d+|b\d+)", "row"),
                         (r"ax\d+_\d", "line"), (r"side\d+", "side"), (r"p\d+", "point"), (r"boundary\d", "boundary"),
                         (r"[xy]", "opt"), (r"z", "z"), (r"slack\d+", "slack"),
                         (r"bind\d+", "bind"), (r"meaning", "meaning"),
                         (r"round", "round")):
        if re.fullmatch(pattern, key):
            return hid
    return "general"


def hints_for(ex, step, grade):
    """Hint ids for the questions that are still wrong or empty, in the order of the questions."""
    out = []
    for q in step["questions"]:
        if not grade["checks"].get(q["key"]):
            hid = hint_id(q["key"])
            if hid == "opt" and step_by_id(ex, "corner"):
                hid = "opt_corner"   # the optimum of an LP is calculated from the corner found before
            if hid not in out:
                out.append(hid)
    return out


def public_steps(ex):
    """The steps without expected answers."""
    return [{"id": s["id"], "points": s["points"],
             "questions": [{k: v for k, v in q.items() if k != "expected"} for q in s["questions"]]} for s in ex["steps"]]
