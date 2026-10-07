"""Sensitivity analysis via the external solver lp_solve."""

import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

from .lp_format import _fmt_coef
from .model import _clean


def find_lp_solve():
    exe = os.environ.get("LP_SOLVE_BIN") or shutil.which("lp_solve")
    if exe:
        return exe
    # repository root: shiny_files/optisense/core/sensitivity.py -> four levels up
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    bin_dir = os.path.join(base, "lp_solve_5.5", "lp_solve", "bin")
    if sys.platform.startswith("linux"):
        return os.path.join(bin_dir, "linux", "lp_solve")
    if sys.platform == "darwin":
        return os.path.join(bin_dir, "mac", "lp_solve")
    if sys.platform.startswith("win"):
        return os.path.join(bin_dir, "windows64", "lp_solve.exe")
    return None


def _num(token):
    v = float(token)
    if v <= -1e29:
        return -math.inf
    if v >= 1e29:
        return math.inf
    return _clean(v)


def run_sensitivity(objective, constraints, var_types, timeout=30):
    """Run lp_solve -S4 and return shadow prices and objective-coefficient limits.

    Rows are named R1..Rn in the order of `constraints`.
    Raises FileNotFoundError / OSError if lp_solve cannot start, subprocess.TimeoutExpired on timeout.
    """
    exe = find_lp_solve()
    if not exe:
        raise FileNotFoundError("lp_solve")
    lines = [f"{objective['sense']}: {_fmt_coef(objective['c1'])} x1 + {_fmt_coef(objective['c2'])} x2;"]
    for i, con in enumerate(constraints, start=1):
        sym = {"≤": "<=", "≥": ">=", "=": "="}[con["op"]]
        lines.append(f"R{i}: {_fmt_coef(con['a1'])} x1 + {_fmt_coef(con['a2'])} x2 {sym} {_fmt_coef(con['b'])};")
    lines += ["x1 >= 0;", "x2 >= 0;"]
    ints = [v for v in ("x1", "x2") if var_types.get(v) == "int"]
    if ints:
        lines.append(f"int {','.join(ints)};")
    path = os.path.join(tempfile.gettempdir(), f"optisense_{uuid.uuid4().hex}.lp")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    try:
        out = subprocess.run([exe, "-S4", path], capture_output=True, text=True, timeout=timeout).stdout
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    return parse_sensitivity(out, len(constraints))


def parse_sensitivity(output, n_constraints):
    shadow = {}
    limits = {}
    section = None
    for raw in output.splitlines():
        line = raw.strip()
        if line.startswith("Objective function limits"):
            section = "limits"
            continue
        if line.startswith("Dual value"):
            section = "dual"
            continue
        if not line or line.startswith("From") or line.startswith("Dual values"):
            continue
        parts = line.split()
        if section == "limits" and parts[0] in ("x1", "x2") and len(parts) >= 4:
            limits[parts[0]] = {"from": _num(parts[1]), "till": _num(parts[2])}
        elif section == "dual" and len(parts) >= 4 and re.fullmatch(r"R\d+", parts[0]):
            idx = int(parts[0][1:]) - 1
            shadow[idx] = {"price": _num(parts[1]), "from": _num(parts[2]), "till": _num(parts[3])}
    if "Dual value" not in output:
        raise ValueError("unexpected lp_solve output")
    return {
        "shadow": [shadow.get(i) for i in range(n_constraints)],
        "limits": {v: limits.get(v) for v in ("x1", "x2")},
    }

