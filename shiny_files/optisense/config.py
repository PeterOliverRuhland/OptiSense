"""App-wide settings: limits, example problem names and design-system colours (used by several pages)."""

# Default names for new functions, per language
DEFAULT_NAMES = {
    "objective": {"en": "F", "de": "F"},
    "constraint": {"en": "C{n}", "de": "NB{n}"},
}

# Constraint names of the textbook example, per language
EXAMPLE_NAMES = {"en": ["C1", "C2"], "de": ["NB1", "NB2"]}

MAX_OBJECTIVES = 2
MAX_CONSTRAINTS = 5
# limits for values sent by the browser or read from a file (the server is shared by all users)
MAX_VALUE = 1e9
MAX_NAME_LENGTH = 40
MAX_IMPORT_BYTES = 20_000

# Design-system tokens used by the graph (see the OptiSense design system: plot-* and constraint-* colours)
INK = "#1d1f21"
GRID = "#dee2e6"
FEASIBLE = "#808080"
DUMMY = "#1f7a1f"
OPTIMIZED = "#0000ff"
OPTIMUM = "#cc0000"
CONSTRAINT_COLORS = ["#00798c", "#7b3fa0", "#b35900", "#a8326e", "#8c4a2f"]


def constraint_style(color_index):
    """Colour and line style for the n-th constraint colour slot (5 colours, then dash-dot)."""
    return CONSTRAINT_COLORS[color_index % len(CONSTRAINT_COLORS)], ("-" if color_index < len(CONSTRAINT_COLORS) else "-.")


def constraint_color(color_index):
    return constraint_style(color_index)[0]
