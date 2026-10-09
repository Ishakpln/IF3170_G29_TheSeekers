from ..core import Result, evaluate_state


def hill_climbing_steepest_ascent(
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
        "Steepest-Ascent Hill Climbing",
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
