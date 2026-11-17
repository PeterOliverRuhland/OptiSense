"""The guided task: a shawarma stand, every step explained and pre-calculated (story learn_shawarma_*, explanations
learn_tut_coach_* / learn_tut_calc_* in texts.py). The same numbers are the practice task “Shawarma” (tasks.py).

Since 2026-11-17 (Robin) a task the students do not know yet – before, it was the burger problem of the lecture, which
is now the practice task “Burger”. Just as hard as the burgers: three ≤ constraints with grams in kg, integer.

max F = 80·x1 + 100·x2 with x1 + x2 ≤ 300 (pita bread), 0.1·x1 + 0.2·x2 ≤ 40 (meat, kg),
0.1·x1 + 0.05·x2 ≤ 27 (vegetables, kg) → optimum (200 | 100), F = 26,000; vegetables have 2 kg left over.
Shawarmas are whole pieces, so x1 and x2 are integer. The optimal corner of the region is already whole, so the
graphical method of the lecture (objective line → corner → calculate it) still gives the integer optimum;
engine.make_exercise keeps the corner step for this task. ANSWERS are the answers of every step as a learner
types them (“Solution” fills in the same).
"""

from .engine import make_exercise
from .tasks import POOL

TASK = next(t for t in POOL[("medium", "ILP")] if t.get("story") == "shawarma")
MODEL = {"c": list(TASK["c"]), "sense": TASK["sense"], "kind": TASK["kind"],
         "rows": [{"a": [a1, a2], "op": op, "b": b} for a1, a2, op, b in TASK["rows"]]}
OPTIONS = {"mode": "practice", "form": "text", "difficulty": "easy", "kind": "ILP", "topic": "random"}
POINTS = [[0.0, 0.0], [250.0, 100.0], [100.0, 100.0], [50.0, 200.0]]   # feasible, not (pita bread), feasible, not (meat)

ANSWERS = {
    "objective": {"sense": "max", "vt0": "int", "vt1": "int", "c0": "80", "c1": "100"},
    "constraints": {"a0_0": "1", "a0_1": "1", "op0": "<=", "b0": "300",
                    "a1_0": "0.1", "a1_1": "0.2", "op1": "<=", "b1": "40",
                    "a2_0": "0.1", "a2_1": "0.05", "op2": "<=", "b2": "27"},
    "lines": {"ax0_0": "300", "ax0_1": "300", "ax1_0": "400", "ax1_1": "200", "ax2_0": "270", "ax2_1": "540"},
    "region": {"side0": "in", "side1": "in", "side2": "in", "p0": "yes", "p1": "no", "p2": "yes", "p3": "no"},
    "corner": {"boundary1": "0", "boundary2": "1"},   # pita bread and meat
    "optimum": {"x": "200", "y": "100", "z": "26000"},
    "slack": {"slack0": "0", "bind0": "yes", "slack1": "0", "bind1": "yes", "slack2": "2", "bind2": "no"},
    "interpret": {"meaning": "max", "round": "no"},
}


def create():
    return make_exercise(OPTIONS, MODEL, {"source": "tutorial"}, points=POINTS)
