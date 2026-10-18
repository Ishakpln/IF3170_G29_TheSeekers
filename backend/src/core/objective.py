def evaluate_obj_func(problem, state):
    return sum(
        problem.get_package(placement.package_id).value
        for placement in state.get_inside_placements()
    )


def evaluate_obj_func2(problem, state):
    return evaluate_obj_func(problem, state)


def evaluate_obj_func3(problem, state):
    return evaluate_obj_func(problem, state)


def evaluate_obj_func4(problem, state):
    return evaluate_obj_func(problem, state)


def evaluate_obj_func5(problem, state):
    return evaluate_obj_func(problem, state)


def get_objective_function(objective_number):
    objective_functions = {
        1: evaluate_obj_func,
        2: evaluate_obj_func2,
        3: evaluate_obj_func3,
        4: evaluate_obj_func4,
        5: evaluate_obj_func5,
    }

    if objective_number not in objective_functions:
        raise ValueError("objective number is not available")

    return objective_functions[objective_number]


def evaluate_state(problem, state, objective_number=1):
    objective_function = get_objective_function(objective_number)
    return objective_function(problem, state)
