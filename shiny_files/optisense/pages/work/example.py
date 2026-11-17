"""The example of “Model & solution” and the guide: the burger problem of the lecture (Prof. Koot, Aalen University),
the same story as the practice task “Burger” of the learn page (pages/learn/tasks.py). Burgers are sold whole, so both
variables are integer. Optimum (300 | 200) with revenue 2,550.

Names and notes are text keys (texts.py). A note is one line of the story, shown below the formula of its row in step 1 (and
above the variable types in step 2) – only while that row still has the example's numbers. Rows the learner adds or
changes have no story: there is none to tell.
"""

from optisense.i18n import t

EXAMPLE = {
    "objective": {"name": "example_revenue", "note": "example_note_revenue", "c1": 4.5, "c2": 6, "sense": "max"},
    "constraints": [{"name": "example_buns", "note": "example_note_buns", "a1": 1, "a2": 1, "op": "≤", "b": 500},
                    {"name": "example_meat", "note": "example_note_meat", "a1": 0.1, "a2": 0.3, "op": "≤", "b": 105},
                    {"name": "example_veg", "note": "example_note_veg", "a1": 0.1, "a2": 0.15, "op": "≤", "b": 60}],
    "var_types": {"x1": "int", "x2": "int"},
    "types_note": "example_note_types",
}

# the numbers a note describes: change one of them and the note no longer fits
FIELDS = {"obj": ("c1", "c2", "sense"), "con": ("a1", "a2", "op", "b")}


def problem(lang):
    """Objective function, constraints and variable types as “Example” loads them, with the names in `lang`."""
    obj = dict(EXAMPLE["objective"], name=t(lang, EXAMPLE["objective"]["name"]))
    cons = [dict(con, name=t(lang, con["name"])) for con in EXAMPLE["constraints"]]
    return obj, cons, dict(EXAMPLE["var_types"])


def note(kind, item):
    """Text key of the story line above a row of step 1 ("obj" or "con"), or None."""
    key = item.get("note")
    refs = [EXAMPLE["objective"]] if kind == "obj" else EXAMPLE["constraints"]
    ref = next((r for r in refs if key and r["note"] == key), None)
    if ref is None or any(item.get(f) != ref[f] for f in FIELDS[kind]):
        return None
    return key


def types_note(objectives, var_types):
    """Text key of the story line in step 2, or None: while the example's objective function and types are unchanged."""
    if dict(var_types) != EXAMPLE["var_types"] or not any(note("obj", o) for o in objectives):
        return None
    return EXAMPLE["types_note"]
