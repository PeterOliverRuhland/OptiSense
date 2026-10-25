"""The three pages (work = start page, learn, guide) stay separate in the code.

Run from the repository root:  python -m unittest discover -s tests
"""
import ast
import os
import pathlib
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shiny_files"))

from optisense.i18n import common  # noqa: E402
from optisense.pages.guide import texts as guide_texts  # noqa: E402
from optisense.pages.learn import texts as learn_texts  # noqa: E402
from optisense.pages.work import texts as work_texts  # noqa: E402

PKG = pathlib.Path(__file__).resolve().parents[1] / "shiny_files" / "optisense"
PAGES = ("work", "learn", "guide")
# the ? dialogs of the start page show sections of the guide
ALLOWED = {("work", "optisense.pages.guide.content")}


def imports(path):
    """Absolute names of the modules a file imports from (relative imports resolved)."""
    package = ".".join(path.relative_to(PKG.parent).with_suffix("").parts[:-1])
    if path.name == "__init__.py":
        package = ".".join(path.relative_to(PKG.parent).parts[:-1])
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom):
            base = package.split(".")[:len(package.split(".")) - node.level + 1] if node.level else []
            name = ".".join(base + ([node.module] if node.module else []))
            yield name
            for alias in node.names:
                yield f"{name}.{alias.name}"
        elif isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)


class StructureTests(unittest.TestCase):
    def test_pages_do_not_import_each_other(self):
        for page in PAGES:
            for path in (PKG / "pages" / page).rglob("*.py"):
                for name in imports(path):
                    parts = name.split(".")
                    if parts[:2] == ["optisense", "pages"] and len(parts) > 2 and parts[2] != page:
                        self.assertIn((page, ".".join(parts[:4])), ALLOWED, f"{path.relative_to(PKG)} imports {name}")

    def test_page_packages_are_free_of_imports(self):
        # i18n reads the texts of every page; imports here would be circular
        for path in [PKG / "pages" / "__init__.py", PKG / "ui" / "__init__.py"] + [PKG / "pages" / p / "__init__.py" for p in PAGES]:
            self.assertEqual(list(imports(path)), [], path)

    def test_text_keys_are_unique_across_pages(self):
        seen = {}
        for owner, table in (("common", common.TEXT), ("work", work_texts.TEXT), ("guide", guide_texts.TEXT),
                             ("learn", learn_texts.LEARN)):
            for key in table:
                self.assertNotIn(key, seen, f"{key} is in {seen.get(key)} and {owner}")
                seen[key] = owner
        self.assertTrue(all(k.startswith("learn_") or k == "tab_learn" for k in learn_texts.LEARN))

    def test_every_page_has_its_files(self):
        www = PKG.parent / "www"
        for page in PAGES:
            for name in ("texts.py", "ui.py"):
                self.assertTrue((PKG / "pages" / page / name).exists(), f"{page}/{name}")
            self.assertTrue((PKG / "pages" / page / "server.py").exists() or (PKG / "pages" / page / "server").is_dir())
            for ext in ("css", "js"):
                self.assertTrue((www / f"{page}.{ext}").exists(), f"www/{page}.{ext}")


if __name__ == "__main__":
    unittest.main()
