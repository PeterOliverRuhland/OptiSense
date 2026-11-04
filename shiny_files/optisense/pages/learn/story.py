"""The task text of an exercise and the names of its constraints, in the chosen language.

Generated tasks use a context (kitchen, workshop …) with its own nouns; the sentences are
templates in texts.py. Numbers are formatted like everywhere else in OptiSense.
"""

from optisense.config import DEFAULT_NAMES
from optisense.i18n import fmt_num, norm_lang, t
from .engine import integrality

BOUND = {"<=": "le", ">=": "ge", "=": "eq"}


def row_labels(ex, lang):
    """Short names shown with the colour swatch: the learner's own names, otherwise NB1 / C1 …"""
    lang = norm_lang(lang)
    rows = ex["model"]["rows"]
    if ex["info"]["source"] == "own":
        return [r.get("name") or DEFAULT_NAMES["constraint"][lang].format(n=i + 1) for i, r in enumerate(rows)]
    return [DEFAULT_NAMES["constraint"][lang].format(n=i + 1) for i in range(len(rows))]


def row_names(ex, lang):
    """What a constraint stands for (resource or total) – only for generated text tasks and the tutorial."""
    info = ex["info"]
    rows = ex["model"]["rows"]
    if info["source"] == "tutorial":
        return [t(lang, f"learn_tut_rn{i + 1}") for i in range(len(rows))]
    if info["source"] != "generated" or ex["options"].get("form") != "text":
        return [None] * len(rows)
    sense = ex["model"]["sense"]
    out = []
    for r in rows:
        role = r.get("role", "r1")
        out.append(t(lang, f"learn_ctx_{info['topic']}_{role}{sense}" if role in ("r1", "r2") else "learn_rn_total"))
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
    ctx = f"learn_ctx_{info['topic']}"
    sense = m["sense"]
    word = lambda field: t(lang, f"{ctx}_{field}")  # noqa: E731
    rows = []
    for r in m["rows"]:
        role = r.get("role", "r1")
        if role in ("r1", "r2"):
            rows.append(t(lang, f"learn_row_{BOUND[r['op']]}", res=word(f"{role}{sense}"), unit=word(f"u{role[1]}{sense}"),
                          a1=n(r["a"][0]), a2=n(r["a"][1]), one1=word("one1"), one2=word("one2"), b=n(r["b"])))
        else:
            rows.append(t(lang, f"learn_row_total_{BOUND[r['op']]}", b=n(r["b"]), all=word("all"),
                          pl1=word("pl1"), pl2=word("pl2")))
    domain = [t(lang, "learn_dom_int" if k else "learn_dom_con", pl=word(f"pl{j + 1}"), n=j + 1)
              for j, k in enumerate(integrality(m))]
    return {"title": word("title"), "intro": " ".join([word("setting"), word(f"goal{sense}"), t(lang, f"learn_story_ctx_{sense}")]),
            "sought": [word("var1"), word("var2")],
            "objective": word(f"c{sense}").format(c1=n(m["c"][0]), c2=n(m["c"][1])), "fname": word(f"f{sense}"),
            "rows": rows, "domain": domain,
            "question": t(lang, "learn_story_q")}
