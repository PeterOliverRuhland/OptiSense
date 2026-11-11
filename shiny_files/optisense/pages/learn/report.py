"""The evaluation of a handed-in exercise as a PDF file (“Save evaluation”).

A compact document that can be read on its own, two A4 pages at most. Page 1: the score, the task text, the correct
model with the optimal solution next to the graphical solution, and the points of every step. Page 2: for every step,
what the learner entered next to the correct answers (the font gets smaller rather than the table longer). The worked
solutions stay in the app.

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
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle

from optisense import core
from optisense.config import DUMMY, FEASIBLE, GRID, INK, OPTIMIZED, OPTIMUM, constraint_color
from optisense.i18n import fmt_num, norm_lang, t

from . import engine, solution, story

W, H = 595.28, 841.89                 # A4 in points
LEFT, RIGHT, TOP, BOTTOM = 42, W - 42, 40, H - 48
FONT = "DejaVu Sans"                  # comes with matplotlib and has ≤ ≥ → · ✓ ✗ ℝ ℕ
MUTED, LINE, SHADE = "#555b61", "#dee2e6", "#f1f3f5"
GOOD, BAD, BAD_ROW = "#1f7a1f", "#cc0000", "#fdf1f1"
PRIMARY, PANEL, PANEL_EDGE, AMBER = "#00629b", "#eef6fc", "#cfe3f2", "#a35f00"   # design tokens of the app
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

    def box(self, x, y, w, h, fill=PANEL, edge="none", r=5, lw=0.6):
        """A rectangle with rounded corners, like the cards of the app."""
        r = min(r, w / 2, h / 2)
        self.ax.add_patch(FancyBboxPatch((x + r, y + r), w - 2 * r, h - 2 * r, boxstyle=f"round,pad={r}", fc=fill, ec=edge, lw=lw))

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
    ax.annotate("x2", (0, 1), xycoords="axes fraction", xytext=(6, 2), textcoords="offset points", ha="left", va="top", color=INK, zorder=8,
                bbox={"boxstyle": "round,pad=0.1", "fc": "white", "ec": "none"}, **text)

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
    # label boxes in points (x from the left, y from the bottom of the plot); a name goes where it hits no other label
    to_pt = lambda px, py: (min(px, 0.99 * xmax) / xmax * w, min(py, 0.95 * ymax) / ymax * h)  # noqa: E731
    hits = lambda a, b: not (a[1] < b[0] or b[1] < a[0] or a[3] < b[2] or b[3] < a[2])  # noqa: E731
    opt_right = x0 > 0.6 * xmax
    ox, oy = to_pt(x0, y0)
    ow = text_width(solution.point(sol["x"], lang), 8, True) + 4
    boxes = [(ox - 7 - ow, ox, oy + 5, oy + 17) if opt_right else (ox, ox + 7 + ow, oy + 5, oy + 17), (ox - 5, ox + 5, oy - 5, oy + 5)]
    for i, con in enumerate(cons):
        seg = core.line_in_box(con["a1"], con["a2"], con["b"], xmax, ymax)
        if not seg:
            continue
        (xa, ya), (xb, yb) = sorted(seg)
        ax.plot([xa, xb], [ya, yb], color=colors[i], lw=1.8, zorder=3)
        short = labels[i] if len(labels[i]) <= 14 else labels[i][:13] + "…"   # own names can be long; the legend has them in full
        tw = text_width(short, 7.5, True) + 3
        options = []
        for f in (1, 0, 0.85, 0.15, 0.7, 0.3, 0.55, 0.45):
            px, py = xa + f * (xb - xa), ya + f * (yb - ya)
            right = px > 0.8 * xmax
            bx, by = to_pt(px, py)
            box = (bx - 3 - tw, bx - 3, by + 2, by + 12) if right else (bx + 3, bx + 3 + tw, by + 2, by + 12)
            options.append((sum(hits(box, b) for b in boxes), (px, py, right, box)))
        px, py, right, box = min(options, key=lambda o: o[0])[1]   # the first spot without a collision, else the fewest
        boxes.append(box)
        ax.annotate(short, (min(px, 0.99 * xmax), min(py, 0.95 * ymax)), xytext=(-3 if right else 3, 3), textcoords="offset points",
                    ha="right" if right else "left", va="bottom", color=colors[i], zorder=5,
                    bbox={"boxstyle": "round,pad=0.12", "fc": "white", "ec": "none", "alpha": 0.8}, **{**text, "fontsize": 7.5})
    seg = core.line_in_box(m["c"][0], m["c"][1], sol["z"], xmax, ymax)
    if seg:
        ax.plot(*zip(*seg), color=DUMMY, lw=1.8, ls=(0, (5, 3.5)), zorder=4)
    ax.plot([x0], [y0], "o", color=OPTIMUM, ms=7.5, mec="white", mew=1.2, zorder=6, clip_on=False)
    ax.annotate(solution.point(sol["x"], lang), (x0, y0), xytext=(-7 if opt_right else 7, 7), textcoords="offset points",
                ha="right" if opt_right else "left", color=OPTIMUM, zorder=7,
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
    labels, names = story.row_labels(ex, lang), boundary_names(ex, lang)
    colors = ex.get("colors") or [constraint_color(i) for i in range(len(m["rows"]))]
    tutorial, exam = info["source"] == "tutorial", options.get("mode") == "exam"
    fname = st.get("fname")
    grades = result["grades"]
    graded = list(zip(ex["steps"], grades))
    doc = Document()

    def section(title, x=LEFT, width=RIGHT - LEFT):
        doc.put(title, x, doc.y, 10.5, bold=True, color=PRIMARY)
        doc.hline(doc.y + 16.5, x, x + width, color=PANEL_EDGE, lw=0.9)
        doc.y += 23

    def marked(color, text, x=LEFT, width=RIGHT - LEFT, size=8.8, label=None, label_color=INK):
        """A line with the colour square in front, like the model list of the app; optionally a bold label."""
        doc.swatch(x, doc.y, color, size=size)
        tx = x + 14
        if label:
            doc.put(label, tx, doc.y, size, bold=True, color=label_color)
            tx += text_width(label, size, True) + 5
        doc.write(text, x=tx, width=x + width - tx, size=size, after=2)

    # ---- head: what was handed in on the left, the score on the right
    doc.rect(0, 0, W, 4, fill=PRIMARY)
    doc.put(f"OptiSense · {t(lang, 'tab_learn')}", LEFT, 16, 8, bold=True, color=PRIMARY)
    doc.put(handed_in(tz_minutes, lang), RIGHT, 16, 8, color=MUTED, ha="right")
    card_w = 150
    card_x, head_w = RIGHT - card_w, RIGHT - card_w - LEFT - 18
    doc.y = 40
    doc.put(tr("res_title").upper(), LEFT, doc.y, 7.5, bold=True, color=MUTED)
    doc.y += 13
    doc.write(st["title"], width=head_w, size=15, bold=True, after=2)
    facts = [tr("mode_tutorial" if tutorial else "mode_exam" if exam else "mode_practice"), t(lang, f"type_{m['kind'].rstrip('12')}")]
    if info["source"] == "generated":
        facts += [tr(f"form_{options['form']}"), tr("diff_" + options["difficulty"])]
    if info.get("task"):
        facts.append(tr("res_task_id", id=info["task"]))
    doc.write(" · ".join(facts), width=head_w, size=8.5, color=MUTED, after=0)
    card_h = 80 if not exam else 68
    doc.box(card_x, 36, card_w, card_h, fill=PANEL, edge=PANEL_EDGE)
    score = num(result["score"])
    doc.put(tr("kpi_score"), card_x + 12, 44, 8, color=MUTED)
    doc.put(score, card_x + 12, 54, 22, bold=True, color=PRIMARY)
    doc.put("/ 100", card_x + 17 + text_width(score, 22, True), 63.5, 10.5, color=MUTED)
    doc.put(f"{tr('kpi_steps')}: {sum(1 for g in grades if g['correct'])} / {len(grades)}", card_x + 12, 86, 7.8, color=MUTED)
    if not exam:
        doc.put(tr("res_hints_seen", h=len(result["hints"]), s=len(result["reveals"])), card_x + 12, 97, 7.8, color=MUTED)
    doc.y = max(doc.y + 6, 36 + card_h + 8)
    doc.write(tr("res_tut_text" if tutorial else "res_note_exam" if exam else "res_note_practice"), width=head_w + card_w + 18,
              size=8, color=MUTED, after=10)

    # ---- the task as it was given: the text of a word problem (formulas only: the model below is the task)
    section(tr("task"))
    if st.get("intro"):
        doc.write(st["intro"], size=8.8, after=3)
        doc.put(f"{tr('story_sought')}:", LEFT, doc.y, 8.8, bold=True)
        sx = LEFT + text_width(f"{tr('story_sought')}:", 8.8, True) + 5
        doc.write("  ·  ".join(f"x{j + 1} = {sought}" for j, sought in enumerate(st["sought"])), x=sx, width=RIGHT - sx, size=8.8, after=3)
        marked(OPTIMIZED, st["objective"])
        for i, row in enumerate(st["rows"]):
            marked(colors[i], row, label=labels[i], label_color=colors[i])
        doc.write(" ".join(st["domain"]), x=LEFT + 14, size=8.3, color=MUTED, after=3)
    if st.get("question"):
        doc.write(st["question"], size=8.8, bold=True, after=2)

    # ---- the model and the optimal solution on the left, the graph on the right
    top = doc.y + 8
    col_l, gap = 212, 22
    xr = LEFT + col_l + gap
    col_r = RIGHT - xr
    n_legend = 3 + len(m["rows"])
    legend_h = -(-n_legend // 2) * 12.5
    points_h = 23 + len(graded) * 15.5 + 22
    room = BOTTOM - top - 23 - 24 - legend_h
    gh = min(col_r * 0.88, room - points_h - 10)
    points_first_page = gh >= 150
    if not points_first_page:
        gh = max(130, min(col_r * 0.88, room))

    doc.y = top
    section(tr("res_model"), LEFT, col_l)
    model = [(OPTIMIZED, f"{fname}:" if fname else "", INK, f"F = {solution.formula(m['c'], lang)} → {m['sense']}")]
    model += [(colors[i], f"{names[i]}:", colors[i], f"{solution.formula(r['a'], lang)} {OP_SIGN[r['op']]} {num(r['b'])}")
              for i, r in enumerate(m["rows"])]
    label_w = max(text_width(lab, 8.8, True) for _, lab, _, _ in model) + 6
    aligned = 14 + label_w + max(text_width(f, 8.8) for *_, f in model) <= col_l
    for color, lab, lab_color, formula in model:
        if aligned:   # the formulas one below the other
            doc.swatch(LEFT, doc.y, color)
            doc.put(lab, LEFT + 14, doc.y, 8.8, bold=True, color=lab_color)
            doc.put(formula, LEFT + 14 + (label_w if lab else 0), doc.y, 8.8)   # F of an own task has no name
            doc.y += 8.8 * 1.38 + 2
        else:
            marked(color, formula, width=col_l, label=lab or None, label_color=lab_color)
    vt = [t(lang, "integer_short" if k else "continuous_short") for k in engine.integrality(m)]
    doc.write(tr("sol_range", vt1=vt[0], vt2=vt[1]), x=LEFT + 14, width=col_l - 14, size=8.3, color=MUTED, after=10)
    section(tr("res_solution"), LEFT, col_l)
    doc.put(f"x1 = {num(sol['x'][0])}    x2 = {num(sol['x'][1])}", LEFT, doc.y, 10, bold=True)
    doc.y += 15
    doc.put(f"{fname}: F = {num(sol['z'])}" if fname else f"F = {num(sol['z'])}", LEFT, doc.y, 10, bold=True, color=OPTIMUM)
    doc.y += 17
    for i, r in enumerate(m["rows"]):
        sl = engine.slack(r, sol["x"])
        bound = tr("res_binding") if engine.binding(r, sol["x"]) else tr("res_not_binding")
        doc.write(f"{tr('a_slack', label=labels[i])} {num(sl)} · {bound}", width=col_l, size=8.3, after=0.5)
    left_end = doc.y

    doc.y = top
    section(tr("res_graph"), xr, col_r)
    gy = doc.y + 2
    draw_graph(doc, ex, lang, xr + 26, gy, col_r - 30, gh)
    legend = [(lambda x, y: doc.ax.plot([x + 5], [y + 5.6], "o", color=OPTIMUM, ms=6, mec="white", mew=0.8),
               f"{t(lang, 'plot_optimum')} {solution.point(sol['x'], lang)}"),
              (lambda x, y: doc.swatch(x, y, DUMMY, dashed=True, size=8), tr("res_objline", z=num(sol["z"])))]
    if m["kind"] == "LP":
        legend.append((lambda x, y: doc.rect(x, y + 1.6, 9, 8, fill="#cfcfcf"), t(lang, "plot_region")))
    elif m["kind"] == "ILP":
        legend.append((lambda x, y: doc.ax.plot([x + 5], [y + 5.6], "o", color=FEASIBLE, ms=3.2, mew=0), t(lang, "plot_points")))
    else:
        legend.append((lambda x, y: doc.hline(y + 5.6, x, x + 11, color=FEASIBLE, lw=1.6, alpha=0.65), t(lang, "plot_points")))
    for i in range(len(m["rows"])):
        legend.append((lambda x, y, c=colors[i]: doc.hline(y + 5.6, x, x + 11, color=c, lw=1.8), names[i]))
    ly = gy + gh + 24
    lx = xr
    for mark, text in legend:   # the entries side by side, a new row when one does not fit any more
        item = 15 + text_width(text, 7.8) + 14
        if lx > xr and lx + item - 14 > xr + col_r:
            lx, ly = xr, ly + 12.5
        mark(lx, ly)
        doc.put(text, lx + 15, ly, 7.8)
        lx += item
    doc.y = max(left_end, ly + 12.5) + 12

    # ---- points of every step: a bar, the points, and whether a hint or the solution was used
    def points_table():
        section(tr("res_points_steps"))
        bar_x, bar_w = LEFT + 214, 112
        for step, g in graded:
            y, sid = doc.y, step["id"]
            doc.put(step_title(ex, step, lang), LEFT, y, 8.6)
            doc.box(bar_x, y + 3.2, bar_w, 6.5, fill=LINE, r=3.2)
            share = g["points"] / g["max"] if g["max"] else 0
            if share > 0:
                doc.box(bar_x, y + 3.2, max(6.5, bar_w * share), 6.5, fill=GOOD if g["correct"] else AMBER, r=3.2)
            doc.put(f"{num(g['points'])} / {num(g['max'])}", bar_x + bar_w + 12, y, 8.6, bold=True)
            note = (tr("res_seen_zero") if g.get("revealed") else tr("res_seen") if sid in result["reveals"]
                    else tr("res_with_hint") if result["hints"].get(sid) else "")
            doc.put(note, bar_x + bar_w + 62, y + 0.6, 7.6, color=AMBER if g.get("revealed") else MUTED)
            doc.y += 15.5
        doc.hline(doc.y + 1, LEFT, RIGHT, color=LINE)
        doc.y += 6
        doc.put(tr("res_total"), LEFT, doc.y, 8.8, bold=True)
        doc.put(f"{score} / 100", bar_x + bar_w + 12, doc.y, 8.8, bold=True, color=PRIMARY)
        doc.y += 16

    if points_first_page:
        points_table()

    # ---- page 2: every entry next to the correct answer – one page, the font adapts
    doc.new_page()
    if not points_first_page:
        points_table()
        doc.y += 6
    section(tr("res_detail"))
    widths = [176, 140, 140, RIGHT - LEFT - 456]
    blocks = []
    for step, g in graded:
        rows = review_rows(ex, step, answers, g["checks"], lang)
        notes = [tr("points_of", got=num(g["points"]), max=num(g["max"]))]
        if g.get("revealed"):
            notes.append(tr("res_seen_zero"))
        elif step["id"] in result["reveals"]:
            notes.append(tr("res_seen"))
        elif result["hints"].get(step["id"]):
            notes.append(tr("res_with_hint"))
        blocks.append((step_title(ex, step, lang), " · ".join(notes), g, rows))

    def measure(size):
        line, pad = size * 1.3, size * 0.32
        total = line + 2 * pad + 2    # column titles
        for _, _, _, rows in blocks:
            total += line + 2 * pad + 5
            for cells in rows:
                n = max(len(wrap(str(c), size, w - 2 * pad)) for c, w in zip(cells[:3], widths))
                total += n * line + 2 * pad
        return total

    size = next((sz for sz in (8.6, 8.2, 7.8, 7.4, 7.0, 6.6, 6.2) if doc.y + measure(sz) <= BOTTOM), 6.2)
    line, pad = size * 1.3, size * 0.32
    xs = [LEFT + sum(widths[:i]) for i in range(len(widths))]
    for x, title in zip(xs, [tr("res_item"), tr("res_your"), tr("res_correct"), tr("res_ok")]):
        doc.put(title, x + pad, doc.y + pad, size * 0.95, bold=True, color=MUTED)
    doc.y += line + 2 * pad
    doc.hline(doc.y, LEFT, RIGHT, color=INK, lw=0.6)
    doc.y += 2
    for title, note, g, rows in blocks:
        doc.room(line + 2 * pad + 5 + line + 2 * pad)
        doc.y += 3
        doc.box(LEFT, doc.y, RIGHT - LEFT, line + 2 * pad, fill=PANEL, r=3)
        doc.put(title, LEFT + pad + 2, doc.y + pad, size + 0.2, bold=True)
        doc.put(note, RIGHT - pad - 2, doc.y + pad + 0.3, size * 0.95, bold=g["correct"],
                color=GOOD if g["correct"] else AMBER if g.get("revealed") else INK, ha="right")
        doc.y += line + 2 * pad + 2
        for label, mine, right, ok in rows:
            wrapped = [wrap(str(c), size, w - 2 * pad) for c, w in zip((label, mine, right), widths)]
            h = max(len(w_) for w_ in wrapped) * line + 2 * pad
            doc.room(h)
            if not ok:
                doc.rect(LEFT, doc.y, RIGHT - LEFT, h, fill=BAD_ROW)
            for x, lines_, color in zip(xs, wrapped, (INK, INK, GOOD if not ok else INK)):
                for n, text in enumerate(lines_):
                    doc.put(text, x + pad, doc.y + pad + n * line - 0.5, size, color=color)
            doc.put("✓" if ok else "✗", xs[3] + widths[3] / 2, doc.y + pad - 0.5, size, bold=True, color=GOOD if ok else BAD, ha="center")
            doc.y += h
            doc.hline(doc.y, LEFT, RIGHT, color=LINE, lw=0.5)

    return doc.save(f"OptiSense · {tr('res_title')} · {st['title']}", f"OptiSense – {tr('res_title')}")
