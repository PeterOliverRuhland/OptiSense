"""The evaluation of a handed-in exercise as a PDF file (“Save evaluation”).

A document that can be read on its own: the score, the task, the correct model, the graphical solution and,
for every step, what the learner entered next to the correct answers and the worked solution.

Drawn with matplotlib alone, so no further package is needed. No pyplot: the pages are plain Figure objects
that are freed with the document. Texts of learners (names of their own constraints, their answers) are
never read as mathtext (parse_math=False). A document takes about half a second, so the server makes it in
a worker thread (server.py) – one at a time, see LOCK.
"""

import io
import re
import threading
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import matplotlib
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties, findfont, get_font
from matplotlib.patches import Polygon, Rectangle

from optisense import core
from optisense.config import DUMMY, FEASIBLE, GRID, INK, OPTIMUM, constraint_color
from optisense.i18n import fmt_num, norm_lang, t

from . import engine, solution, story

W, H = 595.28, 841.89                 # A4 in points
LEFT, RIGHT, TOP, BOTTOM = 50, W - 50, 48, H - 56
FONT = "DejaVu Sans"                  # comes with matplotlib and has ≤ ≥ → · ✓ ✗ ℝ ℕ
MUTED, LINE, SHADE = "#555b61", "#dee2e6", "#f1f3f5"
GOOD, BAD, BAD_ROW = "#1f7a1f", "#cc0000", "#fdf1f1"
OP_SIGN = solution.OP_SIGN
LOCK = threading.Lock()
matplotlib.rcParams["pdf.fonttype"] = 42   # real text in PDF files: searchable, copyable (only this module writes PDFs)


# ---------------------------------------------------------------------------------------------- text
@lru_cache(maxsize=4096)
def text_width(text, size, bold=False):
    """Width of a line in points."""
    font = get_font(findfont(FontProperties(family=FONT, weight="bold" if bold else "normal")))
    font.set_size(size, 72)
    font.set_text(text, 0.0)
    return font.get_width_height()[0] / 64


def wrap(text, size, width, bold=False):
    """The text as lines that fit the width; a word longer than a line is cut."""
    lines = []
    for paragraph in str(text).split("\n"):
        line = ""
        for word in paragraph.split(" "):
            while text_width(word, size, bold) > width and len(word) > 1:
                cut = next(n for n in range(len(word), 0, -1) if n == 1 or text_width(word[:n], size, bold) <= width)
                if line:
                    lines.append(line)
                lines.append(word[:cut])
                line, word = "", word[cut:]
            trial = f"{line} {word}" if line else word
            if line and text_width(trial, size, bold) > width:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
    return lines


class Document:
    """A4 pages that are filled from top to bottom; `y` is the top of the next line (in points from the top)."""

    def __init__(self):
        self.pages = []
        self.new_page()

    def new_page(self):
        self.fig = Figure(figsize=(W / 72, H / 72))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, W)
        self.ax.set_ylim(H, 0)
        self.ax.axis("off")
        self.pages.append(self.fig)
        self.y = TOP

    def room(self, height):
        """Start a new page if `height` does not fit any more."""
        if self.y + height > BOTTOM:
            self.new_page()

    def put(self, text, x, y, size=9.5, bold=False, color=INK, ha="left"):
        """One line; y is its top."""
        self.ax.text(x, y + size, text, fontsize=size, fontfamily=FONT, fontweight="bold" if bold else "normal",
                     color=color, ha=ha, va="baseline", parse_math=False)

    def write(self, text, x=LEFT, width=None, size=9.5, bold=False, color=INK, after=3):
        """A paragraph, wrapped to the width; moves y below it."""
        step = size * 1.38
        for line in wrap(text, size, (RIGHT - x) if width is None else width, bold):
            self.room(step)
            self.put(line, x, self.y, size, bold, color)
            self.y += step
        self.y += after

    def rect(self, x, y, w, h, fill="none", edge="none", lw=0.6):
        self.ax.add_patch(Rectangle((x, y), w, h, fc=fill, ec=edge, lw=lw))

    def hline(self, y, x0=LEFT, x1=RIGHT, color=LINE, lw=0.6, **kw):
        self.ax.plot([x0, x1], [y, y], color=color, lw=lw, solid_capstyle="butt", **kw)

    def heading(self, text, keep=60):
        """Section title with a line below; `keep` points of content stay on the same page."""
        self.y += 8
        self.room(22 + keep)
        self.put(text, LEFT, self.y, 12.5, bold=True)
        self.y += 19
        self.hline(self.y, color=INK, lw=0.8)
        self.y += 7

    def swatch(self, x, y, color, dashed=False, size=9.5):
        """The colour mark in front of a function, like in the app; y is the top of its text line."""
        if dashed:
            self.ax.plot([x, x + 11], [y + size * 0.68] * 2, color=color, lw=1.8, ls=(0, (2.2, 1.4)), solid_capstyle="butt")
        else:
            self.rect(x, y + size * 0.3, 8, 8, fill=color)

    TABLE_SIZE, TABLE_PAD = 8.8, 3.5

    def table_layout(self, widths, header, rows):
        """rows: (cells, shade) with cells as (text, colour, bold). Returns the wrapped lines with their heights,
        header first, and the height of the whole table."""
        size, pad = self.TABLE_SIZE, self.TABLE_PAD
        out = []
        for cells, shade in [([(h, MUTED, True) for h in header], SHADE)] + list(rows):
            wrapped = [wrap(c[0], size, w - 2 * pad, c[2]) for c, w in zip(cells, widths)]
            out.append((cells, shade, wrapped, max(len(w) for w in wrapped) * size * 1.36 + 2 * pad - 1.5))
        return out, sum(line[3] for line in out)

    def table(self, widths, layout):
        """Draws a table from table_layout. A row is never split over two pages."""
        size, pad = self.TABLE_SIZE, self.TABLE_PAD
        xs = [LEFT + sum(widths[:i]) for i in range(len(widths))]
        for cells, shade, wrapped, height in layout:
            self.room(height)
            if shade:
                self.rect(LEFT, self.y, sum(widths), height, fill=shade)
            for c, x, lines_ in zip(cells, xs, wrapped):
                for n, text in enumerate(lines_):
                    self.put(text, x + pad, self.y + pad - 1 + n * size * 1.36, size, c[2], c[1])
            self.y += height
            self.hline(self.y, LEFT, LEFT + sum(widths))

    def save(self, footer, title):
        buf = io.BytesIO()
        with PdfPages(buf, metadata={"Title": title, "Creator": "OptiSense", "Producer": "OptiSense"}) as pdf:
            for n, fig in enumerate(self.pages, start=1):
                ax = fig.axes[0]
                ax.plot([LEFT, RIGHT], [H - 40, H - 40], color=LINE, lw=0.6)
                ax.text(LEFT, H - 28, footer, fontsize=7.5, fontfamily=FONT, color=MUTED, parse_math=False)
                ax.text(RIGHT, H - 28, f"{n} / {len(self.pages)}", fontsize=7.5, fontfamily=FONT, color=MUTED, ha="right")
                pdf.savefig(fig)
        return buf.getvalue()


# ---------------------------------------------------------------------------------------------- labels
def boundary_names(ex, lang):
    """“C1 Buns”, … and the two axes – numbered like the boundaries of the corner step."""
    labels, names = story.row_labels(ex, lang), story.row_names(ex, lang)
    out = [f"{lab} {name}" if name else lab for lab, name in zip(labels, names)]
    return out + [t(lang, "learn_axis_x1"), t(lang, "learn_axis_x2")]


def question_label(ex, key, lang):
    """What a field asks for – the same words as on the evaluation page (www/learn.js: qLabel)."""
    labels = story.row_labels(ex, lang)
    tr = lambda k, **kw: t(lang, f"learn_{k}", **kw)  # noqa: E731
    if key in ("sense", "z"):
        return tr(f"a_{key}")
    if key in ("meaning", "round"):
        return tr(f"q_{key}")
    if key in ("x", "y"):
        return tr("a_opt", n=1 if key == "x" else 2)
    m = re.fullmatch(r"([a-z]+)(\d+)(?:_(\d))?", key)
    if not m:
        return key
    kind, i, j = m.group(1), int(m.group(2)), int(m.group(3) or 0)
    if kind in ("vt", "c"):
        return tr(f"a_{kind}", n=i + 1)
    if kind == "boundary":
        return tr("a_boundary", n=i)
    if kind == "p" and i < len(ex["points"]):
        return f"P{i + 1} {solution.point(ex['points'][i], lang)}"
    if i >= len(labels):
        return key
    if kind == "ax":
        return f"{labels[i]} · {tr('ax_x2' if j else 'ax_x1')}"
    if kind == "a":
        return tr("a_a", label=labels[i], n=j + 1)
    if kind in ("op", "b", "side", "slack", "bind"):
        return tr(f"a_{kind}", label=labels[i])
    return key


def shown(ex, q, value, lang):
    """An answer as text: the label of a choice, a number in the chosen language, the learner's text as typed."""
    if value is None or str(value).strip() == "":
        return "–"
    key = q["key"]
    if "choices" not in q:
        return fmt_num(value, lang) if isinstance(value, (int, float)) else str(value)
    v = str(value)
    if v not in q["choices"]:
        return "–"
    if key == "sense":
        return v
    if key == "meaning":
        return t(lang, f"learn_meaning_{v}")
    if key == "round":
        return t(lang, f"learn_round_{v}")
    if key.startswith("vt"):
        return t(lang, "integer_short" if v == "int" else "continuous_short")
    if key.startswith("op"):
        return OP_SIGN[v]
    if key.startswith("side"):
        p = ex["test_points"][int(key[4:])]
        return t(lang, "learn_side_in", p=solution.point(p, lang)) if v == "in" else t(lang, f"learn_side_{v}")
    if key.startswith("bind"):
        return t(lang, f"learn_bind_{v}")
    if key.startswith("boundary"):
        return boundary_names(ex, lang)[int(v)]
    return t(lang, "learn_feasible_yes" if v == "yes" else "learn_feasible_no")   # p0, p1 …


def review_rows(ex, step, answers, checks, lang):
    """(entry, the learner's answer, the correct answer, right?) for every field of a step."""
    mine = answers.get(step["id"], {})
    right = engine.solution_values(ex, step, answers, lang)
    if step["id"] == "constraints":
        # one line per constraint: its four fields are graded together
        names, rows = boundary_names(ex, lang), []
        for i, r in enumerate(ex["model"]["rows"]):
            a1, a2, op, b = (str(mine.get(k, "")).strip() for k in (f"a{i}_0", f"a{i}_1", f"op{i}", f"b{i}"))
            typed = f"{a1 or '?'}·x1 + {a2 or '?'}·x2 {OP_SIGN.get(op, '?')} {b or '?'}" if (a1 or a2 or op or b) else "–"
            correct = f"{solution.formula(r['a'], lang)} {OP_SIGN[r['op']]} {fmt_num(r['b'], lang)}"
            rows.append((names[i], typed, correct, all(checks.get(k) for k in (f"a{i}_0", f"a{i}_1", f"op{i}", f"b{i}"))))
        return rows
    return [(question_label(ex, q["key"], lang), shown(ex, q, mine.get(q["key"]), lang),
             shown(ex, q, right.get(q["key"]), lang), bool(checks.get(q["key"]))) for q in step["questions"]]


def step_title(ex, step, lang):
    calc = step["id"] == "optimum" and engine.step_by_id(ex, "corner")
    return t(lang, "learn_step_optimum_calc" if calc else f"learn_step_{step['id']}")


def handed_in(tz_minutes, lang):
    """Now, in the learner's time zone (the browser sends its offset to UTC in minutes; the clock is the server's)."""
    try:
        offset = -max(-840, min(720, int(tz_minutes)))
    except (TypeError, ValueError, OverflowError):
        offset = 0
    when = datetime.now(timezone(timedelta(minutes=offset)))
    sign, (hours, minutes) = "+" if offset >= 0 else "−", divmod(abs(offset), 60)
    zone = f"UTC{sign}{hours}" + (f":{minutes:02d}" if minutes else "") if offset else "UTC"
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    date = f"{when.day:02d}.{when.month:02d}.{when.year}" if lang == "de" else f"{when.day} {months[when.month - 1]} {when.year}"
    return f"{date}, {when.hour:02d}:{when.minute:02d} ({zone})"


# ---------------------------------------------------------------------------------------------- graph
def draw_graph(doc, ex, lang, x, y, w, h):
    """The graphical solution: feasible region, constraint lines, the objective line through the optimum and the
    optimal point – the correct solution, so it is complete even if steps were skipped."""
    m, sol = ex["model"], ex["solution"]
    xmax, ymax = ex["extent"]
    colors = ex.get("colors") or [constraint_color(i) for i in range(len(m["rows"]))]
    cons = [{"a1": r["a"][0], "a2": r["a"][1], "op": OP_SIGN[r["op"]], "b": r["b"]} for r in m["rows"]]
    ints = engine.integrality(m)
    ax = doc.fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK)
        ax.spines[side].set_linewidth(0.8)
    ax.grid(True, ls="--", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(colors=INK, labelsize=7.5, labelfontfamily=FONT, width=0.6, length=3)
    ax.xaxis.set_major_formatter(lambda v, _: fmt_num(v, lang))
    ax.yaxis.set_major_formatter(lambda v, _: fmt_num(v, lang))
    text = {"fontsize": 8.5, "fontfamily": FONT, "fontweight": "bold", "parse_math": False}
    ax.annotate("x1", (1, 0), xycoords="axes fraction", xytext=(0, -17), textcoords="offset points", ha="right", va="top", color=INK, **text)
    ax.annotate("x2", (0, 1), xycoords="axes fraction", xytext=(6, 2), textcoords="offset points", ha="left", va="top", color=INK, **text)

    region = core.feasible_region(cons, {"x1": "int" if ints[0] else "con", "x2": "int" if ints[1] else "con"}, xmax, ymax)
    if region["kind"] == "polygon" and region["points"]:
        pts = region["points"]
        area = 0.5 * abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts))))
        if area > 1e-9 * xmax * ymax:
            ax.add_patch(Polygon(pts, closed=True, fc=FEASIBLE, alpha=0.3, ec="none", zorder=1))
        else:   # equations leave a segment
            ax.plot(*zip(*pts), color=FEASIBLE, lw=4, alpha=0.6, solid_capstyle="round", zorder=1)
    elif region["kind"] == "points" and region["points"]:
        xs, ys = zip(*region["points"])
        ax.scatter(xs, ys, s=7 if len(xs) < 400 else 2.5, color=FEASIBLE, alpha=0.85, lw=0, zorder=1)
    elif region["kind"] in ("vsegments", "hsegments"):
        for v, lo, hi in region["segments"]:
            xy = ([v, v], [lo, hi]) if region["kind"] == "vsegments" else ([lo, hi], [v, v])
            ax.plot(*xy, color=FEASIBLE, lw=1.6, alpha=0.65, solid_capstyle="butt", zorder=1)

    labels = story.row_labels(ex, lang)
    x0, y0 = sol["x"]
    taken = [(x0 / xmax * w + 20, y0 / ymax * h + 10)]   # label spots in points; the first is the optimum's
    for i, con in enumerate(cons):
        seg = core.line_in_box(con["a1"], con["a2"], con["b"], xmax, ymax)
        if not seg:
            continue
        (xa, ya), (xb, yb) = sorted(seg)
        ax.plot([xa, xb], [ya, yb], color=colors[i], lw=1.6, zorder=3)
        # the name at the right end of the line – or further along it, where no other label is
        spots = [(xa + f * (xb - xa), ya + f * (yb - ya)) for f in (1, 0, 0.8, 0.2, 0.6, 0.4)]
        free = lambda p: min(abs(p[0] / xmax * w - q[0]) / 30 + abs(p[1] / ymax * h - q[1]) / 14 for q in taken)  # noqa: E731
        px, py = next((p for p in spots if free(p) >= 1), max(spots, key=free))
        taken.append((px / xmax * w, py / ymax * h))
        right = px > 0.8 * xmax
        short = labels[i] if len(labels[i]) <= 14 else labels[i][:13] + "…"   # own names can be long; the legend has them in full
        ax.annotate(short, (min(px, 0.99 * xmax), min(py, 0.95 * ymax)), xytext=(-3 if right else 3, 3), textcoords="offset points",
                    ha="right" if right else "left", va="bottom", color=colors[i], zorder=5,
                    bbox={"boxstyle": "round,pad=0.12", "fc": "white", "ec": "none", "alpha": 0.8}, **{**text, "fontsize": 7.5})
    seg = core.line_in_box(m["c"][0], m["c"][1], sol["z"], xmax, ymax)
    if seg:
        ax.plot(*zip(*seg), color=DUMMY, lw=1.6, ls=(0, (5, 3.5)), zorder=4)
    ax.plot([x0], [y0], "o", color=OPTIMUM, ms=6.5, mec="white", mew=1.1, zorder=6, clip_on=False)
    right = x0 > 0.6 * xmax
    ax.annotate(solution.point(sol["x"], lang), (x0, y0), xytext=(-7 if right else 7, 7), textcoords="offset points",
                ha="right" if right else "left", color=OPTIMUM, zorder=7,
                bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.85}, **{**text, "fontsize": 8})
    return colors


# ---------------------------------------------------------------------------------------------- document
def pdf(ex, result, answers, lang, tz_minutes=0):
    """The evaluation as PDF bytes. result: what “submit” stored (score, grades, hints, reveals, first)."""
    with LOCK:
        return build(ex, result, answers or {}, norm_lang(lang), tz_minutes)


def build(ex, result, answers, lang, tz_minutes):
    tr = lambda k, **kw: t(lang, f"learn_{k}", **kw)  # noqa: E731
    num = lambda v: fmt_num(v, lang)  # noqa: E731
    m, sol, info, options = ex["model"], ex["solution"], ex["info"], ex["options"]
    st = story.story(ex, lang)
    names = boundary_names(ex, lang)
    colors = ex.get("colors") or [constraint_color(i) for i in range(len(m["rows"]))]
    tutorial, exam = info["source"] == "tutorial", options.get("mode") == "exam"
    fname = st.get("fname")
    doc = Document()

    # ---- head: what was handed in, and the score
    doc.put("OptiSense", LEFT, doc.y, 9, bold=True, color=MUTED)
    doc.put(handed_in(tz_minutes, lang), RIGHT, doc.y, 8.5, color=MUTED, ha="right")
    doc.y += 15
    doc.write(tr("res_title"), size=18, bold=True, after=1)
    doc.write(st["title"], size=11.5, bold=True, after=2)
    facts = [tr("mode_tutorial" if tutorial else "mode_exam" if exam else "mode_practice"), t(lang, f"type_{m['kind'].rstrip('12')}")]
    if info["source"] == "generated":
        facts += [tr(f"form_{options['form']}"), f"{tr('opt_difficulty')}: {tr('diff_' + options['difficulty'])}"]
    doc.write(" · ".join(facts), size=9.5, color=MUTED, after=8)

    grades = result["grades"]
    kpis = [(tr("kpi_score"), f"{num(result['score'])} / 100"),
            (tr("kpi_steps"), f"{sum(1 for g in grades if g['correct'])} / {len(grades)}")]
    if not exam:
        kpis += [(tr("kpi_hints"), str(len(result["hints"]))), (tr("kpi_seen"), str(len(result["reveals"])))]
    box_w = (RIGHT - LEFT - 8 * (len(kpis) - 1)) / len(kpis)
    for n, (label, value) in enumerate(kpis):
        x = LEFT + n * (box_w + 8)
        doc.rect(x, doc.y, box_w, 40, fill=SHADE if n else "#e7f1ff", edge=LINE)
        doc.put(label, x + 8, doc.y + 6, 8, color=MUTED)
        doc.put(value, x + 8, doc.y + 18, 14, bold=True)
    doc.y += 46
    doc.write(tr("res_tut_text" if tutorial else "res_note_exam" if exam else "res_note_practice"), size=8.5, color=MUTED, after=2)

    def model_lines(model_names):
        """F and the constraints with their colours, then the value range – like the model list in the app."""
        doc.room(14)
        doc.swatch(LEFT, doc.y, DUMMY, dashed=True)
        doc.write((f"{fname}: " if fname else "") + f"F = {solution.formula(m['c'], lang)} → {m['sense']}", x=LEFT + 16, after=1)
        for i, r in enumerate(m["rows"]):
            doc.room(14)
            doc.swatch(LEFT, doc.y, colors[i])
            doc.write(f"{model_names[i]}: {solution.formula(r['a'], lang)} {OP_SIGN[r['op']]} {num(r['b'])}", x=LEFT + 16, after=1)
        vt = [t(lang, "integer_short" if k else "continuous_short") for k in engine.integrality(m)]
        doc.write(tr("sol_range", vt1=vt[0], vt2=vt[1]), x=LEFT + 16, color=MUTED, after=3)

    # ---- the task
    doc.heading(tr("task"))
    if st.get("intro"):
        doc.write(st["intro"], after=5)
        doc.write(tr("story_sought"), size=9, bold=True, after=1)
        for j, sought in enumerate(st["sought"]):
            doc.room(14)
            doc.put(f"x{j + 1}", LEFT, doc.y, bold=True)
            doc.write(sought, x=LEFT + 20, after=1)
        doc.y += 4
        doc.room(14)
        doc.swatch(LEFT, doc.y, DUMMY, dashed=True)
        doc.write(st["objective"], x=LEFT + 16, after=1.5)
        labels = story.row_labels(ex, lang)
        for i, row in enumerate(st["rows"]):
            doc.room(14)
            doc.swatch(LEFT, doc.y, colors[i])
            doc.put(labels[i], LEFT + 16, doc.y, bold=True, color=colors[i])
            doc.write(row, x=LEFT + 22 + text_width(labels[i], 9.5, True), after=1.5)
        for line in st["domain"]:
            doc.write(line, x=LEFT + 16, color=MUTED, after=1.5)
        doc.y += 3
    else:
        model_lines(names)
    if st.get("question"):
        doc.write(st["question"], bold=True, after=2)
    if st.get("intro"):
        doc.heading(tr("res_model"))
        model_lines(names)

    # ---- the graphical solution, with its legend on the right
    # full size if it fits; a little smaller rather than leaving the rest of the page empty
    room = BOTTOM - doc.y - 82
    gh = 204 if room >= 204 or room < 160 else room
    gw = gh * 1.255
    doc.heading(tr("res_graph"), keep=gh + 44)
    top = doc.y + 4
    draw_graph(doc, ex, lang, LEFT + 30, top, gw, gh)
    lx, ly, lw = LEFT + 30 + gw + 28, top + 2, RIGHT - (LEFT + 30 + gw + 28) - 16

    def legend(mark, text, bold=False):
        nonlocal ly
        mark(ly)
        for line in wrap(text, 8.8, lw, bold):
            doc.put(line, lx + 16, ly, 8.8, bold=bold)
            ly += 12.2
        ly += 3.5

    legend(lambda yy: doc.ax.plot([lx + 5], [yy + 6.2], "o", color=OPTIMUM, ms=6, mec="white", mew=0.8),
           f"{t(lang, 'plot_optimum')} {solution.point(sol['x'], lang)}", bold=True)
    legend(lambda yy: doc.swatch(lx, yy, DUMMY, dashed=True, size=8.8), tr("res_objline", z=num(sol["z"])))
    if m["kind"] == "LP":
        legend(lambda yy: doc.rect(lx, yy + 2.6, 9, 8, fill="#cfcfcf"), t(lang, "plot_region"))
    elif m["kind"] == "ILP":
        legend(lambda yy: doc.ax.plot([lx + 5], [yy + 6.2], "o", color=FEASIBLE, ms=3.2, mew=0), t(lang, "plot_points"))
    else:
        legend(lambda yy: doc.hline(yy + 6.4, lx, lx + 11, color=FEASIBLE, lw=1.6, alpha=0.65), t(lang, "plot_points"))
    for i in range(len(m["rows"])):
        legend(lambda yy, c=colors[i]: doc.hline(yy + 6.4, lx, lx + 11, color=c, lw=1.8), names[i])
    doc.y = max(top + gh + 26, ly + 4)
    doc.write(tr("res_optimum", x1=num(sol["x"][0]), x2=num(sol["x"][1]), f=f"{fname} F" if fname else "F", z=num(sol["z"])), bold=True, after=2)

    # ---- every step: the learner's answers next to the correct ones, then the worked solution
    worked = solution.all_lines(ex, lang)
    widths = [168, 136, 136, RIGHT - LEFT - 440]
    for step, grade in zip(ex["steps"], grades):
        sid = step["id"]
        rows = [([(label, INK, False), (mine, INK, False), (right, INK, False), ("✓" if ok else "✗", GOOD if ok else BAD, True)],
                 None if ok else BAD_ROW) for label, mine, right, ok in review_rows(ex, step, answers, grade["checks"], lang)]
        layout, height = doc.table_layout(widths, [tr("res_item"), tr("res_your"), tr("res_correct"), tr("res_ok")], rows)
        # a step stays on one page: title, notes, table and worked solution
        lines = sum(len(wrap(line, 8.5, RIGHT - LEFT - 18)) for line in worked.get(sid, []))
        keep = min(23 + 14 + height + 18 + lines * 12.3 + 4, BOTTOM - TOP - 40)
        if step is ex["steps"][0]:
            doc.heading(tr("res_steps"), keep=keep)
        doc.room(keep)
        doc.rect(LEFT, doc.y, RIGHT - LEFT, 20, fill="#e7f1ff")
        doc.put(step_title(ex, step, lang), LEFT + 6, doc.y + 4.5, 10.5, bold=True)
        doc.put(tr("points_of", got=num(grade["points"]), max=num(grade["max"])), RIGHT - 6, doc.y + 5.5, 9, bold=True, ha="right",
                color=GOOD if grade["correct"] else INK)
        doc.y += 23
        notes = []
        if sid in result["reveals"]:
            notes.append(tr("res_seen"))
        elif result["hints"].get(sid):
            notes.append(tr("res_with_hint"))
        if sid in result["first"] and not exam:
            first = result["first"][sid]
            notes.append(tr("res_before_solution" if first.get("via") == "solution" else "res_first", got=num(first["points"]), max=num(grade["max"])))
        if notes:
            doc.write(" · ".join(notes), x=LEFT + 6, size=8, color=MUTED, after=2)
        doc.table(widths, layout)
        doc.y += 5
        doc.room(26)
        doc.put(tr("sol_title"), LEFT + 6, doc.y, 8.5, bold=True, color=MUTED)
        doc.y += 12.5
        for line in worked.get(sid, []):
            doc.room(12)
            doc.put("•", LEFT + 8, doc.y, 8.5, color=MUTED)
            doc.write(line, x=LEFT + 18, size=8.5, after=0.5)
        doc.y += 10

    return doc.save(f"OptiSense · {tr('res_title')} · {st['title']}", f"OptiSense – {tr('res_title')}")
