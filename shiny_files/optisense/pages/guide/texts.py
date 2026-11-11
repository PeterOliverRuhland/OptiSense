"""Short texts of the page “Guide”: tab, contents and figure captions. The sections themselves are in content.py."""

TEXT = {
    "tab_guide": {"en": "Guide", "de": "Anleitung"},
    "guide_contents": {"en": "Contents", "de": "Inhalt"},
    "guide_steps": {"en": "How to use OptiSense", "de": "So benutzt du OptiSense"},
    "guide_example": {"en": "Example problem", "de": "Beispielproblem"},
    "guide_lp": {"en": "Linear programming", "de": "Lineare Optimierung"},
    "guide_range": {"en": "Variable types", "de": "Wertebereich"},
    "guide_sens": {"en": "Sensitivity analysis", "de": "Sensitivitätsanalyse"},
    "guide_import": {"en": "Import, export and PNG", "de": "Import, Export und PNG"},
    "guide_about": {"en": "About OptiSense", "de": "Über OptiSense"},
    "fig_app": {"en": "The page “Model & solution” with the solved example: steps (left), graph (middle), results (right).",
                "de": "Die Seite „Modell & Lösung“ mit dem gelösten Beispiel: Schritte (links), Graph (Mitte), Ergebnisse (rechts)."},
    "fig_model": {"en": "The example as a graph: C1 and C2 bound the gray feasible region; the dashed green line is the objective line.",
                  "de": "Das Beispiel als Graph: NB1 und NB2 begrenzen den grauen zulässigen Bereich; die gestrichelte grüne Gerade ist die Zielfunktionsgerade."},
    "fig_solved": {"en": "The solved example: the objective line is shifted in parallel up to the corner (30 | 60), where the optimum F = 1,500 lies.",
                   "de": "Das gelöste Beispiel: Die Zielfunktionsgerade wird parallel bis zur Ecke (30 | 60) verschoben; dort liegt das Optimum F = 1.500."},
    "fig_integer": {"en": "A small ILP: F = 2·x1 + 3·x2 → max with x1 + 2·x2 ≤ 8 and 3·x1 + 2·x2 ≤ 15. Only the gray points are feasible. The optimum (2 | 3) with F = 13 is not a corner. Rounding the LP solution (3.5 | 2.25) gives at best (3 | 2) with only F = 12.",
                    "de": "Ein kleines ILP: F = 2·x1 + 3·x2 → max mit x1 + 2·x2 ≤ 8 und 3·x1 + 2·x2 ≤ 15. Zulässig sind nur die grauen Punkte. Das Optimum (2 | 3) mit F = 13 liegt auf keiner Ecke. Rundet man die LP-Lösung (3,5 | 2,25), erhält man bestenfalls (3 | 2) mit nur F = 12."},
    "fig_sens": {"en": "The tab “Sensitivity” for the example.", "de": "Der Reiter „Sensitivität“ für das Beispiel."},
}
