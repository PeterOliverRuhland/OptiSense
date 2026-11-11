"""The tab “Learn & practise” (drawn by www/learn.js): exercises, checks, hints, solutions, evaluation.

The browser sends {id, action, lang, …} as input.learn_req and receives {id, ok, data | error} as the
custom message "os-learn". The exercise and its expected answers stay in this session. The problem
from “Model & solution” is offered as an own exercise; the custom message "os-learn-own" keeps the
start page's preview of it up to date. After handing in, the evaluation can be fetched as a PDF
(report.py) from an address of this session.
"""

import asyncio
import math

import numpy as np
from shiny import reactive
from starlette.responses import PlainTextResponse, Response

from optisense.config import constraint_color
from optisense.i18n import norm_lang, t

from . import engine, report, solution, story, tutorial
from .engine import LearnError

OPS = {"≤": "<=", "≥": ">=", "=": "="}


def safe(value):
    """JSON-safe values: numpy numbers become floats, ±∞ the strings '∞' and '−∞'."""
    if isinstance(value, np.generic):
        return safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return "∞" if value > 0 else "−∞"
    if isinstance(value, dict):
        return {k: safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [safe(v) for v in value]
    return value


def clean_answers(raw):
    """{step: {key: text}} with short strings only."""
    if not isinstance(raw, dict):
        return {}
    return {str(sid): {str(k): str(v)[:40] for k, v in values.items()} for sid, values in raw.items()
            if isinstance(values, dict)}


def register(ctx):
    input, session = ctx.input, ctx.session
    state = {}
    recent = []   # ids of the last practice tasks of this session, so the next one is a different task

    def reset(ex=None):
        state.clear()
        # own: steps that were already completely right before "Solution" was pressed – they keep their points
        state.update(ex=ex, hints={}, reveals=set(), own=set(), first={}, result=None, answers={}, tz=0, pdf={})

    reset()

    def own_model():
        """The active objective function and constraints of “Model & solution” as an exercise model."""
        obj, cons = ctx.active_objective(), ctx.active_constraints()
        if obj is None or not cons:
            return None, None
        vt = ctx.var_types()
        model = {"c": [obj["c1"], obj["c2"]], "sense": obj["sense"],
                 "kind": engine.kind_of(vt["x1"] == "int", vt["x2"] == "int"),
                 "rows": [{"a": [c["a1"], c["a2"]], "op": OPS.get(c["op"], c["op"]), "b": c["b"], "name": c["name"]}
                          for c in cons]}
        return model, [constraint_color(c["color_index"]) for c in cons]

    def texts(lang):
        """Everything of the exercise that depends on the language."""
        ex = state["ex"]
        out = {"story": story.story(ex, lang), "labels": story.row_labels(ex, lang), "names": story.row_names(ex, lang),
               "solutions": {sid: solution.lines(ex, engine.step_by_id(ex, sid), lang) for sid in state["reveals"]}}
        if state["result"] is not None:
            out["resultSolutions"] = solution.all_lines(ex, lang)
            out["resultCorrect"] = correct_texts(lang)
        return out

    def correct_texts(lang):
        """After handing in: the correct answer of every field as text, for the column “Correct answer”."""
        ex, values = state["ex"], state["result"]["values"]
        return {s["id"]: {q["key"]: report.shown(ex, q, values[s["id"]].get(q["key"]), lang) for q in s["questions"]}
                for s in ex["steps"]}

    def public(lang):
        ex = state["ex"]
        m = ex["model"]
        data = {"source": ex["info"]["source"], "options": ex["options"], "steps": engine.public_steps(ex),
                "extent": ex["extent"], "points": ex["points"], "testPoints": ex["test_points"],
                "colors": ex.get("colors") or [constraint_color(i) for i in range(len(m["rows"]))]}
        if ex["options"].get("form") != "text":
            data["model"] = {"c": m["c"], "sense": m["sense"], "kind": m["kind"],
                             "rows": [{"a": r["a"], "op": r["op"], "b": r["b"]} for r in m["rows"]]}
        data.update(texts(lang))
        return data

    def current_step(req):
        ex = state["ex"]
        if ex["options"]["mode"] == "exam":
            raise LearnError("err_exam")
        step = engine.step_by_id(ex, req.get("step"))
        if step is None:
            raise LearnError("err_request")
        return ex, step

    def handle(req, lang):
        action = req.get("action")
        if action in ("create", "own", "tutorial"):
            if action == "tutorial":
                ex = tutorial.create()
            elif action == "own":
                model, colors = own_model()
                if model is None:
                    raise LearnError("err_own_empty")
                ex = engine.make_exercise(engine.normalize_options(req.get("options")), model, {"source": "own"})
                ex["colors"] = colors
            else:
                ex = engine.make_exercise(engine.normalize_options(req.get("options")), avoid=recent[-5:])
                recent.append(ex["info"]["task"])
            reset(ex)
            return public(lang)
        if action == "quit":
            reset()
            return {}
        if state["ex"] is None:
            raise LearnError("err_expired")
        answers = clean_answers(req.get("answers"))
        if action == "texts":
            return texts(lang)
        if action == "check":
            ex, step = current_step(req)
            grade = engine.grade_step(ex, step, answers.get(step["id"]), answers, lang)
            state["first"].setdefault(step["id"], {**grade, "via": "check"})
            return grade
        if action == "hint":
            ex, step = current_step(req)
            grade = engine.grade_step(ex, step, answers.get(step["id"]), answers, lang)
            reply, seen = engine.hint_reply(engine.hints_for(ex, step, grade), state["hints"].get(step["id"], 0))
            if seen:
                state["hints"][step["id"]] = seen
            return reply
        if action == "solution":
            # the answers go into the fields; what the learner had entered stays their first attempt
            ex, step = current_step(req)
            # the solution builds on the steps before: they must be filled in (right or wrong does not matter)
            if engine.unfilled_before(ex, step, answers):
                raise LearnError("err_prev_steps")
            before = engine.grade_step(ex, step, answers.get(step["id"]), answers, lang)
            state["first"].setdefault(step["id"], {**before, "via": "solution"})
            if before["correct"]:
                state["own"].add(step["id"])
            state["reveals"].add(step["id"])
            values = engine.solution_values(ex, step, answers, lang)
            return {"values": values, "lines": solution.lines(ex, step, lang),
                    "grade": engine.grade_step(ex, step, values, {**answers, step["id"]: values}, lang)}
        if action == "submit":
            ex = state["ex"]
            if state["result"] is None:
                grades = [engine.grade_step(ex, s, answers.get(s["id"]), answers, lang) for s in ex["steps"]]
                grades = engine.without_solutions(ex, grades, state["reveals"], state["own"])
                m = ex["model"]
                # values: the correct entries of every step, model: the correct model – for the column “Correct
                # answer” and the graphical solution on the evaluation page (now that the task is handed in)
                state["result"] = {"score": min(100, round(sum(g["points"] for g in grades), 1)), "grades": grades,
                                   "hints": dict(state["hints"]), "reveals": sorted(state["reveals"]),
                                   "first": dict(state["first"]),
                                   "values": {s["id"]: engine.solution_values(ex, s, answers, lang) for s in ex["steps"]},
                                   "model": {"c": m["c"], "sense": m["sense"], "kind": m["kind"],
                                             "rows": [{"a": r["a"], "op": r["op"], "b": r["b"]} for r in m["rows"]]}}
                # what was graded goes into the PDF; tz: the browser's offset to UTC in minutes, for the time on it
                state.update(answers=answers, tz=req.get("tz"), pdf={})
            return {**state["result"], "solutions": solution.all_lines(ex, lang), "correct": correct_texts(lang),
                    "pdf": pdf_url}
        raise LearnError("err_request")

    async def evaluation_pdf(request):
        """The evaluation of the handed-in exercise as a PDF file. Made once per language, in a worker thread:
        it takes about half a second, during which the other learners on this server are not kept waiting."""
        ex, result, made = state["ex"], state["result"], state["pdf"]
        if ex is None or result is None:
            return PlainTextResponse("Not found", 404)
        lang = norm_lang(request.query_params.get("lang"))
        if lang not in made:
            made[lang] = await asyncio.to_thread(report.pdf, ex, result, state["answers"], lang, state["tz"])
        name = f"OptiSense-{t(lang, 'learn_res_title')}.pdf"
        return Response(made[lang], media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store"})

    pdf_url = session.dynamic_route("learn_pdf", evaluation_pdf)

    @reactive.effect
    @reactive.event(input.learn_req)
    async def _request():
        req = input.learn_req()
        if not isinstance(req, dict):
            return
        lang = norm_lang(req.get("lang"))
        try:
            msg = {"ok": True, "data": safe(handle(req, lang))}
        except LearnError as e:
            msg = {"ok": False, "error": t(lang, f"learn_{e.key}", **e.params)}
        except (KeyError, TypeError, ValueError, IndexError, ZeroDivisionError, OverflowError):
            msg = {"ok": False, "error": t(lang, "learn_err_request")}
        await session.send_custom_message("os-learn", {"id": req.get("id"), **msg})

    @reactive.effect
    async def _own_preview():
        model, colors = own_model()
        payload = {"ready": False}
        if model is not None:
            payload = {"ready": True, "c": model["c"], "sense": model["sense"], "kind": model["kind"],
                       "rows": [{**r, "color": col} for r, col in zip(model["rows"], colors)]}
        await session.send_custom_message("os-learn-own", safe(payload))
