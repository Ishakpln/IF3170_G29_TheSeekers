from concurrent.futures import CancelledError
import random
from time import perf_counter

from ..core import (
    Axis,
    Placement,
    Position,
    Result,
    State,
    evaluate_state,
    generate_initial_state,
    is_valid_state,
    move,
    rotate,
    swap,
)

MIN_MUTATION_RATE = 0.01
MAX_MUTATION_RATE = 0.05


def _raise_if_cancelled(cancel_event):
    if cancel_event is not None and cancel_event.is_set():
        raise CancelledError()


def _select_parent(population, fitness, tot_fitness, rng):
    if tot_fitness <= 0:
        return rng.choice(population) #acak

    selection = rng.random() * tot_fitness
    temp_fitness = 0

    for index in range(len(population)):
        temp_fitness += fitness[index]

        if selection < temp_fitness:
            return population[index]
    return population[-1]

def _crossover(problem, first_parent, second_parent, rng):
    if len(problem.packages) < 2:
        return first_parent.copy(), second_parent.copy()

    crosspoint = rng.randint(1, len(problem.packages) - 1)
    first_child = _make_child(problem, first_parent, second_parent, crosspoint)
    second_child = _make_child(problem, second_parent, first_parent, crosspoint)
    return first_child, second_child


def _make_child(problem, first_parent, second_parent, crosspoint):
    first_gen = {}
    for placement in first_parent.placements:
        first_gen[placement.package_id] = placement

    second_gen = {}
    for placement in second_parent.placements:
        second_gen[placement.package_id] = placement

    child_gen = []

    for i in range(len(problem.packages)):
        package = problem.packages[i]

        if i < crosspoint:
            parent_gen = first_gen
        else:
            parent_gen = second_gen

        inherited = parent_gen[package.id]

        child = Placement(inherited.package_id, position=inherited.position, orientation=inherited.orientation, truck_id=inherited.truck_id,)
        child_gen.append(child)
    return State(child_gen)


def _mutate(problem, state, rng):
    if not problem.packages:
        return state.copy()

    package = rng.choice(problem.packages)
    placement = state.get_placement(package.id)
    mutation = rng.random()

    if len(problem.packages) >= 2:
        if mutation < 0.33:
            mutation_type = "rotate"
        elif mutation < 0.66:
            mutation_type = "move"
        else:
            mutation_type = "swap"
    elif mutation < 0.5:
        mutation_type = "rotate"
    else:
        mutation_type = "move"

    if mutation_type == "swap":
        other = []
        for i in problem.packages:
            if i.id != package.id:
                other.append(i)

        second_package = rng.choice(other)
        neighbor = swap(problem, state, package.id, second_package.id)

        if neighbor is not None:
            return neighbor

        return state.copy()

    if mutation_type == "rotate":
        axis = list(Axis)
        rng.shuffle(axis)

        for a in axis:
            neighbor = rotate(problem, state, package.id, a)

            if neighbor is not None:
                return neighbor
    else:
        if placement.truck_id is not None:
            if rng.random() < 0.5:
                neighbor = move(problem, state, package.id, None, None)

                if neighbor is not None:
                    return neighbor
            else:
                neighbor = _try_random_placement(problem, state, package, rng)

                if neighbor is not None:
                    return neighbor
        else:
            neighbor =_try_random_placement(problem, state, package, rng)

            if neighbor is not None:
                return neighbor

    return state.copy()


def _try_random_placement(problem, state, package, rng):
    placement = state.get_placement(package.id)
    dimensions = placement.orientation.apply(package.dimensions)
    trucks = list(problem.trucks)
    rng.shuffle(trucks)

    for truck in trucks:
        if dimensions.width > truck.dimensions.width:
            continue
        if dimensions.length > truck.dimensions.length:
            continue
        if dimensions.height > truck.dimensions.height:
            continue

        possible_z = [0]
        for lower in state.get_placements_in_truck(truck.id):
            if lower.package_id == package.id:
                continue
            if problem.get_package(lower.package_id).is_fragile:
                continue

            lower_dimensions = lower.orientation.apply(
                problem.get_package(lower.package_id).dimensions
            )
            top = lower.position.z + lower_dimensions.height

            if top + dimensions.height <= truck.dimensions.height:
                possible_z.append(top)

        for i in range(3):
            position = Position(
                rng.randint(0, truck.dimensions.width - dimensions.width),
                rng.randint(0, truck.dimensions.length - dimensions.length),
                rng.choice(possible_z),
            )
            neighbor = move(problem, state, package.id, truck.id, position)

            if neighbor is not None:
                return neighbor

    return None


def genetic_algorithm(
    problem,
    state,
    max_iterations=1000,
    seed=None,
    objective_number=1,
    population_size=20,
    cancel_event=None,
):
    MAX_INVALID_CHILD = population_size * 10
    if (not isinstance(max_iterations, int) or max_iterations < 0 ):
        raise ValueError("max_iteration tidak valid")
    if (not isinstance(population_size, int) or population_size < 2 ):
        raise ValueError("population_size tidak valid")
    if not is_valid_state(problem, state):
        raise ValueError("initial state tidak valid")

    started_at = perf_counter()
    rng = random.Random(seed)
    population = [state.copy()]
    while len(population) < population_size:
        _raise_if_cancelled(cancel_event)
        population.append(generate_initial_state(problem, rng=rng))

    fitness = []
    for individual in population:
        _raise_if_cancelled(cancel_event)
        temp = evaluate_state(problem, individual, objective_number)
        fitness.append(temp)

    initial_value = fitness[0]
    best_index = 0
    max_fitness = fitness[0]
    tot_fitness = 0

    for i in range(population_size):
        tot_fitness += fitness[i]

        if fitness[i] > max_fitness:
            max_fitness = fitness[i]
            best_index = i

    max_fitness_history = [max_fitness]
    avr_fitness_history = [tot_fitness / population_size]
    best_state = population[best_index].copy()
    best_value = fitness[best_index]

    iterations = 0

    while iterations < max_iterations:
        _raise_if_cancelled(cancel_event)
        next_population = []
        invalid_child = 0

        while len(next_population) < population_size:
            _raise_if_cancelled(cancel_event)
            first_parent = _select_parent(population, fitness, tot_fitness, rng)
            second_parent = _select_parent(population, fitness, tot_fitness, rng)
            first_child, second_child = _crossover(problem, first_parent, second_parent, rng)

            for child in (first_child, second_child):
                _raise_if_cancelled(cancel_event)
                if not is_valid_state(problem, child):
                    invalid_child += 1

                    if invalid_child >= MAX_INVALID_CHILD:
                        next_population.append(first_parent.copy())
                        invalid_child = 0

                    if len(next_population) == population_size:
                        break
                    continue

                mutation_rate = rng.uniform(MIN_MUTATION_RATE, MAX_MUTATION_RATE)
                if rng.random() < mutation_rate:
                    child = _mutate(problem, child, rng)

                next_population.append(child)

                if len(next_population) == population_size:
                    break

        population = next_population
        fitness = []
        for individual in population:
            _raise_if_cancelled(cancel_event)
            temp = evaluate_state(problem, individual, objective_number)
            fitness.append(temp)

        best_index = 0
        max_fitness = fitness[0]
        tot_fitness = 0

        for index in range(population_size):
            tot_fitness += fitness[index]

            if fitness[index] > max_fitness:
                max_fitness = fitness[index]
                best_index = index

        if fitness[best_index] > best_value:
            best_value = fitness[best_index]
            best_state = population[best_index].copy()

        max_fitness_history.append(max_fitness)
        avr_fitness_history.append(tot_fitness / population_size)
        iterations += 1

    final_index = 0
    for index in range(population_size):
        if fitness[index] > fitness[final_index]:
            final_index = index

    final_state = population[final_index].copy()
    final_value = fitness[final_index]

    return Result(
        "Genetic Algorithm",
        state.copy(),
        final_state,
        best_state=best_state,
        initial_value=initial_value,
        final_value=final_value,
        best_value=best_value,
        iterations=iterations,
        objective_history=max_fitness_history.copy(),
        execution_time=perf_counter() - started_at,
        termination_reason="telah mencapai iterasi maksimum",
        metrics={
            "population_size": population_size,
            "maximum_fitness_history": max_fitness_history,
            "average_fitness_history": avr_fitness_history,
        },
        problem=problem,
    )
