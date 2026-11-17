"""“Model & solution”: draws the graphical solution with matplotlib, using the OptiSense design-system colours."""

import gc
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.lines as mlines  # noqa: E402
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.transforms import ScaledTranslation  # noqa: E402

from optisense import core  # noqa: E402
from optisense.config import DUMMY, FEASIBLE, GRID, INK, OPTIMIZED, OPTIMUM, constraint_style  # noqa: E402
from optisense.i18n import fmt_num, t  # noqa: E402


def _base_axes(ax, xmax, ymax, k=1.0, compact=False):
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK)
    ax.grid(True, ls="--", color=GRID, lw=0.8 * k)
    ax.set_axisbelow(True)
    ax.annotate("x1", (1, 0), xycoords="axes fraction", xytext=(0, -24), textcoords="offset points",
                ha="right", va="top", color=INK, fontsize=10 * k, fontweight="bold")
    ax.annotate("x2", (0, 1), xycoords="axes fraction", xytext=(10, 0), textcoords="offset points",
                ha="left", va="top", color=INK, fontsize=10 * k, fontweight="bold",
                # on a phone the region fills the axes and lines run through the corner: keep “x2” readable
                bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.85} if compact else None,
                zorder=8 if compact else 3)
    ax.tick_params(colors=INK, labelsize=9 * k)
    ax.plot(1, 0, ">", color=INK, transform=ax.get_yaxis_transform(), clip_on=False, ms=6 * k)
    ax.plot(0, 1, "^", color=INK, transform=ax.get_xaxis_transform(), clip_on=False, ms=6 * k)


def _label_at(ax, end, text, color, xmax, ymax, k):
    x, y = end
    ha = "right" if x > 0.8 * xmax else "left"
    va = "top" if y > 0.9 * ymax else "bottom"   # near the top edge below the line, so it stays inside the axes
    x = min(max(x, 0.01 * xmax), 0.99 * xmax)
    y = min(max(y, 0.0), ymax)
    return ax.annotate(text, (x, y), xytext=(-4 if ha == "right" else 4, -4 if va == "top" else 4), textcoords="offset points",
                       ha=ha, va=va, color=color, fontsize=9 * k, fontweight="bold",
                       bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.75})


def _label_line(ax, seg, text, color, xmax, ymax, k=1.0, taken=None):
    """Write `text` next to a line segment, kept inside the axes.

    The end further right comes first (for vertical lines the upper end), then the other end, then points along the
    line. `taken` holds the boxes of the texts written before: a label that would cover one of them – e.g. two lines
    that meet the x1 axis close together – moves on to the next place."""
    (xa, ya), (xb, yb) = seg
    first = (xb, yb) if (xb, yb) >= (xa, ya) else (xa, ya)
    if abs(xa - xb) < 1e-9:
        first = (xa, max(ya, yb))
    other = (xa, ya) if first == (xb, yb) else (xb, yb)
    along = [(other[0] + f * (first[0] - other[0]), other[1] + f * (first[1] - other[1])) for f in (0.75, 0.25, 0.5)]
    renderer = ax.figure.canvas.get_renderer()
    axes_box = ax.get_window_extent(renderer)
    for place in (first, other, *along):
        label = _label_at(ax, place, text, color, xmax, ymax, k)
        box = label.get_window_extent(renderer).padded(3 * k)
        inside = box.x0 >= axes_box.x0 - 2 and box.x1 <= axes_box.x1 + 2 and box.y1 <= axes_box.y1 + 2
        if taken is None or (inside and not any(box.overlaps(b) for b in taken)):
            break
        label.remove()
    else:   # no free place: the usual end
        label = _label_at(ax, first, text, color, xmax, ymax, k)
        box = label.get_window_extent(renderer).padded(3 * k)
    if taken is not None:
        taken.append(box)


def draw(objective, constraints, var_types, solution, lang, figsize=None, scale=1.0, compact=False):
    """Return a matplotlib Figure.

    objective: dict or None; constraints: active constraints, each with "color_index";
    solution: result of core.solve or None.
    scale: factor for fonts, lines and markers; the page sends it so large screens get larger labels.
    compact: narrow graph (smartphones): the axes zoom to the feasible region and the optimum, the legend has one
    column and keeps a fixed distance below the x1 label, the optimum is labelled with its coordinates only and the
    shift of the objective line without a word – so that everything stays readable on 300 px.
    figsize should be the real size: the line labels are placed in the final layout so that none covers another.
    """
    k = max(0.8, min(float(scale or 1.0), 2.0))
    fig, ax = plt.subplots(figsize=figsize or (7, 6.2))
    fig.patch.set_facecolor("white")

    if objective is None or not constraints:
        _base_axes(ax, 10, 10, k)
        ax.text(5, 5, t(lang, "empty_graph").replace(" — ", "\n").replace(" – ", "\n"), ha="center", va="center", wrap=True, fontsize=11 * k, color=INK,
                bbox={"boxstyle": "round,pad=0.6", "fc": "white", "ec": GRID})
        fig.set_layout_engine("tight", pad=1.2)
        return fig

    sol = solution if solution and solution.get("status") == "optimal" else None
    xmax, ymax = (core.zoom_bounds if compact else core.plot_bounds)(objective, constraints, sol)
    _base_axes(ax, xmax, ymax, k, compact)
    handles = []

    # feasible region
    region = core.feasible_region(constraints, var_types, xmax, ymax)
    if region["kind"] == "polygon" and region["points"]:
        pts = region["points"]
        area = 0.5 * abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts))))
        if area > 1e-9 * xmax * ymax:
            ax.add_patch(mpatches.Polygon(pts, closed=True, fc=FEASIBLE, alpha=0.3, ec="none", zorder=1))
        else:  # equality constraints leave a segment or a point
            xs, ys = zip(*pts)
            ax.plot(xs, ys, color=FEASIBLE, lw=6 * k, alpha=0.6, solid_capstyle="round", zorder=1)
        handles.append(mpatches.Patch(color=FEASIBLE, alpha=0.4, label=t(lang, "plot_region")))
    elif region["kind"] == "points" and region["points"]:
        xs, ys = zip(*region["points"])
        size = 24 if len(xs) < 400 else (8 if len(xs) < 3000 else 3)
        ax.scatter(xs, ys, s=size * k * k, color=FEASIBLE, alpha=0.8, zorder=1, lw=0 * k)
        handles.append(mlines.Line2D([], [], color=FEASIBLE, marker="o", ls="none", ms=5 * k, label=t(lang, "plot_points")))
    elif region["kind"] == "vsegments" and region["segments"]:
        for x, lo, hi in region["segments"]:
            ax.plot([x, x], [lo, hi], color=FEASIBLE, lw=2.2 * k, alpha=0.6, zorder=1, solid_capstyle="butt")
        handles.append(mlines.Line2D([], [], color=FEASIBLE, lw=2.2 * k, alpha=0.6, label=t(lang, "plot_points")))
    elif region["kind"] == "hsegments" and region["segments"]:
        for y, lo, hi in region["segments"]:
            ax.plot([lo, hi], [y, y], color=FEASIBLE, lw=2.2 * k, alpha=0.6, zorder=1, solid_capstyle="butt")
        handles.append(mlines.Line2D([], [], color=FEASIBLE, lw=2.2 * k, alpha=0.6, label=t(lang, "plot_points")))

    # constraints (their labels come last, see below)
    line_labels = []
    for con in constraints:
        color, style = constraint_style(con["color_index"])
        seg = core.line_in_box(con["a1"], con["a2"], con["b"], xmax, ymax)
        if seg:
            (xa, ya), (xb, yb) = seg
            ax.plot([xa, xb], [ya, yb], color=color, ls=style, lw=2.2 * k, zorder=3)
            line_labels.append((seg, con["name"], color))
        handles.append(mlines.Line2D([], [], color=color, ls=style, lw=2.2 * k, label=con["name"]))

    # dummy objective line and, after solving, the optimized line
    a1, a2 = objective["c1"], objective["c2"]
    level = core.dummy_level(objective, constraints, xmax, ymax)
    seg = core.line_in_box(a1, a2, level, xmax, ymax)
    if seg:
        (xa, ya), (xb, yb) = seg
        ax.plot([xa, xb], [ya, yb], color=DUMMY, ls=(0, (6, 4)), lw=2.2 * k, zorder=4)
        handles.append(mlines.Line2D([], [], color=DUMMY, ls=(0, (6, 4)), lw=2.2 * k,
                                     label=t(lang, "plot_dummy", name=objective["name"])))

    if sol:
        x0, y0 = sol["x1"], sol["x2"]
        seg = core.line_in_box(a1, a2, sol["value"], xmax, ymax)
        if seg:
            (xa, ya), (xb, yb) = seg
            ax.plot([xa, xb], [ya, yb], color=OPTIMIZED, ls=(0, (6, 4)), lw=2.2 * k, zorder=4)
            handles.append(mlines.Line2D([], [], color=OPTIMIZED, ls=(0, (6, 4)), lw=2.2 * k,
                                         label=t(lang, "plot_optimized", name=objective["name"])))
        foot = core.perpendicular_foot(a1, a2, level, x0, y0)
        if foot and (abs(foot[0] - x0) + abs(foot[1] - y0)) > 1e-6 * (xmax + ymax):
            ax.annotate("", xy=(x0, y0), xytext=foot, zorder=5,
                        arrowprops={"arrowstyle": "-|>", "color": DUMMY, "lw": 1.8 * k, "shrinkA": 0, "shrinkB": 7})
            mx, my = (foot[0] + x0) / 2, (foot[1] + y0) / 2
            if not compact:   # on a phone the arrow says it alone
                ax.annotate(t(lang, "plot_shift"), (mx, my), xytext=(6, -10), textcoords="offset points",
                            color=DUMMY, fontsize=9 * k, fontweight="bold")
        ax.plot([x0], [y0], "o", color=OPTIMUM, ms=9 * k, zorder=6, mec="white", mew=1.5 * k)
        point = f"({fmt_num(x0, lang)} | {fmt_num(y0, lang)})"
        label = point if compact else f"{t(lang, 'plot_optimum')} {point}"   # the legend names it on a phone
        ha = "right" if x0 > (0.5 if compact else 0.6) * xmax else "left"
        ax.annotate(label, (x0, y0), xytext=(-10 if ha == "right" else 10, 10), textcoords="offset points",
                    ha=ha, color=OPTIMUM, fontsize=10 * k, fontweight="bold", zorder=7,
                    bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none", "alpha": 0.85})
        handles.insert(0, mlines.Line2D([], [], color=OPTIMUM, marker="o", ls="none", ms=8 * k,
                                        label=f"{t(lang, 'plot_optimum')}: {objective['name']} = {fmt_num(sol['value'], lang)}"))

    # below the axes: 10 % of the axes height, or on narrow graphs a fixed 38 pt so that it stays clear of “x1”
    anchor = {"bbox_to_anchor": (0.5, -0.1)}
    if compact:
        anchor = {"bbox_to_anchor": (0.5, 0), "bbox_transform": ax.transAxes + ScaledTranslation(0, -38 * k / 72, fig.dpi_scale_trans)}
    ncol = 1 if compact else (2 if len(handles) > 2 else len(handles))   # one column fits a phone's width
    width, height = fig.get_size_inches()
    if compact and width > 1.3 * height:   # a phone held sideways: the legend beside the axes, so they keep their height
        anchor = {"loc": "center left", "bbox_to_anchor": (1.02, 0.5)}
    ax.legend(handles=handles, **{"loc": "upper center", **anchor}, ncol=ncol, fontsize=9 * k,
              frameon=False, handlelength=2.4 if not compact else 1.8)
    fig.set_layout_engine("tight", pad=1.2)

    # the line labels last, in the final layout: only then are their sizes on screen known, so that none covers
    # another label, the optimum or the word “shift”
    fig.get_layout_engine().execute(fig)
    renderer = fig.canvas.get_renderer()
    taken = [a.get_window_extent(renderer).padded(2 * k) for a in ax.texts if a.get_text()]   # x1, x2, optimum, shift
    for seg, name, color in line_labels:
        _label_line(ax, seg, name, color, xmax, ymax, k, taken)
    return fig


def png_bytes(fig, dpi):
    """The figure as PNG. Closes it: pyplot keeps every open figure, with its image buffer, until the app stops.
    A closed figure is only freed by Python's cycle collector, often many downloads later, so collect right away
    (about 15 ms; an image at 600 dpi needs about 80 MB)."""
    try:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
        return buf.getvalue()
    finally:
        plt.close(fig)
        del fig
        gc.collect()
