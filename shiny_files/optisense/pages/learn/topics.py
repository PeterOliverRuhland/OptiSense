"""More topics for the practice tasks (Robin, 2026-11-17): every list of 15 tasks gets 15 different topics, so the
start page can name every task (“Smoothie bar”, “Pizzeria” …) instead of “Farming 1 … 4”.

The fields are the same as in texts.py (_CONTEXTS for integer and continuous topics, _MIXED for mixed ones; see there
for what each field means). The rules too: things you count are integer, amounts you measure continuous; every
resource is measured (h, kg, liters, ₱ …), never counted; product pairs have no natural order (no small/large),
because the pool's numbers are random; a cost topic (engine.TOPICS: True) also tells a story with minimum
requirements (≥). English money in Philippine pesos with the unit in brackets, German in euros.
"""


def _t(en, de):
    return {"en": en, "de": de}


GOAL_MAX = _t("The contribution margin should be as large as possible.", "Der Deckungsbeitrag soll möglichst groß werden.")
GOAL_MIN = _t("The costs should be as low as possible.", "Die Kosten sollen möglichst gering sein.")
FMAX = _t("Contribution margin", "Deckungsbeitrag")
FMIN = _t("Costs", "Kosten")
MAX = {"goalmax": GOAL_MAX, "fmax": FMAX}
MIN = {"goalmin": GOAL_MIN, "fmin": FMIN}

# short names on the start page (texts topic_*)
LABELS = {
    "print": _t("Print shop", "Druckerei"), "bikes": _t("Bike shop", "Fahrradladen"), "tailor": _t("Tailor shop", "Schneiderei"),
    "phones": _t("Phone repair", "Handyreparatur"), "pottery": _t("Pottery", "Töpferei"), "boats": _t("Boat tours", "Bootstouren"),
    "flowers": _t("Flower shop", "Blumenladen"), "nursery": _t("Tree nursery", "Baumschule"), "energy": _t("Energy kits", "Energie-Sets"),
    "bus": _t("Bus lines", "Buslinien"),
    "smoothie": _t("Smoothie bar", "Smoothie-Bar"), "tea": _t("Tea house", "Teehaus"), "icecream": _t("Ice cream shop", "Eisdiele"),
    "paint": _t("Paint factory", "Farbenfabrik"), "soap": _t("Soap maker", "Seifenmanufaktur"), "chocolate": _t("Chocolate maker", "Schokoladenmanufaktur"),
    "coconut": _t("Coconut farm", "Kokosfarm"), "rice": _t("Rice mill", "Reismühle"), "fertilizer": _t("Fertilizer", "Dünger"),
    "flour": _t("Flour mill", "Getreidemühle"), "soil": _t("Garden soil", "Gartenerde"),
    "pizzeria": _t("Pizzeria", "Pizzeria"), "cafe": _t("Café", "Café"), "farmshop": _t("Farm shop", "Hofladen"),
    "fish": _t("Fish market", "Fischmarkt"), "ice": _t("Ice plant", "Eisfabrik"), "studio": _t("Music studio", "Tonstudio"),
    "laundry": _t("Laundry shop", "Wäscherei"), "candles": _t("Candle shop", "Kerzenwerkstatt"), "dairy": _t("Dairy", "Molkerei"),
    "fruit": _t("Fruit stand", "Obststand"), "butcher": _t("Butcher shop", "Metzgerei"), "hardware": _t("Hardware store", "Baumarkt"),
}


def _count(one, pl, all_):
    """Nouns of an integer topic: (singular, plural) per product in both languages, and the word for both together."""
    (one1, one2), (pl1, pl2) = one, pl
    return {"one1": one1, "one2": one2, "pl1": pl1, "pl2": pl2, "all": all_,
            "var1": _t(f"number of {pl1['en']}", f"Anzahl {pl1['de']}"), "var2": _t(f"number of {pl2['en']}", f"Anzahl {pl2['de']}")}


def _amount(var, one, pl, dom, unit, all_):
    """Nouns of a continuous topic: both products are measured in the same unit (the total row adds them up)."""
    return {"var1": var[0], "var2": var[1], "one1": one[0], "one2": one[1], "pl1": pl[0], "pl2": pl[1],
            "dom1": dom[0], "dom2": dom[1], "unit1": unit, "unit2": unit, "all": all_}


def _res(**rows):
    """Resources: r1max=(name, unit) … → r1max / u1max fields."""
    out = {}
    for key, (name, unit) in rows.items():
        out[key] = name
        out[f"u{key[1:]}"] = unit
    return out


H, MINUTES, KG = _t("h", "h"), _t("min", "min"), _t("kg", "kg")
LITERS = _t("liters", "Liter")
G100 = _t("in 100 g", "in 100 g")

CONTEXTS = {
    # ---------------------------------------------------------------- integer: things you count
    "print": {
        "title": _t("Print shop: T-shirts and mugs", "Druckerei: T-Shirts und Tassen"),
        "setting": _t("A print shop plans how many printed T-shirts (x1) and mugs (x2) to make per day.",
                      "Eine Druckerei plant, wie viele bedruckte T-Shirts (x1) und Tassen (x2) sie pro Tag herstellt."),
        **MAX, "cmax": _t("Contribution margin (in ₱10): {c1} per T-shirt, {c2} per mug.", "Deckungsbeitrag: {c1} € je T-Shirt, {c2} € je Tasse."),
        **_count((_t("T-shirt", "T-Shirt"), _t("mug", "Tasse")), (_t("T-shirts", "T-Shirts"), _t("mugs", "Tassen")), _t("items", "Artikel")),
        **_res(r1max=(_t("Ink", "Druckfarbe"), _t("in 10 ml", "in 10 ml")), r2max=(_t("Press time", "Pressenzeit"), MINUTES)),
    },
    "bikes": {
        "title": _t("Bike shop: city bikes and mountain bikes", "Fahrradladen: Stadträder und Mountainbikes"),
        "setting": _t("A bike shop assembles city bikes (x1) and mountain bikes (x2). It plans how many of each to assemble per week.",
                      "Ein Fahrradladen baut Stadträder (x1) und Mountainbikes (x2) zusammen. Er plant, wie viele davon er pro Woche montiert."),
        **MAX, "cmax": _t("Contribution margin (in ₱1,000): {c1} per city bike, {c2} per mountain bike.",
                          "Deckungsbeitrag (in 10 €): {c1} je Stadtrad, {c2} je Mountainbike."),
        **_count((_t("city bike", "Stadtrad"), _t("mountain bike", "Mountainbike")), (_t("city bikes", "Stadträder"), _t("mountain bikes", "Mountainbikes")),
                 _t("bikes", "Fahrräder")),
        **_res(r1max=(_t("Assembly time", "Montagezeit"), H), r2max=(_t("Parts budget", "Teilebudget"), _t("in ₱1,000", "in 100 €"))),
    },
    "tailor": {
        "title": _t("Tailor shop: shirts and dresses", "Schneiderei: Hemden und Kleider"),
        "setting": _t("A tailor shop plans how many shirts (x1) and dresses (x2) to sew per week.",
                      "Eine Schneiderei plant, wie viele Hemden (x1) und Kleider (x2) sie pro Woche näht."),
        **MAX, "cmax": _t("Contribution margin (in ₱100): {c1} per shirt, {c2} per dress.", "Deckungsbeitrag (in 10 €): {c1} je Hemd, {c2} je Kleid."),
        **_count((_t("shirt", "Hemd"), _t("dress", "Kleid")), (_t("shirts", "Hemden"), _t("dresses", "Kleider")), _t("garments", "Kleidungsstücke")),
        **_res(r1max=(_t("Fabric", "Stoff"), _t("m²", "m²")), r2max=(_t("Sewing time", "Nähzeit"), H)),
    },
    "phones": {
        "title": _t("Phone repair: screens and batteries", "Handyreparatur: Displays und Akkus"),
        "setting": _t("A phone repair shop plans how many screen repairs (x1) and battery changes (x2) to do per week.",
                      "Eine Handywerkstatt plant, wie viele Displayreparaturen (x1) und Akkuwechsel (x2) sie pro Woche erledigt."),
        **MAX, "cmax": _t("Contribution margin (in ₱100): {c1} per screen repair, {c2} per battery change.",
                          "Deckungsbeitrag (in 10 €): {c1} je Displayreparatur, {c2} je Akkuwechsel."),
        **_count((_t("screen repair", "Displayreparatur"), _t("battery change", "Akkuwechsel")),
                 (_t("screen repairs", "Displayreparaturen"), _t("battery changes", "Akkuwechsel")), _t("repairs", "Reparaturen")),
        **_res(r1max=(_t("Technician time", "Technikerzeit"), _t("in 10 min", "in 10 min")), r2max=(_t("Parts budget", "Teilebudget"), _t("in ₱100", "in 10 €"))),
    },
    "pottery": {
        "title": _t("Pottery: bowls and vases", "Töpferei: Schalen und Vasen"),
        "setting": _t("A pottery plans how many bowls (x1) and vases (x2) to make per week.",
                      "Eine Töpferei plant, wie viele Schalen (x1) und Vasen (x2) sie pro Woche herstellt."),
        **MAX, "cmax": _t("Contribution margin (in ₱100): {c1} per bowl, {c2} per vase.", "Deckungsbeitrag (in 10 €): {c1} je Schale, {c2} je Vase."),
        **_count((_t("bowl", "Schale"), _t("vase", "Vase")), (_t("bowls", "Schalen"), _t("vases", "Vasen")), _t("pieces", "Stücke")),
        **_res(r1max=(_t("Clay", "Ton"), KG), r2max=(_t("Kiln time", "Brennofenzeit"), H)),
    },
    "boats": {
        "title": _t("Boat tours: snorkeling trips and sunset cruises", "Bootstouren: Schnorcheltouren und Sonnenuntergangsfahrten"),
        "setting": _t("A boat operator on an island plans how many snorkeling trips (x1) and sunset cruises (x2) to offer per month.",
                      "Ein Bootsanbieter auf einer Insel plant, wie viele Schnorcheltouren (x1) und Sonnenuntergangsfahrten (x2) er pro Monat anbietet."),
        **MAX, "cmax": _t("Contribution margin (in ₱1,000): {c1} per snorkeling trip, {c2} per sunset cruise.",
                          "Deckungsbeitrag (in 10 €): {c1} je Schnorcheltour, {c2} je Sonnenuntergangsfahrt."),
        **_count((_t("snorkeling trip", "Schnorcheltour"), _t("sunset cruise", "Sonnenuntergangsfahrt")),
                 (_t("snorkeling trips", "Schnorcheltouren"), _t("sunset cruises", "Sonnenuntergangsfahrten")), _t("tours", "Touren")),
        **_res(r1max=(_t("Boat time", "Bootszeit"), H), r2max=(_t("Fuel", "Kraftstoff"), _t("in 10 liters", "in 10 Litern"))),
    },
    "flowers": {
        "title": _t("Flower shop: bouquets and flower boxes", "Blumenladen: Sträuße und Blumenkästen"),
        "setting": _t("A flower shop plans how many bouquets (x1) and flower boxes (x2) to arrange per day.",
                      "Ein Blumenladen plant, wie viele Sträuße (x1) und Blumenkästen (x2) er pro Tag gestaltet."),
        **MAX, "cmax": _t("Contribution margin (in ₱100): {c1} per bouquet, {c2} per flower box.", "Deckungsbeitrag: {c1} € je Strauß, {c2} € je Blumenkasten."),
        **_count((_t("bouquet", "Strauß"), _t("flower box", "Blumenkasten")), (_t("bouquets", "Sträuße"), _t("flower boxes", "Blumenkästen")),
                 _t("arrangements", "Stück")),
        **_res(r1max=(_t("Working time", "Arbeitszeit"), MINUTES), r2max=(_t("Ribbon", "Schleifenband"), _t("m", "m"))),
    },
    "nursery": {
        "title": _t("Tree nursery: mango and teak seedlings", "Baumschule: Mango- und Teaksetzlinge"),
        "setting": _t("A tree nursery plans how many mango seedlings (x1) and teak seedlings (x2) to grow this season.",
                      "Eine Baumschule plant, wie viele Mangosetzlinge (x1) und Teaksetzlinge (x2) sie in dieser Saison zieht."),
        "settingmin": _t("A reforestation project plans how many mango seedlings (x1) and teak seedlings (x2) to plant on a hillside.",
                         "Ein Aufforstungsprojekt plant, wie viele Mangosetzlinge (x1) und Teaksetzlinge (x2) es an einem Hang pflanzt."),
        **MAX, **MIN,
        "cmax": _t("Contribution margin (in ₱10): {c1} per mango seedling, {c2} per teak seedling.",
                   "Deckungsbeitrag: {c1} € je Mangosetzling, {c2} € je Teaksetzling."),
        "cmin": _t("Costs (in ₱10): {c1} per mango seedling, {c2} per teak seedling.", "Kosten: {c1} € je Mangosetzling, {c2} € je Teaksetzling."),
        **_count((_t("mango seedling", "Mangosetzling"), _t("teak seedling", "Teaksetzling")),
                 (_t("mango seedlings", "Mangosetzlinge"), _t("teak seedlings", "Teaksetzlinge")), _t("seedlings", "Setzlinge")),
        **_res(r1max=(_t("Potting soil", "Pflanzerde"), _t("in 10 liters", "in 10 Litern")), r2max=(_t("Watering time", "Gießzeit"), MINUTES),
               r1min=(_t("CO₂ stored later", "Später gespeichertes CO₂"), _t("in 10 kg per year", "in 10 kg pro Jahr")),
               r2min=(_t("Shade later", "Späterer Schatten"), _t("m²", "m²"))),
    },
    "energy": {
        "title": _t("Energy kits: solar kits and wind kits", "Energie-Sets: Solar- und Windsets"),
        "setting": _t("An installer plans how many solar kits (x1) and small wind kits (x2) to install per month.",
                      "Ein Installationsbetrieb plant, wie viele Solarsets (x1) und kleine Windsets (x2) er pro Monat montiert."),
        "settingmin": _t("A farm on a small island plans how many solar kits (x1) and small wind kits (x2) to buy for its own power.",
                         "Ein Bauernhof auf einer kleinen Insel plant, wie viele Solarsets (x1) und kleine Windsets (x2) er für den eigenen Strom kauft."),
        **MAX, **MIN,
        "cmax": _t("Contribution margin (in ₱1,000): {c1} per solar kit, {c2} per wind kit.", "Deckungsbeitrag (in 10 €): {c1} je Solarset, {c2} je Windset."),
        "cmin": _t("Costs (in ₱10,000): {c1} per solar kit, {c2} per wind kit.", "Kosten (in 100 €): {c1} je Solarset, {c2} je Windset."),
        **_count((_t("solar kit", "Solarset"), _t("wind kit", "Windset")), (_t("solar kits", "Solarsets"), _t("wind kits", "Windsets")),
                 _t("kits", "Sets")),
        **_res(r1max=(_t("Installation time", "Montagezeit"), H), r2max=(_t("Cable", "Kabel"), _t("in 10 m", "in 10 m")),
               r1min=(_t("Power in the dry season", "Strom in der Trockenzeit"), _t("kWh per day", "kWh pro Tag")),
               r2min=(_t("Power in the rainy season", "Strom in der Regenzeit"), _t("kWh per day", "kWh pro Tag"))),
    },
    "bus": {
        "title": _t("Bus company: two lines", "Busunternehmen: zwei Linien"),
        "setting": _t("A bus company plans how many trips to run per day on line 1 (x1) and on line 2 (x2).",
                      "Ein Busunternehmen plant, wie viele Fahrten es pro Tag auf Linie 1 (x1) und auf Linie 2 (x2) anbietet."),
        "settingmin": _t("For a school sports day, a town orders bus trips to the stadium. It plans how many trips on line 1 (x1) and on line 2 (x2) to order.",
                         "Für ein Schulsportfest bestellt eine Stadt Busfahrten zum Stadion. Sie plant, wie viele Fahrten auf Linie 1 (x1) und auf Linie 2 (x2) sie bestellt."),
        **MAX, **MIN,
        "cmax": _t("Contribution margin (in ₱1,000): {c1} per trip on line 1, {c2} per trip on line 2.",
                   "Deckungsbeitrag (in 10 €): {c1} je Fahrt auf Linie 1, {c2} je Fahrt auf Linie 2."),
        "cmin": _t("Costs (in ₱1,000): {c1} per trip on line 1, {c2} per trip on line 2.", "Kosten (in 10 €): {c1} je Fahrt auf Linie 1, {c2} je Fahrt auf Linie 2."),
        **_count((_t("trip on line 1", "Fahrt auf Linie 1"), _t("trip on line 2", "Fahrt auf Linie 2")),
                 (_t("trips on line 1", "Fahrten auf Linie 1"), _t("trips on line 2", "Fahrten auf Linie 2")), _t("trips", "Fahrten")),
        **_res(r1max=(_t("Driver time", "Fahrerzeit"), H), r2max=(_t("Fuel", "Kraftstoff"), _t("in 10 liters", "in 10 Litern")),
               r1min=(_t("Seats for the north district", "Sitzplätze für den Nordbezirk"), _t("in 10 seats", "in 10 Plätzen")),
               r2min=(_t("Seats for the south district", "Sitzplätze für den Südbezirk"), _t("in 10 seats", "in 10 Plätzen"))),
    },
    # ---------------------------------------------------------------- continuous: amounts you measure
    "smoothie": {
        "title": _t("Smoothie bar: banana and berry smoothie", "Smoothie-Bar: Bananen- und Beerensmoothie"),
        "setting": _t("A smoothie bar plans how many liters of banana smoothie (x1) and berry smoothie (x2) to blend per day.",
                      "Eine Smoothie-Bar plant, wie viele Liter Bananensmoothie (x1) und Beerensmoothie (x2) sie pro Tag mixt."),
        **MAX, "cmax": _t("Contribution margin (in ₱10): {c1} per liter of banana smoothie, {c2} per liter of berry smoothie.",
                          "Deckungsbeitrag: {c1} € je Liter Bananensmoothie, {c2} € je Liter Beerensmoothie."),
        **_amount((_t("liters of banana smoothie", "Liter Bananensmoothie"), _t("liters of berry smoothie", "Liter Beerensmoothie")),
                  (_t("liter of banana smoothie", "Liter Bananensmoothie"), _t("liter of berry smoothie", "Liter Beerensmoothie")),
                  (_t("banana smoothie", "Bananensmoothie"), _t("berry smoothie", "Beerensmoothie")),
                  (_t("banana smoothie in liters", "Bananensmoothie in Litern"), _t("berry smoothie in liters", "Beerensmoothie in Litern")), LITERS, LITERS),
        **_res(r1max=(_t("Yogurt", "Joghurt"), G100), r2max=(_t("Ice", "Eis"), G100)),
    },
    "tea": {
        "title": _t("Tea house: green tea and ginger tea", "Teehaus: Grüntee und Ingwertee"),
        "setting": _t("A tea house plans how many kilograms of green tea (x1) and ginger tea (x2) to blend and pack per week.",
                      "Ein Teehaus plant, wie viele Kilogramm Grüntee (x1) und Ingwertee (x2) es pro Woche mischt und verpackt."),
        **MAX, "cmax": _t("Contribution margin (in ₱100): {c1} per kg of green tea, {c2} per kg of ginger tea.",
                          "Deckungsbeitrag: {c1} € je kg Grüntee, {c2} € je kg Ingwertee."),
        **_amount((_t("kilograms of green tea", "Kilogramm Grüntee"), _t("kilograms of ginger tea", "Kilogramm Ingwertee")),
                  (_t("kg of green tea", "kg Grüntee"), _t("kg of ginger tea", "kg Ingwertee")), (_t("green tea", "Grüntee"), _t("ginger tea", "Ingwertee")),
                  (_t("green tea in kg", "Grüntee in kg"), _t("ginger tea in kg", "Ingwertee in kg")), KG, KG),
        **_res(r1max=(_t("Drying time", "Trocknungszeit"), H), r2max=(_t("Packing time", "Verpackungszeit"), MINUTES)),
    },
    "icecream": {
        "title": _t("Ice cream shop: vanilla and chocolate ice cream", "Eisdiele: Vanille- und Schokoladeneis"),
        "setting": _t("An ice cream shop plans how many liters of vanilla ice cream (x1) and chocolate ice cream (x2) to make per day.",
                      "Eine Eisdiele plant, wie viele Liter Vanilleeis (x1) und Schokoladeneis (x2) sie pro Tag herstellt."),
        **MAX, "cmax": _t("Contribution margin (in ₱10): {c1} per liter of vanilla ice cream, {c2} per liter of chocolate ice cream.",
                          "Deckungsbeitrag: {c1} € je Liter Vanilleeis, {c2} € je Liter Schokoladeneis."),
        **_amount((_t("liters of vanilla ice cream", "Liter Vanilleeis"), _t("liters of chocolate ice cream", "Liter Schokoladeneis")),
                  (_t("liter of vanilla ice cream", "Liter Vanilleeis"), _t("liter of chocolate ice cream", "Liter Schokoladeneis")),
                  (_t("vanilla ice cream", "Vanilleeis"), _t("chocolate ice cream", "Schokoladeneis")),
                  (_t("vanilla ice cream in liters", "Vanilleeis in Litern"), _t("chocolate ice cream in liters", "Schokoladeneis in Litern")), LITERS, LITERS),
        **_res(r1max=(_t("Milk", "Milch"), _t("in 100 ml", "in 100 ml")), r2max=(_t("Machine time", "Maschinenzeit"), MINUTES)),
    },
    "paint": {
        "title": _t("Paint factory: wall paint and wood stain", "Farbenfabrik: Wandfarbe und Holzlasur"),
        "setting": _t("A paint factory plans how many liters of wall paint (x1) and wood stain (x2) to mix per day.",
                      "Eine Farbenfabrik plant, wie viele Liter Wandfarbe (x1) und Holzlasur (x2) sie pro Tag mischt."),
        **MAX, "cmax": _t("Contribution margin (in ₱100): {c1} per liter of wall paint, {c2} per liter of wood stain.",
                          "Deckungsbeitrag: {c1} € je Liter Wandfarbe, {c2} € je Liter Holzlasur."),
        **_amount((_t("liters of wall paint", "Liter Wandfarbe"), _t("liters of wood stain", "Liter Holzlasur")),
                  (_t("liter of wall paint", "Liter Wandfarbe"), _t("liter of wood stain", "Liter Holzlasur")),
                  (_t("wall paint", "Wandfarbe"), _t("wood stain", "Holzlasur")),
                  (_t("wall paint in liters", "Wandfarbe in Litern"), _t("wood stain in liters", "Holzlasur in Litern")), LITERS, LITERS),
        **_res(r1max=(_t("Pigment", "Pigment"), G100), r2max=(_t("Mixing time", "Mischzeit"), MINUTES)),
    },
    "soap": {
        "title": _t("Soap maker: liquid soap and shampoo", "Seifenmanufaktur: Flüssigseife und Shampoo"),
        "setting": _t("A small soap maker plans how many liters of liquid soap (x1) and shampoo (x2) to make per week.",
                      "Eine kleine Seifenmanufaktur plant, wie viele Liter Flüssigseife (x1) und Shampoo (x2) sie pro Woche herstellt."),
        **MAX, "cmax": _t("Contribution margin (in ₱100): {c1} per liter of liquid soap, {c2} per liter of shampoo.",
                          "Deckungsbeitrag: {c1} € je Liter Flüssigseife, {c2} € je Liter Shampoo."),
        **_amount((_t("liters of liquid soap", "Liter Flüssigseife"), _t("liters of shampoo", "Liter Shampoo")),
                  (_t("liter of liquid soap", "Liter Flüssigseife"), _t("liter of shampoo", "Liter Shampoo")),
                  (_t("liquid soap", "Flüssigseife"), _t("shampoo", "Shampoo")),
                  (_t("liquid soap in liters", "Flüssigseife in Litern"), _t("shampoo in liters", "Shampoo in Litern")), LITERS, LITERS),
        **_res(r1max=(_t("Coconut oil", "Kokosöl"), G100), r2max=(_t("Bottling time", "Abfüllzeit"), MINUTES)),
    },
    "chocolate": {
        "title": _t("Chocolate maker: dark and milk chocolate", "Schokoladenmanufaktur: Zartbitter- und Vollmilchschokolade"),
        "setting": _t("A chocolate maker plans how many kilograms of dark chocolate (x1) and milk chocolate (x2) to make per week.",
                      "Eine Schokoladenmanufaktur plant, wie viele Kilogramm Zartbitterschokolade (x1) und Vollmilchschokolade (x2) sie pro Woche herstellt."),
        **MAX, "cmax": _t("Contribution margin (in ₱100): {c1} per kg of dark chocolate, {c2} per kg of milk chocolate.",
                          "Deckungsbeitrag: {c1} € je kg Zartbitterschokolade, {c2} € je kg Vollmilchschokolade."),
        **_amount((_t("kilograms of dark chocolate", "Kilogramm Zartbitterschokolade"), _t("kilograms of milk chocolate", "Kilogramm Vollmilchschokolade")),
                  (_t("kg of dark chocolate", "kg Zartbitterschokolade"), _t("kg of milk chocolate", "kg Vollmilchschokolade")),
                  (_t("dark chocolate", "Zartbitterschokolade"), _t("milk chocolate", "Vollmilchschokolade")),
                  (_t("dark chocolate in kg", "Zartbitterschokolade in kg"), _t("milk chocolate in kg", "Vollmilchschokolade in kg")), KG, KG),
        **_res(r1max=(_t("Cocoa", "Kakao"), G100), r2max=(_t("Machine time", "Maschinenzeit"), MINUTES)),
    },
    "coconut": {
        "title": _t("Coconut farm: coconut oil and coconut vinegar", "Kokosfarm: Kokosöl und Kokosessig"),
        "setting": _t("A coconut farm plans how many liters of coconut oil (x1) and coconut vinegar (x2) to produce per week.",
                      "Eine Kokosfarm plant, wie viele Liter Kokosöl (x1) und Kokosessig (x2) sie pro Woche herstellt."),
        **MAX, "cmax": _t("Contribution margin (in ₱100): {c1} per liter of coconut oil, {c2} per liter of coconut vinegar.",
                          "Deckungsbeitrag: {c1} € je Liter Kokosöl, {c2} € je Liter Kokosessig."),
        **_amount((_t("liters of coconut oil", "Liter Kokosöl"), _t("liters of coconut vinegar", "Liter Kokosessig")),
                  (_t("liter of coconut oil", "Liter Kokosöl"), _t("liter of coconut vinegar", "Liter Kokosessig")),
                  (_t("coconut oil", "Kokosöl"), _t("coconut vinegar", "Kokosessig")),
                  (_t("coconut oil in liters", "Kokosöl in Litern"), _t("coconut vinegar in liters", "Kokosessig in Litern")), LITERS, LITERS),
        **_res(r1max=(_t("Coconut meat", "Kokosfleisch"), KG), r2max=(_t("Working time", "Arbeitszeit"), MINUTES)),
    },
    "rice": {
        "title": _t("Rice mill: white rice and brown rice", "Reismühle: weißer und brauner Reis"),
        "setting": _t("A rice mill plans how many tons of white rice (x1) and brown rice (x2) to mill per week.",
                      "Eine Reismühle plant, wie viele Tonnen weißen Reis (x1) und braunen Reis (x2) sie pro Woche mahlt."),
        "settingmin": _t("A school feeding program buys white rice (x1) and brown rice (x2) for one month. Both are measured in tons.",
                         "Ein Schulspeisungsprogramm kauft für einen Monat weißen Reis (x1) und braunen Reis (x2). Beides wird in Tonnen gemessen."),
        **MAX, **MIN,
        "cmax": _t("Contribution margin (in ₱10,000): {c1} per ton of white rice, {c2} per ton of brown rice.",
                   "Deckungsbeitrag (in 100 €): {c1} je Tonne weißen Reis, {c2} je Tonne braunen Reis."),
        "cmin": _t("Costs (in ₱10,000): {c1} per ton of white rice, {c2} per ton of brown rice.",
                   "Kosten (in 100 €): {c1} je Tonne weißen Reis, {c2} je Tonne braunen Reis."),
        **_amount((_t("tons of white rice", "Tonnen weißer Reis"), _t("tons of brown rice", "Tonnen brauner Reis")),
                  (_t("ton of white rice", "Tonne weißen Reis"), _t("ton of brown rice", "Tonne braunen Reis")),
                  (_t("white rice", "weißer Reis"), _t("brown rice", "brauner Reis")),
                  (_t("white rice in tons", "weißer Reis in Tonnen"), _t("brown rice in tons", "brauner Reis in Tonnen")), _t("tons", "Tonnen"), _t("tons", "Tonnen")),
        **_res(r1max=(_t("Mill time", "Mühlenzeit"), H), r2max=(_t("Drying space", "Trockenfläche"), _t("in 100 m²", "in 100 m²")),
               r1min=(_t("Food energy", "Nahrungsenergie"), _t("in 1,000,000 kcal", "in Mio. kcal")), r2min=(_t("Fiber", "Ballaststoffe"), _t("in 10 kg", "in 10 kg"))),
    },
    "fertilizer": {
        "title": _t("Fertilizer: organic and mineral fertilizer", "Dünger: organischer und mineralischer Dünger"),
        "setting": _t("A fertilizer plant plans how many tons of organic fertilizer (x1) and mineral fertilizer (x2) to produce per week.",
                      "Ein Düngerwerk plant, wie viele Tonnen organischen Dünger (x1) und mineralischen Dünger (x2) es pro Woche herstellt."),
        "settingmin": _t("A rice farmer buys organic fertilizer (x1) and mineral fertilizer (x2) for one season. Both are measured in tons.",
                         "Ein Reisbauer kauft für eine Saison organischen Dünger (x1) und mineralischen Dünger (x2). Beides wird in Tonnen gemessen."),
        **MAX, **MIN,
        "cmax": _t("Contribution margin (in ₱10,000): {c1} per ton of organic fertilizer, {c2} per ton of mineral fertilizer.",
                   "Deckungsbeitrag (in 100 €): {c1} je Tonne organischen Dünger, {c2} je Tonne mineralischen Dünger."),
        "cmin": _t("Costs (in ₱10,000): {c1} per ton of organic fertilizer, {c2} per ton of mineral fertilizer.",
                   "Kosten (in 100 €): {c1} je Tonne organischen Dünger, {c2} je Tonne mineralischen Dünger."),
        **_amount((_t("tons of organic fertilizer", "Tonnen organischer Dünger"), _t("tons of mineral fertilizer", "Tonnen mineralischer Dünger")),
                  (_t("ton of organic fertilizer", "Tonne organischen Dünger"), _t("ton of mineral fertilizer", "Tonne mineralischen Dünger")),
                  (_t("organic fertilizer", "organischer Dünger"), _t("mineral fertilizer", "mineralischer Dünger")),
                  (_t("organic fertilizer in tons", "organischer Dünger in Tonnen"), _t("mineral fertilizer in tons", "mineralischer Dünger in Tonnen")),
                  _t("tons", "Tonnen"), _t("tons", "Tonnen")),
        **_res(r1max=(_t("Machine time", "Maschinenzeit"), H), r2max=(_t("Bagging time", "Absackzeit"), H),
               r1min=(_t("Nitrogen", "Stickstoff"), _t("in 10 kg", "in 10 kg")), r2min=(_t("Phosphorus", "Phosphor"), _t("in 10 kg", "in 10 kg"))),
    },
    "flour": {
        "title": _t("Flour mill: wheat flour and corn flour", "Getreidemühle: Weizenmehl und Maismehl"),
        "setting": _t("A flour mill plans how many tons of wheat flour (x1) and corn flour (x2) to produce per week.",
                      "Eine Getreidemühle plant, wie viele Tonnen Weizenmehl (x1) und Maismehl (x2) sie pro Woche herstellt."),
        "settingmin": _t("A bread factory buys wheat flour (x1) and corn flour (x2) for one month. Both are measured in tons.",
                         "Eine Brotfabrik kauft für einen Monat Weizenmehl (x1) und Maismehl (x2). Beides wird in Tonnen gemessen."),
        **MAX, **MIN,
        "cmax": _t("Contribution margin (in ₱10,000): {c1} per ton of wheat flour, {c2} per ton of corn flour.",
                   "Deckungsbeitrag (in 100 €): {c1} je Tonne Weizenmehl, {c2} je Tonne Maismehl."),
        "cmin": _t("Costs (in ₱10,000): {c1} per ton of wheat flour, {c2} per ton of corn flour.",
                   "Kosten (in 100 €): {c1} je Tonne Weizenmehl, {c2} je Tonne Maismehl."),
        **_amount((_t("tons of wheat flour", "Tonnen Weizenmehl"), _t("tons of corn flour", "Tonnen Maismehl")),
                  (_t("ton of wheat flour", "Tonne Weizenmehl"), _t("ton of corn flour", "Tonne Maismehl")),
                  (_t("wheat flour", "Weizenmehl"), _t("corn flour", "Maismehl")),
                  (_t("wheat flour in tons", "Weizenmehl in Tonnen"), _t("corn flour in tons", "Maismehl in Tonnen")), _t("tons", "Tonnen"), _t("tons", "Tonnen")),
        **_res(r1max=(_t("Mill time", "Mühlenzeit"), H), r2max=(_t("Packing time", "Verpackungszeit"), H),
               r1min=(_t("Protein", "Eiweiß"), _t("in 10 kg", "in 10 kg")), r2min=(_t("Fiber", "Ballaststoffe"), _t("in 10 kg", "in 10 kg"))),
    },
    "soil": {
        "title": _t("Garden soil: compost and coco peat", "Gartenerde: Kompost und Kokoserde"),
        "setting": _t("A garden center plans how many tons of compost (x1) and coco peat (x2) to bag and sell per month.",
                      "Ein Gartencenter plant, wie viele Tonnen Kompost (x1) und Kokoserde (x2) es pro Monat abfüllt und verkauft."),
        "settingmin": _t("A plant nursery buys compost (x1) and coco peat (x2) for its pots. Both are measured in tons.",
                         "Eine Gärtnerei kauft Kompost (x1) und Kokoserde (x2) für ihre Töpfe. Beides wird in Tonnen gemessen."),
        **MAX, **MIN,
        "cmax": _t("Contribution margin (in ₱1,000): {c1} per ton of compost, {c2} per ton of coco peat.",
                   "Deckungsbeitrag (in 10 €): {c1} je Tonne Kompost, {c2} je Tonne Kokoserde."),
        "cmin": _t("Costs (in ₱1,000): {c1} per ton of compost, {c2} per ton of coco peat.", "Kosten (in 10 €): {c1} je Tonne Kompost, {c2} je Tonne Kokoserde."),
        **_amount((_t("tons of compost", "Tonnen Kompost"), _t("tons of coco peat", "Tonnen Kokoserde")),
                  (_t("ton of compost", "Tonne Kompost"), _t("ton of coco peat", "Tonne Kokoserde")),
                  (_t("compost", "Kompost"), _t("coco peat", "Kokoserde")),
                  (_t("compost in tons", "Kompost in Tonnen"), _t("coco peat in tons", "Kokoserde in Tonnen")), _t("tons", "Tonnen"), _t("tons", "Tonnen")),
        **_res(r1max=(_t("Sieving time", "Siebzeit"), H), r2max=(_t("Bagging time", "Abfüllzeit"), H),
               r1min=(_t("Nutrients", "Nährstoffe"), _t("in 10 kg", "in 10 kg")), r2min=(_t("Water storage", "Wasserspeicher"), _t("in 1,000 liters", "in 1.000 Litern"))),
    },
}


# ---------------------------------------------------------------- mixed: one product you count, one you measure
def _product(var, one, pl, q, dom=None, unit=None):
    out = {"var": var, "one": one, "pl": pl, "q": q}
    if dom:
        out.update(dom=dom, unit=unit)
    return out


MIXED = {
    "pizzeria": {
        "count": _product(_t("number of pizzas", "Anzahl Pizzen"), _t("pizza", "Pizza"), _t("pizzas", "Pizzen"), _t("how many pizzas", "wie viele Pizzen")),
        "amount": _product(_t("liters of lemonade", "Liter Limonade"), _t("liter of lemonade", "Liter Limonade"), _t("lemonade", "Limonade"),
                           _t("how many liters of lemonade", "wie viele Liter Limonade"), _t("lemonade in liters", "Limonade in Litern"), LITERS),
        "title": _t("Pizzeria: {pl1} and {pl2}", "Pizzeria: {pl1} und {pl2}"),
        "setting": _t("A pizzeria plans {q1} (x1) and {q2} (x2) to make per evening.", "Eine Pizzeria plant, {q1} (x1) und {q2} (x2) sie pro Abend zubereitet."),
        "settingmin": _t("For a school fair, the parents' association plans {q1} (x1) and {q2} (x2) to order from a pizzeria.",
                         "Für ein Schulfest plant der Elternverein, {q1} (x1) und {q2} (x2) er bei einer Pizzeria bestellt."),
        **MAX, **MIN,
        "cmax": _t("Contribution margin (in ₱10): {c1} per {one1}, {c2} per {one2}.", "Deckungsbeitrag: {c1} € je {one1}, {c2} € je {one2}."),
        "cmin": _t("Costs (in ₱10): {c1} per {one1}, {c2} per {one2}.", "Kosten: {c1} € je {one1}, {c2} € je {one2}."),
        **_res(r1max=(_t("Kitchen time", "Küchenzeit"), MINUTES), r2max=(_t("Ingredient budget", "Zutatenbudget"), _t("in ₱10", "€")),
               r3max=(_t("Delivery weight", "Liefergewicht"), KG),
               r1min=(_t("Food energy", "Nahrungsenergie"), _t("in 100 kcal", "in 100 kcal")),
               r2min=(_t("Carbohydrates", "Kohlenhydrate"), _t("in 10 g", "in 10 g")),
               r3min=(_t("Delivery weight", "Liefergewicht"), KG)),
    },
    "cafe": {
        "count": _product(_t("number of sandwiches", "Anzahl Sandwiches"), _t("sandwich", "Sandwich"), _t("sandwiches", "Sandwiches"),
                          _t("how many sandwiches", "wie viele Sandwiches")),
        "amount": _product(_t("liters of iced coffee", "Liter Eiskaffee"), _t("liter of iced coffee", "Liter Eiskaffee"), _t("iced coffee", "Eiskaffee"),
                           _t("how many liters of iced coffee", "wie viele Liter Eiskaffee"), _t("iced coffee in liters", "Eiskaffee in Litern"), LITERS),
        "title": _t("Café: {pl1} and {pl2}", "Café: {pl1} und {pl2}"),
        "setting": _t("A café plans {q1} (x1) and {q2} (x2) to prepare per day.", "Ein Café plant, {q1} (x1) und {q2} (x2) es pro Tag zubereitet."),
        **MAX, "cmax": _t("Contribution margin (in ₱10): {c1} per {one1}, {c2} per {one2}.", "Deckungsbeitrag: {c1} € je {one1}, {c2} € je {one2}."),
        **_res(r1max=(_t("Ingredient budget", "Zutatenbudget"), _t("in ₱10", "€")), r2max=(_t("Staff time", "Personalzeit"), MINUTES),
               r3max=(_t("Packaging budget", "Verpackungsbudget"), _t("in ₱10", "€"))),
    },
    "farmshop": {
        "count": _product(_t("number of egg cartons", "Anzahl Eierkartons"), _t("egg carton", "Eierkarton"), _t("egg cartons", "Eierkartons"),
                          _t("how many egg cartons", "wie viele Eierkartons")),
        "amount": _product(_t("kilograms of honey", "Kilogramm Honig"), _t("kg of honey", "kg Honig"), _t("honey", "Honig"),
                           _t("how many kilograms of honey", "wie viele Kilogramm Honig"), _t("honey in kg", "Honig in kg"), KG),
        "title": _t("Farm shop: {pl1} and {pl2}", "Hofladen: {pl1} und {pl2}"),
        "setting": _t("A farm shop plans {q1} (x1) and {q2} (x2) to sell per week.", "Ein Hofladen plant, {q1} (x1) und {q2} (x2) er pro Woche verkauft."),
        **MAX, "cmax": _t("Contribution margin (in ₱10): {c1} per {one1}, {c2} per {one2}.", "Deckungsbeitrag: {c1} € je {one1}, {c2} € je {one2}."),
        **_res(r1max=(_t("Packing time", "Packzeit"), MINUTES), r2max=(_t("Cooling space", "Kühlraum"), LITERS),
               r3max=(_t("Transport weight", "Transportgewicht"), KG)),
    },
    "fish": {
        "count": _product(_t("number of tunas", "Anzahl Thunfische"), _t("tuna", "Thunfisch"), _t("tunas", "Thunfische"), _t("how many tunas", "wie viele Thunfische")),
        "amount": _product(_t("kilograms of shrimp", "Kilogramm Garnelen"), _t("kg of shrimp", "kg Garnelen"), _t("shrimp", "Garnelen"),
                           _t("how many kilograms of shrimp", "wie viele Kilogramm Garnelen"), _t("shrimp in kg", "Garnelen in kg"), KG),
        "title": _t("Fish market: {pl1} and {pl2}", "Fischmarkt: {pl1} und {pl2}"),
        "setting": _t("A fish trader plans {q1} (x1) and {q2} (x2) to buy at the port and sell per day.",
                      "Ein Fischhändler plant, {q1} (x1) und {q2} (x2) er pro Tag im Hafen einkauft und verkauft."),
        "settingmin": _t("A restaurant plans {q1} (x1) and {q2} (x2) to buy for a seafood festival.",
                         "Ein Restaurant plant, {q1} (x1) und {q2} (x2) es für ein Meeresfrüchtefest einkauft."),
        **MAX, **MIN,
        "cmax": _t("Contribution margin (in ₱100): {c1} per {one1}, {c2} per {one2}.", "Deckungsbeitrag (in 10 €): {c1} je {one1}, {c2} je {one2}."),
        "cmin": _t("Costs (in ₱100): {c1} per {one1}, {c2} per {one2}.", "Kosten (in 10 €): {c1} je {one1}, {c2} je {one2}."),
        **_res(r1max=(_t("Ice", "Eis"), KG), r2max=(_t("Sorting time", "Sortierzeit"), MINUTES), r3max=(_t("Cold storage", "Kühlraum"), _t("in 10 liters", "in 10 Litern")),
               r1min=(_t("Protein", "Eiweiß"), G100), r2min=(_t("Omega-3", "Omega-3"), _t("in 10 g", "in 10 g")),
               r3min=(_t("Cold storage", "Kühlraum"), _t("in 10 liters", "in 10 Litern"))),
    },
    "ice": {
        "count": _product(_t("number of ice blocks", "Anzahl Eisblöcke"), _t("ice block", "Eisblock"), _t("ice blocks", "Eisblöcke"),
                          _t("how many ice blocks", "wie viele Eisblöcke")),
        "amount": _product(_t("kilograms of crushed ice", "Kilogramm Crushed Ice"), _t("kg of crushed ice", "kg Crushed Ice"), _t("crushed ice", "Crushed Ice"),
                           _t("how many kilograms of crushed ice", "wie viele Kilogramm Crushed Ice"), _t("crushed ice in kg", "Crushed Ice in kg"), KG),
        "title": _t("Ice plant: {pl1} and {pl2}", "Eisfabrik: {pl1} und {pl2}"),
        "setting": _t("An ice plant plans {q1} (x1) and {q2} (x2) to deliver to fish vendors per day.",
                      "Eine Eisfabrik plant, {q1} (x1) und {q2} (x2) sie pro Tag an Fischhändler liefert."),
        **MAX, "cmax": _t("Contribution margin (in ₱10): {c1} per {one1}, {c2} per {one2}.", "Deckungsbeitrag: {c1} € je {one1}, {c2} € je {one2}."),
        **_res(r1max=(_t("Freezer time", "Gefrierzeit"), H), r2max=(_t("Electricity", "Strom"), _t("kWh", "kWh")),
               r3max=(_t("Truck load", "Lkw-Ladung"), _t("in 10 kg", "in 10 kg"))),
    },
    "studio": {
        "count": _product(_t("number of jingles", "Anzahl Jingles"), _t("jingle", "Jingle"), _t("jingles", "Jingles"), _t("how many jingles", "wie viele Jingles")),
        "amount": _product(_t("minutes of background music", "Minuten Hintergrundmusik"), _t("minute of background music", "Minute Hintergrundmusik"),
                           _t("background music", "Hintergrundmusik"), _t("how many minutes of background music", "wie viele Minuten Hintergrundmusik"),
                           _t("background music in minutes", "Hintergrundmusik in Minuten"), _t("minutes", "Minuten")),
        "title": _t("Music studio: {pl1} and {pl2}", "Tonstudio: {pl1} und {pl2}"),
        "setting": _t("A music studio plans {q1} (x1) and {q2} (x2) to produce per month.", "Ein Tonstudio plant, {q1} (x1) und {q2} (x2) es pro Monat produziert."),
        **MAX, "cmax": _t("Contribution margin (in ₱1,000): {c1} per {one1}, {c2} per {one2}.", "Deckungsbeitrag (in 10 €): {c1} je {one1}, {c2} je {one2}."),
        **_res(r1max=(_t("Composing time", "Kompositionszeit"), H), r2max=(_t("Studio time", "Studiozeit"), H), r3max=(_t("Mixing time", "Abmischzeit"), H)),
    },
    "laundry": {
        "count": _product(_t("number of blankets", "Anzahl Decken"), _t("blanket", "Decke"), _t("blankets", "Decken"), _t("how many blankets", "wie viele Decken")),
        "amount": _product(_t("kilograms of clothes", "Kilogramm Kleidung"), _t("kg of clothes", "kg Kleidung"), _t("clothes", "Kleidung"),
                           _t("how many kilograms of clothes", "wie viele Kilogramm Kleidung"), _t("clothes in kg", "Kleidung in kg"), KG),
        "title": _t("Laundry shop: {pl1} and {pl2}", "Wäscherei: {pl1} und {pl2}"),
        "setting": _t("A laundry shop plans {q1} (x1) and {q2} (x2) to wash per day.", "Eine Wäscherei plant, {q1} (x1) und {q2} (x2) sie pro Tag wäscht."),
        **MAX, "cmax": _t("Contribution margin (in ₱10): {c1} per {one1}, {c2} per {one2}.", "Deckungsbeitrag: {c1} € je {one1}, {c2} € je {one2}."),
        **_res(r1max=(_t("Washer time", "Waschmaschinenzeit"), MINUTES), r2max=(_t("Detergent", "Waschmittel"), _t("in 100 ml", "in 100 ml")),
               r3max=(_t("Dryer capacity", "Trocknerkapazität"), KG)),
    },
    "candles": {
        "count": _product(_t("number of pillar candles", "Anzahl Stumpenkerzen"), _t("pillar candle", "Stumpenkerze"), _t("pillar candles", "Stumpenkerzen"),
                          _t("how many pillar candles", "wie viele Stumpenkerzen")),
        "amount": _product(_t("kilograms of wax melts", "Kilogramm Duftwachs"), _t("kg of wax melts", "kg Duftwachs"), _t("wax melts", "Duftwachs"),
                           _t("how many kilograms of wax melts", "wie viele Kilogramm Duftwachs"), _t("wax melts in kg", "Duftwachs in kg"), KG),
        "title": _t("Candle shop: {pl1} and {pl2}", "Kerzenwerkstatt: {pl1} und {pl2}"),
        "setting": _t("A candle shop plans {q1} (x1) and {q2} (x2) to make per week.", "Eine Kerzenwerkstatt plant, {q1} (x1) und {q2} (x2) sie pro Woche herstellt."),
        **MAX, "cmax": _t("Contribution margin (in ₱10): {c1} per {one1}, {c2} per {one2}.", "Deckungsbeitrag: {c1} € je {one1}, {c2} € je {one2}."),
        **_res(r1max=(_t("Wax", "Wachs"), KG), r2max=(_t("Fragrance oil", "Duftöl"), _t("in 10 ml", "in 10 ml")), r3max=(_t("Cooling time", "Abkühlzeit"), H)),
    },
    "dairy": {
        "count": _product(_t("number of cheese wheels", "Anzahl Käselaibe"), _t("cheese wheel", "Käselaib"), _t("cheese wheels", "Käselaibe"),
                          _t("how many cheese wheels", "wie viele Käselaibe")),
        "amount": _product(_t("liters of milk", "Liter Milch"), _t("liter of milk", "Liter Milch"), _t("milk", "Milch"),
                           _t("how many liters of milk", "wie viele Liter Milch"), _t("milk in liters", "Milch in Litern"), LITERS),
        "title": _t("Dairy: {pl1} and {pl2}", "Molkerei: {pl1} und {pl2}"),
        "setting": _t("A dairy plans {q1} (x1) and {q2} (x2) to sell per week.", "Eine Molkerei plant, {q1} (x1) und {q2} (x2) sie pro Woche verkauft."),
        "settingmin": _t("A hotel kitchen plans {q1} (x1) and {q2} (x2) to buy for one week.", "Eine Hotelküche plant, {q1} (x1) und {q2} (x2) sie für eine Woche einkauft."),
        **MAX, **MIN,
        "cmax": _t("Contribution margin (in ₱100): {c1} per {one1}, {c2} per {one2}.", "Deckungsbeitrag (in 10 €): {c1} je {one1}, {c2} je {one2}."),
        "cmin": _t("Costs (in ₱100): {c1} per {one1}, {c2} per {one2}.", "Kosten (in 10 €): {c1} je {one1}, {c2} je {one2}."),
        **_res(r1max=(_t("Packing time", "Verpackungszeit"), MINUTES), r2max=(_t("Delivery time", "Lieferzeit"), MINUTES),
               r3max=(_t("Cold storage", "Kühlraum"), LITERS),
               r1min=(_t("Protein", "Eiweiß"), _t("in 10 g", "in 10 g")), r2min=(_t("Calcium", "Kalzium"), _t("in 100 mg", "in 100 mg")),
               r3min=(_t("Cold storage", "Kühlraum"), LITERS)),
    },
    "fruit": {
        "count": _product(_t("number of pineapples", "Anzahl Ananas"), _t("pineapple", "Ananas"), _t("pineapples", "Ananas"),
                          _t("how many pineapples", "wie viele Ananas")),
        "amount": _product(_t("kilograms of grapes", "Kilogramm Trauben"), _t("kg of grapes", "kg Trauben"), _t("grapes", "Trauben"),
                           _t("how many kilograms of grapes", "wie viele Kilogramm Trauben"), _t("grapes in kg", "Trauben in kg"), KG),
        "title": _t("Fruit stand: {pl1} and {pl2}", "Obststand: {pl1} und {pl2}"),
        "setting": _t("A fruit stand at the market plans {q1} (x1) and {q2} (x2) to sell per day.",
                      "Ein Obststand auf dem Markt plant, {q1} (x1) und {q2} (x2) er pro Tag verkauft."),
        "settingmin": _t("A hospital kitchen plans {q1} (x1) and {q2} (x2) to buy for one week.", "Eine Krankenhausküche plant, {q1} (x1) und {q2} (x2) sie für eine Woche einkauft."),
        **MAX, **MIN,
        "cmax": _t("Contribution margin (in ₱10): {c1} per {one1}, {c2} per {one2}.", "Deckungsbeitrag: {c1} € je {one1}, {c2} € je {one2}."),
        "cmin": _t("Costs (in ₱10): {c1} per {one1}, {c2} per {one2}.", "Kosten: {c1} € je {one1}, {c2} € je {one2}."),
        **_res(r1max=(_t("Cleaning time", "Putzzeit"), MINUTES), r2max=(_t("Cooling space", "Kühlplatz"), LITERS),
               r3max=(_t("Transport weight", "Transportgewicht"), KG),
               r1min=(_t("Vitamin C", "Vitamin C"), _t("in 100 mg", "in 100 mg")), r2min=(_t("Fiber", "Ballaststoffe"), _t("in 10 g", "in 10 g")),
               r3min=(_t("Storage weight", "Lagergewicht"), KG)),
    },
    "butcher": {
        "count": _product(_t("number of roast chickens", "Anzahl Brathähnchen"), _t("roast chicken", "Brathähnchen"), _t("roast chickens", "Brathähnchen"),
                          _t("how many roast chickens", "wie viele Brathähnchen")),
        "amount": _product(_t("kilograms of sausages", "Kilogramm Würstchen"), _t("kg of sausages", "kg Würstchen"), _t("sausages", "Würstchen"),
                           _t("how many kilograms of sausages", "wie viele Kilogramm Würstchen"), _t("sausages in kg", "Würstchen in kg"), KG),
        "title": _t("Butcher shop: {pl1} and {pl2}", "Metzgerei: {pl1} und {pl2}"),
        "setting": _t("A butcher shop plans {q1} (x1) and {q2} (x2) to prepare per day.", "Eine Metzgerei plant, {q1} (x1) und {q2} (x2) sie pro Tag zubereitet."),
        **MAX, "cmax": _t("Contribution margin (in ₱10): {c1} per {one1}, {c2} per {one2}.", "Deckungsbeitrag: {c1} € je {one1}, {c2} € je {one2}."),
        **_res(r1max=(_t("Grill time", "Grillzeit"), MINUTES), r2max=(_t("Spices", "Gewürze"), _t("in 10 g", "in 10 g")), r3max=(_t("Cooling space", "Kühlplatz"), KG)),
    },
    "hardware": {
        "count": _product(_t("number of toolboxes", "Anzahl Werkzeugkästen"), _t("toolbox", "Werkzeugkasten"), _t("toolboxes", "Werkzeugkästen"),
                          _t("how many toolboxes", "wie viele Werkzeugkästen")),
        "amount": _product(_t("kilograms of nails", "Kilogramm Nägel"), _t("kg of nails", "kg Nägel"), _t("nails", "Nägel"),
                           _t("how many kilograms of nails", "wie viele Kilogramm Nägel"), _t("nails in kg", "Nägel in kg"), KG),
        "title": _t("Hardware store: {pl1} and {pl2}", "Baumarkt: {pl1} und {pl2}"),
        "setting": _t("A hardware store plans {q1} (x1) and {q2} (x2) to sell per week.", "Ein Baumarkt plant, {q1} (x1) und {q2} (x2) er pro Woche verkauft."),
        **MAX, "cmax": _t("Contribution margin (in ₱100): {c1} per {one1}, {c2} per {one2}.", "Deckungsbeitrag (in 10 €): {c1} je {one1}, {c2} je {one2}."),
        **_res(r1max=(_t("Shelf space", "Regalfläche"), _t("in 100 cm²", "in 100 cm²")), r2max=(_t("Packing time", "Packzeit"), MINUTES),
               r3max=(_t("Delivery weight", "Liefergewicht"), KG)),
    },
}

# variable type of every topic here and whether it also tells cost problems (engine.TOPICS)
KINDS = {**{t: ("int", t in ("nursery", "energy", "bus")) for t in ("print", "bikes", "tailor", "phones", "pottery", "boats", "flowers", "nursery", "energy", "bus")},
         **{t: ("con", t in ("rice", "fertilizer", "flour", "soil")) for t in CONTEXTS if t not in ("print", "bikes", "tailor", "phones", "pottery", "boats", "flowers", "nursery", "energy", "bus")},
         **{t: ("mix", t in ("pizzeria", "fish", "dairy", "fruit")) for t in MIXED}}
