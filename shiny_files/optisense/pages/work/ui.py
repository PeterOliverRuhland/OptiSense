"""Layout of “Model & solution”: workflow sidebar with three steps, graph card, results tabs."""

from shiny import ui

from optisense.ui.components import tr

STYLESHEET, SCRIPT = "work.css", "work.js"


def help_button(topic):
    """? button of a step; opens a dialog with the matching guide sections (server/help_dialog.py)."""
    return ui.tags.button("?", type="button", class_="os-help", **{"data-help": topic, "data-i18n-aria": "help",
                                                                    "aria-label": "Help"})


def step_card(number, title_key, help_topic, *body, extra=None):
    return ui.div(
        ui.div(
            ui.span(str(number), class_="os-num"),
            tr(title_key, class_="os-step-title"),
            extra,
            help_button(help_topic),
            class_="os-step-head",
        ),
        ui.div(*body, class_="os-step-body"),
        class_="os-card os-step",
        id=f"os-step-{number}",
    )


sidebar = ui.sidebar(
    step_card(
        1, "step1", "steps",
        ui.output_ui("problem_list"),
        ui.div(
            ui.input_action_link("btn_import_export", tr("import_export"), class_="os-link"),
            ui.input_action_link("btn_reset", tr("reset_all"), class_="os-link"),
            class_="os-links",
        ),
        extra=ui.input_action_link("btn_example", tr("example_short"), class_="os-link os-head-link",
                                 **{"data-i18n-aria": "load_example", "aria-label": "Load example"}),
    ),
    step_card(
        2, "step2", "range",
        ui.div(
            ui.span("x1", class_="os-var"),
            ui.input_radio_buttons("vt_x1", None, {"con": tr("continuous_short"), "int": tr("integer_short")}, inline=True),
            class_="os-vt-row",
        ),
        ui.div(
            ui.span("x2", class_="os-var"),
            ui.input_radio_buttons("vt_x2", None, {"con": tr("continuous_short"), "int": tr("integer_short")}, inline=True),
            class_="os-vt-row",
        ),
        ui.output_ui("problem_type"),
    ),
    step_card(
        3, "step3", "solve",
        ui.input_action_button("btn_opt", tr("run_opt"), class_="os-btn", disabled=True),
        ui.input_action_button("btn_sens", tr("run_sens"), class_="os-btn", disabled=True),
        ui.output_ui("solve_hint"),
    ),
    ui.div(tr("credit"), ui.tags.br(), tr("imprint", tag="button", type="button", class_="btn btn-link os-imprint-link", **{"data-os-imprint": ""}),
           class_="os-credit"),
    width="var(--sidebar-width)",
    # smartphones: the steps stay open above the graph (one column, see www/work.css)
    open={"desktop": "open", "mobile": "always-above"},
    gap="12px",
    class_="os-sidebar",
)

graph_card = ui.card(
    ui.card_header(
        ui.tags.button("‹", type="button", class_="os-sidebar-btn", title="Show or hide the steps",
                       **{"data-sidebar-toggle": "1", "data-i18n-aria": "toggle_sidebar", "aria-label": "Show or hide the steps",
                          "aria-expanded": "true"}),
        tr("graph"),
        ui.input_action_button("btn_png", tr("save_png"), class_="btn-link os-header-action", disabled=True),
        class_="os-card-header",
    ),
    ui.output_plot("plot", height="100%", fill=True),
    full_screen=True,
    class_="os-card os-graph",
)

results_card = ui.navset_card_tab(
    ui.nav_panel(tr("tab_solution"), ui.output_ui("solution_view"), value="solution"),
    ui.nav_panel(tr("tab_sensitivity"), ui.output_ui("sensitivity_view"), value="sensitivity"),
    ui.nav_panel(tr("tab_description"), ui.output_ui("description_view"), value="description"),
    id="results_tabs",
    title=tr("results"),
)

panel = ui.nav_panel(
    tr("tab_work"),
    ui.layout_sidebar(
        sidebar,
        ui.div(graph_card, ui.div(results_card, class_="os-results"),
               ui.div(tr("credit"), ui.tags.br(), tr("imprint", tag="button", type="button", class_="btn btn-link os-imprint-link", **{"data-os-imprint": ""}),
                      class_="os-credit os-credit-end"),   # smartphones: at the end of the page
               class_="os-main"),
        class_="os-layout",
        border=False,
    ),
    value="work",
)
