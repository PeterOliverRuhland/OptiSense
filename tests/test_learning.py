"""Tests for the tab “Learn & practise”: exercise generation, grading, texts in all languages.

Run from the repository root:  python -m unittest discover -s tests
"""
import copy
import itertools
import json
import math
import os
import re
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shiny_files"))

from optisense import i18n  # noqa: E402
from optisense.pages.learn import engine, report, solution, story, tutorial  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "shiny_files")


def example(kind="LP"):
    return engine.validate({"c": [3, 4], "sense": "max", "kind": kind,
                            "rows": [{"a": [1, 0], "op": "<=", "b": 4}, {"a": [0, 1], "op": "<=", "b": 3},
                                     {"a": [1, 1], "op": "<=", "b": 5}]})


def step(ex, sid):
    return engine.step_by_id(ex, sid)


def typed(value, lang):
    """A value as the browser puts it into a field (learn.js fmtInput): 4 decimals, decimal comma in German."""
    if not isinstance(value, float):
        return str(value)
    if math.isinf(value):
        return "∞" if value > 0 else "−∞"
    r = round(value * 1e4) / 1e4
    text = str(int(r)) if r.is_integer() else repr(r)
    return text.replace(".", ",") if lang == "de" else text


def exercises():
    """Generated tasks of every kind, the guided example and own tasks (also mixed-integer)."""
    out = [tutorial.create()]
    for form, kind, difficulty, seed in itertools.product(("text", "math"), ("LP", "ILP", "MILP"), ("easy", "medium"), range(6)):
        opts = engine.normalize_options({"form": form, "kind": kind, "difficulty": difficulty})
        opts["seed"] = seed
        out.append(engine.make_exercise(opts))
    for kind in ("LP", "ILP", "MILP1", "MILP2"):
        out.append(engine.make_exercise({}, example(kind), {"source": "own"}))
    for form, task in itertools.product(("text", "math"), ("burger", "shawarma")):   # stories of their own
        out.append(engine.make_exercise(engine.normalize_options({"form": form, "kind": "ILP", "difficulty": "medium", "task": task})))
    return out


class GeneratorTests(unittest.TestCase):
    def test_generated_tasks_are_solvable_and_worth_100_points(self):
        for kind, difficulty, seed in itertools.product(("LP", "ILP", "MILP"), ("easy", "medium"), range(12)):
            opts = engine.normalize_options({"kind": kind, "difficulty": difficulty, "form": "text"})
            opts["seed"] = seed
            ex = engine.make_exercise(opts)
            m = ex["model"]
            self.assertIn(m["kind"], ("MILP1", "MILP2") if kind == "MILP" else (kind,))
            self.assertEqual(ex["solution"]["status"], "optimal")
            self.assertTrue(engine.feasible(m, ex["solution"]["x"]))
            self.assertEqual(sum(s["points"] for s in ex["steps"]), 100)
            self.assertEqual(len(m["rows"]), 2 if difficulty == "easy" else 3)
            if m["kind"] == "ILP" and ex["info"].get("story"):   # burger, shawarma: the LP corner is already whole
                self.assertEqual(engine.solve({**m, "kind": "LP"})["x"], ex["solution"]["x"])
            elif m["kind"] == "ILP":   # independent check by enumeration
                values = [np.dot(m["c"], [i, j]) for i in range(60) for j in range(60) if engine.feasible(m, [i, j])]
                best = max(values) if m["sense"] == "max" else min(values)
                self.assertAlmostEqual(ex["solution"]["z"], best)

    def test_fifteen_named_tasks_five_per_variable_type(self):
        # Robin, 2026-11-17: one field “Task” lists 15 tasks by name, integer first – 5 integer (Burger and Shawarma among
        # them), 5 continuous, 5 mixed; only those of the chosen variable type can be picked. Every task keeps its topic.
        listed = engine.task_list()
        self.assertEqual([t["kind"] for t in listed], ["ILP"] * 5 + ["LP"] * 5 + ["MILP"] * 5)
        self.assertEqual(len({t["name"] for t in listed}), 15)
        for t in listed:
            self.assertIn(f"learn_task_{t['name']}" if t["name"] in ("burger", "shawarma") else f"learn_topic_{t['name']}", i18n.TEXT)
            self.assertEqual(set(t["levels"]), {"easy", "medium"}, t["name"])   # every task on both levels
        for (difficulty, kind), tasks in engine.POOL.items():
            for task in tasks:
                if task.get("story"):
                    self.assertNotIn("topic", task)
                    continue
                self.assertIn(task["topic"], engine.topics_for(kind), task["id"])   # counted → integer, measured → continuous
                if task["sense"] == "min":
                    self.assertIn(task["topic"], engine.MIN_TOPICS, task["id"])   # only topics that make sense as costs
                for seed in range(3):
                    ex = engine.make_exercise({**engine.normalize_options({"kind": kind, "difficulty": difficulty, "task": task["topic"]}), "seed": seed})
                    self.assertEqual((ex["info"]["task"], ex["info"]["topic"]), (task["id"], task["topic"]))
        senses = {d: {t["sense"] for (dd, _), ts in engine.POOL.items() if dd == d for t in ts} for d in ("easy", "medium")}
        self.assertEqual(senses, {"easy": {"max"}, "medium": {"max", "min"}})   # minimisation only on level 2
        # the start page gets this list (pages/learn/ui.py) and starts with integer
        with open(os.path.join(ROOT, "www", "learn.js"), encoding="utf-8") as f:
            js = f.read()
        self.assertIn('kind: "ILP", mode: "practice"', js)
        self.assertRegex(js, r'seg\("o-kind", \[\["ILP"')

    def test_options_are_reduced_to_known_values(self):
        # unknown and removed choices (advanced level, simplex) fall back to the defaults; mixed is chosen as “MILP”
        opts = engine.normalize_options({"mode": "cheat", "kind": "MILP1", "difficulty": "hard", "topic": "space", "task": "x", "simplex": 1})
        self.assertEqual((opts["mode"], opts["kind"], opts["difficulty"], opts["task"]), ("practice", "ILP", "easy", "random"))   # integer first
        self.assertNotIn("topic", opts)   # the topic comes with the task
        self.assertNotIn("simplex", opts)
        self.assertNotIn("method", engine.normalize_options({"method": "calc"}))   # the graph and the calculation always belong together
        self.assertEqual(engine.normalize_options({"kind": "MILP"})["kind"], "MILP")

    def test_integrality_matters_in_generated_integer_tasks(self):
        kinds = set()
        for kind, seed in itertools.product(("ILP", "MILP"), range(20)):
            opts = engine.normalize_options({"kind": kind, "difficulty": "easy" if seed % 2 else "medium"})
            opts["seed"] = seed
            ex = engine.make_exercise(opts)
            m = ex["model"]
            kinds.add(m["kind"])
            relaxed = engine.solve({**m, "kind": "LP"})
            if ex["info"].get("story"):   # burger and shawarma: the optimal corner is whole, the corner step stays
                self.assertTrue(engine.feasible(m, relaxed["x"]), ex["info"])
                continue
            self.assertFalse(engine.feasible(m, relaxed["x"]), (kind, seed))   # just solving the LP would be wrong
            self.assertNotIn("corner", [s["id"] for s in ex["steps"]])
        self.assertTrue({"MILP1", "MILP2"} <= kinds)   # either variable can be the integer one

    def test_fixed_pool_has_good_tasks_for_every_level_and_variable_type(self):
        ids = set()
        for (difficulty, kind), tasks in engine.POOL.items():
            self.assertEqual(len(tasks), 5, (difficulty, kind))   # 5 per level and variable type
            if kind == "MILP":
                self.assertEqual({t["kind"] for t in tasks}, {"MILP1", "MILP2"})   # either variable can be the integer one
            for task in tasks:
                ids.add(task["id"])
                self.assertEqual(len(task["rows"]), 2 if difficulty == "easy" else 3, task["id"])
                if difficulty == "easy":
                    self.assertEqual(task["sense"], "max", task["id"])
                ex = engine.make_exercise(engine.normalize_options({"kind": kind, "difficulty": difficulty, "task": engine.task_name(task)}))
                self.assertEqual(ex["info"]["task"], task["id"])
                m, sol = ex["model"], ex["solution"]
                # every number the learner works out is whole or ,5: axis intercepts, x1, x2, F, slack (no 8,333 or 1,667)
                for step in ex["steps"]:
                    if task.get("story") and step["id"] in ("objective", "constraints"):
                        continue   # read from the story: 100 g are 0.1 kg; what is worked out is checked as for all
                    for q in step["questions"]:
                        v = q["expected"]
                        if isinstance(v, (int, float)) and not isinstance(v, bool):
                            self.assertTrue(engine.half_steps(v), (task["id"], q["key"], v))
                self.assertTrue(engine.half_steps(*(r["b"] for r in m["rows"])), task["id"])
                # every constraint bounds the region, and with integer variables the LP optimum is not allowed
                used = {i for c in engine.corners(m) for i in c[:2]}
                self.assertTrue(set(range(len(m["rows"]))) <= used, task["id"])
                if task.get("story"):   # burger, shawarma: whole optimal corner, told with their own story
                    self.assertEqual(engine.solve({**m, "kind": "LP"})["x"], sol["x"], task["id"])
                    self.assertIn("corner", [s["id"] for s in ex["steps"]])
                elif kind != "LP":
                    self.assertFalse(engine.feasible(m, engine.solve({**m, "kind": "LP"})["x"]), task["id"])
                else:
                    self.assertEqual(len(engine.optimal_corners(m)), 1, task["id"])   # one optimal corner
                self.assertGreater(min(sol["x"]), 0, task["id"])
        self.assertEqual(len(ids), 30)

    def test_hints_are_counted_as_they_really_are(self):
        opts = engine.normalize_options({"form": "text", "difficulty": "medium", "kind": "LP", "seed": 2})
        ex = engine.make_exercise(opts)
        empty = {s["id"]: engine.hints_for(ex, s, engine.grade_step(ex, s, {}, {})) for s in ex["steps"]}
        self.assertEqual(empty["constraints"], ["row"])          # one hint for all rows – so “Hint 1 of 1”
        self.assertEqual(empty["objective"], ["sense", "vt", "c"])
        # every click shows one more, up to the real number; after that nothing new
        reply, seen = engine.hint_reply(empty["objective"], 0)
        self.assertEqual((reply["level"], reply["total"], reply["ids"], reply["more"], reply["last"]), (1, 3, ["sense"], True, False))
        reply, seen = engine.hint_reply(empty["objective"], seen)
        self.assertEqual((reply["level"], reply["ids"]), (2, ["sense", "vt"]))
        reply, seen = engine.hint_reply(empty["objective"], engine.hint_reply(empty["objective"], seen)[1])
        self.assertEqual((reply["level"], reply["total"], reply["more"], reply["last"]), (3, 3, False, True))
        reply, seen = engine.hint_reply(empty["constraints"], 0)
        self.assertEqual((reply["level"], reply["total"], reply["more"]), (1, 1, False))
        self.assertTrue(engine.hint_reply(empty["constraints"], seen)[0]["last"])   # a second click: “no further hints”
        self.assertEqual(engine.hint_reply([], 0)[0]["level"], 0)                    # everything right: no hint needed

    def test_a_filled_in_solution_scores_nothing_a_hint_costs_nothing(self):
        opts = engine.normalize_options({"form": "text", "difficulty": "easy", "kind": "LP", "seed": 1})
        ex = engine.make_exercise(opts)
        answers = {}
        for s in ex["steps"]:
            answers[s["id"]] = engine.solution_values(ex, s, answers)
        grades = [engine.grade_step(ex, s, answers[s["id"]], answers) for s in ex["steps"]]
        self.assertAlmostEqual(sum(g["points"] for g in grades), 100)
        # "lines" with its solution filled in, "region" after the learner had it right already: only "lines" loses its points
        out = engine.without_solutions(ex, grades, {"lines", "region"}, own={"region"})
        lines = next(g for s, g in zip(ex["steps"], out) if s["id"] == "lines")
        region = next(g for s, g in zip(ex["steps"], out) if s["id"] == "region")
        self.assertEqual((lines["points"], lines["correct"], lines["revealed"]), (0, False, True))
        self.assertEqual(region["points"], next(g for s, g in zip(ex["steps"], grades) if s["id"] == "region")["points"])
        self.assertAlmostEqual(sum(g["points"] for g in out), 100 - lines["max"])
        # the guided example is not graded: there the solution costs nothing
        tut = tutorial.create()
        tg = [engine.grade_step(tut, s, {}, {}) for s in tut["steps"]]
        self.assertEqual(engine.without_solutions(tut, tg, {s["id"] for s in tut["steps"]}), tg)

    def test_every_topic_fits_the_variable_type_so_nobody_sells_half_a_smoothie(self):
        # Robin, 2026-11-16: what is counted (shelves, cakes, trips) is integer, what is measured (liters, hectares,
        # kg) continuous. Every task of the pool with every topic it can get, in both languages.
        words = {"en": ("whole numbers only", "fractions allowed", "number of"), "de": ("nur ganze Zahlen", "Bruchteile erlaubt", "Anzahl")}
        measured = ("liters", "hectares", "kilograms", "tons", "minutes")
        combinations = 0
        for task in (t for tasks in engine.POOL.values() for t in tasks if not t.get("story")):   # burger, shawarma: own story
            for topic in [task["topic"]]:
                rows = [{"a": [a1, a2], "op": op, "b": b, "role": ("r1", "r2", "total")[i]} for i, (a1, a2, op, b) in enumerate(task["rows"])]
                m = engine.validate({"c": list(task["c"]), "sense": task["sense"], "kind": task["kind"], "rows": rows})
                ex = {"model": m, "info": {"source": "generated", "topic": topic, "task": task["id"]}, "options": {"form": "text"}}
                combinations += 1
                for lang, (whole, fraction, count) in words.items():
                    st = story.story(ex, lang)
                    text = json.dumps([st, story.row_names(ex, lang)], ensure_ascii=False)
                    self.assertNotIn("learn_", text)
                    self.assertIsNone(re.search(r"\{[a-z0-9_]+\}", text), text)
                    for j, integer in enumerate(engine.integrality(m)):
                        self.assertIn(whole if integer else fraction, st["domain"][j], (task["id"], topic, lang))
                        self.assertEqual(st["sought"][j].startswith(count), bool(integer), (task["id"], topic, st["sought"][j]))
                        if lang == "en" and not integer:
                            self.assertTrue(any(u in st["sought"][j] for u in measured), (task["id"], topic, st["sought"][j]))
                    if engine.TOPICS[topic][0] == "mix" and len(task["rows"]) == 3:
                        # pieces and kilograms cannot be added up: the third row is a resource, not a total
                        self.assertNotIn(i18n.t(lang, "learn_rn_total"), story.row_names(ex, lang))
        self.assertEqual(combinations, sum(1 for tasks in engine.POOL.values() for t in tasks if not t.get("story")))

    def test_every_topic_tells_every_story_it_is_used_for(self):
        # all 45 topics (topics.py, 2026-11-17): each in every variant – maximisation, costs if it has them, and for a
        # mixed topic both orders – with two resources and the total (or third resource), in both languages
        used = {t["topic"] for tasks in engine.POOL.values() for t in tasks if t.get("topic")}
        self.assertTrue(used <= set(engine.TOPICS) and len(used) == 13)   # the rest are stories in reserve
        measured = ("liters", "hectares", "kilograms", "tons", "minutes")
        for topic, (vt, costs) in engine.TOPICS.items():
            kinds = {"int": ["ILP"], "con": ["LP"], "mix": ["MILP1", "MILP2"]}[vt]
            for kind, sense in itertools.product(kinds, ["max"] + (["min"] if costs else [])):
                op = "<=" if sense == "max" else ">="
                rows = [{"a": [2, 3], "op": op, "b": 28.5, "role": "r1"}, {"a": [4, 1], "op": op, "b": 30, "role": "r2"},
                        {"a": [1, 1], "op": "<=", "b": 12, "role": "total"}]
                m = engine.validate({"c": [5, 7], "sense": sense, "kind": kind, "rows": rows})
                ex = {"model": m, "info": {"source": "generated", "topic": topic, "task": "x"}, "options": {"form": "text"}}
                for lang in ("en", "de"):
                    st = story.story(ex, lang)
                    text = json.dumps([st, story.row_names(ex, lang)], ensure_ascii=False)
                    self.assertNotIn("learn_", text, (topic, kind, sense, lang))
                    self.assertIsNone(re.search(r"\{[a-z0-9_]+\}", text), (topic, kind, sense, lang, text))
                    self.assertIn("€" if lang == "de" else "₱", text) if topic not in ("advertising", "radio") or sense == "min" else None
                    for j, integer in enumerate(engine.integrality(m)):
                        if lang == "en" and not integer:
                            self.assertTrue(any(u in st["sought"][j] for u in measured), (topic, st["sought"][j]))
                self.assertIn(f"learn_topic_{topic}", i18n.TEXT)

    def test_the_start_page_lists_the_tasks_and_has_no_topic_field(self):
        # the task list comes from the server (pages/learn/ui.py); learn.js only names and sorts it
        from optisense.pages.learn import ui as learn_ui
        self.assertIn("window.OS_LEARN_TASKS = ", str(learn_ui.panel.content))
        with open(os.path.join(ROOT, "www", "learn.js"), encoding="utf-8") as f:
            js = f.read()
        self.assertIn('data-opt="task"', js)
        self.assertNotIn('data-opt="topic"', js)

    def test_practice_tasks_do_not_repeat(self):
        recent = []
        for seed in range(30):
            ex = engine.make_exercise({**engine.normalize_options({"kind": "LP"}), "seed": seed}, avoid=recent[-4:])
            self.assertNotIn(ex["info"]["task"], recent[-4:])
            recent.append(ex["info"]["task"])


class SolverTests(unittest.TestCase):
    def test_infeasible_and_unbounded_models_are_refused(self):
        bad = {"c": [1, 1], "sense": "max", "kind": "LP", "rows": [{"a": [1, 0], "op": ">=", "b": 1}]}
        with self.assertRaises(engine.LearnError) as err:
            engine.make_exercise({}, bad, {"source": "own"})
        self.assertEqual(err.exception.key, "err_unbounded")
        bad["rows"] = [{"a": [1, 1], "op": "<=", "b": 3}, {"a": [1, 1], "op": ">=", "b": 5}]
        with self.assertRaises(engine.LearnError) as err:
            engine.make_exercise({}, bad, {"source": "own"})
        self.assertEqual(err.exception.key, "err_infeasible")

    def test_numbers_as_learners_type_them(self):
        self.assertEqual(engine.number("3/4"), 0.75)
        self.assertEqual(engine.number("0,25"), 0.25)
        self.assertEqual(engine.number("1.500", "de"), 1500)
        self.assertEqual(engine.number("1,500", "en"), 1500)
        self.assertEqual(engine.number("1.5", "de"), 1.5)
        self.assertEqual(engine.number("0.500", "de"), 0.5)
        self.assertEqual(engine.number("−∞"), -math.inf)
        with self.assertRaises(engine.LearnError):
            engine.number("abc")


class GradingTests(unittest.TestCase):
    def test_tutorial_example_answers_give_100_points(self):
        ex = tutorial.create()
        answers = tutorial.ANSWERS
        total = sum(engine.grade_step(ex, s, answers.get(s["id"]), answers)["points"] for s in ex["steps"])
        self.assertAlmostEqual(total, 100)

    def test_tutorial_is_the_shawarma_stand(self):
        # Robin, 2026-11-17: a task the students do not know yet, as hard as the burgers – every value without a calculator
        ex = tutorial.create()
        self.assertEqual(ex["solution"]["x"], [200, 100])
        self.assertAlmostEqual(ex["solution"]["z"], 26000)
        self.assertTrue(engine.calculator_free(ex["model"], ex["solution"]))
        self.assertEqual(story.story(ex, "en")["title"], "Shawarma stand: regular and special shawarma")
        self.assertEqual(story.row_names(ex, "de"), ["Fladenbrot", "Fleisch", "Gemüse"])

    def test_burger_and_shawarma_are_practice_tasks(self):
        # Robin, 2026-11-17: the lecture's burger problem (the former guided task) and the guided task's shawarma stand
        # are two of the 15 integer tasks on level 2, each with its own story; a task can also be picked by its id
        opts = {"kind": "ILP", "difficulty": "medium"}
        burger = engine.make_exercise(engine.normalize_options({**opts, "task": "burger"}))
        shawarma = engine.make_exercise(engine.normalize_options({**opts, "task": "shawarma"}))
        self.assertEqual((burger["solution"]["x"], burger["solution"]["z"]), ([300, 200], 2550))
        same = lambda m: (m["c"], m["sense"], m["kind"], [(r["a"], r["op"], r["b"]) for r in m["rows"]])  # noqa: E731
        self.assertEqual(same(shawarma["model"]), same(tutorial.create()["model"]))
        self.assertEqual(story.story(burger, "en")["title"], "Burger diner: standard and luxury burgers")   # not a kitchen
        # dollars, not the euros of the slides (Robin, 2026-11-17: students in the Philippines know the dollar)
        self.assertIn("$4.50", story.story(burger, "en")["objective"])
        self.assertIn("4,50 $", story.story(burger, "de")["objective"])
        self.assertEqual(story.story(shawarma, "de"), story.story(tutorial.create(), "de"))
        self.assertEqual(story.row_names(burger, "de"), ["Brötchen", "Fleisch", "Gemüse"])
        for ex in (burger, shawarma):
            self.assertIsNone(ex["info"]["topic"])
            ids = [s["id"] for s in ex["steps"]]
            self.assertEqual(ids[ids.index("region"):ids.index("optimum") + 1], ["region", "corner", "optimum"])
        math_task = engine.make_exercise(engine.normalize_options({**opts, "task": "burger", "form": "math"}))
        self.assertEqual(story.story(math_task, "en")["title"], i18n.t("en", "learn_math_title"))
        # a task id of another level or variable type, or none, means chance – and chance can give them too
        self.assertEqual(engine.normalize_options({"kind": "LP", "difficulty": "medium", "task": "burger"})["task"], "random")
        # on level 1 with bread and meat only (Robin, 2026-11-17): no vegetables, still a whole optimal corner
        easy = {name: engine.make_exercise(engine.normalize_options({"kind": "ILP", "difficulty": "easy", "task": name}))
                for name in ("burger", "shawarma")}
        self.assertEqual((easy["burger"]["solution"]["x"], easy["burger"]["solution"]["z"]), ([225, 275], 2662.5))
        self.assertEqual((easy["shawarma"]["solution"]["x"], easy["shawarma"]["solution"]["z"]), ([200, 100], 26000))
        self.assertEqual(story.row_names(easy["burger"], "de"), ["Brötchen", "Fleisch"])
        self.assertEqual(story.row_names(easy["shawarma"], "en"), ["Pita bread", "Meat"])
        self.assertIn("corner", [s["id"] for s in easy["burger"]["steps"]])
        self.assertEqual(engine.normalize_options({**opts, "task": "<b>"})["task"], "random")
        stories = {engine.make_exercise({**engine.normalize_options(opts), "seed": s})["info"].get("story") for s in range(200)}
        self.assertEqual(stories, {None, "burger", "shawarma"})

    def test_tutorial_shawarmas_are_whole_and_keep_the_corner_step(self):
        # nobody sells half a shawarma: x1 and x2 are integer; the optimal corner is whole, so the method of the
        # lecture (objective line → corner → calculate it) stays
        ex = tutorial.create()
        self.assertEqual(ex["model"]["kind"], "ILP")
        self.assertEqual({q["key"]: q["expected"] for q in step(ex, "objective")["questions"]}["vt0"], "int")
        self.assertEqual([s["id"] for s in ex["steps"]][3:6], ["region", "corner", "optimum"])
        dom = story.story(ex, "en")["domain"][0]
        self.assertIn("whole numbers", dom)
        self.assertNotIn("continuous", dom)

    def test_the_model_is_set_up_in_two_steps(self):
        ex = tutorial.create()
        self.assertEqual([s["id"] for s in ex["steps"]][:3], ["objective", "constraints", "lines"])
        self.assertEqual([q["key"] for q in step(ex, "objective")["questions"]], ["sense", "vt0", "vt1", "c0", "c1"])
        self.assertEqual(len(step(ex, "constraints")["questions"]), 4 * 3)
        s = step(ex, "objective")   # hints only explain the part of this step
        self.assertEqual(engine.hints_for(ex, s, engine.grade_step(ex, s, {})), ["sense", "vt", "c"])
        math_task = engine.make_exercise(engine.normalize_options({"form": "math"}))
        self.assertEqual(math_task["steps"][0]["id"], "lines")

    def test_a_scaled_constraint_counts_as_correct(self):
        ex = tutorial.create()
        answers = dict(tutorial.ANSWERS["constraints"], a1_0="100", a1_1="200", b1="40000")   # meat in grams
        self.assertTrue(engine.grade_step(ex, step(ex, "constraints"), answers)["correct"])
        answers.update(a2_0="-1", a2_1="-0.5", b2="-270", op2=">=")
        self.assertTrue(engine.grade_step(ex, step(ex, "constraints"), answers)["correct"])

    def test_axis_intersections_with_parallel_lines(self):
        ex = engine.make_exercise({}, example(), {"source": "own"})
        answers = {"ax0_0": "4", "ax0_1": "–", "ax1_0": "-", "ax1_1": "3", "ax2_0": "5", "ax2_1": "5"}
        self.assertTrue(engine.grade_step(ex, step(ex, "lines"), answers)["correct"])
        answers.update(ax0_1="0", ax2_0="")
        g = engine.grade_step(ex, step(ex, "lines"), answers)
        self.assertFalse(g["checks"]["ax0_1"] or g["checks"]["ax2_0"])
        self.assertTrue(g["checks"]["ax0_0"] and g["checks"]["ax2_1"])

    def test_sides_use_the_test_point(self):
        m = engine.validate({"c": [1, 1], "sense": "min", "kind": "LP",
                             "rows": [{"a": [1, 1], "op": ">=", "b": 4}, {"a": [1, 0], "op": "<=", "b": 6}, {"a": [1, -1], "op": "=", "b": 0}]})
        ex = engine.make_exercise({}, m, {"source": "own"})
        expected = {q["key"]: q["expected"] for q in step(ex, "region")["questions"]}
        self.assertEqual([expected["side0"], expected["side1"], expected["side2"]], ["out", "in", "line"])
        self.assertNotEqual(ex["test_points"][2], [0.0, 0.0])   # (0 | 0) lies on x1 − x2 = 0

    def test_alternative_optima_and_slack_at_the_learners_point(self):
        m = example()
        m["c"] = [1, 1]
        ex = engine.make_exercise({}, m, {"source": "own"})
        answers = {"optimum": {"x": "4", "y": "1", "z": "5"}}
        self.assertTrue(engine.grade_step(ex, step(ex, "optimum"), answers["optimum"])["correct"])
        g = engine.grade_step(ex, step(ex, "slack"), {"slack0": "0", "bind0": "yes", "slack1": "2", "bind1": "no",
                                                     "slack2": "0", "bind2": "yes"}, answers)
        self.assertTrue(g["correct"], g["checks"])   # at (4 | 1): x1 ≤ 4 and x1 + x2 ≤ 5 are binding, x2 ≤ 3 is not

    def test_hints_name_the_wrong_questions(self):
        ex = tutorial.create()
        s = step(ex, "optimum")
        g = engine.grade_step(ex, s, {"x": "200", "y": "100", "z": "25000"})
        self.assertEqual(engine.hints_for(ex, s, g), ["z"])
        g = engine.grade_step(ex, s, {"x": "100", "y": "200", "z": "26000"})
        self.assertEqual(engine.hints_for(ex, s, g), ["opt_corner"])   # LP: calculated from the corner

    def test_the_filled_in_solution_earns_every_point(self):
        for ex, lang in itertools.product(exercises(), ("de", "en")):
            answers = {}
            for s in ex["steps"]:
                values = engine.solution_values(ex, s, answers, lang)
                answers[s["id"]] = {k: typed(v, lang) for k, v in values.items()}
                g = engine.grade_step(ex, s, answers[s["id"]], answers, lang)
                self.assertTrue(g["correct"], (ex["info"], ex["options"], s["id"], lang, answers[s["id"]], g["checks"]))

    def test_the_solution_follows_the_learners_optimum(self):
        m = example()
        m["c"] = [1, 1]   # every point between (4 | 1) and (2 | 3) is optimal
        ex = engine.make_exercise({}, m, {"source": "own"})
        values = engine.solution_values(ex, step(ex, "slack"), {"optimum": {"x": "4", "y": "1", "z": "5"}})
        self.assertEqual([values[f"slack{i}"] for i in range(3)], [0, 2, 0])
        self.assertEqual([values[f"bind{i}"] for i in range(3)], ["yes", "no", "yes"])

    def test_the_solution_of_the_corner_is_the_optimal_corner(self):
        ex = tutorial.create()
        values = engine.solution_values(ex, step(ex, "corner"))
        self.assertEqual((values["boundary1"], values["boundary2"]), ("0", "1"))   # pita bread and meat
        values = engine.solution_values(ex, step(ex, "optimum"), {"corner": values})
        self.assertTrue(np.allclose([values["x"], values["y"], values["z"]], [200, 100, 26000]))

    def test_the_corner_must_be_optimal(self):
        ex = tutorial.create()
        s = step(ex, "corner")
        for pair, ok in ((("0", "1"), True), (("1", "0"), True), (("0", "2"), False), (("1", "2"), False),
                         (("2", "2"), False), (("3", "4"), False), (("", "2"), False), (("9", "1"), False)):
            g = engine.grade_step(ex, s, {"boundary1": pair[0], "boundary2": pair[1]})
            self.assertEqual(g["correct"], ok, pair)

    def test_every_optimal_corner_counts_and_the_optimum_follows_it(self):
        m = example()
        m["c"] = [1, 1]   # (4 | 1) on rows 0 and 2, (2 | 3) on rows 1 and 2: both optimal
        ex = engine.make_exercise({}, m, {"source": "own"})
        for pair, point in ((("0", "2"), [4, 1]), (("1", "2"), [2, 3])):
            answers = {"boundary1": pair[0], "boundary2": pair[1]}
            self.assertTrue(engine.grade_step(ex, step(ex, "corner"), answers)["correct"])
            values = engine.solution_values(ex, step(ex, "optimum"), {"corner": answers})
            self.assertEqual([values["x"], values["y"]], point)
        self.assertIn(i18n.t("de", "learn_sol_corner_alt"), solution.lines(ex, step(ex, "corner"), "de"))

    def test_the_slack_step_asks_slack_and_binding_only(self):
        ex = tutorial.create()
        keys = [q["key"] for q in step(ex, "slack")["questions"]]
        self.assertEqual(keys, ["slack0", "bind0", "slack1", "bind1", "slack2", "bind2"])
        answers = {"optimum": tutorial.ANSWERS["optimum"]}
        g = engine.grade_step(ex, step(ex, "slack"), dict(tutorial.ANSWERS["slack"], bind2="yes"), answers)
        self.assertEqual(engine.hints_for(ex, step(ex, "slack"), g), ["bind"])   # vegetables have 2 kg left: not binding
        self.assertNotIn("sensitivity", engine.normalize_options({"sensitivity": True}))

    def test_word_problems_name_the_objective(self):
        for ex in exercises():
            st = story.story(ex, "de")
            if ex["options"].get("form") == "text":
                self.assertTrue(st["fname"] and not st["fname"].startswith("learn_"), (ex["info"], st))
            else:
                self.assertNotIn("fname", st)
        self.assertEqual(story.story(tutorial.create(), "de")["fname"], "Umsatz")

    def test_only_lp_tasks_and_the_whole_corner_tasks_have_a_corner_step(self):
        # the guided task and the lecture's burger problem are integer, but their optimal corner is whole
        for ex in exercises():
            ids = [s["id"] for s in ex["steps"]]
            whole_corner = ex["info"]["source"] == "tutorial" or bool(ex["info"].get("story"))
            self.assertEqual("corner" in ids, ex["model"]["kind"] == "LP" or whole_corner, (ex["info"], ids))
            self.assertLess(ids.index("region"), ids.index("optimum"))
            if "corner" in ids:
                self.assertEqual(ids.index("corner") + 1, ids.index("optimum"))

    def test_public_steps_hide_the_answers(self):
        ex = tutorial.create()
        text = json.dumps(engine.public_steps(ex))
        self.assertNotIn("expected", text)


class SolutionLockTests(unittest.TestCase):
    """“Solution” is only given once every step before is filled in – right or wrong does not matter."""

    def test_steps_before_must_be_filled_in(self):
        ex = tutorial.create()
        region = step(ex, "region")
        self.assertEqual(engine.unfilled_before(ex, step(ex, "objective"), {}), [])
        self.assertEqual(engine.unfilled_before(ex, region, {}), ["objective", "constraints", "lines"])
        answers = {sid: dict(tutorial.ANSWERS[sid]) for sid in ("objective", "constraints", "lines")}
        self.assertEqual(engine.unfilled_before(ex, region, answers), [])
        answers["constraints"]["b1"] = " "          # one empty field keeps the step open
        self.assertEqual(engine.unfilled_before(ex, region, answers), ["constraints"])
        answers["constraints"]["b1"] = "999"        # a wrong value is enough
        self.assertEqual(engine.unfilled_before(ex, region, answers), [])

    def test_a_given_model_needs_no_step_before_the_lines(self):
        ex = engine.make_exercise({}, example(), {"source": "own"})
        self.assertEqual(engine.unfilled_before(ex, ex["steps"][0], {}), [])


class ReportTests(unittest.TestCase):
    """The evaluation as a PDF: the learner's answers next to the correct ones."""

    @staticmethod
    def result(ex, answers, lang):
        grades = [engine.grade_step(ex, s, answers.get(s["id"]), answers, lang) for s in ex["steps"]]
        return {"score": round(sum(g["points"] for g in grades), 1), "grades": grades, "hints": {"lines": 1},
                "reveals": ["optimum"], "first": {"objective": grades[0]}}

    def test_rows_show_the_answer_and_the_correct_answer(self):
        ex = tutorial.create()
        answers = copy.deepcopy(tutorial.ANSWERS)
        answers["constraints"]["b1"] = "100"
        answers["slack"]["bind2"] = "yes"
        grades = self.result(ex, answers, "de")["grades"]
        rows = {s["id"]: report.review_rows(ex, s, answers, g["checks"], "de") for s, g in zip(ex["steps"], grades)}
        # one line per constraint
        self.assertEqual(rows["constraints"][1], ("NB2 Fleisch", "0.1·x1 + 0.2·x2 ≤ 100", "0,1·x1 + 0,2·x2 ≤ 40", False))
        self.assertTrue(rows["constraints"][0][3])
        self.assertIn(("NB3: bindend?", "ja", "nein", False), rows["slack"])
        self.assertIn(("Gerade 1", "NB1 Fladenbrot", "NB1 Fladenbrot", True), rows["corner"])
        self.assertIn(("Zielwert F", "26000", "26.000", True), rows["optimum"])
        # every field has a label in words, in every language
        for lang, ex2 in itertools.product(i18n.LANGS, exercises()[:8]):
            for s in ex2["steps"]:
                labels = [row[0] for row in report.review_rows(ex2, s, {}, {}, lang)]
                self.assertNotIn("learn_", " ".join(labels))
                self.assertFalse(set(labels) & {q["key"] for q in s["questions"]}, labels)

    def test_a_choice_the_page_does_not_offer_is_not_shown(self):
        ex = tutorial.create()
        q = step(ex, "interpret")["questions"][0]
        self.assertEqual(report.shown(ex, q, "x<script>", "en"), "–")

    def test_pdf_for_every_kind_of_task(self):
        own = engine.validate({"c": [3, 4], "sense": "max", "kind": "MILP1",
                               "rows": [{"a": [1, 0], "op": "<=", "b": 4.5, "name": "$\\frac{"}, {"a": [1, 1], "op": "<=", "b": 5, "name": "A $x$ B"}]})
        ilp = engine.normalize_options({"kind": "ILP", "difficulty": "medium", "mode": "exam"})
        ilp["seed"] = 3
        cases = [(tutorial.create(), copy.deepcopy(tutorial.ANSWERS)), (engine.make_exercise(ilp), {}),
                 (engine.make_exercise({}, own, {"source": "own"}), {"lines": {"ax0_0": "$\\alpha$ <b>"}})]
        for (ex, answers), lang in itertools.product(cases, i18n.LANGS):
            data = report.pdf(ex, self.result(ex, answers, lang), answers, lang, tz_minutes=-480)
            self.assertTrue(data.startswith(b"%PDF-"))
            self.assertGreater(len(data), 20_000)

    def test_time_of_handing_in_is_shown_in_the_learners_zone(self):
        self.assertRegex(report.handed_in(-480, "de"), r"^\d\d\.\d\d\.\d{4}, \d\d:\d\d \(UTC\+8\)$")
        self.assertRegex(report.handed_in(300, "en"), r"^\d{1,2} [A-Z][a-z]{2} \d{4}, \d\d:\d\d \(UTC−5\)$")
        for odd in (None, "x", 10 ** 9, {"a": 1}):
            self.assertIn("UTC", report.handed_in(odd, "en"))


class TextTests(unittest.TestCase):
    def test_every_text_key_of_the_browser_exists(self):
        with open(os.path.join(ROOT, "www", "learn.js"), encoding="utf-8") as f:
            src = f.read()
        keys = set(re.findall(r'\bL\("([a-zA-Z0-9_]+)"', src)) | set(re.findall(r'\bT\("([a-zA-Z0-9_]+)"', src))
        keys = {k for k in keys if not k.endswith("_")}
        missing = [k for k in keys if k not in i18n.TEXT and f"learn_{k}" not in i18n.TEXT]
        self.assertEqual(missing, [])
        for prefix, ids in (("step_", engine.WEIGHTS), ("help_", engine.WEIGHTS), ("short_", engine.WEIGHTS),
                            ("hint_", [engine.hint_id(q["key"]) for s in tutorial.create()["steps"] for q in s["questions"]])):
            for sid in ids:
                self.assertIn(f"learn_{prefix}{sid}", i18n.TEXT)
        self.assertIn("learn_hint_opt_corner", i18n.TEXT)

    def test_generated_word_problems_use_pesos_in_english_and_euros_in_german(self):
        for (difficulty, kind), tasks in engine.POOL.items():
            for task in tasks:
                opts = engine.normalize_options({"form": "text", "kind": kind, "difficulty": difficulty, "task": engine.task_name(task)})
                ex = engine.make_exercise(opts)
                en, de = (json.dumps(story.story(ex, lang), ensure_ascii=False) for lang in ("en", "de"))
                if task.get("story") == "burger":   # dollars in both languages
                    self.assertTrue("$" in en and "$" in de and "€" not in en + de and "₱" not in en + de)
                    continue
                if task.get("story") == "shawarma":   # pesos in both: the stand is in the Philippines
                    self.assertTrue("₱" in en and "₱" in de and "€" not in en + de)
                    continue
                self.assertNotIn("€", en)
                self.assertNotIn("₱", de)
                if ex["model"]["sense"] == "min" or task["topic"] not in ("advertising", "radio"):   # reach is counted in people
                    self.assertIn("₱", story.story(ex, "en")["objective"])
                    self.assertIn("€", story.story(ex, "de")["objective"])

    def test_task_texts_and_solutions_in_all_languages(self):
        for ex, lang in itertools.product(exercises(), i18n.LANGS):
            text = json.dumps([story.story(ex, lang), story.row_labels(ex, lang), story.row_names(ex, lang),
                               solution.all_lines(ex, lang)], ensure_ascii=False)
            self.assertNotIn("learn_", text)
            self.assertIsNone(re.search(r"\{[a-z0-9_]+\}", text), text)


if __name__ == "__main__":
    unittest.main()
