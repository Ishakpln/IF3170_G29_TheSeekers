def evaluate_obj_func(state):
    return sum(
        package.value
        for package in state.get_inside_packages()
    )


def evaluate_obj_func2(state):
    return sum(
        package.value
        for package in state.get_inside_packages()
    )


def evaluate_obj_func3(state):
    return sum(
        package.value
        for package in state.get_inside_packages()
    )


def evaluate_obj_func4(state):
    return sum(
        package.value
        for package in state.get_inside_packages()
    )


def evaluate_obj_func5(state):
    return sum(
        package.value
        for package in state.get_inside_packages()
    )


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


def evaluate_state(state, objective_number=1):
    objective_function = get_objective_function(objective_number)
    state.value = objective_function(state)
    return state.value
