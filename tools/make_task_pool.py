"""Builds the fixed pool of practice tasks: shiny_files/optisense/pages/learn/tasks.py.

The app does not make up numbers while it runs: "Create task" picks one of 15 fixed tasks for the chosen level and
variable type (6 × 15 = 90). This script found them once – from random candidates it keeps only good ones:
  - calculator-free: every value the learner works out is whole or ends in ,5 (axis intercepts, x1, x2, F, slack)
  - exactly one optimal point (no objective parallel to a side of the region, no ties between lattice points)
  - every constraint bounds the region (none is redundant)
  - with integer variables the LP optimum is not allowed (integrality has to matter)
  - small numbers (axis intercepts up to 40) and coefficient pairs that differ from task to task
Level 2 mixes maximisation and minimisation; mixed tasks have x1 or x2 integer.

Run from the repository root:  python tools/make_task_pool.py   (then run the tests and review the tasks)
Running it again replaces tasks.py – only do that on purpose, the pool is meant to stay fixed.
"""

import itertools
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "shiny_files"))

from optisense.pages.learn import engine  # noqa: E402

OUT = os.path.join(ROOT, "shiny_files", "optisense", "pages", "learn", "tasks.py")
PER_COMBINATION = 15
MIN_SHARE = 6            # level 2: this many of the 15 are minimisation tasks
MAX_CUT = 40


def candidate(rng, difficulty, kind):
    """One random task in the style of the lecture: two resources that meet at a nice point, level 2 a total."""
    a, b, d, e = rng.randint(1, 3), rng.randint(3, 6), rng.randint(3, 6), rng.randint(1, 3)
    if a * e == b * d:
        return None
    target = [rng.randint(3, 9) + rng.choice([0, 0.5]), rng.randint(3, 9) + rng.choice([0, 0.5])]
    c = [rng.randint(3, 12), rng.randint(3, 12)]
    sense = "min" if difficulty == "medium" and rng.random() < 0.45 else "max"
    op = ">=" if sense == "min" else "<="
    rows = [{"a": [a, b], "b": a * target[0] + b * target[1], "op": op, "role": "r1"},
            {"a": [d, e], "b": d * target[0] + e * target[1], "op": op, "role": "r2"}]
    if difficulty == "medium":
        # the total has to cut the region: for max below the meeting point of the two resources, for min anywhere above
        total = math.ceil(sum(target)) + (rng.randint(1, 8) if sense == "min" else rng.randint(-4, -1))
        rows.append({"a": [1, 1], "b": total, "op": "<=", "role": "total"})
    cuts = [engine.axis_cut(r, j) for r in rows for j in range(2)]
    if not engine.half_steps(*cuts) or max(cuts) > MAX_CUT:
        return None
    if kind == "MILP":
        kind = rng.choice(("MILP1", "MILP2"))
    return engine.validate({"c": c, "rows": rows, "sense": sense, "kind": kind})


def unique_optimum(m, sol):
    sign = 1 if m["sense"] == "max" else -1
    ints = engine.integrality(m)
    if not any(ints):
        return len(engine.optimal_corners(m)) == 1
    top = int(max(engine.axis_cut(r, j) or 0 for r in m["rows"] for j in range(2))) + 2
    if all(ints):
        best = [p for p in itertools.product(range(top), repeat=2) if engine.feasible(m, p)]
        zs = [sign * (m["c"][0] * p[0] + m["c"][1] * p[1]) for p in best]
        return sum(abs(z - max(zs)) < 1e-9 for z in zs) == 1
    # mixed: for every value of the integer variable the best value of the continuous one; no two may tie
    k_var = ints.index(1)
    y_var = 1 - k_var
    zs = []
    for k in range(top):
        lo, hi = 0.0, math.inf
        for r in m["rows"]:
            rest, coef = r["b"] - r["a"][k_var] * k, r["a"][y_var]
            if coef == 0:
                if not engine.satisfies(r, [k, 0] if k_var == 0 else [0, k]):
                    lo, hi = 1, 0
                continue
            bound = rest / coef
            if r["op"] in ("<=", "=") and coef > 0 or r["op"] == ">=" and coef < 0:
                hi = min(hi, bound)
            if r["op"] in (">=", "=") and coef > 0 or r["op"] == "<=" and coef < 0:
                lo = max(lo, bound)
        if lo > hi + 1e-9:
            continue
        y = hi if (sign * m["c"][y_var] > 0) else lo
        if math.isfinite(y):
            zs.append(sign * (m["c"][k_var] * k + m["c"][y_var] * y))
    return bool(zs) and sum(abs(z - max(zs)) < 1e-9 for z in zs) == 1


def good(m):
    sol = engine.solve(m)
    if sol["status"] != "optimal" or min(sol["x"]) <= engine.EPS or not engine.calculator_free(m, sol):
        return False
    if m["kind"] != "LP" and engine.feasible(m, engine.solve({**m, "kind": "LP"})["x"]):
        return False
    used = {i for i, j, _ in engine.corners(m)} | {j for i, j, _ in engine.corners(m)}
    if not all(i in used for i in range(len(m["rows"]))):
        return False
    return unique_optimum(m, sol)


def pick(difficulty, kind):
    rng = random.Random(f"{difficulty}-{kind}")
    chosen, pairs, costs = [], set(), set()
    want_min = MIN_SHARE if difficulty == "medium" else 0
    for _ in range(400000):
        m = candidate(rng, difficulty, kind)
        if m is None:
            continue
        pair = tuple(tuple(r["a"]) for r in m["rows"][:2])
        n_min = sum(t["sense"] == "min" for t in chosen)
        if pair in pairs or tuple(m["c"]) in costs:
            continue
        if m["sense"] == "min" and n_min >= want_min or m["sense"] == "max" and len(chosen) - n_min >= PER_COMBINATION - want_min:
            continue
        if kind == "MILP" and sum(t["kind"] == m["kind"] for t in chosen) >= (PER_COMBINATION + 1) // 2:
            continue
        if not good(m):
            continue
        chosen.append(m)
        pairs.add(pair)
        costs.add(tuple(m["c"]))
        if len(chosen) == PER_COMBINATION:
            return chosen
    raise SystemExit(f"only {len(chosen)} good tasks for {difficulty}/{kind}")


def num(v):
    return str(int(v)) if float(v).is_integer() else str(v)


def main():
    lines = ['"""The fixed practice tasks: 15 per level and variable type, picked at random when a task is created.',
             "",
             "Made by tools/make_task_pool.py (see there for what makes a task good) and checked in tests/test_learning.py.",
             "Every value the learner works out is whole or ends in ,5. A row is (a1, a2, op, b): a1·x1 + a2·x2 op b;",
             "the rows are the two resources and, on level 2, the total x1 + x2 ≤ b. The topic (kitchen, workshop …) only",
             'tells the story around the numbers and is chosen separately. Ids stay fixed: they name a task in the logs."""',
             "",
             "POOL = {"]
    for difficulty, kind in itertools.product(("easy", "medium"), ("LP", "ILP", "MILP")):
        tasks = pick(difficulty, kind)
        lines.append(f'    ("{difficulty}", "{kind}"): [')
        for n, m in enumerate(sorted(tasks, key=lambda t: (t["sense"] != "max", t["kind"])), start=1):
            rows = ", ".join(f'({num(r["a"][0])}, {num(r["a"][1])}, "{r["op"]}", {num(r["b"])})' for r in m["rows"])
            tid = f'{kind}-{1 if difficulty == "easy" else 2}-{n:02d}'
            lines.append(f'        {{"id": "{tid}", "sense": "{m["sense"]}", "kind": "{m["kind"]}", '
                         f'"c": ({num(m["c"][0])}, {num(m["c"][1])}), "rows": [{rows}]}},')
        lines.append("    ],")
        print(f"{difficulty:6} {kind:4}: {len(tasks)} Aufgaben", flush=True)
    lines.append("}")
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("geschrieben:", OUT)


if __name__ == "__main__":
    main()
