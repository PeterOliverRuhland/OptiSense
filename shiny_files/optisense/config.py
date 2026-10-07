"""App-wide settings: limits, example problem names and design-system colours."""

# Default names for new functions, per language
DEFAULT_NAMES = {
    "objective": {"en": "F", "de": "F", "fil": "F"},
    "constraint": {"en": "C{n}", "de": "NB{n}", "fil": "C{n}"},
}

# Constraint names of the textbook example, per language
EXAMPLE_NAMES = {"en": ["C1", "C2"], "de": ["NB1", "NB2"], "fil": ["C1", "C2"]}

MAX_OBJECTIVES = 2
MAX_CONSTRAINTS = 5

# Design-system tokens used by the graph (see the OptiSense design system: plot-* and constraint-* colours)
INK = "#1d1f21"
GRID = "#dee2e6"
FEASIBLE = "#808080"
DUMMY = "#1f7a1f"
OPTIMIZED = "#0000ff"
OPTIMUM = "#cc0000"
CONSTRAINT_COLORS = ["#00798c", "#7b3fa0", "#b35900", "#a8326e", "#8c4a2f"]
