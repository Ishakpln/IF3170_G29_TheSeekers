from ..core import *


def hill_climbing_steepest_ascent(
    problem,
    state,
    max_iterations=1000,
    seed=None,
    objective_number=1,
):
    from time import perf_counter

    if not isinstance(max_iterations, int) or max_iterations < 0:
        raise ValueError("max_iteration tidak valid")
    if not is_valid_state(problem, state):
        raise ValueError("initital state tidak valid")

    started_at = perf_counter()
    initial_state = state.copy()
    initial_value = evaluate_state(problem, initial_state, objective_number)
    cur_state = initial_state.copy()
    cur_value = initial_value
    iterations = 0
    objective_history = [initial_value]
    termination_reason = "telah mencapai iterasi maksimum"

    while iterations < max_iterations:
        best_neighbor = None    
        best_neighbor_value = cur_value

        for neighbor in generate_all_neighbors(problem, cur_state):
            neighbor_value = evaluate_state(problem, neighbor, objective_number)
            if neighbor_value > best_neighbor_value:
                best_neighbor = neighbor
                best_neighbor_value = neighbor_value

        if best_neighbor is None:
            termination_reason = "tidak ada neighbor yang valuenya lebih tinggi"
            break

        cur_state = best_neighbor
        cur_value = best_neighbor_value
        iterations += 1
        objective_history.append(cur_value)

    final_state = cur_state.copy()

    return Result(
        "Hill Climbing - Steepest Ascent",
        initial_state,
        final_state,
        best_state=final_state.copy(),
        initial_value=initial_value,
        final_value=cur_value,
        best_value=cur_value,
        iterations=iterations,
        objective_history=objective_history,
        execution_time=perf_counter() - started_at,
        termination_reason=termination_reason,
        problem=problem,
    )


def hill_climbing_stochastic(
    problem,
    state,
    max_iterations=1000,
    seed=None,
    objective_number=1,
    sample_count=10,
):
    from random import Random
    from time import perf_counter

    if not isinstance(max_iterations, int) or max_iterations < 0:
        raise ValueError("max_iteration tidak valid")
    if not isinstance(sample_count, int) or sample_count < 1:
        raise ValueError("sample_count harus berupa bilangan bulat positif")
    if not is_valid_state(problem, state):
        raise ValueError("initial state tidak valid")

    started_at = perf_counter()
    initial_state = state.copy()
    initial_value = evaluate_state(problem, initial_state, objective_number)
    cur_state = initial_state.copy()
    cur_value = initial_value
    iterations = 0
    objective_history = [initial_value]
    termination_reason = "telah mencapai iterasi maksimum"
    rng = Random(seed)

    while iterations < max_iterations:
        positive_neighbors = []
        valid_samples = 0

        for _ in range(sample_count):
            try:
                neighbor = generate_random_neighbor(problem, cur_state, seed=seed, rng=rng)
            except RuntimeError:
                continue

            neighbor_value = evaluate_state(problem, neighbor, objective_number)
            valid_samples += 1
            if neighbor_value > cur_value:
                positive_neighbors.append((neighbor, neighbor_value))

        if not positive_neighbors:
            termination_reason = (
                "tidak ada neighbor sampel yang valuenya lebih tinggi"
                if valid_samples
                else "gagal menghasilkan neighbor yang valid"
            )
            break

        cur_state, cur_value = rng.choice(positive_neighbors)
        iterations += 1
        objective_history.append(cur_value)

    final_state = cur_state.copy()

    return Result(
        "Hill Climbing - Stochastic",
        initial_state,
        final_state,
        best_state=final_state.copy(),
        initial_value=initial_value,
        final_value=cur_value,
        best_value=cur_value,
        iterations=iterations,
        objective_history=objective_history,
        execution_time=perf_counter() - started_at,
        termination_reason=termination_reason,
        metrics={"configured_sample_count": sample_count},
        problem=problem,
    )


def hill_climbing_sideways_move(
    problem,
    state,
    max_iterations=1000,
    seed=None,
    objective_number=1,
    max_sideways=100,
):
    from time import perf_counter

    if not isinstance(max_iterations, int) or max_iterations < 0:
        raise ValueError("max_iteration tidak valid")
    if not isinstance(max_sideways, int) or max_sideways < 0:
        raise ValueError("max_sideways tidak valid")
    if not is_valid_state(problem, state):
        raise ValueError("initial state tidak valid")

    started_at = perf_counter()
    initial_state = state.copy()
    initial_value = evaluate_state(problem, initial_state, objective_number)
    cur_state = initial_state.copy()
    cur_value = initial_value
    iterations = 0
    sideways_moves = 0
    objective_history = [initial_value]
    termination_reason = "telah mencapai iterasi maksimum"

    while iterations < max_iterations:
        best_neighbor = None
        best_neighbor_value = cur_value

        for neighbor in generate_all_neighbors(problem, cur_state):
            neighbor_value = evaluate_state(problem, neighbor, objective_number)
            if neighbor_value >= best_neighbor_value:
                best_neighbor = neighbor
                best_neighbor_value = neighbor_value

        if best_neighbor is None:
            termination_reason = "tidak ada neighbor yang valuenya lebih tinggi atau sama"
            break

        is_sideways = best_neighbor_value == cur_value
        if is_sideways:
            if sideways_moves >= max_sideways:
                termination_reason = "telah mencapai sideways move maksimum"
                break
            sideways_moves += 1

        cur_state = best_neighbor
        cur_value = best_neighbor_value
        iterations += 1
        objective_history.append(cur_value)

        if is_sideways and sideways_moves >= max_sideways:
            termination_reason = "telah mencapai sideways move maksimum"
            break

    final_state = cur_state.copy()

    return Result(
        "Hill Climbing - Sideways Move",
        initial_state,
        final_state,
        best_state=final_state.copy(),
        initial_value=initial_value,
        final_value=cur_value,
        best_value=cur_value,
        iterations=iterations,
        objective_history=objective_history,
        execution_time=perf_counter() - started_at,
        termination_reason=termination_reason,
        metrics={
            "configured_max_sideways": max_sideways,
            "sideways_moves": sideways_moves,
        },
        problem=problem,
    )


def hill_climbing_random_restart(
    problem,
    state,
    max_iterations=1000,
    seed=None,
    objective_number=1,
    max_restarts=5,
):
    from random import Random
    from time import perf_counter

    if not isinstance(max_iterations, int) or max_iterations < 0:
        raise ValueError("max_iteration tidak valid")
    if not isinstance(max_restarts, int) or max_restarts < 0:
        raise ValueError("max_restarts tidak valid")

    started_at = perf_counter()
    rng = Random(seed)
    best_result = None
    initial_state = None
    objective_history = []
    iterations_per_restart = []

    for _ in range(max_restarts + 1):
        random_state = generate_initial_state(problem, seed=seed, rng=rng)
        result = hill_climbing_steepest_ascent(
            problem,
            random_state,
            max_iterations=max_iterations,
            seed=seed,
            objective_number=objective_number,
        )

        if initial_state is None:
            initial_state = result.initial_state.copy()
        if best_result is None or result.best_value > best_result.best_value:
            best_result = result

        iterations_per_restart.append(result.iterations)
        for value in result.objective_history:
            objective_history.append(
                max(objective_history[-1], value) if objective_history else value
            )

    final_state = best_result.best_state.copy()

    return Result(
        "Hill Climbing - Random Restart",
        initial_state,
        final_state,
        best_state=final_state.copy(),
        initial_value=objective_history[0],
        final_value=best_result.best_value,
        best_value=best_result.best_value,
        iterations=len(objective_history) - 1,
        objective_history=objective_history,
        execution_time=perf_counter() - started_at,
        termination_reason="telah mencapai restart maksimum",
        metrics={
            "configured_max_restarts": max_restarts,
            "completed_restarts": len(iterations_per_restart) - 1,
            "iterations_per_restart": iterations_per_restart,
            "total_search_iterations": sum(iterations_per_restart),
        },
        problem=problem,
    )


# nanti hapus saja ini klo dh implement smua di atas
def hill_climbing(
    problem,
    state,
    max_iterations=1000,
    seed=None,
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
