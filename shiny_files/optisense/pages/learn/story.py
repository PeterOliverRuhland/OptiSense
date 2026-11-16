"""The task text of an exercise and the names of its constraints, in the chosen language.

Generated tasks use a context (kitchen, juice bar …) with its own nouns; the sentences are
templates in texts.py. The topic fits the variable type (engine.TOPICS): what is counted is integer,
what is measured continuous. Numbers are formatted like everywhere else in OptiSense.
"""

from optisense.config import DEFAULT_NAMES
from optisense.i18n import TEXT, fmt_num, norm_lang, t
from .engine import TOPICS, integrality

BOUND = {"<=": "le", ">=": "ge", "=": "eq"}


def row_labels(ex, lang):
    """Short names shown with the colour swatch: the learner's own names, otherwise NB1 / C1 …"""
    lang = norm_lang(lang)
    rows = ex["model"]["rows"]
    if ex["info"]["source"] == "own":
        return [r.get("name") or DEFAULT_NAMES["constraint"][lang].format(n=i + 1) for i, r in enumerate(rows)]
    return [DEFAULT_NAMES["constraint"][lang].format(n=i + 1) for i in range(len(rows))]


def context(ex):
    """Key prefix of the texts of a generated word problem. A mixed topic is told with its counted product as the
    integer variable: as x1 in MILP1 tasks (_ca), as x2 in MILP2 tasks (_ac)."""
    topic = ex["info"]["topic"]
    if TOPICS[topic][0] != "mix":
        return f"learn_ctx_{topic}"
    return f"learn_ctx_{topic}_" + ("ca" if integrality(ex["model"])[0] else "ac")


def resource(ctx, role, sense):
    """The resource a row stands for: r1, r2 – or r3, the third resource of a mixed topic, where pieces and
    kilograms cannot be added up; None for a total like “at most 12 liters together”."""
    if role in ("r1", "r2"):
        return role
    return "r3" if f"{ctx}_r3{sense}" in TEXT else None


def row_names(ex, lang):
    """What a constraint stands for (resource or total) – only for generated text tasks and the tutorial."""
    info = ex["info"]
    rows = ex["model"]["rows"]
    if info["source"] == "tutorial":
        return [t(lang, f"learn_tut_rn{i + 1}") for i in range(len(rows))]
    if info["source"] != "generated" or ex["options"].get("form") != "text":
        return [None] * len(rows)
    sense, ctx = ex["model"]["sense"], context(ex)
    out = []
    for r in rows:
        res = resource(ctx, r.get("role", "r1"), sense)
        out.append(t(lang, f"{ctx}_{res}{sense}" if res else "learn_rn_total"))
    return out


def story(ex, lang):
    """{title, intro, sought: [x1, x2], objective, fname (what F stands for), rows: [sentence per constraint], domain,
    question} for text tasks; {title, question} for tasks given as formulas (the browser shows the model instead)."""
    lang = norm_lang(lang)
    info, m = ex["info"], ex["model"]
    n = lambda v: fmt_num(v, lang)  # noqa: E731
    if info["source"] == "tutorial":
        return {"title": t(lang, "learn_tut_title"), "intro": t(lang, "learn_tut_intro"),
                "sought": [t(lang, "learn_tut_var1"), t(lang, "learn_tut_var2")],
                "objective": t(lang, "learn_tut_obj"), "fname": t(lang, "learn_tut_fname"),
                "rows": [t(lang, f"learn_tut_row{i + 1}") for i in range(3)],
                "domain": [t(lang, "learn_tut_domain")], "question": t(lang, "learn_tut_q")}
    if info["source"] == "own":
        return {"title": t(lang, "learn_own_title"), "question": t(lang, "learn_story_q_math")}
    if ex["options"].get("form") != "text":
        return {"title": t(lang, "learn_math_title"), "question": t(lang, "learn_story_q_math")}
    ctx = context(ex)
    sense = m["sense"]
    word = lambda field: t(lang, f"{ctx}_{field}")  # noqa: E731
    rows = []
    for r in m["rows"]:
        res = resource(ctx, r.get("role", "r1"), sense)
        if res:
            rows.append(t(lang, f"learn_row_{BOUND[r['op']]}", res=word(f"{res}{sense}"), unit=word(f"u{res[1]}{sense}"),
                          a1=n(r["a"][0]), a2=n(r["a"][1]), one1=word("one1"), one2=word("one2"), b=n(r["b"])))
        else:
            rows.append(t(lang, f"learn_row_total_{BOUND[r['op']]}", b=n(r["b"]), all=word("all"),
                          pl1=word("pl1"), pl2=word("pl2")))
    # what is counted is whole (“3 tables – not 3.5”), what is measured may be a fraction (“2.5 liters”)
    domain = [t(lang, "learn_dom_int", n=j + 1, pl=word(f"pl{j + 1}"), whole=n(3), half=n(3.5)) if k else
              t(lang, "learn_dom_con", n=j + 1, dom=word(f"dom{j + 1}"), unit=word(f"unit{j + 1}"), ex=n(2.5))
              for j, k in enumerate(integrality(m))]
    # some topics have their own story for cost problems, or their own sentence on what limits the plan
    setting = word(f"setting{sense}") if f"{ctx}_setting{sense}" in TEXT else word("setting")
    limits = word(f"ctx{sense}") if f"{ctx}_ctx{sense}" in TEXT else t(lang, f"learn_story_ctx_{sense}")
    return {"title": word("title"), "intro": " ".join([setting, word(f"goal{sense}"), limits]),
            "sought": [word("var1"), word("var2")],
            "objective": word(f"c{sense}").format(c1=n(m["c"][0]), c2=n(m["c"][1])), "fname": word(f"f{sense}"),
            "rows": rows, "domain": domain,
            "question": t(lang, "learn_story_q")}
