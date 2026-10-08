from src.orchestration import (
    prepare_initial_state,
    run_algorithm,
    run_all_algorithms,
    state_metrics,
    state_rows,
)
from src.core import state_signature


ALGORITHM_NAMES = {
    "hc": "Hill Climbing",
    "sa": "Simulated Annealing",
    "ga": "Genetic Algorithm",
}

PACKAGE_COUNT = 30
DATASET_SEED = 42
MAX_ITERATIONS = 1000


def print_state(state):
    metrics = state_metrics(state)
    print(f'Value: {metrics["objective"]}')
    print(f'Loaded packages: {metrics["loaded_packages"]}')
    print(f'Unloaded packages: {metrics["unloaded_packages"]}')
    print(f'Loaded weight: {metrics["loaded_weight"]} / {metrics["capacity"]}')
    print("Packages:")

    for package in state_rows(state):
        if package["status"] == "inside":
            placement = (
                f'truck={package["truck"]}, '
                f'position=({package["x"]}, {package["y"]}, {package["z"]}), '
                f'orientation={package["orientation"]}'
            )
        else:
            placement = "outside"

        details = (
            f'dimensions=({package["width"]}, {package["length"]}, '
            f'{package["height"]}), value={package["value"]}, '
            f'weight={package["weight"]}, fragile={package["fragile"]}, '
            f'eta={package["eta"]}'
        )
        print(f'  {package["package_id"]}: {placement}, {details}')


def print_result(result):
    print()
    print(f"=== {result.algorithm} ===")
    print(f"Execution time: {result.execution_time:.6f} seconds")
    print(
        "Iterations: "
        + (
            str(result.iterations)
            if result.iterations is not None
            else "not provided"
        )
    )
    print(f"Objective history entries: {len(result.objective_history)}")

    if result.termination_reason:
        print(f"Termination reason: {result.termination_reason}")

    if state_signature(result.final_state) == state_signature(result.best_state):
        print("Final / Best State:")
        print_state(result.best_state)
    else:
        print("Final Visited State:")
        print_state(result.final_state)
        print("Best State:")
        print_state(result.best_state)


def select_algorithm():
    while True:
        choice = input("Pilih algoritma (hc/sa/ga/all): ").strip().lower()

        if choice in ["hc", "sa", "ga", "all"]:
            return choice

        print("Pilihan tidak valid.")


def select_truck_count():
    while True:
        value = input("Jumlah truck: ").strip()

        try:
            truck_count = int(value)
        except ValueError:
            print("Jumlah truck harus berupa bilangan bulat positif.")
            continue

        if truck_count >= 1:
            return truck_count

        print("Jumlah truck minimal 1.")


def main():
    algorithm_choice = select_algorithm()
    truck_count = select_truck_count()
    initial_state = prepare_initial_state(
        PACKAGE_COUNT,
        DATASET_SEED,
        truck_count,
    )

    print("=== Problem ===")
    print(f"Packages: {PACKAGE_COUNT}")
    print(f"Seed: {DATASET_SEED}")
    print(f"Maximum iterations: {MAX_ITERATIONS}")
    print(f"Trucks: {len(initial_state.trucks)}")
    print("Objective: standard total package value")
    print()
    print("=== Initial State ===")
    print_state(initial_state)

    if algorithm_choice == "all":
        results, errors = run_all_algorithms(
            initial_state,
            MAX_ITERATIONS,
            DATASET_SEED,
        )

        for result in results:
            print_result(result)

        for error in errors:
            print()
            print(f'=== {error["algorithm"]} ===')
            print(f'Status: {error["error"]}')
            print("Final state: tidak tersedia")
    else:
        algorithm_name = ALGORITHM_NAMES[algorithm_choice]
        result = run_algorithm(
            algorithm_name,
            initial_state,
            MAX_ITERATIONS,
            DATASET_SEED,
        )
        print_result(result)


if __name__ == "__main__":
    main()
