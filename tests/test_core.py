"""Tests for the solver, geometry, LP-file and translation helpers.

Run from the repository root:  python -m unittest discover -s tests
The sensitivity test needs lp_solve (set LP_SOLVE_BIN or have it on PATH); it is skipped otherwise.
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shiny_files"))

from optisense import core as lp_core  # noqa: E402
from optisense import i18n  # noqa: E402

OBJ = {"name": "F", "c1": 10, "c2": 20, "sense": "max"}
CONS = [
    {"name": "C1", "a1": 1, "a2": 1, "op": "≤", "b": 100},
    {"name": "C2", "a1": 6, "a2": 9, "op": "≤", "b": 720},
    {"name": "C3", "a1": 0, "a2": 1, "op": "≤", "b": 60},
]
LP = {"x1": "con", "x2": "con"}


class SolveTests(unittest.TestCase):
    def test_textbook_example(self):
        s = lp_core.solve(OBJ, CONS, LP)
        self.assertEqual(s["status"], "optimal")
        self.assertAlmostEqual(s["value"], 1500)
        self.assertAlmostEqual(s["x1"], 30)
        self.assertAlmostEqual(s["x2"], 60)

    def test_slack_and_binding(self):
        act = lp_core.constraint_activity(CONS, 30, 60)
        self.assertEqual([a["binding"] for a in act], [False, True, True])
        self.assertAlmostEqual(act[0]["slack"], 10)

    def test_min_problem(self):
        obj = {"c1": 2, "c2": 3, "sense": "min"}
        cons = [{"a1": 1, "a2": 1, "op": "≥", "b": 4}, {"a1": 1, "a2": 3, "op": "≥", "b": 6}]
        s = lp_core.solve(obj, cons, LP)
        self.assertAlmostEqual(s["value"], 9)

    def test_integer_problem(self):
        obj = {"c1": 1, "c2": 1, "sense": "max"}
        cons = [{"a1": 2, "a2": 2, "op": "≤", "b": 7}]
        self.assertAlmostEqual(lp_core.solve(obj, cons, LP)["value"], 3.5)
        self.assertAlmostEqual(lp_core.solve(obj, cons, {"x1": "int", "x2": "int"})["value"], 3)

    def test_unbounded_and_infeasible(self):
        obj = {"c1": 2, "c2": 3, "sense": "max"}
        unb = [{"a1": 1, "a2": 1, "op": "≥", "b": 4}]
        self.assertEqual(lp_core.solve(obj, unb, LP)["status"], "unbounded")
        self.assertEqual(lp_core.solve(obj, unb, {"x1": "int", "x2": "int"})["status"], "unbounded")
        inf = [{"a1": 1, "a2": 1, "op": "≤", "b": 3}, {"a1": 1, "a2": 1, "op": "≥", "b": 5}]
        self.assertEqual(lp_core.solve(obj, inf, LP)["status"], "infeasible")

    def test_problem_type(self):
        self.assertEqual(lp_core.problem_type(LP), "LP")
        self.assertEqual(lp_core.problem_type({"x1": "int", "x2": "con"}), "MILP")
        self.assertEqual(lp_core.problem_type({"x1": "int", "x2": "int"}), "ILP")


class GeometryTests(unittest.TestCase):
    def test_polygon_corners(self):
        poly = lp_core.feasible_polygon(CONS, 150, 120)
        corners = {(round(x, 6), round(y, 6)) for x, y in poly}
        self.assertEqual(corners, {(0, 0), (100, 0), (60, 40), (30, 60), (0, 60)})

    def test_integer_points_are_feasible(self):
        region = lp_core.feasible_region(CONS, {"x1": "int", "x2": "int"}, 20, 20)
        self.assertTrue(region["points"])
        self.assertTrue(all(lp_core.is_feasible(CONS, x, y) for x, y in region["points"]))

    def test_line_in_box(self):
        self.assertEqual(lp_core.line_in_box(1, 1, 100, 150, 120), ((0.0, 100.0), (100.0, 0.0)))
        self.assertIsNone(lp_core.line_in_box(1, 1, 500, 150, 120))


class LPFileTests(unittest.TestCase):
    def test_round_trip(self):
        text = lp_core.to_lp_file(OBJ, CONS, {"x1": "int", "x2": "con"})
        obj, cons, vt = lp_core.parse_lp_file(text)
        self.assertEqual(obj["sense"], "max")
        self.assertEqual([c["b"] for c in cons], [100, 720, 60])
        self.assertEqual(vt, {"x1": "int", "x2": "con"})

    def test_old_optisense_format(self):
        text = "max: 10 x1 + 20 x2;\n1 x1 + 1 x2 <= 100;\n6 x1 + 9 x2 <= 720;\n0 x1 + 1 x2 <= 60;\nx1 >= 0;\nx2 >= 0;"
        obj, cons, vt = lp_core.parse_lp_file(text)
        self.assertEqual(len(cons), 3)
        self.assertEqual(vt, LP)

    def test_rejects_unknown_variable(self):
        with self.assertRaises(lp_core.LPParseError):
            lp_core.parse_lp_file("max: 3 x1 + 2 y;\nx1 <= 4;")

    def test_numbers_in_all_notations(self):
        obj, cons, _ = lp_core.parse_lp_file("max: .5 x1 + 2. x2;\n1.5e2 x1 + 3*x2 <= 1e3;\n-x1 + x2 >= 0;")
        self.assertEqual((obj["c1"], obj["c2"]), (0.5, 2.0))
        self.assertEqual((cons[0]["a1"], cons[0]["a2"], cons[0]["b"]), (150.0, 3.0, 1000.0))
        self.assertEqual((cons[1]["a1"], cons[1]["a2"]), (-1.0, 1.0))

    def test_hostile_files_are_rejected_quickly(self):
        """The server is shared: a crafted file must not keep it busy."""
        import time
        for text in ("max: x1 + x2;\nx1 <= 4" + ";\nx1 <= 4" * 60,        # too many statements
                     "max: x1 + x2;\n" + "1" * 100_000 + " <= 4;",        # one very long statement
                     "max: x1 + x2;\nx1 + " + "+".join(["1"] * 200) + " x2 <= 4;"):
            start = time.perf_counter()
            with self.assertRaises(lp_core.LPParseError):
                lp_core.parse_lp_file(text)
            self.assertLess(time.perf_counter() - start, 1.0)

    def test_solver_has_a_time_limit_and_still_solves(self):
        res = lp_core.solve(OBJ, CONS[1:], {"x1": "int", "x2": "int"})
        self.assertEqual((res["status"], res["x1"], res["x2"]), ("optimal", 30, 60))


class SensitivityTests(unittest.TestCase):
    def test_parse_output(self):
        out = """Dual value
Objective function limits:
                                 From            Till       FromValue
x1                                  0        13.33333          -1e+30
x2                                 15           1e+30          -1e+30

Dual values with from - till limits:
                           Dual value            From            Till
R1                                  0          -1e+30           1e+30
R2                           1.666667             540             780
R3                                  5              40              80
"""
        res = lp_core.parse_sensitivity(out, 3)
        self.assertAlmostEqual(res["shadow"][1]["price"], 1.666667)
        self.assertEqual(res["shadow"][0]["from"], -math.inf)
        self.assertEqual(res["limits"]["x2"]["till"], math.inf)

    @unittest.skipUnless(lp_core.find_lp_solve() and os.path.exists(lp_core.find_lp_solve() or ""), "lp_solve not available")
    def test_run_lp_solve(self):
        res = lp_core.run_sensitivity(OBJ, CONS, LP)
        self.assertAlmostEqual(res["shadow"][2]["price"], 5)


class I18nTests(unittest.TestCase):
    def test_every_text_has_all_languages(self):
        for key, entry in i18n.TEXT.items():
            for lang in i18n.LANGS:
                self.assertIn(lang, entry, f"{key} lacks {lang}")
        for topic, entry in i18n.GUIDE.items():
            for lang in i18n.LANGS:
                self.assertIn(lang, entry, f"guide {topic} lacks {lang}")

    def test_placeholders_match(self):
        import string
        for key, entry in i18n.TEXT.items():
            fields = {lang: {f[1] for f in string.Formatter().parse(text) if f[1]} for lang, text in entry.items()}
            self.assertEqual(fields["en"], fields["de"], key)

    def test_number_format(self):
        self.assertEqual(i18n.fmt_num(1500, "de"), "1.500")
        self.assertEqual(i18n.fmt_num(1500.25, "en"), "1,500.25")
        self.assertEqual(i18n.fmt_num(1.6666667, "de"), "1,6667")
        self.assertEqual(i18n.fmt_num(float("inf"), "en"), "∞")


if __name__ == "__main__":
    unittest.main()
