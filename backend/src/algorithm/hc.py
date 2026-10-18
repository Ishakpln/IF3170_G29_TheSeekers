from ..core import *


def hill_climbing_steepest_ascent(
    problem,
    state,
    max_iterations=1000,
    seed=42,
    objective_number=1,
):
    initial_state = state.copy()
    initial_value = evaluate_state(problem, initial_state, objective_number)


    cur_state = initial_state.copy()
    cur_value = initial_value
    # algo 
    cont = 1
    tempState = cur_state
    max = cur_value 
    i = 0
    while (cont == 1 and i < 1000 ) :
        i += 1
        found = 0
        for neighbor in generate_all_neighbors(problem, cur_state) : 
            neighborVal = evaluate_state(problem, neighbor, objective_number)
            if (neighborVal > max) : 
                max = neighborVal
                tempState = neighbor
                found = 1

        if (found == 1) : 
            cur_state = tempState 
        elif (found == 0) : 
            cur_state = tempState
            cont = 0


    # ini buat kumpul
    final_state = cur_state.copy()

    return Result(
        "Steepest-Ascent Hill Climbing",
        initial_state,
        final_state,
        best_state=final_state.copy(),
        initial_value=initial_value,
        final_value=cur_value,
        best_value=cur_value,
        iterations=0,
        objective_history=[initial_value],
        termination_reason="initial state returned",
        problem=problem,
    )


def hill_climbing_stochastic(
    problem,
    state,
    max_iterations=1000,
    seed=42,
    objective_number=1,
):
    initial_state = state.copy()
    initial_value = evaluate_state(problem, initial_state, objective_number)
    final_state = initial_state.copy()

    return Result(
        "Stochastic Hill Climbing",
        initial_state,
        final_state,
        best_state=final_state.copy(),
        initial_value=initial_value,
        final_value=initial_value,
        best_value=initial_value,
        iterations=0,
        objective_history=[initial_value],
        termination_reason="initial state returned",
        problem=problem,
    )


def hill_climbing_sideways_move(
    problem,
    state,
    max_iterations=1000,
    seed=42,
    objective_number=1,
    max_sideways=100,
):
    initial_state = state.copy()
    initial_value = evaluate_state(problem, initial_state, objective_number)
    final_state = initial_state.copy()

    return Result(
        "Hill Climbing with Sideways Move",
        initial_state,
        final_state,
        best_state=final_state.copy(),
        initial_value=initial_value,
        final_value=initial_value,
        best_value=initial_value,
        iterations=0,
        objective_history=[initial_value],
        termination_reason="initial state returned",
        metrics={
            "configured_max_sideways": max_sideways,
            "sideways_moves": 0,
        },
        problem=problem,
    )


def hill_climbing_random_restart(
    problem,
    state,
    max_iterations=1000,
    seed=42,
    objective_number=1,
    max_restarts=5,
):
    initial_state = state.copy()
    initial_value = evaluate_state(problem, initial_state, objective_number)
    final_state = initial_state.copy()

    return Result(
        "Random-Restart Hill Climbing",
        initial_state,
        final_state,
        best_state=final_state.copy(),
        initial_value=initial_value,
        final_value=initial_value,
        best_value=initial_value,
        iterations=0,
        objective_history=[initial_value],
        termination_reason="initial state returned",
        metrics={
            "configured_max_restarts": max_restarts,
            "completed_restarts": 0,
            "iterations_per_restart": [],
        },
        problem=problem,
    )


# nanti hapus saja ini klo dh implement smua di atas
def hill_climbing(
    problem,
    state,
    max_iterations=1000,
    seed=42,
    objective_number=1,
    max_restarts=5,
):
    return hill_climbing_random_restart(
        problem,
        state,
        max_iterations,
        seed,
        objective_number,
        max_restarts,
    )
