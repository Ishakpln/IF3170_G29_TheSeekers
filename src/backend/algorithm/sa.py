from math import exp, isfinite
from random import Random
from time import perf_counter

from ..core import (
    Result,
    evaluate_state,
    generate_random_neighbor,
    is_valid_state,
)


def simulated_annealing(
    problem,
    state,
    max_iterations=1000,
    seed=None,
    objective_number=1,
    initial_temperature=100.0,
    cooling_rate=0.99,
    minimum_temperature=0.01,
):
    if not isinstance(max_iterations, int) or isinstance(max_iterations, bool):
        raise ValueError("max_iterations must be an integer")
    if max_iterations < 0:
        raise ValueError("max_iterations must not be negative")

    temperatures = {
        "initial_temperature": initial_temperature,
        "cooling_rate": cooling_rate,
        "minimum_temperature": minimum_temperature,
    }

    for name, value in temperatures.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a number")
        if not isfinite(value):
            raise ValueError(f"{name} must be finite")

    if initial_temperature <= 0:
        raise ValueError("initial_temperature must be greater than zero")
    if minimum_temperature <= 0:
        raise ValueError("minimum_temperature must be greater than zero")
    if minimum_temperature >= initial_temperature:
        raise ValueError(
            "minimum_temperature must be lower than initial_temperature"
        )
    if not 0 < cooling_rate <= 1:
        raise ValueError("cooling_rate must be greater than zero and at most one")
    if not is_valid_state(problem, state):
        raise ValueError("initial state is invalid")

    started_at = perf_counter()
    rng = Random(seed)
    initial_state = state.copy()
    initial_value = evaluate_state(problem, initial_state, objective_number)
    current_state = initial_state.copy()
    current_value = initial_value
    best_state = initial_state.copy()
    best_value = initial_value
    temperature = float(initial_temperature)

    iterations = 0
    accepted_moves = 0
    accepted_worse_moves = 0
    rejected_moves = 0
    improving_moves = 0
    objective_history = [best_value]
    current_objective_history = [current_value]
    temperature_history = [temperature]
    acceptance_probability_history = []
    termination_reason = "maximum iterations reached"

    while iterations < max_iterations and temperature > minimum_temperature:
        try:
            neighbor = generate_random_neighbor(
                problem,
                current_state,
                rng=rng,
            )
        except RuntimeError:
            termination_reason = "failed to generate a valid neighbor"
            break

        neighbor_value = evaluate_state(problem, neighbor, objective_number)
        delta_energy = neighbor_value - current_value
        acceptance_probability = (
            1.0 if delta_energy >= 0 else exp(delta_energy / temperature)
        )
        accepted = delta_energy >= 0 or rng.random() < acceptance_probability

        if accepted:
            current_state = neighbor
            current_value = neighbor_value
            accepted_moves += 1

            if delta_energy > 0:
                improving_moves += 1
            elif delta_energy < 0:
                accepted_worse_moves += 1
        else:
            rejected_moves += 1

        if current_value > best_value:
            best_state = current_state.copy()
            best_value = current_value

        iterations += 1
        temperature *= cooling_rate
        acceptance_probability_history.append(acceptance_probability)
        current_objective_history.append(current_value)
        objective_history.append(best_value)
        temperature_history.append(temperature)

    if iterations >= max_iterations:
        termination_reason = "maximum iterations reached"
    elif temperature <= minimum_temperature:
        termination_reason = "minimum temperature reached"

    final_state = current_state.copy()
    stuck_frequency = rejected_moves / iterations if iterations else 0.0

    return Result(
        "Simulated Annealing",
        initial_state,
        final_state,
        best_state=best_state.copy(),
        initial_value=initial_value,
        final_value=current_value,
        best_value=best_value,
        iterations=iterations,
        objective_history=objective_history,
        execution_time=perf_counter() - started_at,
        termination_reason=termination_reason,
        metrics={
            "acceptance_probability_history": acceptance_probability_history,
            "current_objective_history": current_objective_history,
            "temperature_history": temperature_history,
            "stuck_frequency": stuck_frequency,
            "stuck_iterations": rejected_moves,
            "accepted_moves": accepted_moves,
            "accepted_worse_moves": accepted_worse_moves,
            "rejected_moves": rejected_moves,
            "improving_moves": improving_moves,
        },
        problem=problem,
    )
