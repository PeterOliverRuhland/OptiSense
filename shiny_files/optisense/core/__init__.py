"""Core logic of OptiSense (no Shiny code): model, solver, geometry, LP files, sensitivity analysis."""

from .geometry import (dummy_level, feasible_polygon, feasible_region, intercepts, is_feasible, line_in_box,
                       perpendicular_foot, plot_bounds)
from .lp_format import LPParseError, parse_lp_file, to_lp_file
from .model import EPS, OPERATORS, constraint_activity, integrality, problem_type
from .sensitivity import find_lp_solve, parse_sensitivity, run_sensitivity
from .solver import solve

__all__ = [
    "EPS", "OPERATORS", "LPParseError", "constraint_activity", "dummy_level", "feasible_polygon", "feasible_region",
    "find_lp_solve", "integrality", "intercepts", "is_feasible", "line_in_box", "parse_lp_file", "parse_sensitivity",
    "perpendicular_foot", "plot_bounds", "problem_type", "run_sensitivity", "solve", "to_lp_file",
]
