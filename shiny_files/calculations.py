from scipy.optimize import milp, LinearConstraint
import numpy as np
import subprocess
import re


def solve_linear_programming_problem(objective_function, constraints, type_of_problem):
    if type_of_problem == "LP" or type_of_problem == "ILP" or type_of_problem == "MILP_x1_int_x2_con" or type_of_problem == "MILP_x1_con_x2_int":
        upper_borders_list = []
        lower_borders_list = []

        obj_coeff_1 = objective_function[1]
        obj_coeff_2 = objective_function[3]
        if objective_function[5] == "max":
            obj_coeff_1 = obj_coeff_1 * (-1)
            obj_coeff_2 = obj_coeff_2 * (-1)

        constraints_coeff_list = []
        for constraint in constraints:
            constraints_coeff_list.append([constraint[1], constraint[3]])

            upper_borders_list.append(constraint[6])
            if constraint[5] == "≤":
                lower_borders_list.append(-np.inf)
            elif constraint[5] == "=":
                lower_borders_list.append(constraint[6])
            elif constraint[5] == "≥":
                lower_borders_list.append(constraint[6])
                upper_borders_list[(len(upper_borders_list) - 1)] = np.inf

        objective_function_coefficients = np.array([obj_coeff_1, obj_coeff_2])
        constraints_coefficients = np.array(constraints_coeff_list)
        all_functions_upper_border = np.array(upper_borders_list)
        all_functions_lower_border = np.array(lower_borders_list)
        problem_constraints = LinearConstraint(constraints_coefficients, all_functions_lower_border,
                                               all_functions_upper_border)

        if type_of_problem == "LP":
            problem_result = milp(objective_function_coefficients, constraints=problem_constraints)
        elif type_of_problem == "ILP":
            problem_result = milp(objective_function_coefficients, constraints=problem_constraints, integrality=[1, 1])
        elif type_of_problem == "MILP_x1_int_x2_con":
            problem_result = milp(objective_function_coefficients, constraints=problem_constraints, integrality=[1, 0])
        elif type_of_problem == "MILP_x1_con_x2_int":
            problem_result = milp(objective_function_coefficients, constraints=problem_constraints, integrality=[0, 1])

        if objective_function[5] == "max":
            return [-problem_result.fun, problem_result.x]
        elif objective_function[5] == "min":
            return [problem_result.fun, problem_result.x]

    elif type_of_problem == "not defined":
        return "No problem type defined"


def solve_sensitivity_analysis(lp_solve_path, saved_lp_problem_path, parameter=None):
    result = subprocess.run(
        [lp_solve_path, parameter, saved_lp_problem_path],
        capture_output=True,
        text=True,
        timeout=30
    )
    return result

def binding_constraints_and_slack(solved_lp_problem):
    lines_list = solved_lp_problem.splitlines()

    constraint_b_list = []
    for entry in lines_list:
        if entry.startswith("R"):
            # Search for the number at the end of the line
            match = re.search(r"(\d+(\.\d+)?)\s*$", entry)
            # Add the found result (the numerical value) to the list
            constraint_b_list.append(float(match.group(1)) if '.' in match.group(1) else int(match.group(1)))
        elif entry.startswith("Type"):
            break

    actual_values_constraints = []
    note = False
    for entry in lines_list:
        if entry.startswith("Actual values of the constraints"):
            note = True
        if note:
            if entry.startswith("R"):
                match = re.search(r"(\d+(\.\d+)?)\s*$", entry)
                actual_values_constraints.append(
                    float(match.group(1)) if '.' in match.group(1) else int(match.group(1)))
        if entry.startswith("Objective function limits"):
            break

    slack = []
    constraint_characteristic = []
    for counter in range(0, len(actual_values_constraints)):
        slack.append(abs(constraint_b_list[counter] - actual_values_constraints[counter]))
        if (constraint_b_list[counter] - actual_values_constraints[counter]) == 0:
            constraint_characteristic.append("binding")
        else:
            constraint_characteristic.append("non-binding")

    return [constraint_b_list, actual_values_constraints, slack, constraint_characteristic]


def shadow_price(solved_lp_problem):
    lines_list = solved_lp_problem.splitlines()

    sha_price = []
    note = False
    for entry in lines_list:
        if entry.startswith("Dual values with from"):
            note = True
        if note:
            entry_without_space = entry.strip().split()
            if entry_without_space[0].startswith("R"):
                sha_price.append([entry_without_space[1], entry_without_space[2], entry_without_space[3]])
            if entry_without_space[0].startswith("x"):
                break

    return sha_price


def coeff_limits(solved_lp_problem):
    lines_list = solved_lp_problem.splitlines()

    objective_func_limits = []
    note = False
    for entry in lines_list:

        if entry.startswith("Objective function limits"):
            note = True
        if note:

            entry_without_space = entry.strip().split()

            if len(entry_without_space) != 0 and entry_without_space[0].startswith("x"):
                objective_func_limits.append(
                    [entry_without_space[1], entry_without_space[2], entry_without_space[3]])
            if len(entry_without_space) == 0 or entry_without_space[0].startswith("Dual values with from"):
                break

    return objective_func_limits
