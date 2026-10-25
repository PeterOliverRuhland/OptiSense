"""Tests for the tab “Learn & practise”: exercise generation, grading, texts in all languages.

Run from the repository root:  python -m unittest discover -s tests
"""
import contextlib
import copy
import io
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
from optisense.pages.learn import engine, pycode, solution, story, tutorial  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "shiny_files")


def example(kind="LP"):
    return engine.validate({"c": [3, 4], "sense": "max", "kind": kind,
                            "rows": [{"a": [1, 0], "op": "<=", "b": 4}, {"a": [0, 1], "op": "<=", "b": 3},
                                     {"a": [1, 1], "op": "<=", "b": 5}]})


def step(ex, sid):
    return engine.step_by_id(ex, sid)


class GeneratorTests(unittest.TestCase):
    def test_generated_tasks_are_solvable_and_worth_100_points(self):
        for kind, difficulty, seed in itertools.product(("LP", "ILP", "MILP"), ("easy", "medium", "hard"), range(12)):
            opts = engine.normalize_options({"kind": kind, "difficulty": difficulty, "form": "text"})
            opts["seed"] = seed
            ex = engine.make_exercise(opts)
            m = ex["model"]
            self.assertEqual(ex["solution"]["status"], "optimal")
            self.assertTrue(engine.feasible(m, ex["solution"]["x"]))
            self.assertEqual(sum(s["points"] for s in ex["steps"]), 100)
            if m["kind"] == "ILP":   # independent check by enumeration
                values = [np.dot(m["c"], [i, j]) for i in range(60) for j in range(60) if engine.feasible(m, [i, j])]
                best = max(values) if m["sense"] == "max" else min(values)
                self.assertAlmostEqual(ex["solution"]["z"], best)

    def test_minimisation_only_in_matching_topics(self):
        for seed in range(60):
            opts = engine.normalize_options({"difficulty": "hard", "topic": "production"})
            opts["seed"] = seed
            self.assertEqual(engine.make_exercise(opts)["model"]["sense"], "max")

    def test_options_are_reduced_to_known_values(self):
        opts = engine.normalize_options({"mode": "cheat", "kind": "MILP", "topic": "space", "simplex": 1})
        self.assertEqual(opts["mode"], "practice")
        self.assertIn(opts["kind"], ("MILP1", "MILP2"))
        self.assertEqual(opts["topic"], "random")
        self.assertTrue(opts["simplex"])


class SolverTests(unittest.TestCase):
    def test_sensitivity_of_the_example(self):
        m = example()
        sol = engine.solve(m)
        self.assertTrue(np.allclose(sol["x"], [2, 3]))
        sen = engine.sensitivity(m, sol["x"])
        self.assertTrue(np.allclose(sen["slacks"], [2, 0, 0]))
        self.assertTrue(np.allclose(sen["shadow"], [0, 1, 3]))
        self.assertTrue(np.allclose(sen["ranges"][0], [0, 4]))
        self.assertEqual(sen["ranges"][1], [3, math.inf])
        for k in range(3):   # shadow prices agree with re-solving
            changed = copy.deepcopy(m)
            changed["rows"][k]["b"] += 0.001
            self.assertAlmostEqual(engine.solve(changed)["z"] - sol["z"], 0.001 * sen["shadow"][k], places=7)
        self.assertIsNone(engine.sensitivity(example("ILP"), [2, 3])["shadow"])

    def test_infeasible_and_unbounded_models_are_refused(self):
        bad = {"c": [1, 1], "sense": "max", "kind": "LP", "rows": [{"a": [1, 0], "op": ">=", "b": 1}]}
        with self.assertRaises(engine.LearnError) as err:
            engine.make_exercise({"method": "both"}, bad, {"source": "own"})
        self.assertEqual(err.exception.key, "err_unbounded")
        bad["rows"] = [{"a": [1, 1], "op": "<=", "b": 3}, {"a": [1, 1], "op": ">=", "b": 5}]
        with self.assertRaises(engine.LearnError) as err:
            engine.make_exercise({"method": "both"}, bad, {"source": "own"})
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
        answers = ex["tutorial"]["answers"]
        total = sum(engine.grade_step(ex, s, answers.get(s["id"]), answers)["points"] for s in ex["steps"])
        self.assertAlmostEqual(total, 100)

    def test_tutorial_is_the_burger_problem_of_the_lecture(self):
        ex = tutorial.create()
        self.assertEqual(ex["solution"]["x"], [300, 200])
        self.assertAlmostEqual(ex["solution"]["z"], 2550)
        expected = {q["key"]: q["expected"] for q in step(ex, "simplex")["questions"]}
        self.assertEqual([expected[f"nextz{i}"] for i in range(3)], [2100, 2475, 2550])   # tableaus 2–4 of the slides

    def test_a_scaled_constraint_counts_as_correct(self):
        ex = tutorial.create()
        answers = dict(tutorial.ANSWERS["model"], a1_0="100", a1_1="300", b1="105000")   # meat in grams
        self.assertTrue(engine.grade_step(ex, step(ex, "model"), answers)["correct"])
        answers.update(a2_0="-1", a2_1="-1.5", b2="-600", op2=">=")
        self.assertTrue(engine.grade_step(ex, step(ex, "model"), answers)["correct"])

    def test_axis_intersections_with_parallel_lines(self):
        ex = engine.make_exercise({"method": "graph"}, example(), {"source": "own"})
        answers = {"ax0_0": "4", "ax0_1": "–", "ax1_0": "-", "ax1_1": "3", "ax2_0": "5", "ax2_1": "5"}
        self.assertTrue(engine.grade_step(ex, step(ex, "lines"), answers)["correct"])
        answers.update(ax0_1="0", ax2_0="")
        g = engine.grade_step(ex, step(ex, "lines"), answers)
        self.assertFalse(g["checks"]["ax0_1"] or g["checks"]["ax2_0"])
        self.assertTrue(g["checks"]["ax0_0"] and g["checks"]["ax2_1"])

    def test_sides_use_the_test_point(self):
        m = engine.validate({"c": [1, 1], "sense": "min", "kind": "LP",
                             "rows": [{"a": [1, 1], "op": ">=", "b": 4}, {"a": [1, 0], "op": "<=", "b": 6}, {"a": [1, -1], "op": "=", "b": 0}]})
        ex = engine.make_exercise({"method": "graph"}, m, {"source": "own"})
        expected = {q["key"]: q["expected"] for q in step(ex, "region")["questions"]}
        self.assertEqual([expected["side0"], expected["side1"], expected["side2"]], ["out", "in", "line"])
        self.assertNotEqual(ex["test_points"][2], [0.0, 0.0])   # (0 | 0) lies on x1 − x2 = 0

    def test_alternative_optima_and_slack_at_the_learners_point(self):
        m = example()
        m["c"] = [1, 1]
        ex = engine.make_exercise({"method": "calc"}, m, {"source": "own"})
        answers = {"optimum": {"x": "4", "y": "1", "z": "5"}}
        self.assertTrue(engine.grade_step(ex, step(ex, "optimum"), answers["optimum"])["correct"])
        g = engine.grade_step(ex, step(ex, "sensitivity"), {"slack0": "0", "slack1": "2", "slack2": "0"}, answers)
        self.assertTrue(all(g["checks"][f"slack{i}"] for i in range(3)))

    def test_hints_name_the_wrong_questions(self):
        ex = tutorial.create()
        s = step(ex, "optimum")
        g = engine.grade_step(ex, s, {"x": "300", "y": "200", "z": "2549"})
        self.assertEqual(engine.hints_for(s, g), ["z"])

    def test_public_steps_hide_the_answers(self):
        ex = tutorial.create()
        text = json.dumps(engine.public_steps(ex))
        self.assertNotIn("expected", text)


class PythonCodeTests(unittest.TestCase):
    def test_the_code_solves_the_exercise(self):
        cases = [tutorial.create()]
        for kind, difficulty, seed in itertools.product(("LP", "ILP", "MILP"), ("easy", "hard"), range(5)):
            opts = engine.normalize_options({"kind": kind, "difficulty": difficulty})
            opts["seed"] = seed
            cases.append(engine.make_exercise(opts))
        for ex in cases:
            scope = {}
            with contextlib.redirect_stdout(io.StringIO()):
                exec(pycode.python_code(ex), scope)
            r = scope["result"]
            self.assertAlmostEqual(-r.fun if ex["model"]["sense"] == "max" else r.fun, ex["solution"]["z"], places=6)


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

    def test_task_texts_and_solutions_in_all_languages(self):
        exercises = [tutorial.create()]
        for form, seed in itertools.product(("text", "math"), range(10)):
            opts = engine.normalize_options({"form": form, "difficulty": ("easy", "medium", "hard")[seed % 3],
                                             "kind": ("LP", "ILP", "MILP")[seed % 3], "simplex": True})
            opts["seed"] = seed
            exercises.append(engine.make_exercise(opts))
        for ex, lang in itertools.product(exercises, i18n.LANGS):
            text = json.dumps([story.story(ex, lang), story.row_labels(ex, lang), story.row_names(ex, lang),
                               solution.all_lines(ex, lang)], ensure_ascii=False)
            self.assertNotIn("learn_", text)
            self.assertIsNone(re.search(r"\{[a-z0-9_]+\}", text), text)


if __name__ == "__main__":
    unittest.main()
