"""Draws the graphs of the guide (shiny_files/www/guide/<lang>/*.png) from the example problem.

Run from the repository root with the app's Python:  python tools/guide_images.py
The screenshots of the app come from tools/guide_screenshots.py.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "shiny_files"))

from optisense import core  # noqa: E402
from optisense.config import EXAMPLE_NAMES  # noqa: E402
from optisense.i18n import LANGS  # noqa: E402
from optisense.pages.work import plotting  # noqa: E402

OUT = os.path.join(ROOT, "shiny_files", "www", "guide")
OBJECTIVE = {"name": "F", "c1": 10, "c2": 20, "sense": "max"}
CONTINUOUS = {"x1": "con", "x2": "con"}
INTEGER = {"x1": "int", "x2": "int"}


def constraints(lang):
    names = EXAMPLE_NAMES[lang]
    return [{"name": names[0], "a1": 6, "a2": 9, "op": "≤", "b": 720, "color_index": 0},
            {"name": names[1], "a1": 0, "a2": 1, "op": "≤", "b": 60, "color_index": 1}]


def small_ilp(lang):
    """A small ILP where rounding the LP solution (3.5 | 2.25) fails; its optimum (2 | 3) is not a corner."""
    names = EXAMPLE_NAMES[lang]
    objective = {"name": "F", "c1": 2, "c2": 3, "sense": "max"}
    cons = [{"name": names[0], "a1": 1, "a2": 2, "op": "≤", "b": 8, "color_index": 0},
            {"name": names[1], "a1": 3, "a2": 2, "op": "≤", "b": 15, "color_index": 1}]
    return objective, cons


def save(fig, lang, name):
    os.makedirs(os.path.join(OUT, lang), exist_ok=True)
    fig.savefig(os.path.join(OUT, lang, name), dpi=150, facecolor="white")
    plotting.plt.close(fig)


def main():
    for lang in LANGS:
        cons = constraints(lang)
        save(plotting.draw(OBJECTIVE, cons, CONTINUOUS, None, lang), lang, "model.png")
        save(plotting.draw(OBJECTIVE, cons, CONTINUOUS, core.solve(OBJECTIVE, cons, CONTINUOUS), lang), lang, "solved.png")
        objective, cons = small_ilp(lang)
        solution = core.solve(objective, cons, INTEGER)
        save(plotting.draw(objective, cons, INTEGER, solution, lang), lang, "integer.png")
    print("written to", OUT)


if __name__ == "__main__":
    main()
