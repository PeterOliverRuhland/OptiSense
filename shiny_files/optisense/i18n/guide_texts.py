"""Long texts of the guide tab (HTML fragments using only <p>, <ul>, <li>, <b>, <i>, <code>, <h3>, <a>)."""

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
<li>C1 (raw material): 6·x1 + 9·x2 ≤ 720</li>
<li>C2 (assembly P2): x2 ≤ 60</li>
<li>x1, x2 ≥ 0, both continuous</li></ul>
<p>The machine constraint of the textbook (x1 + x2 ≤ 100) is left out here because it does not limit the optimum. The optimum is x1 = 30, x2 = 60 with F = 1,500; both constraints are binding.</p>""",
        "de": """<p>Das Beispiel stammt aus Domschke et al., <i>Einführung in Operations Research</i>, 9. Auflage (2015).</p>
<p>Ein Unternehmen stellt zwei Produkte her, P1 und P2. Die Produktion ist begrenzt durch eine gemeinsam genutzte Maschine, einen verderblichen Rohstoff (720 Einheiten auf Lager) und die Montagekapazität für P2. Der Deckungsbeitrag beträgt 10 je Einheit P1 und 20 je Einheit P2.</p>
<ul><li>Zielfunktion: F = 10·x1 + 20·x2 → max</li>
<li>NB1 (Rohstoff): 6·x1 + 9·x2 ≤ 720</li>
<li>NB2 (Montage P2): x2 ≤ 60</li>
<li>x1, x2 ≥ 0, beide stetig</li></ul>
<p>Die Maschinen-Nebenbedingung aus dem Lehrbuch (x1 + x2 ≤ 100) ist hier weggelassen, weil sie das Optimum nicht begrenzt. Das Optimum liegt bei x1 = 30, x2 = 60 mit F = 1.500; beide Nebenbedingungen sind bindend.</p>""",
        "fil": """<p>Mula ang halimbawa sa Domschke et al., <i>Einführung in Operations Research</i>, ika-9 na edisyon (2015).</p>
<p>Gumagawa ang isang kompanya ng dalawang produkto, P1 at P2. Nililimitahan ang produksyon ng isang makinang pinagsasaluhan, isang raw material na madaling masira (720 unit ang nasa stock) at ng kapasidad sa pag-assemble ng P2. Ang contribution margin ay 10 bawat unit ng P1 at 20 bawat unit ng P2.</p>
<ul><li>Objective function: F = 10·x1 + 20·x2 → max</li>
<li>C1 (raw material): 6·x1 + 9·x2 ≤ 720</li>
<li>C2 (assembly ng P2): x2 ≤ 60</li>
<li>x1, x2 ≥ 0, parehong tuloy-tuloy</li></ul>
<p>Hindi isinama rito ang constraint ng makina mula sa aklat (x1 + x2 ≤ 100) dahil hindi nito nililimitahan ang optimum. Ang optimum ay x1 = 30, x2 = 60 na may F = 1,500; parehong binding ang dalawang constraint.</p>""",
    },
    "steps": {
        "en": """<h3>1 · Enter problem</h3>
<p>Use “+ New” next to the headings to add up to two objective functions and up to five constraints. Each appears as a row with its colour from the graph. Tap a row to change or delete it; the switch decides whether it is used. Only one objective function is active at a time. “Example” at the top loads the textbook example.</p>
<h3>2 · Value range</h3>
<p>Choose once for x1 and x2 whether they are continuous or integer. OptiSense shows the resulting problem type (LP, ILP or MILP).</p>
<h3>3 · Solve &amp; analyse</h3>
<p>The graph updates as soon as you change something. Run the linear optimization to find the optimum; then run the sensitivity analysis. Results appear in the tabs Solution, Sensitivity and Description. Any change to the problem clears old results.</p>
<h3>Tips</h3>
<ul><li>“Example” fills in the textbook example.</li>
<li>The ? next to each step opens the matching part of this guide.</li>
<li>The language can be switched at any time at the top right; your entries are kept.</li></ul>""",
        "de": """<h3>1 · Problem eingeben</h3>
<p>Mit „+ Neu“ neben den Überschriften legst du bis zu zwei Zielfunktionen und bis zu fünf Nebenbedingungen an. Jede erscheint als Zeile mit ihrer Farbe aus dem Graphen. Tippe eine Zeile an, um sie zu ändern oder zu löschen; der Schalter bestimmt, ob sie verwendet wird. Es ist immer nur eine Zielfunktion aktiv. „Beispiel“ oben lädt das Lehrbuchbeispiel.</p>
<h3>2 · Wertebereich</h3>
<p>Lege einmal für x1 und x2 fest, ob sie stetig oder ganzzahlig sind. OptiSense zeigt den daraus folgenden Problemtyp (LP, ILP oder MILP).</p>
<h3>3 · Lösen &amp; analysieren</h3>
<p>Der Graph aktualisiert sich, sobald du etwas änderst. Starte die lineare Optimierung, um das Optimum zu finden, danach die Sensitivitätsanalyse. Die Ergebnisse stehen in den Reitern Lösung, Sensitivität und Beschreibung. Jede Änderung am Problem verwirft alte Ergebnisse.</p>
<h3>Tipps</h3>
<ul><li>„Beispiel“ trägt das Lehrbuchbeispiel ein.</li>
<li>Das ? neben jedem Schritt öffnet den passenden Teil dieser Anleitung.</li>
<li>Die Sprache lässt sich jederzeit oben rechts umstellen; deine Eingaben bleiben erhalten.</li></ul>""",
        "fil": """<h3>1 · Ilagay ang problema</h3>
<p>Gamitin ang “+ Bago” sa tabi ng mga heading para magdagdag ng hanggang dalawang objective function at hanggang limang constraint. Lalabas ang bawat isa bilang hilera na may kulay nito mula sa graph. I-tap ang hilera para baguhin o burahin ito; ang switch ang nagpapasya kung gagamitin ito. Isang objective function lang ang aktibo sa isang pagkakataon. Nilo-load ng “Halimbawa” sa itaas ang halimbawa mula sa aklat.</p>
<h3>2 · Saklaw ng halaga</h3>
<p>Piliin nang isang beses para sa x1 at x2 kung tuloy-tuloy o integer ang mga ito. Ipapakita ng OptiSense ang uri ng problemang lalabas (LP, ILP o MILP).</p>
<h3>3 · Lutasin at suriin</h3>
<p>Nag-a-update ang graph sa sandaling may baguhin ka. Simulan ang linear optimization para hanapin ang optimum; pagkatapos ay ang sensitivity analysis. Lalabas ang mga resulta sa mga tab na Solusyon, Sensitivity at Paglalarawan. Binubura ng anumang pagbabago sa problema ang mga lumang resulta.</p>
<h3>Mga tip</h3>
<ul><li>Pinupunan ng “Halimbawa” ang halimbawa mula sa aklat.</li>
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
