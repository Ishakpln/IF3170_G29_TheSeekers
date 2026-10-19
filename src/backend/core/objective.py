#value paket dimuat
def evaluate_obj_func(problem, state):
    return sum(
        problem.get_package(placement.package_id).value
        for placement in state.get_inside_placements()
    )

#total paket dimuat
def evaluate_obj_func2(problem, state):
    return len(state.get_inside_placements())

#total volume paket yang dimuat
def evaluate_obj_func3(problem, state):
    load_volume = 0

    for placement in state.get_inside_placements():
        package = problem.get_package(placement.package_id)
        load_volume += (
            package.dimensions.width * package.dimensions.length * package.dimensions.height)

    return load_volume

#total volume paket
def evaluate_obj_func4(problem, state):
    tot_value = 0
    load_volume = 0

    for placement in state.get_inside_placements():
        package = problem.get_package(placement.package_id)
        tot_value += package.value
        load_volume += (package.dimensions.width * package.dimensions.length * package.dimensions.height)

    if load_volume == 0:
        return 0

    return tot_value / load_volume


def get_objective_function(objective_number):
    objective_functions = {
        1: evaluate_obj_func,
        2: evaluate_obj_func2,
        3: evaluate_obj_func3,
        4: evaluate_obj_func4,
    }

    if objective_number not in objective_functions:
        raise ValueError("objective number is not available")

    return objective_functions[objective_number]


def evaluate_state(problem, state, objective_number=1):
    objective_function = get_objective_function(objective_number)
    return objective_function(problem, state)
