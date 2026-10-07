"""Reading and writing the LP file format of lp_solve."""

import re


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

