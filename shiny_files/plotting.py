"""Draws the graphical solution with matplotlib, using the OptiSense design-system colours."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.lines as mlines  # noqa: E402
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

import lp_core  # noqa: E402
from i18n import fmt_num, t  # noqa: E402

# Design-system tokens (see the OptiSense design system: plot-* and constraint-* colours)
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


def _base_axes(ax, xmax, ymax):
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK)
    ax.grid(True, ls="--", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.annotate("x1", (1, 0), xycoords="axes fraction", xytext=(0, -24), textcoords="offset points",
                ha="right", va="top", color=INK, fontsize=10, fontweight="bold")
    ax.annotate("x2", (0, 1), xycoords="axes fraction", xytext=(10, 0), textcoords="offset points",
                ha="left", va="top", color=INK, fontsize=10, fontweight="bold")
    ax.tick_params(colors=INK, labelsize=9)
    ax.plot(1, 0, ">", color=INK, transform=ax.get_yaxis_transform(), clip_on=False, ms=6)
    ax.plot(0, 1, "^", color=INK, transform=ax.get_xaxis_transform(), clip_on=False, ms=6)


def _label_line(ax, seg, text, color, xmax, ymax):
    """Write `text` next to the end of a line segment, kept inside the axes."""
    (xa, ya), (xb, yb) = seg
    # prefer the end that is further right; for vertical lines the upper end
    end = (xb, yb) if (xb, yb) >= (xa, ya) else (xa, ya)
    if abs(xa - xb) < 1e-9:
        end = (xa, max(ya, yb))
    x, y = end
    ha = "right" if x > 0.8 * xmax else "left"
    va = "bottom"
    x = min(max(x, 0.01 * xmax), 0.99 * xmax)
    y = min(max(y, 0.0), 0.97 * ymax)
    ax.annotate(text, (x, y), xytext=(-4 if ha == "right" else 4, 4), textcoords="offset points",
                ha=ha, va=va, color=color, fontsize=9, fontweight="bold",
                bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.75})


def draw(objective, constraints, var_types, solution, lang, figsize=None):
    """Return a matplotlib Figure.

    objective: dict or None; constraints: active constraints, each with "color_index";
    solution: result of lp_core.solve or None.
    """
    fig, ax = plt.subplots(figsize=figsize or (7, 6.2))
    fig.patch.set_facecolor("white")

    if objective is None or not constraints:
        _base_axes(ax, 10, 10)
        ax.text(5, 5, t(lang, "empty_graph").replace(" — ", "\n").replace(" – ", "\n"), ha="center", va="center", wrap=True, fontsize=11, color=INK,
                bbox={"boxstyle": "round,pad=0.6", "fc": "white", "ec": GRID})
        fig.set_layout_engine("tight", pad=1.2)
        return fig

    sol = solution if solution and solution.get("status") == "optimal" else None
    xmax, ymax = lp_core.plot_bounds(objective, constraints, sol)
    _base_axes(ax, xmax, ymax)
    handles = []

    # feasible region
    region = lp_core.feasible_region(constraints, var_types, xmax, ymax)
    if region["kind"] == "polygon" and region["points"]:
        pts = region["points"]
        area = 0.5 * abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts))))
        if area > 1e-9 * xmax * ymax:
            ax.add_patch(mpatches.Polygon(pts, closed=True, fc=FEASIBLE, alpha=0.3, ec="none", zorder=1))
        else:  # equality constraints leave a segment or a point
            xs, ys = zip(*pts)
            ax.plot(xs, ys, color=FEASIBLE, lw=6, alpha=0.6, solid_capstyle="round", zorder=1)
        handles.append(mpatches.Patch(color=FEASIBLE, alpha=0.4, label=t(lang, "plot_region")))
    elif region["kind"] == "points" and region["points"]:
        xs, ys = zip(*region["points"])
        size = 24 if len(xs) < 400 else (8 if len(xs) < 3000 else 3)
        ax.scatter(xs, ys, s=size, color=FEASIBLE, alpha=0.8, zorder=1, lw=0)
        handles.append(mlines.Line2D([], [], color=FEASIBLE, marker="o", ls="none", ms=5, label=t(lang, "plot_points")))
    elif region["kind"] == "vsegments" and region["segments"]:
        for x, lo, hi in region["segments"]:
            ax.plot([x, x], [lo, hi], color=FEASIBLE, lw=2.2, alpha=0.6, zorder=1, solid_capstyle="butt")
        handles.append(mlines.Line2D([], [], color=FEASIBLE, lw=2.2, alpha=0.6, label=t(lang, "plot_points")))
    elif region["kind"] == "hsegments" and region["segments"]:
        for y, lo, hi in region["segments"]:
            ax.plot([lo, hi], [y, y], color=FEASIBLE, lw=2.2, alpha=0.6, zorder=1, solid_capstyle="butt")
        handles.append(mlines.Line2D([], [], color=FEASIBLE, lw=2.2, alpha=0.6, label=t(lang, "plot_points")))

    # constraints
    for con in constraints:
        color, style = constraint_style(con["color_index"])
        seg = lp_core.line_in_box(con["a1"], con["a2"], con["b"], xmax, ymax)
        if seg:
            (xa, ya), (xb, yb) = seg
            ax.plot([xa, xb], [ya, yb], color=color, ls=style, lw=2.2, zorder=3)
            _label_line(ax, seg, con["name"], color, xmax, ymax)
        handles.append(mlines.Line2D([], [], color=color, ls=style, lw=2.2, label=con["name"]))

    # dummy objective line and, after solving, the optimized line
    a1, a2 = objective["c1"], objective["c2"]
    level = lp_core.dummy_level(objective, constraints, xmax, ymax)
    seg = lp_core.line_in_box(a1, a2, level, xmax, ymax)
    if seg:
        (xa, ya), (xb, yb) = seg
        ax.plot([xa, xb], [ya, yb], color=DUMMY, ls=(0, (6, 4)), lw=2.2, zorder=4)
        handles.append(mlines.Line2D([], [], color=DUMMY, ls=(0, (6, 4)), lw=2.2,
                                     label=t(lang, "plot_dummy", name=objective["name"])))

    if sol:
        x0, y0 = sol["x1"], sol["x2"]
        seg = lp_core.line_in_box(a1, a2, sol["value"], xmax, ymax)
        if seg:
            (xa, ya), (xb, yb) = seg
            ax.plot([xa, xb], [ya, yb], color=OPTIMIZED, ls=(0, (6, 4)), lw=2.2, zorder=4)
            handles.append(mlines.Line2D([], [], color=OPTIMIZED, ls=(0, (6, 4)), lw=2.2,
                                         label=t(lang, "plot_optimized", name=objective["name"])))
        foot = lp_core.perpendicular_foot(a1, a2, level, x0, y0)
        if foot and (abs(foot[0] - x0) + abs(foot[1] - y0)) > 1e-6 * (xmax + ymax):
            ax.annotate("", xy=(x0, y0), xytext=foot, zorder=5,
                        arrowprops={"arrowstyle": "-|>", "color": DUMMY, "lw": 1.8, "shrinkA": 0, "shrinkB": 7})
            mx, my = (foot[0] + x0) / 2, (foot[1] + y0) / 2
            ax.annotate(t(lang, "plot_shift"), (mx, my), xytext=(6, -10), textcoords="offset points",
                        color=DUMMY, fontsize=9, fontweight="bold")
        ax.plot([x0], [y0], "o", color=OPTIMUM, ms=9, zorder=6, mec="white", mew=1.5)
        label = f"{t(lang, 'plot_optimum')} ({fmt_num(x0, lang)} | {fmt_num(y0, lang)})"
        ha = "right" if x0 > 0.6 * xmax else "left"
        ax.annotate(label, (x0, y0), xytext=(-10 if ha == "right" else 10, 10), textcoords="offset points",
                    ha=ha, color=OPTIMUM, fontsize=10, fontweight="bold", zorder=7,
                    bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none", "alpha": 0.85})
        handles.insert(0, mlines.Line2D([], [], color=OPTIMUM, marker="o", ls="none", ms=8,
                                        label=f"{t(lang, 'plot_optimum')}: {objective['name']} = {fmt_num(sol['value'], lang)}"))

    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2 if len(handles) > 2 else len(handles), fontsize=9,
              frameon=False, handlelength=2.4)
    fig.set_layout_engine("tight", pad=1.2)
    return fig
