"""Python code that checks an exercise with scipy.optimize.milp, written like the code on the lecture slides."""

from .engine import integrality


def _lit(value):
    v = float(value)
    return str(int(v)) if v.is_integer() else repr(round(v, 10))


def _array(values):
    return "np.array([" + ", ".join(_lit(v) for v in values) + "])"


def python_code(ex):
    m = ex["model"]
    rows = m["rows"]
    n = len(rows)
    maximize = m["sense"] == "max"
    sign = -1 if maximize else 1   # milp minimises, so a maximisation uses negative coefficients
    pad = " " * len("coeff  = np.array([")
    coeff = (",\n" + pad).join("[" + ", ".join(_lit(a) for a in r["a"]) + "]" for r in rows)
    ops = {r["op"] for r in rows}
    if ops == {"<="}:
        lb, ub = f"np.repeat(-np.inf, {n})", _array(r["b"] for r in rows)
    elif ops == {">="}:
        lb, ub = _array(r["b"] for r in rows), f"np.repeat(np.inf, {n})"
    else:
        lb = "np.array([" + ", ".join("-np.inf" if r["op"] == "<=" else _lit(r["b"]) for r in rows) + "])"
        ub = "np.array([" + ", ".join("np.inf" if r["op"] == ">=" else _lit(r["b"]) for r in rows) + "])"
    ints = integrality(m)
    call = "result = milp(obj,\n              constraints = cnstr"
    if any(ints):
        call += f",\n              integrality = [{ints[0]}, {ints[1]}]"
    call += ")"
    return "\n".join([
        "# Importing numpy as np",
        "import numpy as np",
        "# Importing function milp and class LinearConstraint",
        "# from scipy.optimize",
        "from scipy.optimize import milp, LinearConstraint",
        "",
        f"# OptiSense exercise ({m['kind'].rstrip('12')}, {m['sense']}.)",
        "",
        f"obj    = {_array(sign * c for c in m['c'])}",
        f"coeff  = np.array([{coeff}])",
        f"ub     = {ub}",
        f"lb     = {lb}",
        "cnstr  = LinearConstraint(coeff, lb, ub)",
        "",
        call,
        "",
        "print(result.message)",
        "print(-result.fun)" if maximize else "print(result.fun)",
        "print(result.x)",
    ])
