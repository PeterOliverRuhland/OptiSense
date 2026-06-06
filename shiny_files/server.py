import os
import platform
import random
import sys
import shutil
import tempfile
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from shiny import render, reactive, ui
from calculations import *
from functions import *


def server(input, output, session):
    # reactive variables
    # If they are located within a @reactive.Calc and they change, the code within the reactive.Calc is re-executed
    dict_reactive_obj_func = reactive.Value({})
    dict_reactive_constraints = reactive.Value({})
    list_reactive_obj_func = reactive.Value([])
    list_reactive_constraints = reactive.value([])
    list_reactive_selected_constraints = reactive.Value([])
    list_reactive_selected_obj_func = reactive.Value([])
    list_reactive_solved_problem = reactive.Value([])
    list_reactive_xlim_var = reactive.Value([])
    list_reactive_ylim_var = reactive.Value([])
    dict_reactive_xlim_var = reactive.Value({})
    dict_reactive_ylim_var = reactive.Value({})
    dict_reactive_func_colors = reactive.Value({})
    string_reactive_problem_type = reactive.Value("")
    reactive_plot_fig = reactive.Value(None)
    list_reactive_y_values_equal_problem = reactive.Value([])
    bool_reactive_import_statement = reactive.Value(False)
    list_reactive_sens_ana_slack = reactive.Value([])
    list_reactive_sens_ana_shadow = reactive.Value([])
    list_reactive_sens_ana_limits = reactive.Value([])
    string_reactive_selected_guide_step = reactive.Value("")

    # Modal1 - Create objective function
    @reactive.effect
    @reactive.event(input.btn_enter_obj_func)
    def modal1():
        m = ui.modal(
            "Please enter your data:",
            ui.HTML("<br><br>"),
            ui.row(
                ui.column(6,
                          ui.input_numeric("obj_func_c1", "enter coefficient c1", 1, min=None, max=None, step=0.01)),
                ui.column(6, ui.input_select(
                    "obj_func_c1_value_range",
                    "value range:",
                    {"con": "continuous", "int": "integer"},
                )),
            ),
            ui.row(
                ui.column(6, ui.input_numeric("obj_func_c2", "enter coefficient c2", 1, min=None, max=None, step=0.01)),
                ui.column(6, ui.input_select(
                    "obj_func_c2_value_range",
                    "value range:",
                    {"con": "continuous", "int": "integer"},
                )
                          )
            ),
            ui.input_text("obj_func_name", "enter name", placeholder="Objective function name"),
            ui.input_select(
                "obj_func_min_max",
                "type of optimization:",
                {"min": "minimization", "max": "maximization"},
            ),
            footer=ui.div(
                ui.input_action_button(id="cancel_button", label="Cancel"),
                ui.input_action_button(id="submit_button", label="Submit"),
            ),
            title="Objective function",
            easy_close=False,
        )
        ui.modal_show(m)

    # Modal2 - Create constraint
    @reactive.effect
    @reactive.event(input.btn_enter_constraint)
    def modal2():
        m2 = ui.modal(
            "Please enter your data:",
            ui.HTML("<br><br>"),
            ui.row(
                ui.column(6,
                          ui.input_numeric("constraint_a1", "enter coefficient a1", 1, min=None, max=None,
                                           step=0.01)),
                ui.column(6, ui.input_select(
                    "constraint_a1_value_range",
                    "value range:",
                    {"con": "continuous", "int": "integer"},
                )),
            ),
            ui.row(
                ui.column(6,
                          ui.input_numeric("constraint_a2", "enter coefficient a2", 2, min=None, max=None, step=0.01)),
                ui.column(6, ui.input_select(
                    "constraint_a2_value_range",
                    "value range:",
                    {"con": "continuous", "int": "integer"},
                )
                          )
            ),
            ui.input_text("constraint_name", "enter name", placeholder="Constraint name"),

            ui.row(
                ui.column(6,
                          ui.input_select(
                              "comparison_operator",
                              "select comparison operator",
                              {"≤": "≤", "≥": "≥",
                               "=": "="},
                          )
                          ),
                ui.column(6,
                          ui.input_numeric("bounding_constant", "enter bounding constant b", 1.11, min=None, max=None,
                                           step=0.01),
                          )
            ),

            footer=ui.div(
                ui.input_action_button(id="cancel_button_2", label="Cancel"),
                ui.input_action_button(id="submit_button_2", label="Submit"),
            ),
            title="Constraint",
            easy_close=False,
        )
        ui.modal_show(m2)

    # Modal3 - Change objective function
    @reactive.effect
    @reactive.event(input.btn_change_obj_func)
    def modal3():
        m3 = ui.modal(
            ui.row(
                ui.column(6, ui.input_select(
                    "select_obj_func_change",
                    "Please select objective function:",
                    choices=dict_reactive_obj_func.get(),
                ), ),

                ui.HTML("<b>Current values are pre-filled. Change if required.</b>"),
                ui.HTML("<br><br>")
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>coefficient c1</b>")),

                ui.column(8, ui.input_numeric("obj_func_c1_update", None, list_reactive_obj_func.get()[0][1], min=None,
                                              max=None,
                                              step=0.01)),
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>value range x1</b>")),
                ui.column(8, ui.input_select(
                    "obj_func_c1_value_range_update",
                    None,
                    {"con": "continuous", "int": "integer"},
                    selected=list_reactive_obj_func.get()[0][2]
                ))
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>coefficient c2</b>")),
                ui.column(8, ui.input_numeric("obj_func_c2_update", None, list_reactive_obj_func.get()[0][3], min=None,
                                              max=None,
                                              step=0.01)),
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>value range x2</b>")),
                ui.column(8, ui.input_select(
                    "obj_func_c2_value_range_update",
                    None,
                    {"con": "continuous", "int": "integer"},
                    selected=list_reactive_obj_func.get()[0][4]
                ))
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>min-max</b>")),
                ui.column(8, ui.input_select(
                    "obj_func_min_max_update",
                    None,
                    {"min": "minimization", "max": "Maximization"},
                    selected=list_reactive_obj_func.get()[0][5]
                ))
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>Name</b>")),
                ui.column(8,
                          ui.input_text("obj_func_name_update", None, list_reactive_obj_func.get()[0][0]))
            ),
            footer=ui.div(
                ui.input_action_button(id="cancel_button_3", label="Cancel"),
                ui.input_action_button(id="submit_button_3", label="Submit"),
            ),
            title="Change objective function",
            easy_close=False,
            style="width: 100%;"
        )

        ui.modal_show(m3)

    # Modal4 - Delete objective function
    @reactive.effect
    @reactive.event(input.btn_delete_obj_func)
    def modal4():
        m4 = ui.modal(
            ui.row(
                ui.column(5, ui.input_select(
                    "select_obj_func_delete",
                    "Please select objective function:",

                    choices=dict_reactive_obj_func.get(),
                ), ),
                ui.column(7, ui.output_text(id="mod4_text"))
            ),
            footer=ui.div(
                ui.input_action_button(id="cancel_button_4", label="Cancel"),
                ui.input_action_button(id="submit_button_4", label="Delete"),
            ),
            title="Delete objective function",
            easy_close=False,
            style="width: 100%;"
        )
        ui.modal_show(m4)

    # Modal5 - Change constraint
    @reactive.effect
    @reactive.event(input.btn_change_constraint)
    def modal5():
        m5 = ui.modal(
            ui.row(
                ui.column(6, ui.input_select(
                    "select_constraint_change",
                    "Please select constraint:",

                    choices=dict_reactive_constraints.get(),
                ), ),

                ui.HTML("<b>Current values are pre-filled. Change if required.</b>"),
                ui.HTML("<br><br>")
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>coefficient a1:</b>")),
                ui.column(8,
                          ui.input_numeric("constraint_a1_update", None, list_reactive_constraints.get()[0][1],
                                           min=None,
                                           max=None,
                                           step=0.01)),
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>value range x1</b>")),
                ui.column(8, ui.input_select(
                    "constraint_a1_value_range_update",
                    None,
                    {"con": "continuous", "int": "integer"},
                    selected=list_reactive_constraints.get()[0][2]
                ))
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>coefficient a2:</b>")),
                ui.column(8,
                          ui.input_numeric("constraint_a2_update", None, list_reactive_constraints.get()[0][3],
                                           min=None,
                                           max=None,
                                           step=0.01)),
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>value range x2</b>")),
                ui.column(8, ui.input_select(
                    "constraint_a2_value_range_update",
                    None,
                    {"con": "continuous", "int": "integer"},
                    selected=list_reactive_constraints.get()[0][4]
                ))
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>comparison operator</b>")),
                ui.column(8, ui.input_select(
                    "comparison_operator_update",
                    None,
                    {"≤": "≤", "≥": "≥",
                     "=": "="},
                    selected=list_reactive_constraints.get()[0][5]
                ))
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>bounding constant b</b>")),
                ui.column(8,
                          ui.input_numeric("bounding_constant_update", None, list_reactive_constraints.get()[0][6],
                                           min=None,
                                           max=None,
                                           step=0.01)),
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>name</b>")),
                ui.column(8,
                          ui.input_text("constraint_name_update", None, list_reactive_constraints.get()[0][0]))
            ),
            footer=ui.div(
                ui.input_action_button(id="cancel_button_5", label="Cancel"),
                ui.input_action_button(id="submit_button_5", label="Submit"),
            ),
            title="Change constraint",
            easy_close=False,
            style="width: 100%;"
        )

        ui.modal_show(m5)

    # Modal6 - Delete constraint
    @reactive.effect
    @reactive.event(input.btn_delete_constraint)
    def modal6():
        m6 = ui.modal(
            ui.row(
                ui.column(5, ui.input_select(
                    "select_constraint_delete",
                    "Please select constraint:",
                    choices=dict_reactive_constraints.get(),
                ), ),
                ui.column(7, ui.output_text(id="mod6_text"))
            ),
            footer=ui.div(
                ui.input_action_button(id="cancel_button_6", label="Cancel"),
                ui.input_action_button(id="submit_button_6", label="Delete"),
            ),
            title="Delete constraint",
            easy_close=False,
            style="width: 100%;"
        )
        ui.modal_show(m6)

    # Modal7 - Save graph as PNG
    @reactive.effect
    @reactive.event(input.btn_save_graph)
    def modal7():
        m7 = ui.modal(
            ui.row(
                ui.column(4, ui.HTML("<b>Name of graph</b>")),
                ui.column(8, ui.input_text("name_graph", None, placeholder="Enter name of graph")),
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>Directory path</b>")),
                ui.column(8, ui.input_text("directory_path_graph", None, placeholder="Bsp.: C:/Users/.../Desktop")),
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>Please choose:</b>")),
                ui.column(8,
                          ui.input_radio_buttons(
                              "radio_graph_dpi",
                              None,
                              {"predefined_dpi": "Predefined DPI", "own_dpi": "Choose own DPI"},
                          )),
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>Choose:</b>")),
                ui.column(8,
                          ui.input_select(
                              "select_dpi",
                              None,
                              {"72": 72, "150": 150, "300": 300, "600": 600},
                          )),
            ),
            ui.row(
                ui.HTML("<b>or (depending on choice above)</b>"),
                ui.HTML("<br><br>")
            ),
            ui.row(
                ui.column(4, ui.HTML("<b>Please enter DPI</b>")),
                ui.column(8,
                          ui.input_numeric("numeric_dpi", None, 1, min=1, max=None, step=1)),
            ),
            footer=ui.div(
                ui.input_action_button(id="cancel_button_7", label="Cancel"),
                ui.input_action_button(id="submit_button_7", label="Submit"),
            ),
            title="Save graph as PNG",
            easy_close=False,
            style="width: 100%;"
        )
        ui.modal_show(m7)

    # Modal8 - Import or export lp-file
    @reactive.effect
    @reactive.event(input.btn_import_export)
    def modal8():
        m8 = ui.modal(
            ui.row(
                ui.column(4, ui.HTML("<b>Name of lp file (for export only)</b>")),
                ui.column(8, ui.input_text("name_export", None, placeholder="Enter name of file")),
            ),
            ui.HTML("<br><br>"),
            ui.row(
                ui.column(4, ui.HTML("<b>File path / saving path</b>")),
                ui.column(8,
                          ui.input_text("saving_path_import_export", None,
                                        placeholder="Bsp.: C:/Users/.../Desktop/lp_file.lp")),
            ),
            ui.HTML("<br><br>"),
            ui.row(
                ui.column(4, ui.HTML("<b>Please choose</b>")),
                ui.column(8,
                          ui.input_radio_buttons(
                              "radio_import_export",
                              None,
                              {"import": "import from lp file", "export": "export to lp file"},
                          )),
            ),

            footer=ui.div(
                ui.input_action_button(id="cancel_button_8", label="Cancel"),
                ui.input_action_button(id="submit_button_8", label="Submit"),
            ),
            title="Import or export lp file",
            easy_close=False,
            style="width: 100%;"
        )
        ui.modal_show(m8)

    # Cancel-buttons for closing modals
    # needs one per cancel button, otherwise cancel-buttons will not close modals
    @reactive.effect
    @reactive.event(input.cancel_button)
    def close_modal_cancel():
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.cancel_button_2)
    def close_modal2_cancel():
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.cancel_button_3)
    def close_modal3_cancel():
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.cancel_button_4)
    def close_modal4_cancel():
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.cancel_button_5)
    def close_modal5_cancel():
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.cancel_button_6)
    def close_modal6_cancel():
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.cancel_button_7)
    def close_modal7_cancel():
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.cancel_button_8)
    def close_modal8_cancel():
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.cancel_button_9)
    def close_modal9_cancel():
        ui.modal_remove()

    # Submit button 1
    @reactive.effect
    @reactive.event(input.submit_button)
    def create_obj_func():

        if input.obj_func_name() == "" or input.obj_func_c1() is None or input.obj_func_c2() is None or not isinstance(
                input.obj_func_c1(), (
                        int, float)) or not isinstance(input.obj_func_c2(), (int, float)) or input.obj_func_c1() < 0 or input.obj_func_c2() < 0:
            notification_popup("You have entered invalid values, please check your entries.",
                               message_type="error")
        else:
            name = ""
            if not list_reactive_obj_func.get():
                name = input.obj_func_name()
            else:
                detected = False
                for function in list_reactive_obj_func.get():
                    if input.obj_func_name() in function[0]:
                        detected = True
                        counter = 0
                        for entry in list_reactive_obj_func.get():
                            if input.obj_func_name() in entry[0]:
                                counter += 1
                        name = input.obj_func_name() + "_" + str(counter)
                if not detected:
                    name = input.obj_func_name()

            c1 = input.obj_func_c1()
            c1_value_range = input.obj_func_c1_value_range()
            c2 = input.obj_func_c2()
            c2_value_range = input.obj_func_c2_value_range()
            min_max = input.obj_func_min_max()

            copy_list_reactive_obj_func = list_reactive_obj_func.get().copy()
            copy_list_reactive_obj_func.append([name, c1, c1_value_range, c2, c2_value_range, min_max])
            list_reactive_obj_func.set(copy_list_reactive_obj_func)

            ui.update_action_button("btn_change_obj_func", disabled=False)
            ui.update_action_button("btn_delete_obj_func", disabled=False)

            copy_dict_obj_func = dict_reactive_obj_func.get().copy()
            for function in list_reactive_obj_func.get():
                copy_dict_obj_func[function[0]] = function[0]
            dict_reactive_obj_func.set(copy_dict_obj_func)

            ui.update_select("select_obj_func", choices=dict_reactive_obj_func.get(), selected=[])

            notification_popup("Objective function added successfully")

            ui.modal_remove()

    # Submit button 2
    @reactive.effect
    @reactive.event(input.submit_button_2)
    def create_restriction():

        if input.constraint_name() == "" or input.constraint_a1() is None or input.constraint_a2() is None or not isinstance(
                input.constraint_a1(), (
                        int, float)) or not isinstance(input.constraint_a2(), (
                int, float)) or not input.bounding_constant() or not isinstance(
            input.bounding_constant(), (int, float)) or input.constraint_a1() < 0 or input.constraint_a2() < 0 or input.bounding_constant() < 0:
            notification_popup("You have entered invalid values, please check your entries",
                               message_type="error")
        else:
            name = ""
            if not list_reactive_constraints.get():
                name = input.constraint_name()
            else:
                detected = False
                for function in list_reactive_constraints.get():
                    if input.constraint_name() in function[0]:
                        detected = True
                        counter = 0
                        for entry in list_reactive_constraints.get():
                            if input.constraint_name() in entry[0]:
                                counter += 1
                        name = input.constraint_name() + "_" + str(counter)
                if not detected:
                    name = input.constraint_name()
            a1 = input.constraint_a1()
            a1_value_range = input.constraint_a1_value_range()
            a2 = input.constraint_a2()
            a2_value_range = input.constraint_a2_value_range()
            comparison_operator = input.comparison_operator()
            bounding_constant = input.bounding_constant()

            copy_list_reactive_constraints = list_reactive_constraints.get().copy()
            copy_list_reactive_constraints.append(
                [name, a1, a1_value_range, a2, a2_value_range, comparison_operator, bounding_constant])
            list_reactive_constraints.set(copy_list_reactive_constraints)

            ui.update_action_button("btn_change_constraint", disabled=False)
            ui.update_action_button("btn_delete_constraint", disabled=False)

            copy_dict_reactive_constraints = dict_reactive_constraints.get().copy()
            for function in list_reactive_constraints.get():
                copy_dict_reactive_constraints[function[0]] = function[0]
            dict_reactive_constraints.set(copy_dict_reactive_constraints)

            ui.update_selectize("selectize_constraints", choices=dict_reactive_constraints.get())

            notification_popup("Constraint added successfully")

            ui.modal_remove()

    # Submit button 3
    @reactive.effect
    @reactive.event(input.submit_button_3)
    def change_obj_func():

        if input.obj_func_name_update() == "" or input.obj_func_c1_update() is None or input.obj_func_c2_update() is None or not isinstance(
                input.obj_func_c1_update(), (int, float)) or not isinstance(input.obj_func_c2_update(), (int, float)) or input.obj_func_c1_update() < 0 or input.obj_func_c2_update() < 0:
            notification_popup("You have entered invalid values, please check your entries.",
                               message_type="error")
        else:

            selected_function_name = input.select_obj_func_change()
            counter = 0
            for function in list_reactive_obj_func.get():
                if function[0] == selected_function_name:
                    copy_list_reactive_obj_func = list_reactive_obj_func.get().copy()
                    if input.obj_func_c1_update() != function[1]:
                        copy_list_reactive_obj_func[counter][1] = input.obj_func_c1_update()
                        list_reactive_obj_func.set(copy_list_reactive_obj_func)

                    if input.obj_func_c1_value_range_update() != function[2]:
                        copy_list_reactive_obj_func[counter][2] = input.obj_func_c1_value_range_update()
                        list_reactive_obj_func.set(copy_list_reactive_obj_func)

                    if input.obj_func_c2_update() != function[3]:
                        copy_list_reactive_obj_func[counter][3] = input.obj_func_c2_update()
                        list_reactive_obj_func.set(copy_list_reactive_obj_func)

                    if input.obj_func_c2_value_range_update() != function[4]:
                        copy_list_reactive_obj_func[counter][4] = input.obj_func_c2_value_range_update()
                        list_reactive_obj_func.set(copy_list_reactive_obj_func)

                    if input.obj_func_min_max_update() != function[5]:
                        copy_list_reactive_obj_func[counter][5] = input.obj_func_min_max_update()
                        list_reactive_obj_func.set(copy_list_reactive_obj_func)

                    if input.obj_func_name_update() != function[0]:
                        copy_list_reactive_obj_func[counter][0] = input.obj_func_name_update()
                        list_reactive_obj_func.set(copy_list_reactive_obj_func)

                        copy_dict_obj_func = dict_reactive_obj_func.get().copy()

                        copy_dict_obj_func[input.obj_func_name_update()] = input.obj_func_name_update()
                        del copy_dict_obj_func[selected_function_name]
                        dict_reactive_obj_func.set(copy_dict_obj_func)

                    ui.update_select("select_obj_func", choices=dict_reactive_obj_func.get())

                counter += 1
            notification_popup("Objective function changed successfully")
            ui.modal_remove()

    # Submit button 4
    @reactive.effect
    @reactive.event(input.submit_button_4)
    def delete_obj_func():
        copy_list_reactive_obj_func = list_reactive_obj_func.get().copy()
        copy_dict_obj_func = dict_reactive_obj_func.get().copy()
        for function in list_reactive_obj_func.get():
            if function[0] == input.select_obj_func_delete():
                copy_list_reactive_obj_func.remove(function)
                list_reactive_obj_func.set(copy_list_reactive_obj_func)

                del copy_dict_obj_func[input.select_obj_func_delete()]
                dict_reactive_obj_func.set(copy_dict_obj_func)

        ui.update_select("select_obj_func", choices=dict_reactive_obj_func.get())
        if not list_reactive_obj_func.get():
            ui.update_action_button("btn_change_obj_func", disabled=True)
            ui.update_action_button("btn_delete_obj_func", disabled=True)

        notification_popup("Objective function deleted successfully")
        ui.modal_remove()

    # Submit button 5
    @reactive.effect
    @reactive.event(input.submit_button_5)
    def change_constraint():

        if input.constraint_name_update() == "" or input.constraint_a1_update() is None or input.constraint_a2_update() is None or not isinstance(
                input.constraint_a1_update(), (int, float)) or not isinstance(input.constraint_a2_update(), (
                int, float)) or not input.bounding_constant_update() or not isinstance(input.bounding_constant_update(),
                                                                                       (int, float)) or input.constraint_a1_update() < 0 or input.constraint_a2_update() < 0 or input.bounding_constant_update() < 0:
            notification_popup("You have entered invalid values, please check your entries.",
                               message_type="error")
        else:

            selected_constraint_name = input.select_constraint_change()
            counter = 0
            for function in list_reactive_constraints.get():
                if function[0] == selected_constraint_name:
                    copy_list_reactive_constraints = list_reactive_constraints.get().copy()
                    if input.constraint_a1_update() != function[1]:
                        copy_list_reactive_constraints[counter][1] = input.constraint_a1_update()
                        list_reactive_constraints.set(copy_list_reactive_constraints)

                    if input.constraint_a1_value_range_update() != function[2]:
                        copy_list_reactive_constraints[counter][2] = input.constraint_a1_value_range_update()
                        list_reactive_constraints.set(copy_list_reactive_constraints)

                    if input.constraint_a2_update() != function[3]:
                        copy_list_reactive_constraints[counter][3] = input.constraint_a2_update()
                        list_reactive_constraints.set(copy_list_reactive_constraints)

                    if input.constraint_a2_value_range_update() != function[4]:
                        copy_list_reactive_constraints[counter][4] = input.constraint_a2_value_range_update()
                        list_reactive_constraints.set(copy_list_reactive_constraints)

                    if input.comparison_operator_update() != function[5]:
                        copy_list_reactive_constraints[counter][5] = input.comparison_operator_update()
                        list_reactive_constraints.set(copy_list_reactive_constraints)

                    if input.bounding_constant_update() != function[6]:
                        copy_list_reactive_constraints[counter][6] = input.bounding_constant_update()
                        list_reactive_constraints.set(copy_list_reactive_constraints)

                    if input.constraint_name_update() != function[0]:
                        copy_list_reactive_constraints[counter][0] = input.constraint_name_update()
                        list_reactive_constraints.set(copy_list_reactive_constraints)

                        copy_dict_reactive_constraints = dict_reactive_constraints.get().copy()
                        copy_dict_reactive_constraints[input.constraint_name_update()] = input.constraint_name_update()
                        del copy_dict_reactive_constraints[selected_constraint_name]
                        dict_reactive_constraints.set(copy_dict_reactive_constraints)

                    ui.update_select("selectize_constraints", choices=dict_reactive_constraints.get())

                counter += 1

            notification_popup("Constraint changed successfully")
            ui.modal_remove()

    # Submit button 6
    @reactive.effect
    @reactive.event(input.submit_button_6)
    def delete_restriction():
        copy_list_reactive_constraints = list_reactive_constraints.get().copy()
        copy_dict_constraints = dict_reactive_constraints.get().copy()
        for function in list_reactive_constraints.get():
            if function[0] == input.select_constraint_delete():
                copy_list_reactive_constraints.remove(function)
                list_reactive_constraints.set(copy_list_reactive_constraints)

                del copy_dict_constraints[input.select_constraint_delete()]
                dict_reactive_constraints.set(copy_dict_constraints)
        ui.update_selectize("selectize_constraints", choices=dict_reactive_constraints.get())
        if not list_reactive_constraints.get():
            ui.update_action_button("btn_change_constraint", disabled=True)
            ui.update_action_button("btn_delete_constraint", disabled=True)

        notification_popup("Constraint deleted successfully")
        ui.modal_remove()

    # Render text
    @output
    @render.ui
    def txt_constraint():
        return txt_constraint_reactive()

    @reactive.Calc
    def txt_constraint_reactive():
        summarized_text_constraint = ""
        for function in list_reactive_constraints.get():
            summarized_text_constraint += function_as_text(function) + "<br><br>"
        return ui.HTML(summarized_text_constraint)

    @output
    @render.ui
    def txt_obj_func():
        return txt_obj_func_reactive()

    @reactive.Calc
    def txt_obj_func_reactive():
        summarized_text_obj_func = ""
        for function in list_reactive_obj_func.get():
            summarized_text_obj_func += function_as_text(function) + "<br><br>"
        return ui.HTML(summarized_text_obj_func)

    @reactive.effect
    @reactive.event(input.select_obj_func_change)
    def update_obj_func_changing_placeholder():
        selected_function_name = input.select_obj_func_change()
        for function in list_reactive_obj_func.get():
            if function[0] == selected_function_name:
                ui.update_text("obj_func_name_update", value=function[0])
                ui.update_numeric("obj_func_c1_update", value=function[1])
                ui.update_select("obj_func_c1_value_range_update", selected=function[2])
                ui.update_numeric("obj_func_c2_update", value=function[3])
                ui.update_select("obj_func_c2_value_range_update", selected=function[4])
                ui.update_select("obj_func_min_max_update", selected=function[5])

    @output
    @render.text
    def mod4_text():
        return update_mod4_text()

    @reactive.event(input.select_obj_func_delete)
    def update_mod4_text():
        for function in list_reactive_obj_func.get():
            if function[0] == input.select_obj_func_delete():
                return function_as_text(function)

    @reactive.effect
    @reactive.event(input.select_constraint_change)
    def update_constraint_changing_placeholder():
        selected_function_name = input.select_constraint_change()
        for function in list_reactive_constraints.get():
            if function[0] == selected_function_name:
                ui.update_text("constraint_name_update", value=function[0])
                ui.update_numeric("constraint_a1_update", value=function[1])
                ui.update_select("constraint_a1_value_range_update", selected=function[2])
                ui.update_numeric("constraint_a2_update", value=function[3])
                ui.update_select("constraint_a2_value_range_update", selected=function[4])
                ui.update_select("comparison_operator_update", selected=function[5])
                ui.update_numeric("bounding_constant_update", value=function[6])

    @output
    @render.text
    def mod6_text():
        return update_mod6_text()

    @reactive.event(input.select_constraint_delete)
    def update_mod6_text():
        for function in list_reactive_constraints.get():
            if function[0] == input.select_constraint_delete():
                return function_as_text(function)

    @output
    @render.ui
    def txt_lin_prog_type():
        return update_txt_lin_prog_type()

    @reactive.Calc
    def update_txt_lin_prog_type():

        if not list_reactive_selected_obj_func.get() and not list_reactive_selected_constraints.get():
            return ui.HTML(
                '<div style="text-align: center;"><b>Please select objective function and constraint(s).</b></div>')

        else:
            try:

                copy_list_reactive_selected_constraints = list_reactive_selected_constraints.get().copy()
                copy_list_reactive_selected_obj_func = list_reactive_selected_obj_func.get().copy()

                for constraint in list_reactive_constraints.get():
                    if constraint[
                        0] in input.selectize_constraints() and constraint not in list_reactive_selected_constraints.get():
                        copy_list_reactive_selected_constraints.append(constraint)
                        list_reactive_selected_constraints.set(copy_list_reactive_selected_constraints)

                for obj_func in list_reactive_obj_func.get():
                    if obj_func[
                        0] in input.select_obj_func() and obj_func not in list_reactive_selected_obj_func.get():
                        copy_list_reactive_selected_obj_func.append(obj_func)
                        list_reactive_selected_obj_func.set(copy_list_reactive_selected_obj_func)

                if not list_reactive_selected_obj_func.get() and not list_reactive_selected_constraints.get():
                    copy_string_reactive_problem_type = "not defined"
                    string_reactive_problem_type.set(copy_string_reactive_problem_type)
                    return ui.HTML(
                        '<div style="text-align: center;"><b>Please select objective function and constraint(s).</b></div>')


                elif list_reactive_selected_obj_func.get() or list_reactive_selected_constraints.get():
                    summarized_text_constraint = "<br>The selection of objective functions<br> <br>and constraints results in the<br> <br>following final selection for your problem:<br>"

                    value_range_list = []
                    for function in list_reactive_selected_obj_func.get():
                        value_range_list.append([function[2], "x1"])
                        value_range_list.append([function[4], "x2"])

                    for function in list_reactive_selected_constraints.get():
                        value_range_list.append([function[2], "x1"])
                        value_range_list.append([function[4], "x2"])

                    value_ranges_only = [entry[0] for entry in value_range_list]

                    if "int" in value_ranges_only and not "con" in value_ranges_only:
                        summarized_text_constraint += "<br><b>Integer Linear Programming (ILP)</b><br>within this value range:<br> <br><div style='text-align: center;'><b>x1 ∈ ℕ<sub>0</sub> ; x2 ∈ ℕ<sub>0</sub></b></div>"
                        copy_string_reactive_problem_type = "ILP"
                        string_reactive_problem_type.set(copy_string_reactive_problem_type)
                    elif "con" in value_ranges_only and not "int" in value_ranges_only:
                        summarized_text_constraint += "<br><b>Linear Programming (LP)</b><br>within this value range:<br> <br><div style='text-align: center;'><b>x1 ≥ 0 ; x2 ≥ 0</b></div>"
                        copy_string_reactive_problem_type = "LP"
                        string_reactive_problem_type.set(copy_string_reactive_problem_type)
                    elif "int" in value_ranges_only and "con" in value_ranges_only:
                        summarized_text_constraint += "<br><b>Mixed Integer Linear Programming (MILP)</b>"

                        x1_int_counter = 0
                        x1_con_counter = 0
                        x2_int_counter = 0
                        x2_con_counter = 0
                        for entry in value_range_list:
                            if entry[1] == "x1" and entry[0] == "int":
                                x1_int_counter += 1
                            elif entry[1] == "x1" and entry[0] == "con":
                                x1_con_counter += 1
                            elif entry[1] == "x2" and entry[0] == "int":
                                x2_int_counter += 1
                            elif entry[1] == "x2" and entry[0] == "con":
                                x2_con_counter += 1

                        if (len(value_range_list) / 2) == x1_int_counter and (
                                len(value_range_list) / 2) == x2_con_counter:
                            summarized_text_constraint += "<br>within this value range:<br> <br><div style='text-align: center;'><b>x1 ∈ ℕ<sub>0</sub> ; x2 ≥ 0</b></div>"
                            copy_string_reactive_problem_type = "MILP_x1_int_x2_con"
                            string_reactive_problem_type.set(copy_string_reactive_problem_type)
                        elif (len(value_range_list) / 2) == x1_con_counter and (
                                len(value_range_list) / 2) == x2_int_counter:
                            summarized_text_constraint += "<br>within this value range:<br> <br><div style='text-align: center;'><b>x1 ≥ 0 ; x2 ∈ ℕ<sub>0</sub></b></div>"
                            copy_string_reactive_problem_type = "MILP_x1_con_x2_int"
                            string_reactive_problem_type.set(copy_string_reactive_problem_type)
                        else:
                            if list_reactive_selected_constraints.get():
                                summarized_text_constraint += "<br>within this value range:<br> <br><div style='text-align: center;'><b>Please set x1 and x2 to one value only</b></div>"
                                copy_string_reactive_problem_type = "not defined"
                                string_reactive_problem_type.set(copy_string_reactive_problem_type)

                    return ui.HTML(f'<div style="text-align: center;">{summarized_text_constraint}</div>')
            except TypeError:
                return ui.HTML(
                    '<div style="text-align: center;"><b>Please select objective function and constraint(s).</b></div>')

    # Render data frame
    @output
    @render.data_frame
    def df_output_value_ranges():
        return update_df_output_value_ranges()

    @reactive.Calc
    def update_df_output_value_ranges():

        df_value_ranges = pd.DataFrame(columns=["Name", "x1", "x2", "Total"])

        for function in list_reactive_obj_func.get():

            value_range_total = None
            if function[2] == "int" and function[4] == "int":
                value_range_total = "integer lp (ILP)"
            elif (function[2] == "int" and function[4] == "con") or (function[2] == "con" and function[4] == "int"):
                value_range_total = "mixed integer lp (MILP)"
            elif function[2] == "con" and function[4] == "con":
                value_range_total = "linear programming (LP)"

            df_value_ranges.loc[len(df_value_ranges)] = [function[0], function[2], function[4], value_range_total]

        for function in list_reactive_constraints.get():

            value_range_total = None
            if function[2] == "int" and function[4] == "int":
                value_range_total = "integer lp (ILP)"
            elif (function[2] == "int" and function[4] == "con") or (function[2] == "con" and function[4] == "int"):
                value_range_total = "mixed integer lp (MILP)"
            elif function[2] == "con" and function[4] == "con":
                value_range_total = "linear programming (LP)"

            df_value_ranges.loc[len(df_value_ranges)] = [function[0], function[2], function[4], value_range_total]

        return render.DataGrid(df_value_ranges)

    @output
    @render.data_frame
    def df_lp_results():
        return update_df_lp_results()

    @reactive.Calc
    def update_df_lp_results():

        try:
            if not list_reactive_solved_problem.get():
                df_result = pd.DataFrame({
                    "Name": [""],
                    "x1": [""],
                    "x2": [""]
                })

                return render.DataGrid(df_result)

            if list_reactive_solved_problem.get():
                name_column = ""
                for function in list_reactive_obj_func.get():
                    if function[0] in input.select_obj_func():
                        name_column = function[0]

                df_result = pd.DataFrame({
                    name_column: [list_reactive_solved_problem.get()[0][6]],
                    "x1": [list_reactive_solved_problem.get()[1][0]],
                    "x2": [list_reactive_solved_problem.get()[1][1]]
                })

                return render.DataGrid(df_result)

        except TypeError:
            df_result = pd.DataFrame({
                "Name": [""],
                "x1": [""],
                "x2": [""]
            })

            return render.DataGrid(df_result)

    # Procedure if something changes in the function selection
    @reactive.effect
    @reactive.event(input.selectize_constraints, input.select_obj_func)
    def update_selected_lists():
        # Initialise updated lists
        updated_list_reactive_selected_constraints = []
        updated_list_reactive_selected_obj_func = []

        # Only add the constraints that are actually selected
        for constraint in list_reactive_constraints.get():
            if constraint[0] in input.selectize_constraints():
                updated_list_reactive_selected_constraints.append(constraint)

        # Only add the objective function that is actually selected
        for obj_func in list_reactive_obj_func.get():
            if obj_func[0] == input.select_obj_func():
                updated_list_reactive_selected_obj_func.append(obj_func)

        # Set the updated lists
        list_reactive_selected_constraints.set(updated_list_reactive_selected_constraints)
        list_reactive_selected_obj_func.set(updated_list_reactive_selected_obj_func)

        # Reset the solved problem
        list_reactive_solved_problem.set([])

    # Render the graph / plot
    @output
    @render.plot()
    def plot_output_graph():
        plot_output_graph_reactive()

    @reactive.event(input.selectize_constraints, input.select_obj_func, input.btn_lin_opt)
    def plot_output_graph_reactive():


        status_value_ranges_coeffs = check_coeff_value_ranges()

        if (not input.selectize_constraints() and not input.select_obj_func()) or status_value_ranges_coeffs[
            2] == "unselected_obj_func" or status_value_ranges_coeffs[2] == "unselected_constraints":
            fig, ax = plt.subplots()
            ax.spines["top"].set_color("none")
            ax.spines["right"].set_color("none")
            ax.grid(True, ls="--")
            ax.set_xlabel("x1-axis")
            ax.set_ylabel("x2-axis")
            ax.plot(1, 0, ">k", transform=ax.get_yaxis_transform(), clip_on=False)
            ax.plot(0, 1, "^k", transform=ax.get_xaxis_transform(), clip_on=False)
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 10)
            ui.update_action_button("btn_lin_opt", disabled=True)
            ui.update_action_button("btn_sens_ana", disabled=True)
            ui.update_action_button("btn_save_graph", disabled=True)
            if input.selectize_constraints() and not input.select_obj_func():
                notification_popup("Please select an objective function.", message_type="warning")
            elif not input.selectize_constraints() and input.select_obj_func():
                notification_popup("Please select at least one constraint.", message_type="warning")
            return fig


        elif (status_value_ranges_coeffs[0] != 1 or status_value_ranges_coeffs[1] != 1) and status_value_ranges_coeffs[
            2] == "all_selected":
            notification_popup(
                "The defined value ranges for x1 and x2 are not consistent, please check your entries so that all x1 have the same value range and all x2 have the same value range.",
                message_type="error")
            notification_popup("Graph could not be generated.",
                               message_type="error")
            fig, ax = plt.subplots()
            ax.spines["top"].set_color("none")
            ax.spines["right"].set_color("none")
            ax.grid(True, ls="--")
            ax.set_xlabel("x1-axis")
            ax.set_ylabel("x2-axis")
            ax.plot(1, 0, ">k", transform=ax.get_yaxis_transform(), clip_on=False)
            ax.plot(0, 1, "^k", transform=ax.get_xaxis_transform(), clip_on=False)
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 10)
            ui.update_action_button("btn_lin_opt", disabled=True)
            ui.update_action_button("btn_sens_ana", disabled=True)
            ui.update_action_button("btn_save_graph", disabled=True)
            return fig



        else:
            try:
                ui.update_action_button("btn_save_graph", disabled=False)

                fig, ax = plt.subplots()

                ax.spines["top"].set_color("none")
                ax.spines["right"].set_color("none")
                ax.grid(True, ls="--")
                ax.set_xlabel("x1-axis")
                ax.set_ylabel("x2-axis")

                update_list_reactive_xlim_var = []
                update_list_reactive_ylim_var = []
                update_dict_reactive_func_colors = {}
                update_dict_reactive_xlim_var = {}
                update_dict_reactive_ylim_var = {}

                for constraint in list_reactive_selected_constraints.get():

                    cutting_point_x1 = calculate_cutting_points_x1_x2_axis(constraint)[0]
                    cutting_point_x2 = calculate_cutting_points_x1_x2_axis(constraint)[1]
                    random_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                    if constraint[1] != 0 and constraint[3] != 0:
                        ax.plot([0, cutting_point_x1], [cutting_point_x2, 0], label=constraint[0], color=random_color)
                    elif constraint[1] == 0 and constraint[3] != 0:
                        ax.axhline(y=cutting_point_x2, color=random_color, linestyle='-', label=constraint[0])
                    elif constraint[1] != 0 and constraint[3] == 0:
                        ax.axvline(x=cutting_point_x1, color=random_color, linestyle='-', label=constraint[0])

                    update_list_reactive_xlim_var.append([cutting_point_x1, constraint[0]])
                    update_list_reactive_ylim_var.append([cutting_point_x2, constraint[0]])
                    update_dict_reactive_xlim_var[constraint[0]] = cutting_point_x1
                    update_dict_reactive_ylim_var[constraint[0]] = cutting_point_x2
                    update_dict_reactive_func_colors[constraint[0]] = random_color
                    list_reactive_xlim_var.set(update_list_reactive_xlim_var)
                    list_reactive_ylim_var.set(update_list_reactive_ylim_var)
                    dict_reactive_xlim_var.set(update_dict_reactive_xlim_var)
                    dict_reactive_ylim_var.set(update_dict_reactive_ylim_var)
                    dict_reactive_func_colors.set(update_dict_reactive_func_colors)

                for obj_func in list_reactive_selected_obj_func.get():
                    cutting_point_x1, cutting_point_x2 = calculate_cutting_points_x1_x2_axis(obj_func,
                                                                                             update_list_reactive_xlim_var,
                                                                                             update_list_reactive_ylim_var)

                    ax.plot([0, cutting_point_x1], [cutting_point_x2, 0], label=obj_func[0] + " (dummy)",
                            color="#00FF00",
                            ls="--")

                    update_list_reactive_xlim_var.append([cutting_point_x1, obj_func[0]])

                    update_list_reactive_ylim_var.append([cutting_point_x2, obj_func[0]])

                    update_dict_reactive_xlim_var[obj_func[0]] = cutting_point_x1
                    update_dict_reactive_ylim_var[obj_func[0]] = cutting_point_x2

                    update_dict_reactive_func_colors[obj_func[0]] = "#00FF00"

                    list_reactive_xlim_var.set(update_list_reactive_xlim_var)
                    list_reactive_ylim_var.set(update_list_reactive_ylim_var)

                    dict_reactive_xlim_var.set(update_dict_reactive_xlim_var)
                    dict_reactive_ylim_var.set(update_dict_reactive_ylim_var)

                    dict_reactive_func_colors.set(update_dict_reactive_func_colors)

                ax.set_xlim(0, math.ceil(((calculate_highest_xlim_ylim(list_reactive_xlim_var.get(),
                                                                       list_reactive_ylim_var.get())[0]) * 1.1)))
                ax.set_ylim(0, math.ceil(((calculate_highest_xlim_ylim(list_reactive_xlim_var.get(),
                                                                       list_reactive_ylim_var.get())[1]) * 1.1)))

                ax.plot(1, 0, ">k", transform=ax.get_yaxis_transform(), clip_on=False)
                ax.plot(0, 1, "^k", transform=ax.get_xaxis_transform(), clip_on=False)

                ui.update_action_button("btn_lin_opt", disabled=False)

                # Feasible region

                if input.selectize_constraints():
                    with ui.Progress() as progress_bar_feasible_region:
                        progress_bar_feasible_region.set(message="Calculating graph", detail="loading... please wait")
                        progress_bar_feasible_region.set(0.1)

                        # collects sets. Each set contains points that belong to a constraint
                        list_sets_constraint_points_feasible_region = []

                        list_reactive_y_values_equal_problem.set([])
                        equals_detected = False

                        highest_selected_a1 = 0
                        highest_selected_a2 = 0

                        # The highest a1 and a2 values of the selected constraints are identified
                        # In addition, the constraints with an ‘=’ are identified and sorted to the front. These must be calculated first in order to determine the feasible region
                        # otherwise it would have to be calculated twice
                        sorted_constraints = []

                        for constraint in list_reactive_selected_constraints.get():
                            if dict_reactive_xlim_var.get()[constraint[0]] > highest_selected_a1:
                                highest_selected_a1 = dict_reactive_xlim_var.get()[constraint[0]]
                            if dict_reactive_ylim_var.get()[constraint[0]] > highest_selected_a2:
                                highest_selected_a2 = dict_reactive_ylim_var.get()[constraint[0]]
                            if constraint[5] == "=":
                                sorted_constraints.insert(0, constraint)
                            elif constraint[5] != "=":
                                sorted_constraints.append(constraint)

                        # The a1 and a2 values of the selected constraints are displayed on a specific scale. For further calculations.
                        scale_x = (highest_selected_a1 / 750) + ((1 / 750) * (highest_selected_a1 / 750))
                        if scale_x == 0:
                            scale_x = 1
                        scale_y = (highest_selected_a2 / 400) + ((1 / 400) * (highest_selected_a2 / 400))
                        if scale_y == 0:
                            scale_y = 1
                        # additional x and y values that must be added to the x and y values of the selected constraints to determine the feasible region.
                        x_values_to_add_to_x_range = []
                        y_values_to_add_to_y_range = []
                        y_values_equal_problems = []

                        for_counter = 0

                        progress_bar_feasible_region.set(0.2)
                        for constraint in sorted_constraints:
                            points = set()

                            if constraint[5] == "=":

                                x_range = None

                                if string_reactive_problem_type.get() == "LP" or string_reactive_problem_type.get() == "MILP_x1_con_x2_int" or string_reactive_problem_type.get() == "MILP_x1_int_x2_con":
                                    if dict_reactive_xlim_var.get()[constraint[0]] != 0:
                                        if dict_reactive_ylim_var.get()[constraint[0]] != 0:
                                            x_range = np.arange(0, dict_reactive_xlim_var.get()[constraint[0]], scale_x)
                                        elif dict_reactive_ylim_var.get()[constraint[0]] == 0:
                                            x_range = dict_reactive_xlim_var.get()[constraint[0]]
                                    elif dict_reactive_xlim_var.get()[constraint[0]] == 0:
                                        x_range = np.arange(0, ax.get_xlim()[1], scale_x)
                                    if dict_reactive_xlim_var.get()[constraint[0]] not in x_range:
                                        x_range = np.append(x_range, dict_reactive_xlim_var.get()[constraint[0]])
                                        x_values_to_add_to_x_range.append(
                                            dict_reactive_xlim_var.get()[constraint[0]])
                                    if for_counter > 0 and x_values_to_add_to_x_range:
                                        for entry in x_values_to_add_to_x_range:

                                            if entry not in x_range and entry < dict_reactive_xlim_var.get()[
                                                constraint[0]]:
                                                x_range = np.append(x_range, entry)

                                    progress_bar_feasible_region.set(0.5)
                                    for x in x_range:
                                        if dict_reactive_ylim_var.get()[constraint[0]] != 0:
                                            y_max = y_result_to_linear_equation(
                                                dict_reactive_xlim_var.get()[constraint[0]],
                                                dict_reactive_ylim_var.get()[constraint[0]],
                                                x)
                                        elif dict_reactive_ylim_var.get()[constraint[0]] == 0:
                                            y_max = ax.get_ylim()[1]

                                        if dict_reactive_ylim_var.get()[constraint[0]] != 0:
                                            points.add((x, y_max))
                                        elif dict_reactive_ylim_var.get()[constraint[0]] == 0:
                                            for number in np.arange(0, ax.get_ylim()[1], scale_y):
                                                points.add((x, number))

                                        y_values_equal_problems.append((x, y_max))

                                    equals_detected = True
                                    list_reactive_y_values_equal_problem.set(y_values_equal_problems)
                                    progress_bar_feasible_region.set(0.8)




                                elif string_reactive_problem_type.get() == "ILP" or string_reactive_problem_type.get() == "MILP_x1_int_x2_con" or string_reactive_problem_type.get() == "MILP_x1_con_x2_int":

                                    if dict_reactive_xlim_var.get()[constraint[0]] % 1 != 0:
                                        x_range = np.arange(0, dict_reactive_xlim_var.get()[constraint[0]], 1)
                                    elif dict_reactive_xlim_var.get()[constraint[0]] % 1 == 0:
                                        if dict_reactive_xlim_var.get()[constraint[0]] != 0:
                                            x_range = np.arange(0, dict_reactive_xlim_var.get()[constraint[0]] + 1, 1)
                                        elif dict_reactive_xlim_var.get()[constraint[0]] == 0:
                                            x_range = np.arange(0, ax.get_xlim()[1], 1)

                                    if dict_reactive_xlim_var.get()[constraint[0]] != 0 and \
                                            dict_reactive_ylim_var.get()[constraint[0]] == 0:
                                        if dict_reactive_xlim_var.get()[constraint[0]] % 1 == 0:
                                            x_range = dict_reactive_xlim_var.get()[constraint[0]]
                                        elif dict_reactive_xlim_var.get()[constraint[0]] % 1 != 0:
                                            x_range = 0

                                    progress_bar_feasible_region.set(0.5)
                                    for x in x_range:
                                        if dict_reactive_ylim_var.get()[constraint[0]] != 0:
                                            y = y_result_to_linear_equation(dict_reactive_xlim_var.get()[constraint[0]],
                                                                            dict_reactive_ylim_var.get()[constraint[0]],
                                                                            x)
                                        elif dict_reactive_ylim_var.get()[constraint[0]] == 0:
                                            y_max = ax.get_ylim()[1]

                                        if y % 1 != 0:
                                            continue
                                        elif y % 1 == 0:
                                            if dict_reactive_ylim_var.get()[constraint[0]] != 0:
                                                points.add((x, y))
                                            elif dict_reactive_ylim_var.get()[constraint[0]] == 0:
                                                for number in range(0, ax.get_ylim()[1] + 1, 1):
                                                    points.add((x, number))

                                    equals_detected = True
                                    progress_bar_feasible_region.set(0.8)




                            elif constraint[5] == "≤":

                                x_range = None

                                if string_reactive_problem_type.get() == "LP" or string_reactive_problem_type.get() == "MILP_x1_con_x2_int":
                                    if dict_reactive_xlim_var.get()[constraint[0]] != 0:
                                        x_range = np.arange(0, dict_reactive_xlim_var.get()[constraint[0]], scale_x)
                                    elif dict_reactive_xlim_var.get()[constraint[0]] == 0:
                                        x_range = np.arange(0, ax.get_xlim()[1], scale_x)
                                    if dict_reactive_xlim_var.get()[constraint[0]] not in x_range:
                                        x_range = np.append(x_range, dict_reactive_xlim_var.get()[constraint[0]])
                                        x_values_to_add_to_x_range.append(
                                            dict_reactive_xlim_var.get()[constraint[0]])
                                    if for_counter > 0 and x_values_to_add_to_x_range:
                                        for entry in x_values_to_add_to_x_range:
                                            if entry not in x_range and entry < dict_reactive_xlim_var.get()[
                                                constraint[0]]:
                                                x_range = np.append(x_range, entry)
                                    progress_bar_feasible_region.set(0.5)



                                elif string_reactive_problem_type.get() == "ILP" or string_reactive_problem_type.get() == "MILP_x1_int_x2_con":

                                    # integer only
                                    # for continuous numbers at the last x-value: the last straight x-value is included
                                    if dict_reactive_xlim_var.get()[constraint[0]] % 1 != 0:
                                        x_range = np.arange(0, dict_reactive_xlim_var.get()[constraint[0]], 1)
                                    # for integer numbers at the last x-value: the last straight x-value is not included, therefore +1
                                    elif dict_reactive_xlim_var.get()[constraint[0]] % 1 == 0:
                                        if dict_reactive_xlim_var.get()[constraint[0]] != 0:
                                            x_range = np.arange(0, dict_reactive_xlim_var.get()[constraint[0]] + 1, 1)
                                        elif dict_reactive_xlim_var.get()[constraint[0]] == 0:
                                            x_range = np.arange(0, ax.get_xlim()[1], 1)
                                    progress_bar_feasible_region.set(0.5)

                                for x in x_range:
                                    if dict_reactive_ylim_var.get()[constraint[0]] != 0:
                                        y_max = y_result_to_linear_equation(dict_reactive_xlim_var.get()[constraint[0]],
                                                                            dict_reactive_ylim_var.get()[constraint[0]],
                                                                            x)
                                    elif dict_reactive_ylim_var.get()[constraint[0]] == 0:
                                        y_max = ax.get_ylim()[1]

                                    if string_reactive_problem_type.get() == "LP" or string_reactive_problem_type.get() == "MILP_x1_int_x2_con":

                                        y_range = np.arange(0, y_max, scale_y)
                                        if y_max not in y_range:
                                            y_range = np.append(y_range, y_max)
                                            y_values_to_add_to_y_range.append(
                                                y_max)
                                        if for_counter > 0 and y_values_to_add_to_y_range:
                                            for entry in y_values_to_add_to_y_range:
                                                if entry not in y_range and entry < y_max:
                                                    y_range = np.append(y_range, entry)

                                        for y in y_range:
                                            points.add(
                                                (x, y))

                                        if list_reactive_y_values_equal_problem.get():
                                            for equal_problem_points in list_reactive_y_values_equal_problem.get():
                                                x_value, y_value = equal_problem_points
                                                if x_value == x and y_value <= y_max:
                                                    points.add((x, y_value))

                                        progress_bar_feasible_region.set(0.8)




                                    elif string_reactive_problem_type.get() == "ILP" or string_reactive_problem_type.get() == "MILP_x1_con_x2_int":

                                        if y_max % 1 != 0:
                                            for y in np.arange(0, y_max, 1):
                                                points.add((x, y))


                                        elif y_max % 1 == 0:
                                            for y in np.arange(0, y_max + 1, 1):
                                                points.add((x, y))
                                        progress_bar_feasible_region.set(0.8)



                            elif constraint[5] == "≥":

                                max_y_value = ax.get_ylim()[1]
                                x_range = None
                                y_range = None

                                if string_reactive_problem_type.get() == "LP" or string_reactive_problem_type.get() == "MILP_x1_con_x2_int":

                                    x_range = np.arange(0, ax.get_xlim()[1], scale_x)
                                    if dict_reactive_xlim_var.get()[constraint[0]] not in x_range:
                                        x_range = np.append(x_range, dict_reactive_xlim_var.get()[constraint[0]])
                                        x_values_to_add_to_x_range.append(
                                            dict_reactive_xlim_var.get()[constraint[0]])
                                    if for_counter > 0 and x_values_to_add_to_x_range:
                                        for entry in x_values_to_add_to_x_range:

                                            if entry not in x_range:
                                                x_range = np.append(x_range, entry)

                                    progress_bar_feasible_region.set(0.5)




                                elif string_reactive_problem_type.get() == "ILP" or string_reactive_problem_type.get() == "MILP_x1_int_x2_con":

                                    if ax.get_xlim()[1] % 1 != 0:
                                        x_range = np.arange(0, ax.get_xlim()[1], 1)
                                    elif ax.get_xlim()[1] % 1 == 0:
                                        x_range = np.arange(0, ax.get_xlim()[1] + 1, 1)

                                    progress_bar_feasible_region.set(0.5)

                                for x in x_range:

                                    y_min = None
                                    if dict_reactive_ylim_var.get()[constraint[0]] != 0:
                                        if dict_reactive_xlim_var.get()[constraint[0]] != 0:
                                            if x <= dict_reactive_xlim_var.get()[constraint[0]]:
                                                y_min = y_result_to_linear_equation(
                                                    dict_reactive_xlim_var.get()[constraint[0]],
                                                    dict_reactive_ylim_var.get()[constraint[0]],
                                                    x
                                                )
                                            elif x > dict_reactive_xlim_var.get()[constraint[0]]:

                                                y_min = 0
                                        elif dict_reactive_xlim_var.get()[constraint[0]] == 0:
                                            y_min = calculate_cutting_points_x1_x2_axis(constraint)[1]
                                    elif dict_reactive_ylim_var.get()[constraint[0]] == 0:
                                        y_min = 0

                                    if string_reactive_problem_type.get() == "LP" or string_reactive_problem_type.get() == "MILP_x1_int_x2_con":

                                        y_range_total = np.arange(0, max_y_value, scale_y)
                                        if max_y_value not in y_range_total:
                                            y_range_total = np.append(y_range_total, max_y_value)
                                        if y_min not in y_range_total:
                                            y_range_total = np.append(y_range_total, y_min)
                                            y_values_to_add_to_y_range.append(y_min)
                                        if for_counter > 0 and y_values_to_add_to_y_range:
                                            for entry in y_values_to_add_to_y_range:
                                                if entry not in y_range_total and entry < y_min:
                                                    y_range_total = np.append(y_range_total, entry)

                                        if x <= dict_reactive_xlim_var.get()[constraint[0]]:
                                            y_range_under_line = np.arange(0, y_min, scale_y)
                                            if y_min in y_range_under_line:
                                                y_range_under_line = y_range_under_line[y_range_under_line != y_min]

                                            # returns symmetrical difference with unique elements
                                            y_range = np.setxor1d(y_range_total, y_range_under_line)

                                        elif x > dict_reactive_xlim_var.get()[constraint[0]]:
                                            y_range = y_range_total

                                        for y in y_range:
                                            points.add(
                                                (x, y))

                                        if list_reactive_y_values_equal_problem.get():
                                            for equal_problem_points in list_reactive_y_values_equal_problem.get():

                                                x_value, y_value = equal_problem_points
                                                if x_value == x and y_value >= y_min:
                                                    points.add((x, y_value))

                                        progress_bar_feasible_region.set(0.8)



                                    elif string_reactive_problem_type.get() == "ILP" or string_reactive_problem_type.get() == "MILP_x1_con_x2_int":

                                        if y_min % 1 != 0:
                                            for y in np.arange(math.trunc(y_min) + 1, max_y_value + 1, 1):
                                                points.add((x, y))

                                        elif y_min % 1 == 0:
                                            for y in np.arange(y_min, max_y_value + 1, 1):
                                                points.add((x, y))

                                        progress_bar_feasible_region.set(0.8)

                            list_sets_constraint_points_feasible_region.append(points)

                            for_counter += 1

                        progress_bar_feasible_region.set(0.9)
                        intersection_points = None
                        counter = 0

                        for set_entry in list_sets_constraint_points_feasible_region:
                            if counter == 0:
                                intersection_points = set_entry
                            elif counter > 0:
                                intersection_points = intersection_points.intersection(set_entry)
                            counter += 1

                        common_x_values = [point[0] for point in intersection_points]
                        common_y_values = [point[1] for point in intersection_points]

                        if string_reactive_problem_type.get() == "ILP":
                            ax.scatter(common_x_values, common_y_values, color='grey', s=5, alpha=0.8)
                        elif equals_detected:
                            ax.scatter(common_x_values, common_y_values, color='grey', s=8, alpha=1)
                        elif string_reactive_problem_type.get() == "MILP_x1_int_x2_con" or string_reactive_problem_type.get() == "MILP_x1_con_x2_int":
                            ax.scatter(common_x_values, common_y_values, color='lightgrey', s=5, alpha=0.6)
                        else:
                            ax.scatter(common_x_values, common_y_values, color='lightgrey', s=4, alpha=0.2)

                        progress_bar_feasible_region.set(1)

                if list_reactive_solved_problem.get():
                    update_dict_reactive_func_colors = dict_reactive_func_colors.get().copy()

                    cutting_point_x1 = calculate_cutting_points_x1_x2_axis(list_reactive_solved_problem.get()[0])[0]
                    cutting_point_x2 = calculate_cutting_points_x1_x2_axis(list_reactive_solved_problem.get()[0])[1]
                    ax.plot([0, cutting_point_x1], [cutting_point_x2, 0],
                            label=list_reactive_solved_problem.get()[0][0] + " (optimized)", color="#0000FF", ls="--")

                    ax.plot(list_reactive_solved_problem.get()[1][0], list_reactive_solved_problem.get()[1][1], "or",
                            markersize=8)

                    x_axis_ticks = ax.get_xticks()
                    y_axis_ticks = ax.get_yticks()
                    distance_between_two_xticks = x_axis_ticks[2] - x_axis_ticks[1]
                    distance_between_two_yticks = y_axis_ticks[2] - y_axis_ticks[1]
                    opt_solution_arrow_start_x = list_reactive_solved_problem.get()[1][0] + distance_between_two_xticks
                    opt_solution_arrow_start_y = list_reactive_solved_problem.get()[1][1] + distance_between_two_yticks
                    ax.arrow(opt_solution_arrow_start_x, opt_solution_arrow_start_y,
                             distance_between_two_xticks * 0.9 * -1,
                             distance_between_two_yticks * 0.9 * -1, color="red",
                             width=(((distance_between_two_xticks + distance_between_two_yticks) / 2) * (1 / 50)),
                             head_width=distance_between_two_xticks * 0.05,
                             head_length=distance_between_two_yticks * 0.15,
                             length_includes_head=True)
                    ax.annotate("Optimum solution", [opt_solution_arrow_start_x, opt_solution_arrow_start_y],
                                color="red")

                    # Creation of the green arrow and the label ‘’displacement‘’. By calculating the linear equation of the dummy objective function (mx +b)
                    if dict_reactive_xlim_var.get()[list_reactive_selected_obj_func.get()[0][0]] != 0: # to avoid division by zero
                        gradient_obj_func_dummy = (
                                (dict_reactive_ylim_var.get()[list_reactive_selected_obj_func.get()[0][0]] - 0) / (
                                0 - dict_reactive_xlim_var.get()[list_reactive_selected_obj_func.get()[0][0]]))
                        b_dummy = (-1) * gradient_obj_func_dummy * dict_reactive_xlim_var.get()[
                            list_reactive_selected_obj_func.get()[0][0]]

                        # the variables required for calculating the coordinates of the perpendicular base point
                        b = 1 * dict_reactive_xlim_var.get()[list_reactive_selected_obj_func.get()[0][0]]
                        a = gradient_obj_func_dummy * dict_reactive_xlim_var.get()[
                            list_reactive_selected_obj_func.get()[0][0]] * (-1)
                        c = b_dummy * dict_reactive_xlim_var.get()[list_reactive_selected_obj_func.get()[0][0]] * (-1)
                        x0 = list_reactive_solved_problem.get()[1][0]
                        y0 = list_reactive_solved_problem.get()[1][1]

                        # The coordinates of the perpendicular base point are calculated as follows
                        coord_perp_x = ((b * ((b * x0) - (a * y0))) - (a * c)) / ((a * a) + (b * b))
                        coord_perp_y = ((a * ((((-1) * b) * x0) + (a * y0))) - (b * c)) / ((a * a) + (b * b))

                        # After that, the distance of the perpendicular base point to the optimum solution is then calculated
                        x_distance_perp_x_to_opt_sol = list_reactive_solved_problem.get()[1][0] - coord_perp_x
                        y_distance_perp_y_to_opt_sol = list_reactive_solved_problem.get()[1][1] - coord_perp_y

                        # Depending on the objective function, the arrow is drawn in the corresponding direction
                        if list_reactive_selected_obj_func.get()[0][5] == "max":

                            ax.arrow(coord_perp_x, coord_perp_y, x_distance_perp_x_to_opt_sol * 0.9,
                                     y_distance_perp_y_to_opt_sol * 0.9, color="#008800",
                                     width=(((distance_between_two_xticks + distance_between_two_yticks) / 2) * (1 / 50)),
                                     head_width=distance_between_two_xticks * 0.05,
                                     head_length=distance_between_two_yticks * 0.15,
                                     length_includes_head=True)
                            ax.annotate("Displacement", [coord_perp_x, coord_perp_y], color="#008800")
                        elif list_reactive_selected_obj_func.get()[0][5] == "min":

                            ax.arrow(coord_perp_x, coord_perp_y, x_distance_perp_x_to_opt_sol * 0.9,
                                     y_distance_perp_y_to_opt_sol * 0.9, color="#008800",
                                     width=(((distance_between_two_xticks + distance_between_two_yticks) / 2) * (1 / 50)),
                                     head_width=distance_between_two_xticks * 0.05,
                                     head_length=distance_between_two_yticks * 0.15,
                                     length_includes_head=True)
                            ax.annotate("Displacement", [coord_perp_x, coord_perp_y], color="#008800")

                        update_dict_reactive_func_colors[list_reactive_solved_problem.get()[0][0]] = "#0000FF"
                        dict_reactive_func_colors.set(update_dict_reactive_func_colors)

                if list_reactive_selected_constraints.get() and not list_reactive_solved_problem.get():
                    dummy_patch = mpatches.Patch(color='grey', label='Feasible region')

                    ax.legend(handles=[dummy_patch] + ax.get_legend_handles_labels()[0], loc="upper right")
                elif list_reactive_selected_constraints.get() and list_reactive_solved_problem.get():

                    dummy_patch_1 = mlines.Line2D([], [], color='red', marker='o', linestyle='None', markersize=10,
                                                  label=f'Optimum solution\n{list_reactive_solved_problem.get()[0][0]}: {list_reactive_solved_problem.get()[0][6]}\nx1: {list_reactive_solved_problem.get()[1][0]}\nx2: {list_reactive_solved_problem.get()[1][1]}')
                    dummy_patch_2 = mpatches.Patch(color='grey', label='Feasible region')
                    ax.legend(handles=[dummy_patch_1, dummy_patch_2] + ax.get_legend_handles_labels()[0],
                              loc="upper right")
                else:
                    ax.legend(loc="upper right")

                reactive_plot_fig.set(fig)
                notification_popup("Graph created successfully")


                return fig

            except TypeError:
                notification_popup(
                    "An error occurred: Please unselect the constraints and select the ones you need again.")

                fig, ax = plt.subplots()
                ax.spines["top"].set_color("none")
                ax.spines["right"].set_color("none")
                ax.grid(True, ls="--")
                ax.set_xlabel("x1-axis")
                ax.set_ylabel("x2-axis")
                ax.plot(1, 0, ">k", transform=ax.get_yaxis_transform(), clip_on=False)
                ax.plot(0, 1, "^k", transform=ax.get_xaxis_transform(), clip_on=False)
                ax.set_xlim(0, 10)
                ax.set_ylim(0, 10)
                ui.update_action_button("btn_lin_opt", disabled=True)
                ui.update_action_button("btn_sens_ana", disabled=True)
                ui.update_action_button("btn_save_graph", disabled=True)
                return fig

    # Function if the linear optimization button is clicked
    @reactive.effect
    @reactive.event(input.btn_lin_opt)
    def initialize_lin_opt():


        selected_comparison_operator = [entry[5] for entry in list_reactive_selected_constraints.get()]

        status_x1_x2_value_range = check_coeff_value_ranges()

        if status_x1_x2_value_range[0] != 1 or status_x1_x2_value_range[1] != 1:
            notification_popup("Please specify only one value range each for x1 and x2.", message_type="error")

        if selected_comparison_operator.count("≥") == len(selected_comparison_operator) and \
                list_reactive_selected_obj_func.get()[0][
                    5] == "max":
            notification_popup(
                "Linear optimization not possible! The problem is unbounded. Please change the constraints or the objective function.",
                message_type="error")


        else:

            updated_solved_problems_list = []

            solution, intersection = solve_linear_programming_problem(list_reactive_selected_obj_func.get()[0],
                                                                      list_reactive_selected_constraints.get(),
                                                                      string_reactive_problem_type.get())

            solved_target_function = [list_reactive_selected_obj_func.get()[0][0],
                                      list_reactive_selected_obj_func.get()[0][1],
                                      list_reactive_selected_obj_func.get()[0][2],
                                      list_reactive_selected_obj_func.get()[0][3],
                                      list_reactive_selected_obj_func.get()[0][4], "=", solution]

            updated_solved_problems_list.append(solved_target_function)
            updated_solved_problems_list.append(intersection)
            list_reactive_solved_problem.set(updated_solved_problems_list)

            ui.update_action_button("btn_sens_ana", disabled=False)

            notification_popup("Linear optimization successfully completed.")


    # Render text
    @output
    @render.ui
    def txt_description():
        return update_txt_description()

    @reactive.event(input.selectize_constraints, input.select_obj_func, input.btn_lin_opt,
                    input.btn_sens_ana)
    def update_txt_description():
        try:
            status_x1_x2_value_range = check_coeff_value_ranges()

            if status_x1_x2_value_range[0] != 1 or status_x1_x2_value_range[1] != 1 or (
                    not list_reactive_selected_obj_func.get() and not list_reactive_selected_constraints.get()):
                return ui.HTML(
                    '<div style="text-align: center;"><b>Please select objective function and constraint(s).</b></div>')

            elif list_reactive_selected_obj_func.get() or list_reactive_selected_constraints.get():
                summarized_text_constraints = ""

                if list_reactive_solved_problem.get():
                    summarized_text_constraints += '<div style="text-align: center;"><u><b>--------Optimum solution - Information--------</b></u></div><br>'
                    summarized_text_constraints += f'The optimum solution for the objective function <p style="color: #0000FF;">{list_reactive_solved_problem.get()[0][0]} (optimized)</p> intersects the <b>x1-axis</b> at <b>{list_reactive_solved_problem.get()[1][0]}</b> and the <b>x2-axis</b> at <b>{list_reactive_solved_problem.get()[1][1]}</b> and has the optimum value <p style="color: #FF0000;">{list_reactive_solved_problem.get()[0][6]}</p><br><br>'

                if list_reactive_sens_ana_slack.get():
                    summarized_text_constraints += '<div style="text-align: center;"><u><b>--------Sensitivity analysis - Information--------</b></u></div><br>'
                    summarized_text_constraints += '<div style="text-align: center;"><u><b>---(Non-)Binding constraints and slack---</b></u></div><br>'

                    counter = 0
                    for entry in list_reactive_sens_ana_slack.get()[2]:
                        if entry == 0:
                            name = list_reactive_selected_constraints.get()[counter][0]
                            summarized_text_constraints += f'The constraint <p style="color: {dict_reactive_func_colors.get()[name]};"> {name}</p> is a <b>binding</b> constraint. It has a <b>slack of 0</b>.<br><br>'
                        elif entry != 0:
                            name = list_reactive_selected_constraints.get()[counter][0]
                            summarized_text_constraints += f'The constraint <p style="color: {dict_reactive_func_colors.get()[name]};"> {name}</p> is a <b>non-binding</b> constraint. It has a <b>slack of {entry}</b>.<br><br>'
                        counter += 1

                if list_reactive_sens_ana_shadow.get():
                    summarized_text_constraints += '<div style="text-align: center;"><u><b>---Shadow prices / Dual prices---</b></u></div><br>'

                    counter = 0
                    for entry in list_reactive_sens_ana_shadow.get():

                        max_or_min = list_reactive_selected_obj_func.get()[0][5]
                        status = None
                        if max_or_min == "max":
                            status = "increase"
                        elif max_or_min == "min":
                            status = "decrease"
                        name = list_reactive_selected_constraints.get()[counter][0]

                        if float(entry[0]) != 0:
                            if list_reactive_solved_problem.get():
                                summarized_text_constraints += (
                                    f'An {status} of the right value b (bounding constant) of the constraint <p style="color: {dict_reactive_func_colors.get()[name]};"> {name}</p> of <b>1</b> would {status} the value of the objective function by <b>{entry[0]}</b>, from <b>{list_reactive_solved_problem.get()[0][6]}</b> to <b>{list_reactive_solved_problem.get()[0][6] + float(entry[0])}</b>. This {status} is valid, '
                                    f'as long as the right value b lays between <b>{entry[1]}</b> and <b>{entry[2]}</b>.<br><br>')
                            elif not list_reactive_solved_problem.get():
                                summarized_text_constraints += (
                                    f'A {status} of the right value b (bounding constant) of the constraint <p style="color: {dict_reactive_func_colors.get()[name]};"> {name}</p> of <b>1</b> would {status} the value of the objective function by <b>{entry[0]}</b>. This {status} is valid, '
                                    f'as long as the right value b lays between <b>{entry[1]}</b> and <b>{entry[2]}</b>.<br><br>')
                        elif float(entry[0]) == 0:
                            summarized_text_constraints += (
                                f'The constraint <p style="color: {dict_reactive_func_colors.get()[name]};"> {name}</p> is non-binding. Its shadow price is <b>0</b> and therefore the change in the right-hand side of this constraint is irrelevant.<br><br>')
                        counter += 1

                if list_reactive_sens_ana_limits.get():
                    summarized_text_constraints += '<div style="text-align: center;"><u><b>---Objective function coefficient limits---</b></u></div><br>'
                    summarized_text_constraints += f'As long as the objective function coefficient of <b>x1</b> lays between <b>{list_reactive_sens_ana_limits.get()[0][0]}</b> and <b>{list_reactive_sens_ana_limits.get()[0][1]}</b> and the objective function coefficient of <b>x2</b> lays between <b>{list_reactive_sens_ana_limits.get()[1][0]}</b> and <b>{list_reactive_sens_ana_limits.get()[1][1]}</b>, the optimum solution stays at <b>x1 = {list_reactive_solved_problem.get()[1][0]}</b> and <b>x2 = {list_reactive_solved_problem.get()[1][1]}</b>.<br><br>'

                value_1 = None
                value_2 = None

                for obj_func in list_reactive_selected_obj_func.get():
                    summarized_text_constraints += '<div style="text-align: center;"><u><b>--------Dummy-Objective function - Information--------</b></u></div><br>'
                    if obj_func[1] == 0:
                        value_1 = "no point"
                    if obj_func[3] == 0:
                        value_2 = "no point"
                    if obj_func[1] != 0:
                        value_1 = dict_reactive_xlim_var.get()[obj_func[0]]
                    if obj_func[3] != 0:
                        value_2 = dict_reactive_ylim_var.get()[obj_func[0]]
                    summarized_text_constraints += f'The <p style="color: #00FF00;">(Dummy)-Objective function {obj_func[0]}</p> intersects the <b>x1-axis</b> at <b>{value_1}</b> and the <b>x2-axis</b> at <b>{value_2}</b>.<br><br>'

                counter = 0
                for constraint in list_reactive_selected_constraints.get():
                    if counter == 0:
                        summarized_text_constraints += '<div style="text-align: center;"><u><b>--------Constraint(s) - Information--------</b></u></div><br>'
                    if constraint[1] == 0:
                        value_1 = "no point"
                    if constraint[3] == 0:
                        value_2 = "no point"
                    if constraint[1] != 0:
                        value_1 = dict_reactive_xlim_var.get()[constraint[0]]
                    if constraint[3] != 0:
                        value_2 = dict_reactive_ylim_var.get()[constraint[0]]
                    summarized_text_constraints += f'The <p style="color: {dict_reactive_func_colors.get()[constraint[0]]};">constraint {constraint[0]}</p> intersects the <b>x1-axis</b> at <b>{value_1}</b> and the <b>x2-axis</b> at <b>{value_2}</b>.<br><br>'
                    counter += 1

                return ui.HTML(f'<div style="text-align: center;">{summarized_text_constraints}</div>')

        except TypeError:
            notification_popup(
                "Your problem has no feasible region in the valid range. Please change the constraints or the objective function.")
            return ui.HTML(
                '<div style="text-align: center;"><b>Please select objective function and constraint(s).</b></div>')
        except IndexError:
            return ui.HTML(
                '<div style="text-align: center;"><b>Please select objective function and constraint(s).</b></div>')

    # submit button 7
    @reactive.effect
    @reactive.event(input.submit_button_7)
    def save_graph_png():

        try:

            if input.name_graph() == "" or input.directory_path_graph() == "":
                notification_popup("Please enter a valid name and directory path.", message_type="error")
            elif input.numeric_dpi() == "" or input.numeric_dpi() <= 0 or not isinstance(input.numeric_dpi(),
                                                                                         (int, float)):
                notification_popup("Please enter a valid DPI number.", message_type="error")
            else:

                fig = reactive_plot_fig.get()
                directory = input.directory_path_graph()
                if directory[-1] != "/":
                    directory += "/"

                selected_dpi = 0

                if input.radio_graph_dpi() == "predefined_dpi":
                    selected_dpi = input.select_dpi()
                elif input.radio_graph_dpi() == "own_dpi":
                    selected_dpi = input.numeric_dpi()

                fig.savefig(directory + input.name_graph() + ".png", dpi=int(selected_dpi))

                notification_popup("Graph saved successfully")

                ui.modal_remove()

        except FileNotFoundError:
            notification_popup("Please enter a valid directory path.", message_type="error")
        except TypeError:
            notification_popup("Please check your entries.", message_type="error")

    def notification_popup(text_message, message_type="message", message_duration=4.0):
        ui.notification_show(
            text_message,
            type=message_type,
            duration=message_duration,
        )

    # submit button 8
    @reactive.effect
    @reactive.event(input.submit_button_8)
    def import_export_lp_file():
        try:

            status_x1_x2_value_range = check_coeff_value_ranges()

            if (input.radio_import_export() == "export" and input.name_export() == "") or (
                    input.radio_import_export() == "export" and input.saving_path_import_export() == "") or (
                    input.radio_import_export() == "export" and input.saving_path_import_export().endswith(
                ".lp") == True):
                notification_popup(
                    "When exporting, please enter a valid name and select a directory path.",
                    message_type="error")

            elif (input.radio_import_export() == "import" and input.saving_path_import_export() == "") or (
                    input.radio_import_export() == "import" and not input.saving_path_import_export().endswith(".lp")):
                notification_popup("Please select a valid file in .lp format.", message_type="error")
            elif (input.radio_import_export() == "export" and not list_reactive_selected_obj_func.get()) or (
                    input.radio_import_export() == "export" and not list_reactive_selected_constraints.get()):
                notification_popup("Please select an objective function and constraint(s) before exporting.",
                                   message_type="error")
            elif input.radio_import_export() == "export" and (
                    status_x1_x2_value_range[0] != 1 or status_x1_x2_value_range[1] != 1):
                notification_popup("Please select the same value range for each x1 and x2.",
                                   message_type="error")


            else:

                user_operating_system = platform.system()
                memory_path_separation_symbol = None
                if user_operating_system == "Windows" or user_operating_system.startswith(
                        "win") or user_operating_system.startswith("Win"):
                    memory_path_separation_symbol = "\\"
                elif user_operating_system == "Linux":
                    memory_path_separation_symbol = "/"
                # For Mac OS
                elif user_operating_system == "Darwin":
                    memory_path_separation_symbol = "/"

                if input.radio_import_export() == "export":
                    generate_lp_file(list_reactive_selected_obj_func.get()[0],
                                     list_reactive_selected_constraints.get(), string_reactive_problem_type.get(),
                                     memory_path=(
                                             input.saving_path_import_export() + memory_path_separation_symbol + input.name_export() + ".lp"))
                    notification_popup("File successfully exported to .lp format.")

                elif input.radio_import_export() == "import":
                    import_list = []
                    with open(input.saving_path_import_export(), "r") as file:
                        for line in file:
                            elements = line.strip().split()

                            import_list.append(elements)

                    type_of_optimization_import = None
                    x1_type = None
                    x2_type = None
                    if import_list[(len(import_list) - 1)][0] == "int" and import_list[(len(import_list) - 1)][
                        (len(import_list[(len(import_list) - 1)]) - 1)] == "x2;" and \
                            import_list[(len(import_list) - 1)][
                                (len(import_list[(len(import_list) - 1)]) - 2)] == "x1,":
                        type_of_optimization_import = "ILP"
                        x1_type = "int"
                        x2_type = "int"
                    elif import_list[(len(import_list) - 1)][0] == "int" and import_list[(len(import_list) - 1)][
                        (len(import_list[(len(import_list) - 1)]) - 1)] == "x1;":
                        type_of_optimization_import = "MILP_x1_int_x2_con"
                        x1_type = "int"
                        x2_type = "con"
                    elif import_list[(len(import_list) - 1)][0] == "int" and import_list[(len(import_list) - 1)][
                        (len(import_list[(len(import_list) - 1)]) - 1)] == "x2;" and not \
                            import_list[(len(import_list) - 1)][(
                                    len(import_list[(len(import_list) - 1)]) - 2)] == "x1,":
                        type_of_optimization_import = "MILP_x1_con_x2_int"
                        x1_type = "con"
                        x2_type = "int"
                    elif import_list[(len(import_list) - 1)][1] == "=" or import_list[(len(import_list) - 1)][
                        1] == "<=" or \
                            import_list[(len(import_list) - 1)][1] == ">=":
                        type_of_optimization_import = "LP"
                        x1_type = "con"
                        x2_type = "con"

                    imported_obj_func = []
                    imported_constraints = []
                    counter = 1
                    for element in import_list:
                        if element[0] == "max:" or element[0] == "min:":

                            imported_obj_func = ["Function", float(element[1]), x1_type, float(element[4]), x2_type,
                                                 element[0][0:3]]
                        elif element[0] not in ["max:", "min:", "x1", "x2", "int"]:
                            operator = None

                            if element[5] == "<=":
                                operator = "≤"
                            elif element[5] == ">=":
                                operator = "≥"
                            elif element[5] == "=":
                                operator = "="

                            imported_constraint = ["Constraint_" + str(counter), float(element[0]), x1_type,
                                                   float(element[3]), x2_type, operator, float(element[6][:-1])]
                            imported_constraints.append(imported_constraint)

                            counter += 1

                    list_reactive_obj_func.set([imported_obj_func])
                    list_reactive_constraints.set(imported_constraints)

                    dict_reactive_obj_func.set({})
                    copy_dict_obj_func = dict_reactive_obj_func.get().copy()
                    for obj_func in list_reactive_obj_func.get():
                        copy_dict_obj_func[obj_func[0]] = obj_func[0]
                    dict_reactive_obj_func.set(copy_dict_obj_func)

                    all_names_constraints = []
                    dict_reactive_constraints.set({})
                    copy_dict_reactive_constraints = dict_reactive_constraints.get().copy()
                    for constraint in list_reactive_constraints.get():
                        copy_dict_reactive_constraints[constraint[0]] = constraint[0]
                        all_names_constraints.append(constraint[0])
                    dict_reactive_constraints.set(copy_dict_reactive_constraints)

                    list_reactive_selected_obj_func.set([imported_obj_func])
                    list_reactive_selected_constraints.set(imported_constraints)
                    string_reactive_problem_type.set(type_of_optimization_import)

                    bool_reactive_import_statement.set(True)

                    ui.update_action_button("btn_change_obj_func", disabled=False)
                    ui.update_action_button("btn_delete_obj_func", disabled=False)
                    ui.update_action_button("btn_change_constraint", disabled=False)
                    ui.update_action_button("btn_delete_constraint", disabled=False)
                    ui.update_action_button("btn_lin_opt", disabled=False)
                    ui.update_selectize("selectize_constraints", choices=dict_reactive_constraints.get(),
                                        selected=all_names_constraints)
                    ui.update_select("select_obj_func", choices=dict_reactive_obj_func.get())
                    ui.update_action_button("btn_sens_ana", disabled=True)

                    notification_popup("Data imported successfully.")

                ui.modal_remove()
        except FileNotFoundError:
            if input.radio_import_export() == "export":
                notification_popup("Please enter a valid directory path.", message_type="error")
            else:
                notification_popup("Please select a valid file.", message_type="error")
        except IndexError:
            notification_popup("Please select at least one objective function before exporting.", message_type="error")
        except ValueError:
            notification_popup("Please check your file for correct content before importing.",
                               message_type="error")

# Function if the sensitivity analysis button is clicked
@reactive.effect
@reactive.event(input.btn_sens_ana)
def sensitivity_analysis():
    try:
        # Base path relative to server.py
        base_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Detect current operating system
        current_os = sys.platform

        if current_os.startswith("linux"):
            # On Render/Linux, use the lp_solve installed inside the Docker image via apt-get.
            executable_lp = shutil.which("lp_solve")

            if executable_lp is None:
                notification_popup(
                    "lp_solve was not found on the Linux server. Please check the Dockerfile installation.",
                    message_type="error",
                    message_duration=8.0,
                )
                return

        elif current_os == "darwin":
            executable_lp = os.path.join(
                base_directory,
                "lp_solve_5.5",
                "lp_solve",
                "bin",
                "mac",
                "lp_solve",
            )

        elif current_os.startswith("win"):
            executable_lp = os.path.join(
                base_directory,
                "lp_solve_5.5",
                "lp_solve",
                "bin",
                "windows64",
                "lp_solve.exe",
            )

        else:
            notification_popup(
                f"Unsupported operating system: {current_os}",
                message_type="error",
                message_duration=8.0,
            )
            return

        # Important for multiple users:
        # Use a temporary file instead of always writing to shiny_files/lp_file.lp.
        with tempfile.TemporaryDirectory() as tmpdir:
            lp_problem_saving_path = os.path.join(tmpdir, "lp_file.lp")

            generate_lp_file(
                list_reactive_selected_obj_func.get()[0],
                list_reactive_selected_constraints.get(),
                string_reactive_problem_type.get(),
                lp_problem_saving_path,
            )

            lp_solve_output = solve_sensitivity_analysis(
                executable_lp,
                lp_problem_saving_path,
                "-S5",
            )

        sens_ana_binding_slack = binding_constraints_and_slack(lp_solve_output.stdout)
        list_reactive_sens_ana_slack.set(sens_ana_binding_slack)

        sens_ana_shadow_price = shadow_price(lp_solve_output.stdout)
        list_reactive_sens_ana_shadow.set(sens_ana_shadow_price)

        sens_ana_coeff_limits = coeff_limits(lp_solve_output.stdout)
        list_reactive_sens_ana_limits.set(sens_ana_coeff_limits)

        notification_popup("Sensitivity analysis completed successfully.")

    except Exception as e:
        notification_popup(
            f"Sensitivity analysis failed: {e}",
            message_type="error",
            message_duration=10.0,
        )
        raise


    # Render data frame
    @output
    @render.data_frame
    def df_sens_ana_slack():
        return update_df_sens_ana_slack()

    @reactive.Calc
    def update_df_sens_ana_slack():

        try:
            if not list_reactive_sens_ana_slack.get():
                sens_result_df_1 = pd.DataFrame({
                    "Name": [""],
                    "Right border": [""],
                    "Actual value": [""],
                    "Slack": [""],
                    "Characteristic": [""],
                })

                return render.DataGrid(sens_result_df_1)

            if list_reactive_sens_ana_slack.get():

                names = []
                for function in list_reactive_selected_constraints.get():
                    names.append(function[0])

                sens_result_df_1 = pd.DataFrame({
                    "Name": names,
                    "Right border": list_reactive_sens_ana_slack.get()[0],
                    "Actual value": list_reactive_sens_ana_slack.get()[1],
                    "Slack": list_reactive_sens_ana_slack.get()[2],
                    "Characteristic": list_reactive_sens_ana_slack.get()[3],
                })

                return render.DataGrid(sens_result_df_1)
        except ValueError:
            sens_result_df_1 = pd.DataFrame({
                "Name": [""],
                "Right border": [""],
                "Actual value": [""],
                "Slack": [""],
                "Characteristic": [""],
            })

            return render.DataGrid(sens_result_df_1)

    # Render data frame
    @output
    @render.data_frame
    def df_sens_ana_shadow():
        return update_df_sens_ana_shadow()

    @reactive.Calc
    def update_df_sens_ana_shadow():

        try:
            if not list_reactive_sens_ana_shadow.get():
                sens_result_df_2 = pd.DataFrame({
                    "Name": [""],
                    "Shadow price": [""],
                    "From (lower border)": [""],
                    "Till (upper border)": [""]
                })

                return render.DataGrid(sens_result_df_2)

            if list_reactive_sens_ana_shadow.get():

                names = []
                for function in list_reactive_selected_constraints.get():
                    names.append(function[0])

                sens_result_df_2 = pd.DataFrame({
                    "Name": names,
                    "Shadow price": [entry[0] for entry in list_reactive_sens_ana_shadow.get()],
                    "From (lower border)": [entry[1] for entry in list_reactive_sens_ana_shadow.get()],
                    "Till (upper border)": [entry[2] for entry in list_reactive_sens_ana_shadow.get()]
                })

                return render.DataGrid(sens_result_df_2)
        except ValueError:
            sens_result_df_2 = pd.DataFrame({
                "Name": [""],
                "Shadow price": [""],
                "From (lower border)": [""],
                "Till (upper border)": [""]
            })

            return render.DataGrid(sens_result_df_2)

    # Render data frame
    @output
    @render.data_frame
    def df_sens_ana_limits():
        return update_df_sens_ana_limits()

    @reactive.Calc
    def update_df_sens_ana_limits():

        try:
            if not list_reactive_sens_ana_limits.get():
                sens_result_df_3 = pd.DataFrame({
                    "Variable": ["x1", "x2"],
                    "From": ["", ""],
                    "Till": ["", ""],
                    "FromValue": ["", ""]
                })

                return render.DataGrid(sens_result_df_3)

            if list_reactive_sens_ana_limits.get():
                sens_result_df_3 = pd.DataFrame({
                    "Variable": ["x1", "x2"],
                    "From": [entry[0] for entry in list_reactive_sens_ana_limits.get()],
                    "Till": [entry[1] for entry in list_reactive_sens_ana_limits.get()],
                    "FromValue": [entry[2] for entry in list_reactive_sens_ana_limits.get()]
                })

                return render.DataGrid(sens_result_df_3)

        except ValueError:
            sens_result_df_3 = pd.DataFrame({
                "Variable": ["x1", "x2"],
                "From": ["", ""],
                "Till": ["", ""],
                "FromValue": ["", ""]
            })

            return render.DataGrid(sens_result_df_3)

    # Function if the reset button is clicked
    @reactive.effect
    @reactive.event(input.btn_reset)
    def reset_all():

        dict_reactive_obj_func.set({})
        dict_reactive_constraints.set({})
        list_reactive_obj_func.set([])
        list_reactive_constraints.set([])
        list_reactive_selected_constraints.set([])
        list_reactive_selected_obj_func.set([])
        list_reactive_solved_problem.set([])
        list_reactive_xlim_var.set([])
        list_reactive_ylim_var.set([])
        dict_reactive_xlim_var.set({})
        dict_reactive_ylim_var.set({})
        dict_reactive_func_colors.set({})
        string_reactive_problem_type.set("")
        reactive_plot_fig.set(None)
        list_reactive_y_values_equal_problem.set([])
        bool_reactive_import_statement.set(False)
        list_reactive_sens_ana_slack.set([])
        list_reactive_sens_ana_shadow.set([])
        list_reactive_sens_ana_limits.set([])

        ui.update_action_button("btn_change_obj_func", disabled=True)
        ui.update_action_button("btn_delete_obj_func", disabled=True)
        ui.update_action_button("btn_change_constraint", disabled=True)
        ui.update_action_button("btn_delete_constraint", disabled=True)
        ui.update_action_button("btn_lin_opt", disabled=True)
        ui.update_action_button("btn_sens_ana", disabled=True)
        ui.update_action_button("set_x1_x2_value_range", disabled=True)
        ui.update_selectize("selectize_constraints", choices={},
                            selected=[])
        ui.update_select("select_obj_func", choices={})

        notification_popup("All data has been reset", message_type="warning")

    # Modal9 for changing the value range of x1 and x2 for all
    @reactive.effect
    @reactive.event(input.set_x1_x2_value_range)
    def modal9():
        values_1 = {"LP": "con", "ILP": "int", "MILP_x1_int_x2_con": "int", "MILP_x1_con_x2_int": "con"}
        values_2 = {"LP": "con", "ILP": "int", "MILP_x1_int_x2_con": "con", "MILP_x1_con_x2_int": "int"}
        m9 = ui.modal(
            ui.row(
                ui.column(4, ui.HTML("<b>Value range x1</b>")),
                ui.column(3, ui.HTML(
                    f'current:<b>{values_1.get(string_reactive_problem_type.get(), "not consistent or nothing selected")}</b>')),
                ui.column(2, ui.HTML("choose:")),
                ui.column(3, ui.input_select(
                    "select_x1_value_range_for_all",
                    None,
                    choices={"con": "con", "int": "int"}),
                          ),
            ),
            ui.HTML("<br><br>"),
            ui.row(
                ui.column(4, ui.HTML("<b>Value range x2</b>")),
                ui.column(3, ui.HTML(
                    f'current:<b>{values_2.get(string_reactive_problem_type.get(), "not consistent or nothing selected")}</b>')),
                ui.column(2, ui.HTML("choose:")),
                ui.column(3, ui.input_select(
                    "select_x2_value_range_for_all",
                    None,
                    choices={"con": "con", "int": "int"}),
                          ),
            ),

            footer=ui.div(
                ui.input_action_button(id="cancel_button_9", label="Cancel"),
                ui.input_action_button(id="submit_button_9", label="Submit"),
            ),
            title="Set the value range for all x1 and x2 at once",
            easy_close=False,
            style="width: 100%;"
        )
        ui.modal_show(m9)

    # Submit button 9
    @reactive.effect
    @reactive.event(input.submit_button_9)
    def set_x1_and_x2_all():

        x1_value_range = input.select_x1_value_range_for_all()
        x2_value_range = input.select_x2_value_range_for_all()

        copy_list_reactive_obj_func = list_reactive_obj_func.get().copy()
        copy_list_reactive_constraints = list_reactive_constraints.get().copy()

        for obj_func in copy_list_reactive_obj_func:
            obj_func[2] = x1_value_range
            obj_func[4] = x2_value_range
        list_reactive_obj_func.set(copy_list_reactive_obj_func)

        list_reactive_selected_obj_func.set([])

        for constraint in copy_list_reactive_constraints:
            constraint[2] = x1_value_range
            constraint[4] = x2_value_range
        list_reactive_constraints.set(copy_list_reactive_constraints)

        list_reactive_selected_constraints.set([])

        ui.update_selectize("selectize_constraints", choices=dict_reactive_constraints.get(),
                            selected=[])
        ui.update_select("select_obj_func", choices=dict_reactive_obj_func.get(), selected=[])

        notification_popup("Value range for x1 and / or x2 changed successfully.")

        ui.modal_remove()

    # Activates and deactivates the button for setting the value range for x1 and x2
    @reactive.effect
    @reactive.Calc
    def set_value_range_listener():
        if list_reactive_obj_func.get() and list_reactive_constraints.get():
            ui.update_action_button("set_x1_x2_value_range", disabled=False)
        else:
            ui.update_action_button("set_x1_x2_value_range", disabled=True)

    # Check that each type of coefficient has the same range of value.
    def check_coeff_value_ranges():

        type_all_a1_constraints = None
        type_all_c1_obj_func = None
        type_all_a2_constraints = None
        type_all_c2_obj_func = None

        if list_reactive_selected_obj_func.get():
            selected_obj_func = None
            for entry in list_reactive_obj_func.get():
                if entry[0] == input.select_obj_func():
                    selected_obj_func = entry
            type_all_c1_obj_func = selected_obj_func[2]
            type_all_c2_obj_func = selected_obj_func[4]

        if list_reactive_selected_constraints.get():
            selected_constraints = []
            for entry in list_reactive_constraints.get():
                if entry[0] in input.selectize_constraints():
                    selected_constraints.append(entry)

            type_all_a1_constraints = [entry[2] for entry in selected_constraints]
            type_all_a2_constraints = [entry[4] for entry in selected_constraints]

        if not list_reactive_selected_obj_func.get():
            return [2, 2, "unselected_obj_func"]
        if not list_reactive_selected_constraints.get():
            return [2, 2, "unselected_constraints"]

        else:
            type_all_coeff1 = type_all_a1_constraints + [type_all_c1_obj_func]
            type_all_coeff2 = type_all_a2_constraints + [type_all_c2_obj_func]

            return [len(set(type_all_coeff1)), len(set(type_all_coeff2)), "all_selected"]

    @reactive.effect
    @reactive.event(input.btn_about)
    def about_button():
        string_reactive_selected_guide_step.set("about")

    @reactive.effect
    @reactive.event(input.btn_about_lp)
    def about_lp_button():
        string_reactive_selected_guide_step.set("about_lp")

    @reactive.effect
    @reactive.event(input.btn_about_sens_ana)
    def about_sens_ana_button():
        string_reactive_selected_guide_step.set("about_sens_ana")

    @reactive.effect
    @reactive.event(input.btn_step_1)
    def step_1_button():
        string_reactive_selected_guide_step.set("step_1")

    @reactive.effect
    @reactive.event(input.btn_step_2)
    def step_2_button():
        string_reactive_selected_guide_step.set("step_2")

    @reactive.effect
    @reactive.event(input.btn_step_3)
    def step_3_button():
        string_reactive_selected_guide_step.set("step_3")

    @reactive.effect
    @reactive.event(input.btn_step_4)
    def step_4_button():
        string_reactive_selected_guide_step.set("step_4")

    @reactive.effect
    @reactive.event(input.btn_step_5)
    def step_5_button():
        string_reactive_selected_guide_step.set("step_5")

    @reactive.effect
    @reactive.event(input.btn_step_6)
    def step_6_button():
        string_reactive_selected_guide_step.set("step_6")

    @reactive.effect
    @reactive.event(input.btn_step_7)
    def step_6_button():
        string_reactive_selected_guide_step.set("step_7")

    @reactive.effect
    @reactive.event(input.btn_example)
    def example_button():
        string_reactive_selected_guide_step.set("example")

    # Render text
    @output
    @render.ui
    def txt_how_to_use():
        return update_txt_how_to_use_btn_about()

    @reactive.Calc
    def update_txt_how_to_use_btn_about():

        if string_reactive_selected_guide_step.get() == "about" or string_reactive_selected_guide_step.get() == "":
            return ui.HTML(
                '<div style="text-align: center;"><b>About OptiSense</b></div><br><br>'
                '<div style="text-align: center;">'
                'Welcome to OptiSense! OptiSense is designed to help you with linear programming (LP), integer linear programming (ILP) and mixed-integer linear programming (MILP) tasks, including sensitivity analysis.'
                'This app was designed as part of the bachelor thesis on "Shiny in Python: Eine Anwendung zur interaktiven Visualisierung, Lösung und Untersuchung der Sensitivität einfacher LP- und (M)ILP-Probleme mit scipy.optimize.milp und lp solve“.<br>'
                'The app is intended to help you understand the topic of linear programming and some of the starting points of sensitivity analysis. It serves as a teaching tool.'
                '<br><br>'
                '<div style="text-align: center;">The app was designed and developed by Peter Oliver Ruhland.</div>'
                '<br><br>'
                'The code of the individual Python libraries required, such as shiny, matplotlib, pandas, os, sys, random, platform, math, scipy, numpy, subprocess and re, are not my brainchild.'
                '<br><br>'
                'The open source solver ‘lp_solve’ is also not my brainchild. It was originally developed by Michel Berkelaar at Eindhoven University of Technology and by other developers such as Jeroen Dirks and Kjell Eikland and Peter Notebaert as well as Juergen Ebert. See <a href="https://lpsolve.sourceforge.net/5.5/">sourceforge</a> for more information.'
                '</div>'
            )

        elif string_reactive_selected_guide_step.get() == "about_lp":
            return ui.HTML(
                '<div style="text-align: center;"><b>About OptiSense - About Linear Programming</b></div><br><br>'
                '<div style="text-align: center;">'
                'Linear Programming (LP), also known as linear optimization, is a mathematical method for finding the best possible outcome '
                '(e.g. maximum profit or minimum cost) for a problem described by a linear objective function and a set of linear constraints.'
                'The goal is to maximize or minimize the objective function while satisfying the constraints.'
                '<br><br>'
                'Structure of the objective function (generally): c1*x1 + c2*x2 + ... + cn*xn'
                '<br><br>'
                'Due to the fact that this app is limited to simple problems, the number of variables is limited to two variables: x1 and x2.'
                '<br><br>'
                'Structure of the objective function for simple problems: Z = c1*x1 + c2*x2'
                '<br><br>'
                'Structure of the constraints (generally): a11*x1 + a12*x2 + ... + a1n*xn <= b1'
                '<br><br>'
                'Structure of a constraint for simple problems: a1*x1 + a2*x2 <= b<br>'
                '<br><br>'
                'Main components of LP'
                '<br><br>'
                'Decision Variables: Represent the quantities you want to determine. For example, the number of chairs (x1) and tables (x2).'
                '<br><br>'
                'Non-negativity is required: x1 ≥ 0 ; x2 ≥ 0'
                '<br><br>'
                'In LP, the decision variables are continuous. For example, the number of chairs and tables can be any real number.'
                '<br><br>'
                '<br><br>'
                'Integer Linear Programming (ILP)'
                '<br><br>'
                'In ILP, the decision variables are integers. For example, the number of chairs and tables must be whole numbers.'
                '<br><br>'
                '<br><br>'
                'Mixed-Integer Linear Programming (MILP)'
                '<br><br>'
                'In MILP, some variables must be integers, while others can be continuous (real numbers). For example all x1 must be integers, while x2 can be any real (continous) number.'
                '</div>'

            )

        elif string_reactive_selected_guide_step.get() == "about_sens_ana":
            return ui.HTML(
                '<div style="text-align: center;"><b>About OptiSense - About sensitivity analysis</b></div><br><br>'
                '<div style="text-align: center;">'
                'Before solving or analyzing your optimization problem, you need to define an objective function and at least one constraint.'
                'Sensitivity analysis in linear programming (LP) examines how changes in the problem’s parameters—such as objective function coefficients or constraint limits—affect the optimal solution.'
                '<br><br>'
                'In OptiSense, sensitivity analysis provides insights into three key aspects:<br>'
                'Exploitation of constraints with slack; Shadow prices / Dual prices; Objective function coefficient limits.'
                '<br><br>'
                '<br><br>'
                'Exploitation of Constraints with Slack'
                '<br><br>'
                'Slack refers to the unused capacity in a constraint. In LP, constraints are mathematical expressions that limit the feasible region where the optimum solution must lie.<br>'
                'Slack tells us how much of a resource is left over after reaching the optimum solution.<br>'
                'Binding Constraints: A constraint is binding if all available resources are fully used (slack = 0). This means the constraint directly influences the optimal solution.<br>'
                'Non-Binding Constraints: A constraint is non-binding if there is leftover capacity (slack > 0). This means the constraint is not actively restricting the solution.'
                '<br><br>'
                '<br><br>'
                'Shadow prices (Dual prices)'
                '<br><br>'
                'A shadow price represents the change in the objective function’s value (e.g., profit or cost) for a 1-unit increase in a constraint’s right-hand side value (b), assuming all other parameters remain constant.<br>'
                'For binding constraints (slack = 0), shadow prices tell us how valuable an additional unit of the resource would be.<br>'
                'For non-binding constraints (slack > 0), the shadow price is 0 because the resource is not fully utilized.'
                '<br><br>'
                '<br><br>'
                'Objective function coefficient limits'
                '<br><br>'
                'These limits define the range within which the coefficients of the objective function (e.g., profit per unit of a product) can change without altering the optimal solution.'
                '</div>'
            )

        elif string_reactive_selected_guide_step.get() == "example":
            return ui.HTML(
                '<div style="text-align: center;"><b>About OptiSense - Example</b></div><br><br>'
                '<div style="text-align: center;">'
                'Foreword: From now on, the explanation will be based on a simple example. The example is taken from the book ‘Einführung in Operations Research’ by Wolfgang Domschke et al. from the 9th edition year 2015.'
                '<br><br>'
                '<br><br>'
                'Example from the book:'
                '<br><br>'
                'A company can produce two products, P1 and P2, during a planning period, based on its available personnel, equipment, and raw materials. The feasible production quantities (units) of the products are limited by three input factors:<br>'
                'A machine that is used jointly for the production of all products. Only periodic depreciation costs are incurred for the machine, meaning that its use for production does not cause any direct costs.<br>'
                'A perishable raw material, of which 720 units are in stock. Any remaining amount at the end of the period cannot be used further.<br>'
                'Limited assembly capacity for P2.'
                '<br><br>'
                'The available capacity units (CU) per period and the resource requirements per produced unit (production coefficients), as well as the contribution margins dbj, are provided in the following table:'
                '<br><br>'
                '<img src="/table_domschke_bsp.png" style="width: 100%; max-width: 600px;">'
                '(Domschke et al., 2015)'
                '<br><br>'
                'This gives us the following model:'
                '<br><br>'
                '<img src="/problem_domschke.png" style="width: 100%; max-width: 600px;">'
                '(Domschke et al., 2015)'
                '<br><br>'
                '<br><br>'
                'Objective function: (max) F = 10 * x1 + 20 * x2'
                '<br><br>'
                'Constraint 1: 1 * x1 + 1 * x2 ≤ 100<br>'
                'Constraint 2: 6 * x1 + 9 * x2 ≤ 720<br>'
                'Constraint 3: 0 * x1 + 1 * x2 ≤ 60'
                '<br><br>'
                'x1 ≥ 0 ; x2 ≥ 0<br>'
                '(x1 = continuous and x2 = continuous)'
                '</div>'

            )

        elif string_reactive_selected_guide_step.get() == "step_1":
            return ui.HTML(
                '<div style="text-align: center;"><b>About OptiSense - Step 1: Set up</b></div><br><br>'
                '<div style="text-align: center;">'
                'The first step in solving any LP problem is defining your objective function and constraints. In OptiSense, this is done in the User Inputs section on the left sidebar.'
                '<br><br>'
                '<img src="/enter_obj_func_btn.png" style="width: 100%; max-width: 600px;"><br>'
                '<img src="/enter_obj_func_modal.png" style="width: 100%; max-width: 600px;">'
                '<br><br>'
                '<img src="/enter_constraint_btn.png" style="width: 100%; max-width: 600px;"><br>'
                '<img src="/enter_constraint_modal.png" style="width: 100%; max-width: 600px;">'
                '<br><br>'
                'All input data is presented in these panel for an overview:'
                '<br><br>'
                '<img src="/overview_data.png" style="width: 100%; max-width: 600px;">'
                '<br><br>'
                'Incorrectly entered data can be changed or deleted using the corresponding buttons.'
                '</div>'

            )



        elif string_reactive_selected_guide_step.get() == "step_2":
            return ui.HTML(
                '<div style="text-align: center;"><b>About OptiSense - Step 2: Select functions</b></div><br><br>'
                '<div style="text-align: center;">'
                'Once you’ve defined your functions and constraints, you can select which ones to use in your calculations.'
                '<br><br>'
                'Go to the "Selecting the functions" panel.<br>'
                'Choose the objective function from the dropdown menu.<br>'
                'Select one or more constraints using the multi-select field'
                '<br><br>'
                '<img src="/choosing_functions.png" style="width: 100%; max-width: 600px;">'
                '<br><br>'
                'If an objective function and at least one constraint have been selected, OptiSense calculates the corresponding graph.'
                '<br><br>'
                '<img src="graph_without_solution.png" style="width: 100%; max-width: 600px;">'
                '</div>'

            )

        elif string_reactive_selected_guide_step.get() == "step_3":
            return ui.HTML(
                '<div style="text-align: center;"><b>About OptiSense - Step 3: Solving with linear optimization</b></div><br><br>'
                '<div style="text-align: center;">'
                'Now that your problem is set up, you can find the optimal solution.'
                '<br><br>'
                'Click the "Linear optimization" button in the "Main functions" section and OptiSense will solve the problem using scipy.optimize.milp and scipy.optimize.LinearConstraint.'
                '<br><br>'
                'If the problem is solvable, the graph will be updated with the optimal solution.'
                '<br><br>'
                '<img src="/graph_with_solution.png" style="width: 100%; max-width: 600px;">'
                '<br><br>'
                'The results can also be seen in the table below the graph.'
                '<br><br>'
                '<img src="optimum_solution.png" style="width: 100%; max-width: 600px;">'
                '</div>'

            )

        elif string_reactive_selected_guide_step.get() == "step_4":
            return ui.HTML(
                '<div style="text-align: center;"><b>About OptiSense - Step 4: Sensitivity analysis</b></div><br><br>'
                '<div style="text-align: center;">'
                'Once OptiSense has performed the linear optimization, the sensitivity analysis can be started using the corresponding button.'
                '<br><br>'
                '<img src="sens_ana_button.png" style="width: 100%; max-width: 600px;">'
                '<br><br>'
                'The results of the sensitivity analysis are displayed in the tables below the graph.'
                '<br><br>'
                '<img src="sens_ana_1.png" style="width: 100%; max-width: 600px;">'
                '<img src="sens_ana_2.png" style="width: 100%; max-width: 600px;">'
                '</div>'

            )

        elif string_reactive_selected_guide_step.get() == "step_5":
            return ui.HTML(
                '<div style="text-align: center;"><b>About OptiSense - Step 5: Save graph as PNG</b></div><br><br>'
                '<div style="text-align: center;">'
                'The graph can be saved as a PNG file using the "Save graph as PNG" button.'
                '<br><br>'
                '<img src="save_graph.png" style="width: 100%; max-width: 600px;">'
                '<br><br>'
                'A window opens in which the DPI (Dots Per Inch) number can be set.'
                '<br><br>'
                '<img src="save_modal.png" style="width: 100%; max-width: 600px;">'
                '<br><br>'
                'IMPORTANT: Copy a valid file path for saving into the provided field.'
                '<br><br>'
                'Example for Mac OS:'
                '<br><br>'
                '<img src="mac_save_1.png" style="width: 100%; max-width: 600px;">'
                '<img src="mac_save_2.png" style="width: 100%; max-width: 600px;">'
                '<br><br>'
                'Example for Windows:'
                '<br><br>'
                '<img src="win_save_1.png" style="width: 100%; max-width: 600px;">'
                '<img src="win_save_2.png" style="width: 100%; max-width: 600px;">'
                '</div>'

            )

        elif string_reactive_selected_guide_step.get() == "step_6":
            return ui.HTML(
                '<div style="text-align: center;"><b>About OptiSense - Step 6: Import or Export</b></div><br><br>'
                '<div style="text-align: center;">'
                'OptiSense supports importing and exporting LP problems in the LP format.'
                '<br><br>'
                'Click the "Import & export" button in the Extras section.'
                '<br><br>'
                '<img src="import_export.png" style="width: 100%; max-width: 600px;">'
                '<br><br>'
                'A window opens in which can be choosen whether to import or to export.'
                '<br><br>'
                '<img src="im_ex_modal.png" style="width: 100%; max-width: 600px;">'
                '<br><br>'
                'IMPORTANT: Copy a valid file path. For this procedure, see Step 5.'
                '<br><br>'
                'IMPORTANT: The file path must contain the file name and the file extension.'
                '<br><br>'
                '<img src="lp_import.png" style="width: 100%; max-width: 1000px;">'
                '</div>'

            )

        elif string_reactive_selected_guide_step.get() == "step_7":
            return ui.HTML(
                '<div style="text-align: center;"><b>About OptiSense - Step 7: Reset and adjust</b></div><br><br>'
                '<div style="text-align: center;">'
                'Use the "Reset all" button to clear OptiSense and start fresh.'
                '<br><br>'
                '<img src="reset.png" style="width: 100%; max-width: 600px;">'
                '<br><br>'
                '<br><br>'
                'If the value ranges of all x1 and x2 values need to be changed quickly, this can be done using the "Set value range for x1 and x2" button.'
                '<br><br>'
                '<img src="set_value_btn.png" style="width: 100%; max-width: 600px;">'
                '<br><br>'
                '<img src="set_value_modal.png" style="width: 100%; max-width: 600px;">'
                '</div>'

            )
