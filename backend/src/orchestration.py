import random
from time import perf_counter

from .algorithm import Result, ga, hc, sa
from .core import (
    Dimensions,
    Package,
    Problem,
    REQUIRED_METRICS,
    Truck,
    evaluate_state,
    generate_initial_state,
    is_valid_state,
)


ALGORITHMS = {
    "Hill Climbing - Steepest-Ascent": hc.hill_climbing_steepest_ascent,
    "Hill Climbing - Stochastic": hc.hill_climbing_stochastic,
    "Hill Climbing - Sideways Move": hc.hill_climbing_sideways_move,
    "Hill Climbing - Random Restart": hc.hill_climbing_random_restart,
    "Simulated Annealing": sa.simulated_annealing,
    "Genetic Algorithm": ga.genetic_algorithm,
}


def generate_problem(package_count=30, seed=42, truck_count=1):
    if truck_count < 1:
        raise ValueError("truck_count must be at least 1")

    rng = random.Random(seed)
    trucks = [
        Truck(f"T{index + 1:03d}", Dimensions(10, 20, 5), 500)
        for index in range(truck_count)
    ]
    packages = []

    for index in range(package_count):
        packages.append(
            Package(
                f"P{index + 1:03d}",
                Dimensions(
                    rng.randint(1, 4),
                    rng.randint(1, 4),
                    rng.randint(1, 3),
                ),
                rng.randint(10, 100),
                rng.randint(1, 20),
                rng.random() < 0.2,
                rng.randint(1, 7),
            )
        )

    return Problem(trucks, packages)


def prepare_initial_state(package_count=30, seed=42, truck_count=1):
    problem = generate_problem(package_count, seed, truck_count)
    state = generate_initial_state(problem, seed=seed)

    if not is_valid_state(problem, state):
        raise RuntimeError("generated initial state is invalid")

    return problem, state


def state_rows(problem, state):
    rows = []

    for placement in state.placements:
        package = problem.get_package(placement.package_id)
        position = placement.position
        inside = position is not None and placement.truck_id is not None
        dimensions = placement.orientation.apply(package.dimensions)

        rows.append(
            {
                "package_id": package.id,
                "status": "inside" if inside else "outside",
                "truck": placement.truck_id if inside else None,
                "x": position.x if inside else None,
                "y": position.y if inside else None,
                "z": position.z if inside else None,
                "orientation": placement.orientation.name,
                "width": dimensions.width,
                "length": dimensions.length,
                "height": dimensions.height,
                "value": package.value,
                "weight": package.weight,
                "fragile": package.is_fragile,
                "eta": package.eta,
            }
        )

    return rows


def state_metrics(problem, state, objective_number=1):
    inside = state.get_inside_placements()
    outside = state.get_outside_placements()

    return {
        "objective": evaluate_state(problem, state, objective_number),
        "loaded_packages": len(inside),
        "unloaded_packages": len(outside),
        "loaded_weight": sum(
            problem.get_package(placement.package_id).weight
            for placement in inside
        ),
        "capacity": sum(truck.max_capacity for truck in problem.trucks),
    }


def _validate_result_contract(result):
    if not isinstance(result.iterations, int) or result.iterations < 0:
        raise RuntimeError("iterations must be a non-negative integer")
    if len(result.objective_history) != result.iterations + 1:
        raise RuntimeError(
            "objective_history length must equal iterations + 1"
        )
    if result.objective_history[-1] != result.best_value:
        raise RuntimeError("objective_history must end with best_value")
    if result.best_value < result.initial_value:
        raise RuntimeError("best_value must not be lower than initial_value")
    if result.best_value < result.final_value:
        raise RuntimeError("best_value must not be lower than final_value")

    required_metrics = REQUIRED_METRICS.get(result.algorithm, set())
    missing_metrics = required_metrics.difference(result.metrics)

    if missing_metrics:
        missing = ", ".join(sorted(missing_metrics))
        raise RuntimeError(f"missing required metrics: {missing}")

    if result.algorithm != "Genetic Algorithm":
        if result.objective_history[0] != result.initial_value:
            raise RuntimeError(
                "objective_history must start with initial_value"
            )

    if result.algorithm == "Hill Climbing - Sideways Move":
        if result.metrics["configured_max_sideways"] < 0:
            raise RuntimeError("configured_max_sideways must not be negative")
        if result.metrics["sideways_moves"] < 0:
            raise RuntimeError("sideways_moves must not be negative")
        if (
            result.metrics["sideways_moves"]
            > result.metrics["configured_max_sideways"]
        ):
            raise RuntimeError("sideways_moves exceeds configured maximum")

    if result.algorithm == "Hill Climbing - Random Restart":
        restart_iterations = result.metrics["iterations_per_restart"]

        if result.metrics["configured_max_restarts"] < 0:
            raise RuntimeError("configured_max_restarts must not be negative")
        if result.metrics["completed_restarts"] < 0:
            raise RuntimeError("completed_restarts must not be negative")
        if any(
            not isinstance(value, int) or value < 0
            for value in restart_iterations
        ):
            raise RuntimeError(
                "iterations_per_restart must contain non-negative integers"
            )
        if sum(restart_iterations) != result.iterations:
            raise RuntimeError(
                "iterations_per_restart must sum to iterations"
            )
        if (
            result.metrics["completed_restarts"]
            > result.metrics["configured_max_restarts"]
        ):
            raise RuntimeError("completed_restarts exceeds configured maximum")

    if result.algorithm == "Simulated Annealing":
        if (
            len(result.metrics["current_objective_history"])
            != result.iterations + 1
        ):
            raise RuntimeError(
                "current_objective_history length must equal iterations + 1"
            )
        if (
            len(result.metrics["temperature_history"])
            != result.iterations + 1
        ):
            raise RuntimeError(
                "temperature_history length must equal iterations + 1"
            )
        if (
            len(result.metrics["acceptance_probability_history"])
            != result.iterations
        ):
            raise RuntimeError(
                "acceptance_probability_history length must equal iterations"
            )
        if not 0 <= result.metrics["stuck_frequency"] <= 1:
            raise RuntimeError("stuck_frequency must be between 0 and 1")
        if any(
            probability < 0 or probability > 1
            for probability in result.metrics[
                "acceptance_probability_history"
            ]
        ):
            raise RuntimeError(
                "acceptance probabilities must be between 0 and 1"
            )
        if result.metrics["current_objective_history"][-1] != result.final_value:
            raise RuntimeError(
                "current_objective_history must end with final_value"
            )

    if result.algorithm == "Genetic Algorithm":
        maximum_history = result.metrics["maximum_fitness_history"]
        average_history = result.metrics["average_fitness_history"]

        if result.metrics["population_size"] < 2:
            raise RuntimeError("population_size must be at least 2")
        if len(maximum_history) != result.iterations + 1:
            raise RuntimeError(
                "maximum_fitness_history length must equal iterations + 1"
            )
        if len(average_history) != result.iterations + 1:
            raise RuntimeError(
                "average_fitness_history length must equal iterations + 1"
            )
        if result.objective_history != maximum_history:
            raise RuntimeError(
                "GA objective_history must equal maximum_fitness_history"
            )
        if any(
            average > maximum
            for maximum, average in zip(maximum_history, average_history)
        ):
            raise RuntimeError(
                "average fitness must not exceed maximum fitness"
            )


def run_algorithm(
    algorithm_name,
    problem,
    initial_state,
    max_iterations=1000,
    seed=42,
    algorithm_parameters=None,
    objective_number=1,
    experiment_name=None,
):
    if algorithm_name not in ALGORITHMS:
        raise ValueError(f"unknown algorithm: {algorithm_name}")
    if not is_valid_state(problem, initial_state):
        raise ValueError("initial state is invalid")

    algorithm = ALGORITHMS[algorithm_name]
    parameters = dict(algorithm_parameters or {})
    reserved_parameters = {
        "problem",
        "state",
        "max_iterations",
        "seed",
        "objective_number",
    }

    if reserved_parameters.intersection(parameters):
        raise ValueError("algorithm parameters contain a reserved parameter")

    working_state = initial_state.copy()
    started_at = perf_counter()
    result = algorithm(
        problem,
        working_state,
        max_iterations=max_iterations,
        seed=seed,
        objective_number=objective_number,
        **parameters,
    )
    execution_time = perf_counter() - started_at

    if not isinstance(result, Result):
        raise RuntimeError(f"{algorithm_name} tidak mengembalikan Result")
    if result.final_state is None:
        raise RuntimeError(f"{algorithm_name} tidak memiliki final state")
    if result.best_state is None:
        raise RuntimeError(f"{algorithm_name} tidak memiliki best state")
    if not is_valid_state(problem, result.final_state):
        raise RuntimeError(f"{algorithm_name} mengembalikan final state tidak valid")
    if not is_valid_state(problem, result.best_state):
        raise RuntimeError(f"{algorithm_name} mengembalikan best state tidak valid")

    initial_snapshot = initial_state.copy()
    initial_value = evaluate_state(problem, initial_snapshot, objective_number)
    final_value = evaluate_state(problem, result.final_state, objective_number)
    best_value = evaluate_state(problem, result.best_state, objective_number)
    metrics = state_metrics(problem, result.best_state, objective_number)

    result.algorithm = algorithm_name
    result.problem = problem
    result.initial_state = initial_snapshot
    result.initial_value = initial_value
    result.final_value = final_value
    result.best_value = best_value
    result.experiment_name = experiment_name or result.experiment_name
    result.execution_time = execution_time
    result.metrics.update(
        {
            "loaded_packages": metrics["loaded_packages"],
            "unloaded_packages": metrics["unloaded_packages"],
            "loaded_weight": metrics["loaded_weight"],
            "capacity": metrics["capacity"],
            "configured_max_iterations": max_iterations,
            "seed": seed,
            "objective_number": objective_number,
            "algorithm_parameters": parameters,
        }
    )

    if not result.objective_history:
        result.objective_history.append(result.best_value)

    _validate_result_contract(result)

    return result


def run_all_algorithms(
    problem,
    initial_state,
    max_iterations=1000,
    seed=42,
    parameters_by_algorithm=None,
    algorithm_names=None,
    objective_number=1,
    experiment_name=None,
):
    results = []
    errors = []
    parameters_by_algorithm = parameters_by_algorithm or {}
    algorithm_names = algorithm_names or [
        "Hill Climbing - Random Restart",
        "Simulated Annealing",
        "Genetic Algorithm",
    ]

    for algorithm_name in algorithm_names:
        try:
            results.append(
                run_algorithm(
                    algorithm_name,
                    problem,
                    initial_state,
                    max_iterations,
                    seed,
                    parameters_by_algorithm.get(algorithm_name),
                    objective_number,
                    experiment_name,
                )
            )
        except Exception as error:
            errors.append(
                {
                    "algorithm": algorithm_name,
                    "error": str(error),
                }
            )

    return results, errors
