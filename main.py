from src.orchestration import (
    prepare_initial_state,
    run_algorithm,
    run_all_algorithms,
    state_metrics,
    state_rows,
)
from src.core import ResultContainer, state_signature


ALGORITHM_NAMES = {
    "sa": "Simulated Annealing",
    "ga": "Genetic Algorithm",
}

HC_ALGORITHM_NAMES = {
    "1": "Hill Climbing - Steepest-Ascent",
    "2": "Hill Climbing - Stochastic",
    "3": "Hill Climbing - Sideways Move",
    "4": "Hill Climbing - Random Restart",
}

PACKAGE_COUNT = 30
DATASET_SEED = 42
DEFAULT_MAX_ITERATIONS = 1000
DEFAULT_MAX_RESTARTS = 5
DEFAULT_MAX_SIDEWAYS = 100
DEFAULT_INITIAL_TEMPERATURE = 100.0
DEFAULT_COOLING_RATE = 0.99
DEFAULT_MINIMUM_TEMPERATURE = 0.01
DEFAULT_POPULATION_SIZE = 20


def print_state(problem, state):
    metrics = state_metrics(problem, state)
    print(f'Value: {metrics["objective"]}')
    print(f'Loaded packages: {metrics["loaded_packages"]}')
    print(f'Unloaded packages: {metrics["unloaded_packages"]}')
    print(f'Loaded weight: {metrics["loaded_weight"]} / {metrics["capacity"]}')
    print("Packages:")

    for package in state_rows(problem, state):
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


def print_result(problem, result):
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
        print_state(problem, result.best_state)
    else:
        print("Final Visited State:")
        print_state(problem, result.final_state)
        print("Best State:")
        print_state(problem, result.best_state)


def select_algorithm():
    while True:
        choice = input("Pilih algoritma (hc/sa/ga/all): ").strip().lower()

        if choice in ["hc", "sa", "ga", "all"]:
            return choice

        print("Pilihan tidak valid.")


def select_hc_algorithm():
    print("Jenis Hill Climbing:")
    print("  1. Steepest-Ascent")
    print("  2. Stochastic")
    print("  3. Sideways Move")
    print("  4. Random Restart")

    while True:
        choice = input("Pilih jenis HC (1/2/3/4): ").strip()

        if choice in HC_ALGORITHM_NAMES:
            return HC_ALGORITHM_NAMES[choice]

        print("Pilihan jenis HC tidak valid.")


def select_yes_no(prompt):
    while True:
        choice = input(f"{prompt} (y/n): ").strip().lower()

        if choice in ["y", "yes", "ya"]:
            return True
        if choice in ["n", "no", "tidak"]:
            return False

        print("Masukkan y atau n.")


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


def select_integer(prompt, default, minimum):
    while True:
        value = input(f"{prompt} [{default}]: ").strip()

        if not value:
            return default

        try:
            result = int(value)
        except ValueError:
            print("Nilai harus berupa bilangan bulat.")
            continue

        if result >= minimum:
            return result

        print(f"Nilai minimal {minimum}.")


def select_float(prompt, default, minimum, maximum=None):
    while True:
        value = input(f"{prompt} [{default}]: ").strip()

        if not value:
            return default

        try:
            result = float(value)
        except ValueError:
            print("Nilai harus berupa angka.")
            continue

        if result <= minimum:
            print(f"Nilai harus lebih besar dari {minimum}.")
            continue
        if maximum is not None and result > maximum:
            print(f"Nilai maksimal {maximum}.")
            continue

        return result


def select_algorithm_parameters(algorithm_choice, hc_algorithm_name=None):
    parameters = {}

    if algorithm_choice in ["hc", "all"]:
        hc_parameters = {}

        if hc_algorithm_name == "Hill Climbing - Sideways Move":
            hc_parameters["max_sideways"] = select_integer(
                "Maximum sideways move HC",
                DEFAULT_MAX_SIDEWAYS,
                0,
            )
        elif hc_algorithm_name == "Hill Climbing - Random Restart":
            hc_parameters["max_restarts"] = select_integer(
                "Maximum restart HC",
                DEFAULT_MAX_RESTARTS,
                0,
            )

        parameters[hc_algorithm_name] = hc_parameters

    if algorithm_choice in ["sa", "all"]:
        initial_temperature = select_float(
            "Initial temperature SA",
            DEFAULT_INITIAL_TEMPERATURE,
            0,
        )
        minimum_temperature = select_float(
            "Minimum temperature SA",
            DEFAULT_MINIMUM_TEMPERATURE,
            0,
        )

        while minimum_temperature >= initial_temperature:
            print("Minimum temperature harus lebih kecil dari initial temperature.")
            minimum_temperature = select_float(
                "Minimum temperature SA",
                DEFAULT_MINIMUM_TEMPERATURE,
                0,
            )

        parameters["Simulated Annealing"] = {
            "initial_temperature": initial_temperature,
            "cooling_rate": select_float(
                "Cooling rate SA",
                DEFAULT_COOLING_RATE,
                0,
                1,
            ),
            "minimum_temperature": minimum_temperature,
        }

    if algorithm_choice in ["ga", "all"]:
        parameters["Genetic Algorithm"] = {
            "population_size": select_integer(
                "Population size GA",
                DEFAULT_POPULATION_SIZE,
                2,
            )
        }

    return parameters


def save_result(container, result):
    if select_yes_no(f"Simpan hasil {result.algorithm} ke container?"):
        container.addRes(result)
        print(f"Hasil disimpan. Total tersimpan: {container.countRes()}")
    else:
        print("Hasil tidak disimpan.")


def print_saved_results(container):
    print()
    print("=== Saved Results ===")

    if container.countRes() == 0:
        print("Belum ada hasil yang disimpan.")
        return

    for index, result in enumerate(container, start=1):
        print(
            f"{index}. {result.algorithm}, "
            f"iterations={result.iterations}, "
            f"final_value={result.final_value}, "
            f"execution_time={result.execution_time:.6f} seconds"
        )


def main():
    container = ResultContainer()

    while True:
        algorithm_choice = select_algorithm()
        hc_algorithm_name = None

        if algorithm_choice in ["hc", "all"]:
            hc_algorithm_name = select_hc_algorithm()

        truck_count = select_truck_count()
        max_iterations = select_integer(
            "Maximum iterations",
            DEFAULT_MAX_ITERATIONS,
            1,
        )
        experiment_seed = select_integer(
            "Experiment seed",
            DATASET_SEED,
            0,
        )
        algorithm_parameters = select_algorithm_parameters(
            algorithm_choice,
            hc_algorithm_name,
        )
        problem, initial_state = prepare_initial_state(
            PACKAGE_COUNT,
            experiment_seed,
            truck_count,
        )

        print("=== Problem ===")
        print(f"Packages: {PACKAGE_COUNT}")
        print(f"Seed: {experiment_seed}")
        print(f"Maximum iterations: {max_iterations}")
        print(f"Trucks: {len(problem.trucks)}")
        print("Objective: standard total package value")

        for algorithm_name, parameters in algorithm_parameters.items():
            print(f"{algorithm_name} parameters: {parameters}")

        print()
        print("=== Initial State ===")
        print_state(problem, initial_state)

        if algorithm_choice == "all":
            results, errors = run_all_algorithms(
                problem,
                initial_state,
                max_iterations,
                experiment_seed,
                algorithm_parameters,
                [
                    hc_algorithm_name,
                    "Simulated Annealing",
                    "Genetic Algorithm",
                ],
            )

            for result in results:
                print_result(problem, result)
                save_result(container, result)

            for error in errors:
                print()
                print(f'=== {error["algorithm"]} ===')
                print(f'Status: {error["error"]}')
                print("Final state: tidak tersedia")
        else:
            algorithm_name = (
                hc_algorithm_name
                if algorithm_choice == "hc"
                else ALGORITHM_NAMES[algorithm_choice]
            )
            result = run_algorithm(
                algorithm_name,
                problem,
                initial_state,
                max_iterations,
                experiment_seed,
                algorithm_parameters.get(algorithm_name),
            )
            print_result(problem, result)
            save_result(container, result)

        print_saved_results(container)

        if not select_yes_no("Jalankan eksperimen lagi?"):
            break

        print()

    print()
    print(f"Program selesai. Total hasil tersimpan: {container.countRes()}")
    return container


if __name__ == "__main__":
    main()
