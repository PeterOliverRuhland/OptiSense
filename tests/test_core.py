"""Tests for the solver, geometry, LP-file and translation helpers.

Run from the repository root:  python -m unittest discover -s tests
The sensitivity test needs lp_solve (set LP_SOLVE_BIN or have it on PATH); it is skipped otherwise.
"""
import html
import math
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shiny_files"))

from optisense import core as lp_core  # noqa: E402
from optisense import i18n  # noqa: E402
from optisense.pages.work import example  # noqa: E402
from optisense.pages.work.example import EXAMPLE  # noqa: E402
from optisense.pages.learn.tasks import POOL  # noqa: E402

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


class ExampleTests(unittest.TestCase):
    """The burger example that “Example” in step 1 loads and the guide explains (pages/work/example.py)."""

    @staticmethod
    def problem(lang):
        return example.problem(lang)[:2]

    def test_burger_example_is_the_lecture_problem_and_its_practice_task(self):
        obj, cons = self.problem("en")
        s = lp_core.solve(obj, cons, EXAMPLE["var_types"])
        self.assertEqual((s["x1"], s["x2"], s["value"]), (300, 200, 2550))
        self.assertEqual(EXAMPLE["var_types"], {"x1": "int", "x2": "int"})   # no half burgers
        burger = next(t for t in POOL[("medium", "ILP")] if t.get("story") == "burger")   # the practice task “Burger”
        self.assertEqual((obj["c1"], obj["c2"]), burger["c"])
        self.assertEqual([(c["a1"], c["a2"], c["b"]) for c in cons], [(a1, a2, b) for a1, a2, _, b in burger["rows"]])

    def test_example_texts_exist_in_both_languages(self):
        names = [EXAMPLE["objective"]["name"]] + [c["name"] for c in EXAMPLE["constraints"]]
        story = ["example_title", "example_story", "example_limits", "example_whole"] + [n + "_use" for n in names[1:]]
        story += [EXAMPLE["objective"]["note"], EXAMPLE["types_note"]] + [c["note"] for c in EXAMPLE["constraints"]]
        for key in names + story:
            en, de = i18n.t("en", key), i18n.t("de", key)
            self.assertNotEqual(en, key)
            self.assertNotEqual(en, de, key)

    def test_guide_shows_the_file_the_export_writes(self):
        for lang in ("en", "de"):
            obj, cons = self.problem(lang)
            text = lp_core.to_lp_file(obj, cons, EXAMPLE["var_types"]).strip()
            code = re.search(r"<code>(.*?)</code>", i18n.guide(lang, "import"), re.S).group(1)
            self.assertEqual(html.unescape(code.replace("<br>", "\n")), text, lang)

    def test_story_lines_only_while_the_rows_are_the_examples(self):
        obj, cons, vt = example.problem("en")
        self.assertEqual(example.note("obj", obj), "example_note_revenue")
        self.assertEqual([example.note("con", c) for c in cons], ["example_note_buns", "example_note_meat", "example_note_veg"])
        self.assertEqual(example.types_note([obj], vt), "example_note_types")
        # saved again unchanged (the edit dialog sends floats) – the story stays
        self.assertEqual(example.note("con", dict(cons[0], a1=1.0, b=500.0)), "example_note_buns")
        # a changed number, operator or direction: the line would be wrong, so it goes
        self.assertIsNone(example.note("con", dict(cons[0], b=600.0)))
        self.assertIsNone(example.note("con", dict(cons[1], op="≥")))
        self.assertIsNone(example.note("obj", dict(obj, sense="min")))
        self.assertIsNone(example.types_note([dict(obj, c1=5.0)], vt))
        self.assertIsNone(example.types_note([obj], {"x1": "con", "x2": "int"}))
        # the learner's own rows and imported files have no story
        own = {"name": "C1", "a1": 1, "a2": 1, "op": "≤", "b": 500}
        self.assertIsNone(example.note("con", own))
        self.assertIsNone(example.note("con", dict(own, note=None)))
        self.assertIsNone(example.types_note([{"c1": 4.5, "c2": 6, "sense": "max"}], vt))

    def test_lp_file_writes_umlauts_out(self):
        obj, cons = self.problem("de")
        text = lp_core.to_lp_file(obj, cons, EXAMPLE["var_types"])
        self.assertIn("Broetchen:", text)
        self.assertIn("Gemuese:", text)
        _, back, vt = lp_core.parse_lp_file(text)
        self.assertEqual([c["name"] for c in back], ["Broetchen", "Fleisch", "Gemuese"])
        self.assertEqual(vt, EXAMPLE["var_types"])


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

    def test_errors_give_the_line_but_no_file_text(self):
        """Error messages are shown to the user: they must not repeat what is in the file."""
        cases = (("max: x1 + x2;\n/* a\nb */\nx1 + SECRET <= 4;", 4),
                 ("max: x1 + x2;\n\n" + "SECRET" * 60 + " <= 4;", 3),
                 ("max: x1 + x2; x1 <= 4;\nint SECRET;", 2),
                 ("token: SECRET;", 1))
        for text, line in cases:
            with self.assertRaises(lp_core.LPParseError) as cm:
                lp_core.parse_lp_file(text)
            self.assertEqual(cm.exception.line, line, text)
            self.assertNotIn("SECRET", str(cm.exception))

    def test_solver_has_a_time_limit_and_still_solves(self):
        res = lp_core.solve(OBJ, CONS[1:], {"x1": "int", "x2": "int"})
        self.assertEqual((res["status"], res["x1"], res["x2"]), ("optimal", 30, 60))


class UploadPathTests(unittest.TestCase):
    """The browser can send any "datapath"; only files Shiny saved for this session may be opened."""

    def setUp(self):
        from types import SimpleNamespace
        from shiny._fileupload import FileUploadManager
        manager = FileUploadManager()
        self.addCleanup(manager.rm_upload_dir)
        op = manager.get_upload_operation(manager.create_upload_operation([{"name": "a.lp", "size": 3, "type": ""}]))
        with op:
            op.write_chunk(b"max")
        self.files = op.finish()
        self.session = SimpleNamespace(root_scope=lambda: SimpleNamespace(_file_upload_manager=manager))

    def test_accepts_a_real_upload(self):
        from optisense.pages.work.server.files import upload_path
        self.assertEqual(upload_path(self.session, self.files), os.path.realpath(self.files[0]["datapath"]))

    def test_rejects_other_paths(self):
        from optisense.pages.work.server.files import upload_path
        inside = os.path.dirname(self.files[0]["datapath"])
        for path in ("/etc/passwd", "/proc/self/environ", os.path.join(inside, "..", "..", "..", "etc", "passwd"),
                     inside, os.path.join(inside, "missing.lp"), "a\0b", 42):
            self.assertIsNone(upload_path(self.session, [{"name": "a.lp", "datapath": path}]), path)
        for files in (None, (), "x", {"datapath": "/etc/passwd"}, ["/etc/passwd"]):
            self.assertIsNone(upload_path(self.session, files), files)


class PngExportTests(unittest.TestCase):
    def test_download_closes_the_figure(self):
        """An open figure keeps its image buffer (about 80 MB at 600 dpi) until the app stops."""
        import matplotlib.pyplot as plt
        from optisense.pages.work import plotting
        before = len(plt.get_fignums())
        cons = [dict(c, color_index=i) for i, c in enumerate(CONS)]
        png = plotting.png_bytes(plotting.draw(OBJ, cons, LP, lp_core.solve(OBJ, cons, LP), "de", figsize=(8, 7)), 72)
        self.assertTrue(png.startswith(b"\x89PNG"))
        self.assertEqual(len(plt.get_fignums()), before)


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
