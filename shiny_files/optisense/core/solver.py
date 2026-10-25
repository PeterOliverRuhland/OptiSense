"""Solving with scipy.optimize.milp."""

import numpy as np
from scipy.optimize import LinearConstraint, milp

from .model import _clean, integrality


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
        res = milp(c, options={"time_limit": 5}, **kwargs)   # never block the shared server for long
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

