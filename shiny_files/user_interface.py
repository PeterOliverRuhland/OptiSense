from shiny import ui

from i18n import GUIDE_ORDER, LANGS, client_dictionary


def tr(key, tag="span", **attrs):
    """Static text translated in the browser (see www/optisense.js). English is the fallback content."""
    from i18n import t
    return getattr(ui.tags, tag)(t("en", key), {"data-i18n": key}, **attrs)


def help_button(topic):
    return ui.tags.button("?", type="button", class_="os-help", **{"data-help": topic, "data-i18n-aria": "help",
                                                                    "aria-label": "Help"})


def step_card(number, title_key, status_id, help_topic, *body):
    return ui.div(
        ui.div(
            ui.span(str(number), class_="os-num"),
            tr(title_key, class_="os-step-title"),
            ui.output_text(status_id, inline=True, container=ui.tags.span).add_class("os-step-status"),
            help_button(help_topic),
            class_="os-step-head",
        ),
        ui.div(*body, class_="os-step-body"),
        class_="os-card os-step",
        id=f"os-step-{number}",
    )


sidebar = ui.sidebar(
    step_card(
        1, "step1", "status_step1", "steps",
        ui.output_ui("problem_list"),
        ui.div(
            ui.input_action_button("btn_add_obj", tr("add_objective_short"), class_="os-btn",
                                   **{"data-i18n-aria": "add_objective", "aria-label": "Add objective function"}),
            ui.input_action_button("btn_add_con", tr("add_constraint_short"), class_="os-btn",
                                   **{"data-i18n-aria": "add_constraint", "aria-label": "Add constraint"}),
            class_="os-btn-row",
        ),
        ui.div(
            ui.input_action_link("btn_import_export", tr("import_export"), class_="os-link"),
            ui.input_action_link("btn_example", tr("load_example"), class_="os-link"),
            ui.input_action_link("btn_reset", tr("reset_all"), class_="os-link"),
            class_="os-links",
        ),
    ),
    step_card(
        2, "step2", "status_step2", "lp",
        ui.div(
            ui.span("x1", class_="os-var"),
            ui.input_radio_buttons("vt_x1", None, {"con": tr("continuous"), "int": tr("integer")}, inline=True),
            class_="os-vt-row",
        ),
        ui.div(
            ui.span("x2", class_="os-var"),
            ui.input_radio_buttons("vt_x2", None, {"con": tr("continuous"), "int": tr("integer")}, inline=True),
            class_="os-vt-row",
        ),
        ui.output_ui("problem_type"),
    ),
    step_card(
        3, "step3", "status_step3", "sens",
        ui.input_action_button("btn_opt", tr("run_opt"), class_="os-btn os-btn-primary", disabled=True),
        ui.input_action_button("btn_sens", tr("run_sens"), class_="os-btn", disabled=True),
        ui.output_ui("solve_hint"),
    ),
    tr("credit", tag="div", class_="os-credit"),
    width="var(--sidebar-width)",
    open="desktop",
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

work_panel = ui.nav_panel(
    tr("tab_work"),
    ui.layout_sidebar(
        sidebar,
        ui.div(graph_card, ui.div(results_card, class_="os-results"), class_="os-main"),
        class_="os-layout",
        border=False,
    ),
    value="work",
)

guide_panel = ui.nav_panel(
    tr("tab_guide"),
    ui.div(
        ui.div(
            *[ui.tags.button(tr(label_key), type="button", class_="os-guide-tab", **{"data-guide": topic})
              for topic, label_key in GUIDE_ORDER],
            class_="os-guide-nav os-card",
            role="tablist",
        ),
        ui.div(ui.output_ui("guide_view"), class_="os-guide-body os-card"),
        class_="os-guide",
    ),
    value="guide",
)

language_switch = ui.nav_control(
    ui.div(
        ui.input_select("lang", None, LANGS, selected="en", selectize=False, width="auto"),
        class_="os-lang",
        **{"data-i18n-aria": "language", "aria-label": "Language"},
    )
)

app_ui = ui.page_navbar(
    work_panel,
    guide_panel,
    ui.nav_spacer(),
    language_switch,
    title=ui.span("OptiSense", class_="os-brand"),
    id="page",
    window_title="OptiSense",
    header=ui.head_content(
        ui.tags.meta(name="viewport", content="width=device-width, initial-scale=1"),
        ui.tags.link(rel="stylesheet", href="optisense.css"),
        ui.tags.script(f"window.OS_I18N = {client_dictionary()};"),
        ui.tags.script(src="optisense.js"),
    ),
    bg="#b0e2ff",
    fillable=["work"],
    lang="en",
)
