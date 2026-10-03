"""All user-facing text of OptiSense in English (source), German and Filipino.

Rules: every string has a key; whole sentences with {placeholders}; mathematical notation
(x1, x2, c1, a1, b, ≤ ≥ =, ℕ0) is never translated. Filipino is a first draft and should be
reviewed by a native speaker; technical terms follow common Philippine university usage
(English term kept, Filipino explanation around it).
"""

import json

LANGS = {"en": "English", "de": "Deutsch", "fil": "Filipino"}
DEFAULT_LANG = "en"

TEXT = {
    # ------------------------------------------------------------------ navigation
    "tab_work": {"en": "Model & solution", "de": "Modell & Lösung", "fil": "Modelo at solusyon"},
    "tab_guide": {"en": "Guide", "de": "Anleitung", "fil": "Gabay"},
    "language": {"en": "Language", "de": "Sprache", "fil": "Wika"},
    "help": {"en": "Help", "de": "Hilfe", "fil": "Tulong"},
    "credit": {"en": "OptiSense 2.0 · by Peter Oliver Ruhland", "de": "OptiSense 2.0 · von Peter Oliver Ruhland",
               "fil": "OptiSense 2.0 · gawa ni Peter Oliver Ruhland"},
    # ------------------------------------------------------------------ step 1
    "step1": {"en": "Enter problem", "de": "Problem eingeben", "fil": "Ilagay ang problema"},
    "n_functions": {"en": "{n} active", "de": "{n} aktiv", "fil": "{n} aktibo"},
    "objective_function": {"en": "Objective function", "de": "Zielfunktion", "fil": "Objective function"},
    "constraints": {"en": "Constraints", "de": "Nebenbedingungen", "fil": "Mga constraint"},
    "no_objective": {"en": "No objective function yet.", "de": "Noch keine Zielfunktion.",
                     "fil": "Wala pang objective function."},
    "no_constraints": {"en": "No constraints yet.", "de": "Noch keine Nebenbedingungen.",
                       "fil": "Wala pang constraint."},
    "add_objective": {"en": "Add objective function", "de": "Zielfunktion hinzufügen",
                      "fil": "Magdagdag ng objective function"},
    "add_constraint": {"en": "Add constraint", "de": "Nebenbedingung hinzufügen", "fil": "Magdagdag ng constraint"},
    "add_objective_short": {"en": "+ Objective function", "de": "+ Zielfunktion", "fil": "+ Objective function"},
    "add_constraint_short": {"en": "+ Constraint", "de": "+ Nebenbedingung", "fil": "+ Constraint"},
    "import_export": {"en": "Import & export", "de": "Import & Export", "fil": "Import at export"},
    "load_example": {"en": "Load example", "de": "Beispiel laden", "fil": "I-load ang halimbawa"},
    "reset_all": {"en": "Reset all", "de": "Alles zurücksetzen", "fil": "I-reset lahat"},
    "toggle_active": {"en": "Use in calculation", "de": "In Berechnung verwenden", "fil": "Gamitin sa kalkulasyon"},
    "edit_item": {"en": "Edit {name}", "de": "{name} bearbeiten", "fil": "I-edit ang {name}"},
    "row_hint": {"en": "Tap a row to edit it. The switch decides whether it is used.",
                 "de": "Zeile antippen zum Bearbeiten. Der Schalter bestimmt, ob sie verwendet wird.",
                 "fil": "I-tap ang hilera para i-edit. Ang switch ang nagpapasya kung gagamitin ito."},
    # ------------------------------------------------------------------ step 2
    "step2": {"en": "Value range", "de": "Wertebereich", "fil": "Saklaw ng halaga"},
    "continuous": {"en": "continuous ≥ 0", "de": "stetig ≥ 0", "fil": "tuloy-tuloy ≥ 0"},
    "integer": {"en": "integer ℕ0", "de": "ganzzahlig ℕ0", "fil": "integer ℕ0"},
    "type_LP": {"en": "Linear programming (LP)", "de": "Lineare Optimierung (LP)", "fil": "Linear programming (LP)"},
    "type_ILP": {"en": "Integer linear programming (ILP)", "de": "Ganzzahlige lineare Optimierung (ILP)",
                 "fil": "Integer linear programming (ILP)"},
    "type_MILP": {"en": "Mixed-integer linear programming (MILP)", "de": "Gemischt-ganzzahlige lineare Optimierung (MILP)",
                  "fil": "Mixed-integer linear programming (MILP)"},
    "nonneg_note": {"en": "x1 and x2 are always ≥ 0.", "de": "x1 und x2 sind immer ≥ 0.",
                    "fil": "Ang x1 at x2 ay laging ≥ 0."},
    # ------------------------------------------------------------------ step 3
    "step3": {"en": "Solve & analyse", "de": "Lösen & analysieren", "fil": "Lutasin at suriin"},
    "run_opt": {"en": "Run linear optimization", "de": "Lineare Optimierung starten",
                "fil": "Simulan ang linear optimization"},
    "run_sens": {"en": "Run sensitivity analysis", "de": "Sensitivitätsanalyse starten",
                 "fil": "Simulan ang sensitivity analysis"},
    "need_objective": {"en": "Needs an active objective function.", "de": "Benötigt eine aktive Zielfunktion.",
                       "fil": "Kailangan ng aktibong objective function."},
    "need_constraint": {"en": "Needs at least one active constraint.",
                        "de": "Benötigt mindestens eine aktive Nebenbedingung.",
                        "fil": "Kailangan ng kahit isang aktibong constraint."},
    "need_optimum": {"en": "Available after a successful linear optimization.",
                     "de": "Möglich nach einer erfolgreichen linearen Optimierung.",
                     "fil": "Magagamit pagkatapos ng matagumpay na linear optimization."},
    "status_ready": {"en": "ready", "de": "bereit", "fil": "handa na"},
    "status_open": {"en": "incomplete", "de": "unvollständig", "fil": "kulang pa"},
    "status_solved": {"en": "solved", "de": "gelöst", "fil": "nalutas na"},
    "status_analysed": {"en": "analysed", "de": "analysiert", "fil": "nasuri na"},
    # ------------------------------------------------------------------ graph & results
    "graph": {"en": "Graphical solution", "de": "Graphische Lösung", "fil": "Grapikong solusyon"},
    "save_png": {"en": "Save as PNG", "de": "Als PNG speichern", "fil": "I-save bilang PNG"},
    "results": {"en": "Results", "de": "Ergebnisse", "fil": "Mga resulta"},
    "tab_solution": {"en": "Solution", "de": "Lösung", "fil": "Solusyon"},
    "tab_sensitivity": {"en": "Sensitivity", "de": "Sensitivität", "fil": "Sensitivity"},
    "tab_description": {"en": "Description", "de": "Beschreibung", "fil": "Paglalarawan"},
    "empty_graph": {"en": "Add an objective function and a constraint — the graph appears here.",
                    "de": "Füge eine Zielfunktion und eine Nebenbedingung hinzu – hier erscheint der Graph.",
                    "fil": "Magdagdag ng objective function at constraint — lalabas dito ang graph."},
    "empty_solution": {"en": "Run the linear optimization to see the optimum here.",
                       "de": "Starte die lineare Optimierung, um hier das Optimum zu sehen.",
                       "fil": "Simulan ang linear optimization para makita rito ang optimum."},
    "empty_sensitivity": {"en": "Run the sensitivity analysis after the optimization to see shadow prices and coefficient ranges here.",
                          "de": "Starte nach der Optimierung die Sensitivitätsanalyse, um hier Schattenpreise und Koeffizientenbereiche zu sehen.",
                          "fil": "Pagkatapos ng optimization, simulan ang sensitivity analysis para makita rito ang mga shadow price at saklaw ng coefficient."},
    "empty_description": {"en": "The description appears once the problem has an objective function and a constraint.",
                          "de": "Die Beschreibung erscheint, sobald das Problem eine Zielfunktion und eine Nebenbedingung hat.",
                          "fil": "Lalabas ang paglalarawan kapag may objective function at constraint na ang problema."},
    "optimal_value": {"en": "Optimal value {name}", "de": "Optimaler Zielwert {name}", "fil": "Optimal na halaga ng {name}"},
    "problem_is": {"en": "Problem type: {type}", "de": "Problemtyp: {type}", "fil": "Uri ng problema: {type}"},
    "col_constraint": {"en": "Constraint", "de": "Nebenbedingung", "fil": "Constraint"},
    "col_status": {"en": "Status", "de": "Status", "fil": "Status"},
    "col_lhs": {"en": "Value vs. b", "de": "Wert vs. b", "fil": "Halaga vs. b"},
    "col_b": {"en": "b", "de": "b", "fil": "b"},
    "col_slack": {"en": "Slack", "de": "Schlupf", "fil": "Slack"},
    "binding": {"en": "binding", "de": "bindend", "fil": "binding"},
    "non_binding": {"en": "non-binding", "de": "nicht bindend", "fil": "non-binding"},
    "solution_sentence": {"en": "The optimum lies at x1 = {x1} and x2 = {x2}; the objective function {name} reaches {value} there.",
                          "de": "Das Optimum liegt bei x1 = {x1} und x2 = {x2}; die Zielfunktion {name} erreicht dort {value}.",
                          "fil": "Ang optimum ay nasa x1 = {x1} at x2 = {x2}; doon umaabot ang objective function na {name} sa {value}."},
    "binding_sentence": {"en": "Binding constraints (slack 0) determine the optimum: {names}.",
                         "de": "Bindende Nebenbedingungen (Schlupf 0) bestimmen das Optimum: {names}.",
                         "fil": "Ang mga binding constraint (slack 0) ang nagtatakda ng optimum: {names}."},
    "infeasible": {"en": "No feasible solution: the active constraints contradict each other. Change or deactivate a constraint.",
                   "de": "Keine zulässige Lösung: Die aktiven Nebenbedingungen widersprechen sich. Ändere oder deaktiviere eine Nebenbedingung.",
                   "fil": "Walang feasible na solusyon: nagkakasalungat ang mga aktibong constraint. Baguhin o i-deactivate ang isang constraint."},
    "unbounded": {"en": "The problem is unbounded: the objective function can improve without limit. Add or change a constraint.",
                  "de": "Das Problem ist unbeschränkt: Die Zielfunktion kann sich unbegrenzt verbessern. Füge eine Nebenbedingung hinzu oder ändere eine.",
                  "fil": "Walang hangganan ang problema: maaaring gumanda nang walang limitasyon ang objective function. Magdagdag o magbago ng constraint."},
    "solver_error": {"en": "The solver could not finish. Please check your entries.",
                     "de": "Der Solver konnte nicht abschließen. Bitte prüfe deine Eingaben.",
                     "fil": "Hindi natapos ng solver. Pakisuri ang iyong mga input."},
    # sensitivity
    "shadow_title": {"en": "Shadow prices / dual prices", "de": "Schattenpreise / Dualwerte", "fil": "Shadow price / dual price"},
    "col_shadow": {"en": "Shadow price", "de": "Schattenpreis", "fil": "Shadow price"},
    "col_from": {"en": "valid from b =", "de": "gültig von b =", "fil": "balido mula b ="},
    "col_till": {"en": "to b =", "de": "bis b =", "fil": "hanggang b ="},
    "limits_title": {"en": "Objective function coefficient ranges", "de": "Bereiche der Zielfunktionskoeffizienten",
                     "fil": "Saklaw ng mga coefficient ng objective function"},
    "col_variable": {"en": "Variable", "de": "Variable", "fil": "Variable"},
    "col_coef": {"en": "Coefficient", "de": "Koeffizient", "fil": "Coefficient"},
    "col_lower": {"en": "from", "de": "von", "fil": "mula"},
    "col_upper": {"en": "to", "de": "bis", "fil": "hanggang"},
    "shadow_sentence": {"en": "If b of {name} rises by 1, the objective value changes by {price} — as long as b stays between {lo} and {hi}.",
                        "de": "Steigt b von {name} um 1, ändert sich der Zielwert um {price} – solange b zwischen {lo} und {hi} bleibt.",
                        "fil": "Kapag tumaas nang 1 ang b ng {name}, magbabago ang halaga ng objective function nang {price} — basta't nasa pagitan ng {lo} at {hi} ang b."},
    "shadow_zero_sentence": {"en": "{name} has slack, so its shadow price is 0: a little more b would not change the optimum.",
                             "de": "{name} hat Schlupf, daher ist ihr Schattenpreis 0: etwas mehr b würde das Optimum nicht verändern.",
                             "fil": "May slack ang {name}, kaya 0 ang shadow price nito: hindi magbabago ang optimum kahit dagdagan nang kaunti ang b."},
    "limits_sentence": {"en": "The optimum stays at x1 = {x1}, x2 = {x2} as long as c1 stays between {c1lo} and {c1hi} and c2 between {c2lo} and {c2hi} (each changed on its own).",
                        "de": "Das Optimum bleibt bei x1 = {x1}, x2 = {x2}, solange c1 zwischen {c1lo} und {c1hi} und c2 zwischen {c2lo} und {c2hi} bleibt (jeweils einzeln verändert).",
                        "fil": "Mananatili ang optimum sa x1 = {x1}, x2 = {x2} basta't ang c1 ay nasa pagitan ng {c1lo} at {c1hi} at ang c2 ay nasa pagitan ng {c2lo} at {c2hi} (isa-isang binabago)."},
    "not_reported": {"en": "not reported", "de": "nicht ausgegeben", "fil": "hindi naiulat"},
    "integer_note": {"en": "For ILP and MILP, lp_solve reports these values for the last LP relaxation it solved. Read them as a guide, not as exact integer results.",
                     "de": "Bei ILP und MILP gibt lp_solve diese Werte für die zuletzt gelöste LP-Relaxation aus. Lies sie als Orientierung, nicht als exakte ganzzahlige Ergebnisse.",
                     "fil": "Para sa ILP at MILP, iniuulat ng lp_solve ang mga halagang ito para sa huling LP relaxation na nilutas nito. Gamitin bilang gabay, hindi bilang eksaktong resulta para sa integer."},
    # description
    "desc_obj": {"en": "The dashed {name} line shows all points with the same objective value {level} (dummy line). It meets the x1-axis at {i1} and the x2-axis at {i2}. Moving it parallel in the direction of {dir} leads to the optimum.",
                 "de": "Die gestrichelte Linie {name} zeigt alle Punkte mit demselben Zielwert {level} (Dummy-Linie). Sie schneidet die x1-Achse bei {i1} und die x2-Achse bei {i2}. Parallel in Richtung {dir} verschoben, führt sie zum Optimum.",
                 "fil": "Ipinapakita ng putol-putol na linyang {name} ang lahat ng punto na may parehong halaga ng objective {level} (dummy line). Tumatama ito sa x1-axis sa {i1} at sa x2-axis sa {i2}. Kapag inilipat nang parallel patungo sa {dir}, aabot ito sa optimum."},
    "dir_max": {"en": "larger values", "de": "größerer Werte", "fil": "mas malalaking halaga"},
    "dir_min": {"en": "smaller values", "de": "kleinerer Werte", "fil": "mas maliliit na halaga"},
    "desc_con": {"en": "{name}: {formula}. The line meets the x1-axis at {i1} and the x2-axis at {i2}.",
                 "de": "{name}: {formula}. Die Gerade schneidet die x1-Achse bei {i1} und die x2-Achse bei {i2}.",
                 "fil": "{name}: {formula}. Tumatama ang linya sa x1-axis sa {i1} at sa x2-axis sa {i2}."},
    "desc_con_h": {"en": "{name}: {formula}. The line runs parallel to the x1-axis at x2 = {i2}.",
                   "de": "{name}: {formula}. Die Gerade verläuft parallel zur x1-Achse bei x2 = {i2}.",
                   "fil": "{name}: {formula}. Parallel sa x1-axis ang linya sa x2 = {i2}."},
    "desc_con_v": {"en": "{name}: {formula}. The line runs parallel to the x2-axis at x1 = {i1}.",
                   "de": "{name}: {formula}. Die Gerade verläuft parallel zur x2-Achse bei x1 = {i1}.",
                   "fil": "{name}: {formula}. Parallel sa x2-axis ang linya sa x1 = {i1}."},
    "no_intercept": {"en": "nowhere", "de": "nirgends", "fil": "wala"},
    "desc_region": {"en": "The grey area is the feasible region: every point there satisfies all active constraints and x1, x2 ≥ 0.",
                    "de": "Die graue Fläche ist der zulässige Bereich: Jeder Punkt dort erfüllt alle aktiven Nebenbedingungen und x1, x2 ≥ 0.",
                    "fil": "Ang abong bahagi ang feasible region: bawat punto roon ay sumusunod sa lahat ng aktibong constraint at x1, x2 ≥ 0."},
    "desc_region_int": {"en": "The grey points (or lines) are the feasible solutions: they satisfy all active constraints and the chosen integer conditions.",
                        "de": "Die grauen Punkte (bzw. Linien) sind die zulässigen Lösungen: Sie erfüllen alle aktiven Nebenbedingungen und die gewählten Ganzzahligkeitsbedingungen.",
                        "fil": "Ang mga abong punto (o linya) ang mga feasible na solusyon: sumusunod sila sa lahat ng aktibong constraint at sa piniling kondisyon ng integer."},
    "desc_thinned": {"en": "The range is large, so only every n-th integer value is drawn.",
                     "de": "Der Bereich ist groß, daher wird nur jeder n-te ganzzahlige Wert gezeichnet.",
                     "fil": "Malaki ang saklaw, kaya bawat ika-n na integer lamang ang iginuhit."},
    "desc_heading_functions": {"en": "Functions in the graph", "de": "Funktionen im Graphen", "fil": "Mga function sa graph"},
    "desc_heading_solution": {"en": "Optimum", "de": "Optimum", "fil": "Optimum"},
    # ------------------------------------------------------------------ plot
    "plot_region": {"en": "Feasible region", "de": "Zulässiger Bereich", "fil": "Feasible region"},
    "plot_points": {"en": "Feasible solutions", "de": "Zulässige Lösungen", "fil": "Mga feasible na solusyon"},
    "plot_optimum": {"en": "Optimum", "de": "Optimum", "fil": "Optimum"},
    "plot_dummy": {"en": "{name} (dummy)", "de": "{name} (Dummy)", "fil": "{name} (dummy)"},
    "plot_optimized": {"en": "{name} (optimized)", "de": "{name} (optimiert)", "fil": "{name} (optimized)"},
    "plot_shift": {"en": "Shift", "de": "Verschiebung", "fil": "Paglipat"},
    # ------------------------------------------------------------------ modals
    "cancel": {"en": "Cancel", "de": "Abbrechen", "fil": "Kanselahin"},
    "save": {"en": "Save", "de": "Speichern", "fil": "I-save"},
    "delete": {"en": "Delete", "de": "Löschen", "fil": "Burahin"},
    "close": {"en": "Close", "de": "Schließen", "fil": "Isara"},
    "new_objective": {"en": "New objective function", "de": "Neue Zielfunktion", "fil": "Bagong objective function"},
    "edit_objective": {"en": "Edit objective function", "de": "Zielfunktion bearbeiten", "fil": "I-edit ang objective function"},
    "new_constraint": {"en": "New constraint", "de": "Neue Nebenbedingung", "fil": "Bagong constraint"},
    "edit_constraint": {"en": "Edit constraint", "de": "Nebenbedingung bearbeiten", "fil": "I-edit ang constraint"},
    "name": {"en": "Name", "de": "Name", "fil": "Pangalan"},
    "coef_c1": {"en": "Coefficient c1 (for x1)", "de": "Koeffizient c1 (für x1)", "fil": "Coefficient c1 (para sa x1)"},
    "coef_c2": {"en": "Coefficient c2 (for x2)", "de": "Koeffizient c2 (für x2)", "fil": "Coefficient c2 (para sa x2)"},
    "coef_a1": {"en": "Coefficient a1 (for x1)", "de": "Koeffizient a1 (für x1)", "fil": "Coefficient a1 (para sa x1)"},
    "coef_a2": {"en": "Coefficient a2 (for x2)", "de": "Koeffizient a2 (für x2)", "fil": "Coefficient a2 (para sa x2)"},
    "sense": {"en": "Goal", "de": "Ziel", "fil": "Layunin"},
    "maximize": {"en": "maximize", "de": "maximieren", "fil": "i-maximize"},
    "minimize": {"en": "minimize", "de": "minimieren", "fil": "i-minimize"},
    "operator": {"en": "Comparison", "de": "Vergleich", "fil": "Paghahambing"},
    "rhs_b": {"en": "Right-hand side b", "de": "Rechte Seite b", "fil": "Kanang bahagi b"},
    "preview": {"en": "Preview", "de": "Vorschau", "fil": "Silip"},
    "err_name": {"en": "Enter a name.", "de": "Gib einen Namen ein.", "fil": "Maglagay ng pangalan."},
    "err_name_taken": {"en": "This name is already used.", "de": "Dieser Name ist schon vergeben.",
                       "fil": "Nagamit na ang pangalang ito."},
    "err_number": {"en": "{field}: enter a number ≥ 0.", "de": "{field}: Gib eine Zahl ≥ 0 ein.",
                   "fil": "{field}: maglagay ng numerong ≥ 0."},
    "err_both_zero": {"en": "At least one coefficient must be greater than 0.",
                      "de": "Mindestens ein Koeffizient muss größer als 0 sein.",
                      "fil": "Kailangang mas malaki sa 0 ang kahit isang coefficient."},
    "nonneg_inputs": {"en": "All values must be ≥ 0.", "de": "Alle Werte müssen ≥ 0 sein.",
                      "fil": "Dapat ≥ 0 ang lahat ng halaga."},
    # png
    "png_title": {"en": "Save graph as PNG", "de": "Graph als PNG speichern", "fil": "I-save ang graph bilang PNG"},
    "file_name": {"en": "File name", "de": "Dateiname", "fil": "Pangalan ng file"},
    "dpi": {"en": "Resolution (DPI)", "de": "Auflösung (DPI)", "fil": "Resolusyon (DPI)"},
    "download_png": {"en": "Download PNG", "de": "PNG herunterladen", "fil": "I-download ang PNG"},
    "dpi_hint": {"en": "150 DPI suits slides, 300 DPI suits print.", "de": "150 DPI passt für Folien, 300 DPI für den Druck.",
                 "fil": "Bagay ang 150 DPI sa slides, 300 DPI sa pag-print."},
    # import / export
    "export_title": {"en": "Export", "de": "Exportieren", "fil": "I-export"},
    "export_text": {"en": "Saves the active objective function and constraints as an .lp file.",
                    "de": "Speichert die aktive Zielfunktion und die aktiven Nebenbedingungen als .lp-Datei.",
                    "fil": "Sine-save ang aktibong objective function at mga constraint bilang .lp file."},
    "download_lp": {"en": "Download .lp file", "de": ".lp-Datei herunterladen", "fil": "I-download ang .lp file"},
    "import_title": {"en": "Import", "de": "Importieren", "fil": "I-import"},
    "import_text": {"en": "Loads an .lp file. This replaces the current problem.",
                    "de": "Lädt eine .lp-Datei. Das ersetzt das aktuelle Problem.",
                    "fil": "Naglo-load ng .lp file. Papalitan nito ang kasalukuyang problema."},
    "choose_file": {"en": "Choose .lp file", "de": ".lp-Datei auswählen", "fil": "Pumili ng .lp file"},
    "import_btn": {"en": "Import", "de": "Importieren", "fil": "I-import"},
    "export_needs": {"en": "Export needs an active objective function and at least one active constraint.",
                     "de": "Für den Export braucht es eine aktive Zielfunktion und mindestens eine aktive Nebenbedingung.",
                     "fil": "Kailangan ng aktibong objective function at kahit isang aktibong constraint para mag-export."},
    # reset
    "reset_title": {"en": "Reset all?", "de": "Alles zurücksetzen?", "fil": "I-reset lahat?"},
    "reset_text": {"en": "This removes all functions and results.", "de": "Damit werden alle Funktionen und Ergebnisse entfernt.",
                   "fil": "Mabubura nito ang lahat ng function at resulta."},
    "reset_btn": {"en": "Reset", "de": "Zurücksetzen", "fil": "I-reset"},
    "example_replace": {"en": "Loading the example replaces the current problem.",
                        "de": "Das Beispiel ersetzt das aktuelle Problem.",
                        "fil": "Papalitan ng halimbawa ang kasalukuyang problema."},
    # ------------------------------------------------------------------ notifications
    "n_obj_added": {"en": "Objective function added.", "de": "Zielfunktion hinzugefügt.", "fil": "Naidagdag ang objective function."},
    "n_con_added": {"en": "Constraint added.", "de": "Nebenbedingung hinzugefügt.", "fil": "Naidagdag ang constraint."},
    "n_saved": {"en": "Changes saved.", "de": "Änderungen gespeichert.", "fil": "Na-save ang mga pagbabago."},
    "n_deleted": {"en": "{name} deleted.", "de": "{name} gelöscht.", "fil": "Nabura ang {name}."},
    "n_reset": {"en": "All data has been reset.", "de": "Alle Daten wurden zurückgesetzt.", "fil": "Na-reset ang lahat ng data."},
    "n_example": {"en": "Example loaded.", "de": "Beispiel geladen.", "fil": "Na-load ang halimbawa."},
    "n_imported": {"en": "File imported.", "de": "Datei importiert.", "fil": "Na-import ang file."},
    "n_import_failed": {"en": "The file could not be read. Line: {line}", "de": "Die Datei konnte nicht gelesen werden. Zeile: {line}",
                        "fil": "Hindi mabasa ang file. Linya: {line}"},
    "n_import_none": {"en": "Choose an .lp file first.", "de": "Wähle zuerst eine .lp-Datei aus.", "fil": "Pumili muna ng .lp file."},
    "n_import_negative": {"en": "The file contains negative values; OptiSense only supports values ≥ 0.",
                          "de": "Die Datei enthält negative Werte; OptiSense unterstützt nur Werte ≥ 0.",
                          "fil": "May negatibong halaga ang file; ≥ 0 lamang ang suportado ng OptiSense."},
    "n_optimized": {"en": "Linear optimization completed.", "de": "Lineare Optimierung abgeschlossen.",
                    "fil": "Tapos na ang linear optimization."},
    "n_sens_done": {"en": "Sensitivity analysis completed.", "de": "Sensitivitätsanalyse abgeschlossen.",
                    "fil": "Tapos na ang sensitivity analysis."},
    "n_lpsolve_missing": {"en": "lp_solve could not be started on this system.",
                          "de": "lp_solve konnte auf diesem System nicht gestartet werden.",
                          "fil": "Hindi mapatakbo ang lp_solve sa system na ito."},
    "n_lpsolve_timeout": {"en": "The problem took too long to solve.", "de": "Die Berechnung hat zu lange gedauert.",
                          "fil": "Masyadong natagalan ang paglutas."},
    "n_one_objective": {"en": "Only one objective function can be active; {name} is now active.",
                        "de": "Es kann nur eine Zielfunktion aktiv sein; jetzt ist {name} aktiv.",
                        "fil": "Isang objective function lang ang maaaring aktibo; aktibo na ngayon ang {name}."},
    # ------------------------------------------------------------------ guide
    "guide_about": {"en": "About OptiSense", "de": "Über OptiSense", "fil": "Tungkol sa OptiSense"},
    "guide_lp": {"en": "Linear programming", "de": "Lineare Optimierung", "fil": "Linear programming"},
    "guide_sens": {"en": "Sensitivity analysis", "de": "Sensitivitätsanalyse", "fil": "Sensitivity analysis"},
    "guide_example": {"en": "Example problem", "de": "Beispielproblem", "fil": "Halimbawang problema"},
    "guide_steps": {"en": "How to use OptiSense", "de": "So benutzt du OptiSense", "fil": "Paano gamitin ang OptiSense"},
    "guide_import": {"en": "Import, export and PNG", "de": "Import, Export und PNG", "fil": "Import, export at PNG"},
}

# Long guide texts (HTML fragments). Only <p>, <ul>, <li>, <b>, <code>, <h3> are used.
GUIDE = {
    "about": {
        "en": """<p>OptiSense helps you understand linear programming (LP), integer linear programming (ILP) and mixed-integer linear programming (MILP) with two variables — including sensitivity analysis. It is a teaching tool: you enter a small problem, see it as a graph, solve it and read what the result means.</p>
<p>OptiSense was developed by Peter Oliver Ruhland as part of the bachelor thesis “Shiny in Python: Eine Anwendung zur interaktiven Visualisierung, Lösung und Untersuchung der Sensitivität einfacher LP- und (M)ILP-Probleme mit scipy.optimize.milp und lp_solve”.</p>
<p>Optimization uses <code>scipy.optimize.milp</code>; sensitivity analysis uses the open-source solver lp_solve, originally developed by Michel Berkelaar (Eindhoven University of Technology) with Jeroen Dirks, Kjell Eikland, Peter Notebaert and Juergen Ebert (<a href="https://lpsolve.sourceforge.net/5.5/" target="_blank" rel="noopener">lpsolve.sourceforge.net</a>). The app is built with Shiny for Python, matplotlib, NumPy and SciPy.</p>""",
        "de": """<p>OptiSense hilft dir, lineare Optimierung (LP), ganzzahlige lineare Optimierung (ILP) und gemischt-ganzzahlige lineare Optimierung (MILP) mit zwei Variablen zu verstehen – einschließlich Sensitivitätsanalyse. Es ist ein Lernwerkzeug: Du gibst ein kleines Problem ein, siehst es als Graph, löst es und liest ab, was das Ergebnis bedeutet.</p>
<p>OptiSense wurde von Peter Oliver Ruhland im Rahmen der Bachelorarbeit „Shiny in Python: Eine Anwendung zur interaktiven Visualisierung, Lösung und Untersuchung der Sensitivität einfacher LP- und (M)ILP-Probleme mit scipy.optimize.milp und lp_solve“ entwickelt.</p>
<p>Die Optimierung nutzt <code>scipy.optimize.milp</code>, die Sensitivitätsanalyse den Open-Source-Solver lp_solve, ursprünglich entwickelt von Michel Berkelaar (TU Eindhoven) mit Jeroen Dirks, Kjell Eikland, Peter Notebaert und Juergen Ebert (<a href="https://lpsolve.sourceforge.net/5.5/" target="_blank" rel="noopener">lpsolve.sourceforge.net</a>). Die App basiert auf Shiny for Python, matplotlib, NumPy und SciPy.</p>""",
        "fil": """<p>Tinutulungan ka ng OptiSense na maunawaan ang linear programming (LP), integer linear programming (ILP) at mixed-integer linear programming (MILP) na may dalawang variable — kasama ang sensitivity analysis. Isa itong kasangkapan sa pag-aaral: maglalagay ka ng maliit na problema, makikita mo ito bilang graph, lulutasin mo ito, at babasahin mo kung ano ang ibig sabihin ng resulta.</p>
<p>Binuo ni Peter Oliver Ruhland ang OptiSense bilang bahagi ng kanyang bachelor thesis na “Shiny in Python: Eine Anwendung zur interaktiven Visualisierung, Lösung und Untersuchung der Sensitivität einfacher LP- und (M)ILP-Probleme mit scipy.optimize.milp und lp_solve”.</p>
<p>Gumagamit ang optimization ng <code>scipy.optimize.milp</code>; ang sensitivity analysis ay gumagamit ng open-source na solver na lp_solve, na orihinal na binuo ni Michel Berkelaar (Eindhoven University of Technology) kasama sina Jeroen Dirks, Kjell Eikland, Peter Notebaert at Juergen Ebert (<a href="https://lpsolve.sourceforge.net/5.5/" target="_blank" rel="noopener">lpsolve.sourceforge.net</a>). Ginawa ang app gamit ang Shiny for Python, matplotlib, NumPy at SciPy.</p>""",
    },
    "lp": {
        "en": """<p>Linear programming finds the best value — for example the highest profit or the lowest cost — of a <b>linear objective function</b> while a set of <b>linear constraints</b> is respected.</p>
<p>OptiSense works with two decision variables, x1 and x2, so every problem can be drawn:</p>
<ul><li>Objective function: F = c1·x1 + c2·x2 → max or min</li>
<li>Constraint: a1·x1 + a2·x2 ≤ b (or ≥ b, = b)</li>
<li>Non-negativity: x1 ≥ 0, x2 ≥ 0</li></ul>
<p><b>LP:</b> x1 and x2 may take any real value (continuous) — for example 12.5 hours.</p>
<p><b>ILP:</b> x1 and x2 must be whole numbers (ℕ0) — for example a number of tables.</p>
<p><b>MILP:</b> one variable is a whole number, the other continuous.</p>
<p>Graphically, each constraint is a line that cuts the plane in two; the points that satisfy all constraints form the feasible region. The optimum of an LP lies on a corner of this region.</p>""",
        "de": """<p>Lineare Optimierung sucht den besten Wert – zum Beispiel den höchsten Gewinn oder die niedrigsten Kosten – einer <b>linearen Zielfunktion</b>, wobei eine Reihe von <b>linearen Nebenbedingungen</b> eingehalten wird.</p>
<p>OptiSense arbeitet mit zwei Entscheidungsvariablen, x1 und x2, damit jedes Problem gezeichnet werden kann:</p>
<ul><li>Zielfunktion: F = c1·x1 + c2·x2 → max oder min</li>
<li>Nebenbedingung: a1·x1 + a2·x2 ≤ b (oder ≥ b, = b)</li>
<li>Nichtnegativität: x1 ≥ 0, x2 ≥ 0</li></ul>
<p><b>LP:</b> x1 und x2 dürfen jeden reellen Wert annehmen (stetig) – zum Beispiel 12,5 Stunden.</p>
<p><b>ILP:</b> x1 und x2 müssen ganze Zahlen sein (ℕ0) – zum Beispiel eine Anzahl Tische.</p>
<p><b>MILP:</b> Eine Variable ist ganzzahlig, die andere stetig.</p>
<p>Grafisch ist jede Nebenbedingung eine Gerade, die die Ebene in zwei Hälften teilt; die Punkte, die alle Nebenbedingungen erfüllen, bilden den zulässigen Bereich. Das Optimum eines LP liegt auf einer Ecke dieses Bereichs.</p>""",
        "fil": """<p>Hinahanap ng linear programming ang pinakamainam na halaga — halimbawa ang pinakamataas na kita o pinakamababang gastos — ng isang <b>linear na objective function</b> habang sinusunod ang ilang <b>linear na constraint</b>.</p>
<p>Gumagamit ang OptiSense ng dalawang decision variable, x1 at x2, para maiguhit ang bawat problema:</p>
<ul><li>Objective function: F = c1·x1 + c2·x2 → max o min</li>
<li>Constraint: a1·x1 + a2·x2 ≤ b (o ≥ b, = b)</li>
<li>Non-negativity: x1 ≥ 0, x2 ≥ 0</li></ul>
<p><b>LP:</b> maaaring kahit anong real na halaga ang x1 at x2 (tuloy-tuloy) — halimbawa 12.5 oras.</p>
<p><b>ILP:</b> dapat buong numero ang x1 at x2 (ℕ0) — halimbawa bilang ng mesa.</p>
<p><b>MILP:</b> buong numero ang isang variable, tuloy-tuloy ang isa.</p>
<p>Sa graph, bawat constraint ay isang linyang naghahati sa plane sa dalawa; ang mga puntong sumusunod sa lahat ng constraint ang bumubuo sa feasible region. Nasa isang sulok ng rehiyong ito ang optimum ng isang LP.</p>""",
    },
    "sens": {
        "en": """<p>Sensitivity analysis asks: how does the optimum react when a number in the problem changes? OptiSense shows three parts.</p>
<p><b>Slack and binding constraints.</b> Slack is the unused capacity of a constraint at the optimum. A constraint with slack 0 is <b>binding</b>: it actually limits the solution. A constraint with slack &gt; 0 is <b>non-binding</b>.</p>
<p><b>Shadow prices (dual prices).</b> The shadow price says how much the objective value changes when b of a constraint rises by one unit, everything else unchanged. It holds only within the stated range of b. Non-binding constraints have a shadow price of 0.</p>
<p><b>Objective function coefficient ranges.</b> Each coefficient c1, c2 may move within a range without moving the optimum to another corner.</p>""",
        "de": """<p>Die Sensitivitätsanalyse fragt: Wie reagiert das Optimum, wenn sich eine Zahl im Problem ändert? OptiSense zeigt drei Teile.</p>
<p><b>Schlupf und bindende Nebenbedingungen.</b> Schlupf ist die ungenutzte Kapazität einer Nebenbedingung im Optimum. Eine Nebenbedingung mit Schlupf 0 ist <b>bindend</b>: Sie begrenzt die Lösung tatsächlich. Eine mit Schlupf &gt; 0 ist <b>nicht bindend</b>.</p>
<p><b>Schattenpreise (Dualwerte).</b> Der Schattenpreis gibt an, um wie viel sich der Zielwert ändert, wenn b einer Nebenbedingung um eine Einheit steigt und alles andere gleich bleibt. Er gilt nur innerhalb des angegebenen Bereichs von b. Nicht bindende Nebenbedingungen haben den Schattenpreis 0.</p>
<p><b>Bereiche der Zielfunktionskoeffizienten.</b> Jeder Koeffizient c1, c2 darf sich innerhalb eines Bereichs bewegen, ohne dass das Optimum in eine andere Ecke wandert.</p>""",
        "fil": """<p>Tinatanong ng sensitivity analysis: paano tutugon ang optimum kapag nagbago ang isang numero sa problema? Tatlong bahagi ang ipinapakita ng OptiSense.</p>
<p><b>Slack at binding constraint.</b> Ang slack ay ang hindi nagamit na kapasidad ng isang constraint sa optimum. Ang constraint na may slack 0 ay <b>binding</b>: talagang nililimitahan nito ang solusyon. Ang may slack &gt; 0 ay <b>non-binding</b>.</p>
<p><b>Shadow price (dual price).</b> Sinasabi ng shadow price kung gaano magbabago ang halaga ng objective kapag tumaas nang isang unit ang b ng isang constraint, habang walang ibang nagbabago. Balido lamang ito sa loob ng ibinigay na saklaw ng b. 0 ang shadow price ng mga non-binding constraint.</p>
<p><b>Saklaw ng mga coefficient ng objective function.</b> Maaaring gumalaw ang bawat coefficient c1, c2 sa loob ng isang saklaw nang hindi lumilipat ang optimum sa ibang sulok.</p>""",
    },
    "example": {
        "en": """<p>The example comes from Domschke et al., <i>Einführung in Operations Research</i>, 9th edition (2015).</p>
<p>A company makes two products, P1 and P2. Production is limited by a shared machine, a perishable raw material (720 units in stock) and the assembly capacity for P2. The contribution margin is 10 per unit of P1 and 20 per unit of P2.</p>
<ul><li>Objective function: F = 10·x1 + 20·x2 → max</li>
<li>C1 (machine): x1 + x2 ≤ 100</li>
<li>C2 (raw material): 6·x1 + 9·x2 ≤ 720</li>
<li>C3 (assembly P2): x2 ≤ 60</li>
<li>x1, x2 ≥ 0, both continuous</li></ul>
<p>The optimum is x1 = 30, x2 = 60 with F = 1,500. C2 and C3 are binding.</p>""",
        "de": """<p>Das Beispiel stammt aus Domschke et al., <i>Einführung in Operations Research</i>, 9. Auflage (2015).</p>
<p>Ein Unternehmen stellt zwei Produkte her, P1 und P2. Die Produktion ist begrenzt durch eine gemeinsam genutzte Maschine, einen verderblichen Rohstoff (720 Einheiten auf Lager) und die Montagekapazität für P2. Der Deckungsbeitrag beträgt 10 je Einheit P1 und 20 je Einheit P2.</p>
<ul><li>Zielfunktion: F = 10·x1 + 20·x2 → max</li>
<li>NB1 (Maschine): x1 + x2 ≤ 100</li>
<li>NB2 (Rohstoff): 6·x1 + 9·x2 ≤ 720</li>
<li>NB3 (Montage P2): x2 ≤ 60</li>
<li>x1, x2 ≥ 0, beide stetig</li></ul>
<p>Das Optimum liegt bei x1 = 30, x2 = 60 mit F = 1.500. NB2 und NB3 sind bindend.</p>""",
        "fil": """<p>Mula ang halimbawa sa Domschke et al., <i>Einführung in Operations Research</i>, ika-9 na edisyon (2015).</p>
<p>Gumagawa ang isang kompanya ng dalawang produkto, P1 at P2. Nililimitahan ang produksyon ng isang makinang pinagsasaluhan, isang raw material na madaling masira (720 unit ang nasa stock) at ng kapasidad sa pag-assemble ng P2. Ang contribution margin ay 10 bawat unit ng P1 at 20 bawat unit ng P2.</p>
<ul><li>Objective function: F = 10·x1 + 20·x2 → max</li>
<li>C1 (makina): x1 + x2 ≤ 100</li>
<li>C2 (raw material): 6·x1 + 9·x2 ≤ 720</li>
<li>C3 (assembly ng P2): x2 ≤ 60</li>
<li>x1, x2 ≥ 0, parehong tuloy-tuloy</li></ul>
<p>Ang optimum ay x1 = 30, x2 = 60 na may F = 1,500. Binding ang C2 at C3.</p>""",
    },
    "steps": {
        "en": """<h3>1 · Enter problem</h3>
<p>Add one objective function and your constraints. Each appears as a row with its colour from the graph. Tap a row to change or delete it; the switch decides whether it is used. Only one objective function can be active at a time.</p>
<h3>2 · Value range</h3>
<p>Choose once for x1 and x2 whether they are continuous or integer. OptiSense shows the resulting problem type (LP, ILP or MILP).</p>
<h3>3 · Solve &amp; analyse</h3>
<p>The graph updates as soon as you change something. Run the linear optimization to find the optimum; then run the sensitivity analysis. Results appear in the tabs Solution, Sensitivity and Description. Any change to the problem clears old results.</p>
<h3>Tips</h3>
<ul><li>“Load example” fills in the textbook example.</li>
<li>The ? next to each step opens the matching part of this guide.</li>
<li>The language can be switched at any time at the top right; your entries are kept.</li></ul>""",
        "de": """<h3>1 · Problem eingeben</h3>
<p>Füge eine Zielfunktion und deine Nebenbedingungen hinzu. Jede erscheint als Zeile mit ihrer Farbe aus dem Graphen. Tippe eine Zeile an, um sie zu ändern oder zu löschen; der Schalter bestimmt, ob sie verwendet wird. Es kann immer nur eine Zielfunktion aktiv sein.</p>
<h3>2 · Wertebereich</h3>
<p>Lege einmal für x1 und x2 fest, ob sie stetig oder ganzzahlig sind. OptiSense zeigt den daraus folgenden Problemtyp (LP, ILP oder MILP).</p>
<h3>3 · Lösen &amp; analysieren</h3>
<p>Der Graph aktualisiert sich, sobald du etwas änderst. Starte die lineare Optimierung, um das Optimum zu finden, danach die Sensitivitätsanalyse. Die Ergebnisse stehen in den Reitern Lösung, Sensitivität und Beschreibung. Jede Änderung am Problem verwirft alte Ergebnisse.</p>
<h3>Tipps</h3>
<ul><li>„Beispiel laden“ trägt das Lehrbuchbeispiel ein.</li>
<li>Das ? neben jedem Schritt öffnet den passenden Teil dieser Anleitung.</li>
<li>Die Sprache lässt sich jederzeit oben rechts umstellen; deine Eingaben bleiben erhalten.</li></ul>""",
        "fil": """<h3>1 · Ilagay ang problema</h3>
<p>Magdagdag ng isang objective function at ng iyong mga constraint. Lalabas ang bawat isa bilang hilera na may kulay nito mula sa graph. I-tap ang hilera para baguhin o burahin ito; ang switch ang nagpapasya kung gagamitin ito. Isang objective function lang ang maaaring aktibo sa isang pagkakataon.</p>
<h3>2 · Saklaw ng halaga</h3>
<p>Piliin nang isang beses para sa x1 at x2 kung tuloy-tuloy o integer ang mga ito. Ipapakita ng OptiSense ang uri ng problemang lalabas (LP, ILP o MILP).</p>
<h3>3 · Lutasin at suriin</h3>
<p>Nag-a-update ang graph sa sandaling may baguhin ka. Simulan ang linear optimization para hanapin ang optimum; pagkatapos ay ang sensitivity analysis. Lalabas ang mga resulta sa mga tab na Solusyon, Sensitivity at Paglalarawan. Binubura ng anumang pagbabago sa problema ang mga lumang resulta.</p>
<h3>Mga tip</h3>
<ul><li>Pinupunan ng “I-load ang halimbawa” ang halimbawa mula sa aklat.</li>
<li>Binubuksan ng ? sa tabi ng bawat hakbang ang katugmang bahagi ng gabay na ito.</li>
<li>Mapapalitan ang wika anumang oras sa kanang itaas; mananatili ang iyong mga input.</li></ul>""",
    },
    "import": {
        "en": """<p><b>Save as PNG</b> (in the header of the graph) downloads the current graph. Choose 150 DPI for slides or 300 DPI for print. Your browser saves the file in its download folder.</p>
<p><b>Import &amp; export</b> (in step 1) saves the active problem as an .lp file in lp_solve's LP format, or loads such a file. Importing replaces the current problem. Files exported by earlier OptiSense versions can be imported too.</p>
<p>Example of a file:</p>
<p><code>max: 10 x1 + 20 x2;<br>C1: 1 x1 + 1 x2 &lt;= 100;<br>C2: 6 x1 + 9 x2 &lt;= 720;<br>C3: 0 x1 + 1 x2 &lt;= 60;<br>int x1;</code></p>""",
        "de": """<p><b>Als PNG speichern</b> (im Kopf des Graphen) lädt den aktuellen Graphen herunter. Wähle 150 DPI für Folien oder 300 DPI für den Druck. Der Browser speichert die Datei in seinem Download-Ordner.</p>
<p><b>Import &amp; Export</b> (in Schritt 1) speichert das aktive Problem als .lp-Datei im LP-Format von lp_solve oder lädt eine solche Datei. Der Import ersetzt das aktuelle Problem. Auch Dateien aus früheren OptiSense-Versionen lassen sich importieren.</p>
<p>Beispiel einer Datei:</p>
<p><code>max: 10 x1 + 20 x2;<br>NB1: 1 x1 + 1 x2 &lt;= 100;<br>NB2: 6 x1 + 9 x2 &lt;= 720;<br>NB3: 0 x1 + 1 x2 &lt;= 60;<br>int x1;</code></p>""",
        "fil": """<p>Dina-download ng <b>I-save bilang PNG</b> (sa itaas ng graph) ang kasalukuyang graph. Piliin ang 150 DPI para sa slides o 300 DPI para sa pag-print. Ise-save ng browser ang file sa download folder nito.</p>
<p>Sine-save ng <b>Import at export</b> (sa hakbang 1) ang aktibong problema bilang .lp file sa LP format ng lp_solve, o naglo-load ng ganitong file. Papalitan ng import ang kasalukuyang problema. Maaari ring i-import ang mga file mula sa mas lumang bersyon ng OptiSense.</p>
<p>Halimbawa ng file:</p>
<p><code>max: 10 x1 + 20 x2;<br>C1: 1 x1 + 1 x2 &lt;= 100;<br>C2: 6 x1 + 9 x2 &lt;= 720;<br>C3: 0 x1 + 1 x2 &lt;= 60;<br>int x1;</code></p>""",
    },
}

GUIDE_ORDER = [("steps", "guide_steps"), ("lp", "guide_lp"), ("sens", "guide_sens"),
               ("example", "guide_example"), ("import", "guide_import"), ("about", "guide_about")]

# Default names for new functions, per language
DEFAULT_NAMES = {
    "objective": {"en": "F", "de": "F", "fil": "F"},
    "constraint": {"en": "C{n}", "de": "NB{n}", "fil": "C{n}"},
}

# Constraint names of the textbook example, per language
EXAMPLE_NAMES = {"en": ["C1", "C2", "C3"], "de": ["NB1", "NB2", "NB3"], "fil": ["C1", "C2", "C3"]}


def norm_lang(lang):
    return lang if lang in LANGS else DEFAULT_LANG


def t(lang, key, **kwargs):
    entry = TEXT.get(key)
    if entry is None:
        return key
    text = entry.get(norm_lang(lang)) or entry[DEFAULT_LANG]
    return text.format(**kwargs) if kwargs else text


def guide(lang, topic):
    return GUIDE[topic].get(norm_lang(lang)) or GUIDE[topic][DEFAULT_LANG]


def fmt_num(value, lang, digits=4):
    """Number for display: up to `digits` decimals, trailing zeros removed, locale separators.
    German uses 1.500,5; English and Filipino use 1,500.5."""
    if value is None:
        return "–"
    if value == float("inf"):
        return "∞"
    if value == float("-inf"):
        return "−∞"
    v = round(float(value), digits)
    if v == 0:
        v = 0.0
    s = f"{v:,.{digits}f}".rstrip("0").rstrip(".")
    if norm_lang(lang) == "de":
        s = s.replace(",", "\u0000").replace(".", ",").replace("\u0000", ".")
    return s.replace("-", "−")


def client_dictionary():
    """The short texts as {lang: {key: text}} for the browser-side translator."""
    out = {code: {} for code in LANGS}
    for key, entry in TEXT.items():
        for code in LANGS:
            out[code][key] = entry.get(code) or entry[DEFAULT_LANG]
    return json.dumps(out, ensure_ascii=False)
