"""Draws the graphs of the guide (shiny_files/www/guide/<lang>/*.png) from the example problem.

Run from the repository root with the app's Python:  python tools/guide_images.py
The screenshots of the app come from tools/guide_screenshots.py.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "shiny_files"))

from optisense import core  # noqa: E402
from optisense.config import DEFAULT_NAMES  # noqa: E402
from optisense.i18n import LANGS  # noqa: E402
from optisense.pages.work import example as burger, plotting  # noqa: E402

OUT = os.path.join(ROOT, "shiny_files", "www", "guide")
INTEGER = {"x1": "int", "x2": "int"}


def example(lang):
    """The burger example as “Example” in step 1 loads it (pages/work/example.py)."""
    objective, cons, var_types = burger.problem(lang)
    return objective, [dict(con, color_index=i) for i, con in enumerate(cons)], var_types


def small_ilp(lang):
    """A small ILP where rounding the LP solution (3.5 | 2.25) fails; its optimum (2 | 3) is not a corner."""
    names = [DEFAULT_NAMES["constraint"][lang].format(n=n) for n in (1, 2)]
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
        objective, cons, var_types = example(lang)
        save(plotting.draw(objective, cons, var_types, None, lang), lang, "model.png")
        save(plotting.draw(objective, cons, var_types, core.solve(objective, cons, var_types), lang), lang, "solved.png")
        objective, cons = small_ilp(lang)
        solution = core.solve(objective, cons, INTEGER)
        save(plotting.draw(objective, cons, INTEGER, solution, lang), lang, "integer.png")
    print("written to", OUT)


if __name__ == "__main__":
    main()
