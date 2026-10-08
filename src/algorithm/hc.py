from ..core import Result, evaluate_state


def _placeholder_result(algorithm, problem, state, objective_number):
    initial_state = state.copy()
    initial_value = evaluate_state(problem, initial_state, objective_number)
    final_state = initial_state.copy()

    return Result(
        algorithm,
        initial_state,
        final_state,
        best_state=final_state.copy(),
        initial_value=initial_value,
        final_value=initial_value,
        best_value=initial_value,
        iterations=0,
        objective_history=[initial_value],
        termination_reason="placeholder return",
        problem=problem,
    )


def hill_climbing_steepest_ascent(
    problem,
    state,
    max_iterations=1000,
    seed=42,
    objective_number=1,
):
    return _placeholder_result(
        "Steepest-Ascent Hill Climbing",
        problem,
        state,
        objective_number,
    )


def hill_climbing_stochastic(
    problem,
    state,
    max_iterations=1000,
    seed=42,
    objective_number=1,
):
    return _placeholder_result(
        "Stochastic Hill Climbing",
        problem,
        state,
        objective_number,
    )


def hill_climbing_sideways_move(
    problem,
    state,
    max_iterations=1000,
    seed=42,
    objective_number=1,
    max_sideways=100,
):
    return _placeholder_result(
        "Hill Climbing with Sideways Move",
        problem,
        state,
        objective_number,
    )


def hill_climbing_random_restart(
    problem,
    state,
    max_iterations=1000,
    seed=42,
    objective_number=1,
    max_restarts=5,
):
    return _placeholder_result(
        "Random-Restart Hill Climbing",
        problem,
        state,
        objective_number,
    )


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
