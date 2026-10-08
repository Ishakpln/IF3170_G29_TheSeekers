import random
from time import perf_counter

from .algorithm import Result, ga, hc, sa
from .core import (
    Dimensions,
    Package,
    Truck,
    evaluate_state,
    generate_initial_state,
    is_valid_state,
)


ALGORITHMS = {
    "Hill Climbing": hc.hill_climbing,
    "Simulated Annealing": sa.simulated_annealing,
    "Genetic Algorithm": ga.genetic_algorithm,
}


def generate_problem(package_count=30, seed=42, truck_count=1):
    if truck_count < 1:
        raise ValueError("truck_count must be at least 1")

    rng = random.Random(seed)
    trucks = [
        Truck(Dimensions(10, 20, 5), 500)
        for _ in range(truck_count)
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

    return trucks, packages


def prepare_initial_state(package_count=30, seed=42, truck_count=1):
    trucks, packages = generate_problem(package_count, seed, truck_count)
    state = generate_initial_state(
        trucks,
        packages,
        seed=seed,
        objective_number=1,
    )

    if not is_valid_state(state):
        raise RuntimeError("generated initial state is invalid")

    return state


def state_rows(state):
    rows = []

    for package in state.packages:
        inside = package.position is not None and package.truck_index is not None
        dimensions = package.get_oriented_dimensions()

        rows.append(
            {
                "package_id": package.id,
                "status": "inside" if inside else "outside",
                "truck": package.truck_index + 1 if inside else None,
                "x": package.position.x if inside else None,
                "y": package.position.y if inside else None,
                "z": package.position.z if inside else None,
                "orientation": package.orientation.name,
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


def state_metrics(state):
    inside = state.get_inside_packages()
    outside = state.get_outside_packages()

    return {
        "objective": state.value,
        "loaded_packages": len(inside),
        "unloaded_packages": len(outside),
        "loaded_weight": sum(package.weight for package in inside),
        "capacity": sum(truck.max_capacity for truck in state.trucks),
    }


def run_algorithm(
    algorithm_name,
    initial_state,
    max_iterations=1000,
    seed=42,
):
    if algorithm_name not in ALGORITHMS:
        raise ValueError(f"unknown algorithm: {algorithm_name}")

    algorithm = ALGORITHMS[algorithm_name]

    working_state = initial_state.copy()
    started_at = perf_counter()
    result = algorithm(
        working_state,
        max_iterations=max_iterations,
        seed=seed,
        objective_number=1,
    )
    execution_time = perf_counter() - started_at

    if not isinstance(result, Result):
        raise RuntimeError(f"{algorithm_name} tidak mengembalikan Result")
    if result.final_state is None:
        raise RuntimeError(f"{algorithm_name} tidak memiliki final state")
    if result.best_state is None:
        raise RuntimeError(f"{algorithm_name} tidak memiliki best state")
    if not is_valid_state(result.final_state):
        raise RuntimeError(f"{algorithm_name} mengembalikan final state tidak valid")
    if not is_valid_state(result.best_state):
        raise RuntimeError(f"{algorithm_name} mengembalikan best state tidak valid")

    evaluate_state(result.final_state, 1)
    evaluate_state(result.best_state, 1)
    metrics = state_metrics(result.best_state)

    result.algorithm = algorithm_name
    result.initial_state = initial_state.copy()
    result.execution_time = execution_time
    result.metrics.update(
        {
            "loaded_packages": metrics["loaded_packages"],
            "unloaded_packages": metrics["unloaded_packages"],
            "loaded_weight": metrics["loaded_weight"],
            "capacity": metrics["capacity"],
            "configured_max_iterations": max_iterations,
            "seed": seed,
        }
    )

    if not result.objective_history:
        result.objective_history.append(result.best_state.value)

    return result


def run_all_algorithms(initial_state, max_iterations=1000, seed=42):
    results = []
    errors = []

    for algorithm_name in ALGORITHMS:
        try:
            results.append(
                run_algorithm(
                    algorithm_name,
                    initial_state,
                    max_iterations,
                    seed,
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
