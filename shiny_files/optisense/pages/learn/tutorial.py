"""The guided example: the burger problem from the lecture, every step explained and pre-calculated.

max F = 4.5·x1 + 6·x2 with x1 + x2 ≤ 500 (buns), 0.1·x1 + 0.3·x2 ≤ 105 (meat, kg),
0.1·x1 + 0.15·x2 ≤ 60 (vegetables, kg) → optimum (300 | 200), F = 2,550. Solved as an LP, like in
the lecture; the simplex tableaus are the same as on its slides.
The example answers are sent to the browser so “Fill in the example values” can show them.
"""

from .engine import make_exercise

MODEL = {"c": [4.5, 6], "sense": "max", "kind": "LP",
         "rows": [{"a": [1, 1], "op": "<=", "b": 500}, {"a": [0.1, 0.3], "op": "<=", "b": 105},
                  {"a": [0.1, 0.15], "op": "<=", "b": 60}]}
OPTIONS = {"mode": "practice", "form": "text", "method": "both", "difficulty": "easy", "kind": "LP", "topic": "random",
           "sensitivity": True, "simplex": True}
POINTS = [[0.0, 0.0], [400.0, 200.0], [200.0, 200.0], [100.0, 350.0]]   # feasible, not (buns), feasible, not (meat)

ANSWERS = {
    "model": {"sense": "max", "vt0": "con", "vt1": "con", "c0": "4.5", "c1": "6",
              "a0_0": "1", "a0_1": "1", "op0": "<=", "b0": "500",
              "a1_0": "0.1", "a1_1": "0.3", "op1": "<=", "b1": "105",
              "a2_0": "0.1", "a2_1": "0.15", "op2": "<=", "b2": "60"},
    "lines": {"ax0_0": "500", "ax0_1": "500", "ax1_0": "1050", "ax1_1": "350", "ax2_0": "600", "ax2_1": "400"},
    "region": {"side0": "in", "side1": "in", "side2": "in", "p0": "yes", "p1": "no", "p2": "yes", "p3": "no"},
    "intersection": {"boundary1": "0", "boundary2": "2", "crossx": "300", "crossy": "200"},
    "optimum": {"x": "300", "y": "200", "z": "2550"},
    "sensitivity": {"slack0": "0", "slack1": "15", "slack2": "0", "shadow0": "1.5", "shadow1": "0", "shadow2": "30",
                    "range0_0": "4", "range0_1": "6", "range1_0": "4.5", "range1_1": "6.75"},
    "interpret": {"meaning": "max", "round": "no"},
}


def _text(value):
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else f"{round(value, 4):g}"
    return str(value)


def create():
    ex = make_exercise(OPTIONS, MODEL, {"source": "tutorial"}, points=POINTS)
    answers = {k: dict(v) for k, v in ANSWERS.items()}
    simplex = next((s for s in ex["steps"] if s["id"] == "simplex"), None)
    if simplex:
        answers["simplex"] = {q["key"]: _text(q["expected"]) for q in simplex["questions"]}
    ex["tutorial"] = {"answers": answers}
    return ex
