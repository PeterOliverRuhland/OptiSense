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
from optisense.pages.learn import engine, solution, story, tutorial  # noqa: E402

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
        opts = engine.normalize_options({"form": form, "kind": kind, "difficulty": difficulty, "topic": engine.MIN_TOPICS[seed % 4]})
        opts["seed"] = seed
        out.append(engine.make_exercise(opts))
    for kind in ("LP", "ILP", "MILP1", "MILP2"):
        out.append(engine.make_exercise({}, example(kind), {"source": "own"}))
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
            if m["kind"] == "ILP":   # independent check by enumeration
                values = [np.dot(m["c"], [i, j]) for i in range(60) for j in range(60) if engine.feasible(m, [i, j])]
                best = max(values) if m["sense"] == "max" else min(values)
                self.assertAlmostEqual(ex["solution"]["z"], best)

    def test_minimisation_only_at_the_second_level_and_in_matching_topics(self):
        senses = {}
        for difficulty, topic, seed in itertools.product(("easy", "medium"), ("production", "farming"), range(30)):
            opts = engine.normalize_options({"difficulty": difficulty, "topic": topic})
            opts["seed"] = seed
            senses.setdefault((difficulty, topic), set()).add(engine.make_exercise(opts)["model"]["sense"])
        self.assertEqual(senses[("easy", "farming")], {"max"})
        self.assertEqual(senses[("medium", "production")], {"max"})
        self.assertEqual(senses[("medium", "farming")], {"max", "min"})

    def test_options_are_reduced_to_known_values(self):
        # unknown and removed choices (advanced level, simplex) fall back to the defaults; mixed is chosen as “MILP”
        opts = engine.normalize_options({"mode": "cheat", "kind": "MILP1", "difficulty": "hard", "topic": "space", "simplex": 1})
        self.assertEqual((opts["mode"], opts["kind"], opts["difficulty"], opts["topic"]), ("practice", "LP", "easy", "random"))
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
            self.assertFalse(engine.feasible(m, relaxed["x"]), (kind, seed))   # just solving the LP would be wrong
            self.assertNotIn("corner", [s["id"] for s in ex["steps"]])
        self.assertTrue({"MILP1", "MILP2"} <= kinds)   # either variable can be the integer one


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

    def test_tutorial_is_the_burger_problem_of_the_lecture(self):
        ex = tutorial.create()
        self.assertEqual(ex["solution"]["x"], [300, 200])
        self.assertAlmostEqual(ex["solution"]["z"], 2550)

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
        answers = dict(tutorial.ANSWERS["constraints"], a1_0="100", a1_1="300", b1="105000")   # meat in grams
        self.assertTrue(engine.grade_step(ex, step(ex, "constraints"), answers)["correct"])
        answers.update(a2_0="-1", a2_1="-1.5", b2="-600", op2=">=")
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
        g = engine.grade_step(ex, s, {"x": "300", "y": "200", "z": "2549"})
        self.assertEqual(engine.hints_for(ex, s, g), ["z"])
        g = engine.grade_step(ex, s, {"x": "200", "y": "300", "z": "2550"})
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
        self.assertEqual((values["boundary1"], values["boundary2"]), ("0", "2"))   # buns and vegetables
        values = engine.solution_values(ex, step(ex, "optimum"), {"corner": values})
        self.assertTrue(np.allclose([values["x"], values["y"], values["z"]], [300, 200, 2550]))

    def test_the_corner_must_be_optimal(self):
        ex = tutorial.create()
        s = step(ex, "corner")
        for pair, ok in ((("0", "2"), True), (("2", "0"), True), (("1", "2"), False), (("0", "1"), False),
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
        g = engine.grade_step(ex, step(ex, "slack"), dict(tutorial.ANSWERS["slack"], bind1="yes"), answers)
        self.assertEqual(engine.hints_for(ex, step(ex, "slack"), g), ["bind"])   # meat has 15 kg left: not binding
        self.assertNotIn("sensitivity", engine.normalize_options({"sensitivity": True}))

    def test_word_problems_name_the_objective(self):
        for ex in exercises():
            st = story.story(ex, "de")
            if ex["options"].get("form") == "text":
                self.assertTrue(st["fname"] and not st["fname"].startswith("learn_"), (ex["info"], st))
            else:
                self.assertNotIn("fname", st)
        self.assertEqual(story.story(tutorial.create(), "de")["fname"], "Umsatz")

    def test_only_lp_tasks_have_a_corner_step(self):
        for ex in exercises():
            ids = [s["id"] for s in ex["steps"]]
            self.assertEqual("corner" in ids, ex["model"]["kind"] == "LP", (ex["info"], ids))
            self.assertLess(ids.index("region"), ids.index("optimum"))
            if "corner" in ids:
                self.assertEqual(ids.index("corner") + 1, ids.index("optimum"))

    def test_public_steps_hide_the_answers(self):
        ex = tutorial.create()
        text = json.dumps(engine.public_steps(ex))
        self.assertNotIn("expected", text)


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

    def test_task_texts_and_solutions_in_all_languages(self):
        for ex, lang in itertools.product(exercises(), i18n.LANGS):
            text = json.dumps([story.story(ex, lang), story.row_labels(ex, lang), story.row_names(ex, lang),
                               solution.all_lines(ex, lang)], ensure_ascii=False)
            self.assertNotIn("learn_", text)
            self.assertIsNone(re.search(r"\{[a-z0-9_]+\}", text), text)


if __name__ == "__main__":
    unittest.main()
