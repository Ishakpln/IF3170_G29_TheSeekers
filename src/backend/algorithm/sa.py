from concurrent.futures import CancelledError
from math import exp, isfinite
from random import Random
from time import perf_counter

from ..core import (
    Position,
    Result,
    evaluate_state,
    generate_all_neighbors,
    generate_random_neighbor,
    is_valid_state,
    swap,
)


def _raise_if_cancelled(cancel_event):
    if cancel_event is not None and cancel_event.is_set():
        raise CancelledError()


def _oriented_dimensions(problem, placement):
    package = problem.get_package(placement.package_id)
    return placement.orientation.apply(package.dimensions)


def _intervals_overlap(start_a, size_a, start_b, size_b):
    return max(start_a, start_b) < min(start_a + size_a, start_b + size_b)


def _footprints_overlap(position_a, size_a, position_b, size_b):
    return _intervals_overlap(
        position_a.x,
        size_a.width,
        position_b.x,
        size_b.width,
    ) and _intervals_overlap(
        position_a.y,
        size_a.length,
        position_b.y,
        size_b.length,
    )


def _volumes_overlap(position_a, size_a, position_b, size_b):
    return _footprints_overlap(
        position_a,
        size_a,
        position_b,
        size_b,
    ) and _intervals_overlap(
        position_a.z,
        size_a.height,
        position_b.z,
        size_b.height,
    )


def _can_add_to_truck(
    problem,
    placement,
    truck,
    position,
    truck_placements,
    loaded_weight,
):
    package = problem.get_package(placement.package_id)
    size = _oriented_dimensions(problem, placement)

    if loaded_weight + package.weight > truck.max_capacity:
        return False
    if position.x + size.width > truck.dimensions.width:
        return False
    if position.y + size.length > truck.dimensions.length:
        return False
    if position.z + size.height > truck.dimensions.height:
        return False

    for other in truck_placements:
        other_size = _oriented_dimensions(problem, other)

        if _volumes_overlap(position, size, other.position, other_size):
            return False

    if position.z > 0:
        has_support = False

        for lower in truck_placements:
            lower_size = _oriented_dimensions(problem, lower)
            lower_top = lower.position.z + lower_size.height

            if lower_top != position.z:
                continue
            if not _footprints_overlap(
                position,
                size,
                lower.position,
                lower_size,
            ):
                continue
            if problem.get_package(lower.package_id).is_fragile:
                return False

            has_support = True

        if not has_support:
            return False

    if package.is_fragile:
        candidate_top = position.z + size.height

        for upper in truck_placements:
            if upper.position.z != candidate_top:
                continue

            upper_size = _oriented_dimensions(problem, upper)

            if _footprints_overlap(
                position,
                size,
                upper.position,
                upper_size,
            ):
                return False

    return True


def _has_value_improving_neighbor(problem, state, cancel_event=None):
    inside = state.get_inside_placements()
    outside = state.get_outside_placements()

    for outside_placement in outside:
        _raise_if_cancelled(cancel_event)
        outside_value = problem.get_package(outside_placement.package_id).value

        for inside_placement in inside:
            inside_value = problem.get_package(inside_placement.package_id).value

            if outside_value <= inside_value:
                continue
            if swap(
                problem,
                state,
                outside_placement.package_id,
                inside_placement.package_id,
            ) is not None:
                return True

    placements_by_truck = {
        truck.id: state.get_placements_in_truck(truck.id)
        for truck in problem.trucks
    }
    weight_by_truck = {
        truck.id: sum(
            problem.get_package(placement.package_id).weight
            for placement in placements_by_truck[truck.id]
        )
        for truck in problem.trucks
    }

    for placement in outside:
        _raise_if_cancelled(cancel_event)
        package = problem.get_package(placement.package_id)

        if package.value <= 0:
            continue

        size = _oriented_dimensions(problem, placement)

        for truck in problem.trucks:
            if size.width > truck.dimensions.width:
                continue
            if size.length > truck.dimensions.length:
                continue
            if size.height > truck.dimensions.height:
                continue

            truck_placements = placements_by_truck[truck.id]
            possible_z = {0}

            for lower in truck_placements:
                if problem.get_package(lower.package_id).is_fragile:
                    continue

                lower_size = _oriented_dimensions(problem, lower)
                top = lower.position.z + lower_size.height

                if top + size.height <= truck.dimensions.height:
                    possible_z.add(top)

            for x in range(truck.dimensions.width - size.width + 1):
                _raise_if_cancelled(cancel_event)
                for y in range(truck.dimensions.length - size.length + 1):
                    for z in possible_z:
                        if _can_add_to_truck(
                            problem,
                            placement,
                            truck,
                            Position(x, y, z),
                            truck_placements,
                            weight_by_truck[truck.id],
                        ):
                            return True

    return False


def _is_local_optimum(
    problem,
    state,
    current_value,
    objective_number,
    cancel_event=None,
):
    if objective_number == 1:
        return not _has_value_improving_neighbor(problem, state, cancel_event)

    for neighbor in generate_all_neighbors(problem, state):
        _raise_if_cancelled(cancel_event)
        neighbor_value = evaluate_state(problem, neighbor, objective_number)

        if neighbor_value > current_value:
            return False

    return True


def simulated_annealing(
    problem,
    state,
    max_iterations=1000,
    seed=None,
    objective_number=1,
    initial_temperature=100.0,
    cooling_rate=0.99,
    minimum_temperature=0.01,
    cancel_event=None,
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
    if not 0 < cooling_rate < 1:
        raise ValueError("cooling_rate must be between zero and one")
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
    stuck_iterations = 0
    local_optimum_history = []
    current_local_optimum = None
    objective_history = [current_value]
    current_objective_history = [current_value]
    best_objective_history = [best_value]
    temperature_history = [temperature]
    acceptance_probability_history = []
    termination_reason = "maximum iterations reached"

    while iterations < max_iterations and temperature > minimum_temperature:
        _raise_if_cancelled(cancel_event)
        try:
            neighbor = generate_random_neighbor(
                problem,
                current_state,
                rng=rng,
            )
        except RuntimeError:
            termination_reason = "failed to generate a valid neighbor"
            break

        if current_local_optimum is None:
            current_local_optimum = _is_local_optimum(
                problem,
                current_state,
                current_value,
                objective_number,
                cancel_event,
            )
        iteration_at_local_optimum = current_local_optimum

        neighbor_value = evaluate_state(problem, neighbor, objective_number)
        delta_energy = neighbor_value - current_value
        acceptance_probability = (
            1.0 if delta_energy >= 0 else exp(delta_energy / temperature)
        )
        accepted = delta_energy >= 0 or rng.random() < acceptance_probability

        if accepted:
            current_state = neighbor
            current_value = neighbor_value
            current_local_optimum = None
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
        stuck_iterations += int(iteration_at_local_optimum)
        local_optimum_history.append(iteration_at_local_optimum)
        temperature *= cooling_rate
        acceptance_probability_history.append(acceptance_probability)
        current_objective_history.append(current_value)
        objective_history.append(current_value)
        best_objective_history.append(best_value)
        temperature_history.append(temperature)

    if iterations >= max_iterations:
        termination_reason = "maximum iterations reached"
    elif temperature <= minimum_temperature:
        termination_reason = "minimum temperature reached"

    final_state = current_state.copy()
    rejection_rate = rejected_moves / iterations if iterations else 0.0
    stuck_at_local_optimum = current_local_optimum
    if stuck_at_local_optimum is None:
        stuck_at_local_optimum = _is_local_optimum(
            problem,
            final_state,
            current_value,
            objective_number,
            cancel_event,
        )
    stuck_frequency = stuck_iterations / iterations if iterations else 0.0

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
            "best_objective_history": best_objective_history,
            "temperature_history": temperature_history,
            "stuck_frequency": stuck_frequency,
            "stuck_iterations": stuck_iterations,
            "local_optimum_history": local_optimum_history,
            "stuck_frequency_definition": (
                "Fraction of completed iterations whose pre-move current state "
                "has no strictly improving valid one-step neighbor."
            ),
            "stuck_at_local_optimum": stuck_at_local_optimum,
            "rejection_rate": rejection_rate,
            "accepted_moves": accepted_moves,
            "accepted_worse_moves": accepted_worse_moves,
            "rejected_moves": rejected_moves,
            "improving_moves": improving_moves,
        },
        problem=problem,
    )
