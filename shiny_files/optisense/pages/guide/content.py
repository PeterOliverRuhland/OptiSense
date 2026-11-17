"""The sections of the page “Guide” in English and German (HTML fragments using only <p>, <ul>, <ol>, <li>, <b>, <i>, <code>, <h3>, <a>),
their order and their figures. The ? buttons of “Model & solution” show the same sections as help dialogs."""

GUIDE = {
    "steps": {
        "en": """<p>OptiSense takes you from a problem to its solution in three steps. Everything happens on the page “Model &amp; solution”: the steps on the left, the graph in the middle, the results on the right. On a smartphone they are shown one below the other.</p>
<h3>1 · Enter problem</h3>
<p>Use “+ New” to add an objective function and one or more constraints (up to 2 objective functions and 5 constraints). Click a row to change or delete it. The switch on the right takes a function out of the calculation without deleting it. Only one objective function is active at a time. “Example” briefly describes the example problem of this guide and then loads it.</p>
<h3>2 · Variable types</h3>
<p>Choose for x1 and x2 whether they are continuous or integer. See “Variable types” below.</p>
<h3>3 · Solve &amp; analyze</h3>
<p>The graph is redrawn after every change. “Run linear optimization” calculates the optimum; after that you can run the sensitivity analysis. The results appear on the right in the tabs Solution, Sensitivity and Description. A blue button shows that its result is up to date. When you change the problem, the results are cleared and the buttons turn white again.</p>
<h3>Good to know</h3>
<ul><li>The ? next to each step explains exactly that step.</li>
<li>You can switch the language at the top right at any time; your entries are kept.</li>
<li>All numbers must be ≥ 0.</li></ul>""",
        "de": """<p>OptiSense führt dich in drei Schritten von der Aufgabe zur Lösung. Alles passiert auf der Seite „Modell &amp; Lösung“: links die Schritte, in der Mitte der Graph, rechts die Ergebnisse. Auf dem Smartphone stehen sie untereinander.</p>
<h3>1 · Problem eingeben</h3>
<p>Lege mit „+ Neu“ eine Zielfunktion und eine oder mehrere Nebenbedingungen an (höchstens 2 Zielfunktionen und 5 Nebenbedingungen). Ein Klick auf eine Zeile öffnet sie zum Ändern oder Löschen. Mit dem Schalter rechts nimmst du eine Funktion aus der Rechnung, ohne sie zu löschen. Es ist immer nur eine Zielfunktion aktiv. „Beispiel“ beschreibt kurz das Beispielproblem dieser Anleitung und lädt es dann.</p>
<h3>2 · Wertebereich</h3>
<p>Lege für x1 und x2 fest, ob sie stetig oder ganzzahlig sind. Mehr dazu unter „Wertebereich“.</p>
<h3>3 · Lösen &amp; analysieren</h3>
<p>Der Graph zeichnet sich nach jeder Änderung neu. „Lineare Optimierung starten“ berechnet das Optimum; danach kannst du die Sensitivitätsanalyse starten. Die Ergebnisse stehen rechts in den Reitern Lösung, Sensitivität und Beschreibung. Ein blauer Button zeigt, dass sein Ergebnis aktuell ist. Änderst du das Problem, werden die Ergebnisse verworfen und die Buttons wieder weiß.</p>
<h3>Gut zu wissen</h3>
<ul><li>Das ? an jedem Schritt erklärt genau diesen Schritt.</li>
<li>Die Sprache kannst du oben rechts jederzeit wechseln; deine Eingaben bleiben erhalten.</li>
<li>Alle Zahlen müssen ≥ 0 sein.</li></ul>""",
    },
    "example": {
        "en": """<p>This example runs through the whole guide. “Example” in step 1 first tells its story in a few lines and then loads it. After that, a gray line below each function and above the variable types recalls the story; it disappears as soon as you change the numbers of that row. It is the burger problem of the lecture (Prof. Dr. Christian Koot, Aalen University) – on the page “Learn &amp; practice” you can solve it yourself as the practice task “Burger”.</p>
<p>Michael runs a burger diner in Aalen. He sells standard burgers for $4.50 and luxury burgers for $6.00 and looks for the daily production plan with the highest revenue. His suppliers deliver at most 500 buns, 105 kg of meat and 60 kg of vegetables per day.</p>
<ul><li>x1, x2: number of standard and luxury burgers per day</li>
<li>Objective function: Revenue = 4.5·x1 + 6·x2 → max</li>
<li>Buns: x1 + x2 ≤ 500 — every burger needs one bun.</li>
<li>Meat: 0.1·x1 + 0.3·x2 ≤ 105 — 100 g = 0.1 kg per standard burger, 300 g = 0.3 kg per luxury burger.</li>
<li>Vegetables: 0.1·x1 + 0.15·x2 ≤ 60 — 100 g per standard burger, 150 g per luxury burger.</li>
<li>x1, x2 ≥ 0 and integer — burgers are only sold whole.</li></ul>
<p><b>Result:</b> x1 = 300 standard and x2 = 200 luxury burgers with a revenue of $2,550. The lecture treats x1 and x2 as continuous; the optimal corner is whole anyway, so the result is the same.</p>""",
        "de": """<p>Dieses Beispiel zieht sich durch die ganze Anleitung. „Beispiel“ in Schritt 1 erzählt zuerst in wenigen Zeilen die Geschichte und lädt es dann. Danach erinnert eine graue Zeile unter jeder Funktion und über dem Wertebereich an die Geschichte; sie verschwindet, sobald du die Zahlen dieser Zeile änderst. Es ist das Burger-Problem aus der Vorlesung (Prof. Dr. Christian Koot, Hochschule Aalen) – auf der Seite „Lernen &amp; Üben“ kannst du es als Übungsaufgabe „Burger“ selbst lösen.</p>
<p>Michael betreibt ein Burger-Diner in Aalen. Er verkauft Standardburger für 4,50 $ und Luxusburger für 6,00 $ und sucht das tägliche Produktionsprogramm mit dem höchsten Umsatz. Seine Lieferanten liefern pro Tag höchstens 500 Brötchen, 105 kg Fleisch und 60 kg Gemüse.</p>
<ul><li>x1, x2: Anzahl Standard- bzw. Luxusburger pro Tag</li>
<li>Zielfunktion: Umsatz = 4,5·x1 + 6·x2 → max</li>
<li>Brötchen: x1 + x2 ≤ 500 – jeder Burger braucht ein Brötchen.</li>
<li>Fleisch: 0,1·x1 + 0,3·x2 ≤ 105 – 100 g = 0,1 kg je Standardburger, 300 g = 0,3 kg je Luxusburger.</li>
<li>Gemüse: 0,1·x1 + 0,15·x2 ≤ 60 – 100 g je Standardburger, 150 g je Luxusburger.</li>
<li>x1, x2 ≥ 0 und ganzzahlig – Burger gibt es nur am Stück.</li></ul>
<p><b>Ergebnis:</b> x1 = 300 Standard- und x2 = 200 Luxusburger mit einem Umsatz von 2.550 $. Die Vorlesung rechnet mit stetigen x1 und x2; die optimale Ecke ist ohnehin ganzzahlig, das Ergebnis ist also dasselbe.</p>""",
    },
    "lp": {
        "en": """<p>Linear programming looks for the best of all allowed solutions — for example the highest profit or the lowest cost. It needs three building blocks:</p>
<ul><li><b>Decision variables</b> x1 and x2: the quantities you can decide, for example production amounts.</li>
<li><b>Objective function</b> F = c1·x1 + c2·x2: to be maximized or minimized.</li>
<li><b>Constraints</b> a1·x1 + a2·x2 ≤ b (or ≥ b, = b): limits such as raw material or capacity. In addition, x1, x2 ≥ 0 always holds.</li></ul>
<p>“Linear” means that each variable only appears multiplied by a fixed number — no squares, no products such as x1·x2.</p>
<h3>The graphical solution</h3>
<p>With two variables, every problem can be drawn:</p>
<ol><li>Each constraint is a line. The allowed side is the one where the constraint holds.</li>
<li>The points that satisfy all constraints form the <b>feasible region</b> (gray).</li>
<li>The dashed green <b>objective line</b> – “F (dummy)” in the legend – joins all points with the same objective value.</li>
<li>This line is shifted in parallel — toward larger values when maximizing, toward smaller values when minimizing — until it just touches the feasible region. That point is the <b>optimum</b> (red).</li></ol>
<p>If there is an optimum, at least one optimum lies on a corner of the feasible region. In the example it is the corner x1 = 300, x2 = 200 with Revenue = 4.5·300 + 6·200 = 2,550.</p>
<p>Two special cases: if the constraints contradict each other, the region is empty and there is <b>no feasible solution</b>. If the region is open in the direction of the goal, F can improve without limit — the problem is <b>unbounded</b>.</p>""",
        "de": """<p>Lineare Optimierung sucht unter allen erlaubten Lösungen die beste – zum Beispiel den höchsten Gewinn oder die niedrigsten Kosten. Dafür braucht es drei Bausteine:</p>
<ul><li><b>Entscheidungsvariablen</b> x1 und x2: die Größen, die du festlegen kannst, zum Beispiel Produktionsmengen.</li>
<li><b>Zielfunktion</b> F = c1·x1 + c2·x2: Sie soll maximiert oder minimiert werden.</li>
<li><b>Nebenbedingungen</b> a1·x1 + a2·x2 ≤ b (oder ≥ b, = b): Grenzen wie Rohstoff oder Kapazität. Zusätzlich gilt immer x1, x2 ≥ 0.</li></ul>
<p>„Linear“ heißt: Jede Variable kommt nur mit einer festen Zahl multipliziert vor – keine Quadrate, keine Produkte wie x1·x2.</p>
<h3>Die grafische Lösung</h3>
<p>Mit zwei Variablen lässt sich jedes Problem zeichnen:</p>
<ol><li>Jede Nebenbedingung ist eine Gerade. Erlaubt ist die Seite, auf der die Bedingung erfüllt ist.</li>
<li>Die Punkte, die alle Nebenbedingungen erfüllen, bilden den <b>zulässigen Bereich</b> (grau).</li>
<li>Die gestrichelte grüne <b>Zielfunktionsgerade</b> – in der Legende „F (Dummy)“ – verbindet alle Punkte mit demselben Zielwert.</li>
<li>Diese Gerade wird parallel verschoben – beim Maximieren zu größeren Werten, beim Minimieren zu kleineren –, bis sie den zulässigen Bereich gerade noch berührt. Dieser Punkt ist das <b>Optimum</b> (rot).</li></ol>
<p>Gibt es ein Optimum, liegt mindestens eines auf einer Ecke des zulässigen Bereichs. Im Beispiel ist das die Ecke x1 = 300, x2 = 200 mit Umsatz = 4,5·300 + 6·200 = 2.550.</p>
<p>Zwei Sonderfälle: Widersprechen sich die Nebenbedingungen, ist der Bereich leer – es gibt <b>keine zulässige Lösung</b>. Ist der Bereich in Richtung des Ziels offen, kann F sich unbegrenzt verbessern – das Problem ist <b>unbeschränkt</b>.</p>""",
    },
    "range": {
        "en": """<p>Here you decide which values x1 and x2 may take. Both are always ≥ 0.</p>
<ul><li><b>continuous (ℝ≥0):</b> any value, including decimals — for example 12.5 hours.</li>
<li><b>integer (ℕ0):</b> whole numbers only — for example a number of tables.</li></ul>
<p>The choice sets the problem type shown below the two rows:</p>
<ul><li><b>LP:</b> both variables continuous.</li>
<li><b>ILP:</b> both variables integer.</li>
<li><b>MILP:</b> one integer, one continuous.</li></ul>
<p>With integer variables, the feasible region shrinks to single points (or lines for MILP). The optimum is the best of these points. It does not have to lie on a corner, and simply rounding the LP solution does not always lead to it.</p>
<p>Changing a variable type clears earlier results; run the optimization again afterwards.</p>""",
        "de": """<p>Hier legst du fest, welche Werte x1 und x2 annehmen dürfen. Beide sind immer ≥ 0.</p>
<ul><li><b>stetig (ℝ≥0):</b> jeder Wert, auch mit Nachkommastellen – zum Beispiel 12,5 Stunden.</li>
<li><b>ganzzahlig (ℕ0):</b> nur ganze Zahlen – zum Beispiel eine Anzahl Tische.</li></ul>
<p>Die Auswahl bestimmt den Problemtyp, der unter den beiden Zeilen steht:</p>
<ul><li><b>LP:</b> beide Variablen stetig.</li>
<li><b>ILP:</b> beide Variablen ganzzahlig.</li>
<li><b>MILP:</b> eine ganzzahlig, eine stetig.</li></ul>
<p>Mit ganzzahligen Variablen besteht der zulässige Bereich nur noch aus einzelnen Punkten (bei MILP aus Linien). Das Optimum ist der beste dieser Punkte. Es muss nicht auf einer Ecke liegen, und einfaches Runden der LP-Lösung führt nicht immer dorthin.</p>
<p>Eine Änderung des Wertebereichs verwirft bisherige Ergebnisse; starte die Optimierung danach erneut.</p>""",
    },
    "sens": {
        "en": """<p>Sensitivity analysis asks: what happens to the optimum when a number in the problem changes? It is available after a successful linear optimization; the results appear in the tab “Sensitivity”.</p>
<h3>Slack: binding or non-binding</h3>
<p>Slack is the capacity of a constraint that remains unused at the optimum (tab “Solution”). With slack 0 a constraint is <b>binding</b>: it limits the solution. In the example buns and vegetables are binding: all 500 buns (300 + 200) and all 60 kg of vegetables (0.1·300 + 0.15·200) are used. Meat is not binding: only 0.1·300 + 0.3·200 = 90 of 105 kg are needed, a slack of 15 kg.</p>
<h3>Shadow prices</h3>
<p>The shadow price says how much the objective value changes when the right-hand side b of a constraint rises by 1. It holds only within the stated range of b. Non-binding constraints have a shadow price of 0.</p>
<p>In the example, Buns have a shadow price of 1.5: one more bun per day raises the revenue by $1.50 (valid for b from 450 to 600). Vegetables have a shadow price of 30: one more kilogram raises the revenue by $30 (valid from 50 to 63.75 kg). Meat has a shadow price of 0 – more meat does not help.</p>
<h3>Objective function coefficient ranges</h3>
<p>Each coefficient c1, c2 may move within a range without changing the optimal solution (x1, x2); the objective value F changes with it, of course. The range holds when only one coefficient changes at a time. In the example the solution stays at x1 = 300, x2 = 200 as long as the price of a standard burger c1 is between 4 and 6.</p>
<p>For ILP and MILP these values are only a guide: lp_solve reports them for the last LP relaxation it solved. In the example this is the LP of the lecture, because its optimum is already whole.</p>""",
        "de": """<p>Die Sensitivitätsanalyse fragt: Was passiert mit dem Optimum, wenn sich eine Zahl im Problem ändert? Sie ist nach einer erfolgreichen linearen Optimierung möglich; die Ergebnisse stehen im Reiter „Sensitivität“.</p>
<h3>Schlupf: bindend oder nicht bindend</h3>
<p>Schlupf ist die Kapazität einer Nebenbedingung, die im Optimum ungenutzt bleibt (Reiter „Lösung“). Bei Schlupf 0 ist die Nebenbedingung <b>bindend</b>: Sie begrenzt die Lösung. Im Beispiel sind Brötchen und Gemüse bindend: Alle 500 Brötchen (300 + 200) und alle 60 kg Gemüse (0,1·300 + 0,15·200) werden verbraucht. Fleisch ist nicht bindend: Gebraucht werden nur 0,1·300 + 0,3·200 = 90 von 105 kg, ein Schlupf von 15 kg.</p>
<h3>Schattenpreise</h3>
<p>Der Schattenpreis gibt an, um wie viel sich der Zielwert ändert, wenn die rechte Seite b einer Nebenbedingung um 1 steigt. Er gilt nur innerhalb des angegebenen Bereichs von b. Nicht bindende Nebenbedingungen haben den Schattenpreis 0.</p>
<p>Im Beispiel haben die Brötchen den Schattenpreis 1,5: Ein Brötchen mehr pro Tag erhöht den Umsatz um 1,50 $ (gültig für b von 450 bis 600). Gemüse hat den Schattenpreis 30: Ein Kilogramm mehr erhöht den Umsatz um 30 $ (gültig von 50 bis 63,75 kg). Fleisch hat den Schattenpreis 0 – mehr Fleisch bringt nichts.</p>
<h3>Bereiche der Zielfunktionskoeffizienten</h3>
<p>Jeder Koeffizient c1, c2 darf sich in einem Bereich bewegen, ohne dass sich die optimale Lösung (x1, x2) ändert; der Zielwert F ändert sich dabei natürlich mit. Der Bereich gilt, wenn jeweils nur ein Koeffizient verändert wird. Im Beispiel bleibt die Lösung bei x1 = 300, x2 = 200, solange der Preis eines Standardburgers c1 zwischen 4 und 6 liegt.</p>
<p>Bei ILP und MILP sind diese Werte nur eine Orientierung: lp_solve gibt sie für die zuletzt gelöste LP-Relaxation aus. Im Beispiel ist das das LP der Vorlesung, weil dessen Optimum schon ganzzahlig ist.</p>""",
    },
    "import": {
        "en": """<p><b>Save as PNG</b> (at the top of the graph) downloads the current graph. Choose 150 DPI for slides or 300 DPI for print. Your browser saves the file in its download folder.</p>
<p><b>Import &amp; export</b> (in step 1) saves the active problem as an .lp file in lp_solve's LP format, or loads such a file. Importing replaces the current problem. Files exported by earlier OptiSense versions can be imported too.</p>
<p>The example as a file:</p>
<p><code>max: 4.5 x1 + 6 x2;<br>Buns: 1 x1 + 1 x2 &lt;= 500;<br>Meat: 0.1 x1 + 0.3 x2 &lt;= 105;<br>Vegetables: 0.1 x1 + 0.15 x2 &lt;= 60;<br>x1 &gt;= 0;<br>x2 &gt;= 0;<br>int x1,x2;</code></p>
<p>The last line makes x1 and x2 integer; without it, both variables are continuous.</p>""",
        "de": """<p><b>Als PNG speichern</b> (oben am Graphen) lädt den aktuellen Graphen herunter. Wähle 150 DPI für Folien oder 300 DPI für den Druck. Der Browser speichert die Datei in seinem Download-Ordner.</p>
<p><b>Import &amp; Export</b> (in Schritt 1) speichert das aktive Problem als .lp-Datei im LP-Format von lp_solve oder lädt eine solche Datei. Der Import ersetzt das aktuelle Problem. Auch Dateien aus früheren OptiSense-Versionen lassen sich importieren.</p>
<p>Das Beispiel als Datei:</p>
<p><code>max: 4.5 x1 + 6 x2;<br>Broetchen: 1 x1 + 1 x2 &lt;= 500;<br>Fleisch: 0.1 x1 + 0.3 x2 &lt;= 105;<br>Gemuese: 0.1 x1 + 0.15 x2 &lt;= 60;<br>x1 &gt;= 0;<br>x2 &gt;= 0;<br>int x1,x2;</code></p>
<p>Die letzte Zeile macht x1 und x2 ganzzahlig; ohne sie sind beide Variablen stetig. Das LP-Format kennt keine Umlaute, deshalb schreibt der Export sie aus (Brötchen → Broetchen).</p>""",
    },
    "about": {
        "en": """<p>OptiSense helps you understand linear programming (LP), integer linear programming (ILP) and mixed-integer linear programming (MILP) with two variables — including sensitivity analysis. It is a teaching tool: you enter a small problem, see it as a graph, solve it and read what the result means.</p>
<p>OptiSense 1.0 was developed by Peter Ruhland as part of his bachelor thesis “Shiny in Python: Eine Anwendung zur interaktiven Visualisierung, Lösung und Untersuchung der Sensitivität einfacher LP- und (M)ILP-Probleme mit scipy.optimize.milp und lp_solve” at Aalen University. Version 2.0 was further developed and optimized by Peter Ruhland and Robin Heissler as part of their master's studies.</p>
<p>Optimization uses <code>scipy.optimize.milp</code>; sensitivity analysis uses the open-source solver lp_solve, originally developed by Michel Berkelaar (Eindhoven University of Technology) with Jeroen Dirks, Kjell Eikland, Peter Notebaert and Juergen Ebert (<a href="https://lpsolve.sourceforge.net/5.5/" target="_blank" rel="noopener">lpsolve.sourceforge.net</a>). The app is built with Shiny for Python, matplotlib, NumPy and SciPy.</p>
<p><button type="button" class="btn btn-link os-imprint-link" data-os-imprint>Legal notice</button></p>""",
        "de": """<p>OptiSense hilft dir, lineare Optimierung (LP), ganzzahlige lineare Optimierung (ILP) und gemischt-ganzzahlige lineare Optimierung (MILP) mit zwei Variablen zu verstehen – einschließlich Sensitivitätsanalyse. Es ist ein Lernwerkzeug: Du gibst ein kleines Problem ein, siehst es als Graph, löst es und liest ab, was das Ergebnis bedeutet.</p>
<p>OptiSense 1.0 wurde von Peter Ruhland im Rahmen seiner Bachelorarbeit „Shiny in Python: Eine Anwendung zur interaktiven Visualisierung, Lösung und Untersuchung der Sensitivität einfacher LP- und (M)ILP-Probleme mit scipy.optimize.milp und lp_solve“ an der Hochschule Aalen entwickelt. Version 2.0 wurde im Rahmen des Masterstudiums von Peter Ruhland und Robin Heissler weiterentwickelt und optimiert.</p>
<p>Die Optimierung nutzt <code>scipy.optimize.milp</code>, die Sensitivitätsanalyse den Open-Source-Solver lp_solve, ursprünglich entwickelt von Michel Berkelaar (TU Eindhoven) mit Jeroen Dirks, Kjell Eikland, Peter Notebaert und Juergen Ebert (<a href="https://lpsolve.sourceforge.net/5.5/" target="_blank" rel="noopener">lpsolve.sourceforge.net</a>). Die App basiert auf Shiny for Python, matplotlib, NumPy und SciPy.</p>
<p><button type="button" class="btn btn-link os-imprint-link" data-os-imprint>Impressum</button></p>""",
    },
}

# order of the sections in the guide tab: (topic, label key)
GUIDE_ORDER = [("steps", "guide_steps"), ("example", "guide_example"), ("lp", "guide_lp"), ("range", "guide_range"),
               ("sens", "guide_sens"), ("import", "guide_import"), ("about", "guide_about")]

# picture next to a section: (file in www/guide/<lang>/, caption key)
# made by tools/guide_images.py and tools/guide_screenshots.py
FIGURES = {
    "steps": ("app.png", "fig_app"),
    "example": ("model.png", "fig_model"),
    "lp": ("solved.png", "fig_solved"),
    "range": ("integer.png", "fig_integer"),
    "sens": ("sensitivity.png", "fig_sens"),
}
