"""Problem model helpers: problem type, integrality, constraint activity."""

EPS = 1e-9
OPERATORS = ("≤", "≥", "=")


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

