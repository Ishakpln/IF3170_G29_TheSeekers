import re
from math import exp, isfinite


MISSING = "Not recorded"
OBJECTIVES = {
    1: ("Total package value", "Sum of the values of all loaded packages"),
    2: ("Loaded package count", "Number of loaded packages"),
    3: ("Loaded package volume", "Sum of the volumes of all loaded packages"),
    4: ("Value per loaded volume", "Total loaded value / total loaded volume; 0 if empty"),
}


def _cell(value):
    if value is None:
        return MISSING
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value).replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")


def _table(headers, rows):
    cells = [[_cell(value) for value in row] for row in rows]
    if not cells:
        return "No rows recorded."
    widths = [max(len(header), *(len(row[index]) for row in cells)) for index, header in enumerate(headers)]
    formatted = [" | ".join(header.ljust(width) for header, width in zip(headers, widths))]
    formatted.append("-+-".join("-" * width for width in widths))
    formatted.extend(" | ".join(value.ljust(width) for value, width in zip(row, widths)) for row in cells)
    return "\n".join(formatted)


def _section(title, content):
    return f"{title}\n{'=' * len(title)}\n{content}\n"


def _fields(items):
    return "\n".join(f"{label}: {_cell(value)}" for label, value in items)


def _at(values, index):
    return values[index] if isinstance(values, (list, tuple)) and 0 <= index < len(values) else None


def _numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def _sum(rows, key):
    values = [row.get(key) for row in rows]
    return sum(values) if all(_numeric(value) for value in values) else None


def _state_section(title, rows, objective, trucks):
    if rows is None:
        return _section(title, MISSING)
    loaded = [row for row in rows if row.get("status") == "inside"]
    content = [_fields([
        ("Objective value", objective),
        ("Loaded packages", len(loaded)),
        ("Outside packages", sum(row.get("status") == "outside" for row in rows)),
        ("Total loaded package value", _sum(loaded, "value")),
        ("Total loaded weight", _sum(loaded, "weight")),
    ])]
    content.append(_table(
        ["Truck", "Loaded packages", "Loaded value", "Loaded weight", "Weight capacity"],
        [
            [truck.get("id"), len(items), _sum(items, "value"), _sum(items, "weight"), truck.get("max_capacity")]
            for truck in trucks
            for items in [[row for row in loaded if row.get("truck") == truck.get("id")]]
        ],
    ))
    content.append(_table(
        ["Package", "Status", "Truck", "X", "Y", "Z", "Width", "Length", "Height", "Orientation", "Value", "Weight", "Fragile", "ETA (days)"],
        [
            [row.get("package_id"), row.get("status"),
             *[row.get(key) if row.get("status") == "inside" else "-" for key in ("truck", "x", "y", "z")],
             *[row.get(key) for key in ("width", "length", "height", "orientation", "value", "weight", "fragile", "eta")]]
            for row in rows
        ],
    ))
    return _section(title, "\n\n".join(content))


def _raw_exponential(metrics, index):
    probability = _at(metrics.get("acceptance_probability_history"), index)
    if not _numeric(probability) or not 0 <= probability <= 1:
        return None
    if probability < 1:
        return probability if probability else "0 (floating-point underflow)"
    previous = _at(metrics.get("current_objective_history"), index)
    current = _at(metrics.get("current_objective_history"), index + 1)
    temperature = _at(metrics.get("temperature_history"), index)
    if not all(_numeric(value) for value in (previous, current, temperature)) or temperature <= 0:
        return None
    delta = current - previous
    try:
        value = exp(delta / temperature)
        if isfinite(value):
            return value
    except OverflowError:
        pass
    return f"exp({_cell(delta)} / {_cell(temperature)}) (above floating-point range)"


def _sa_sections(data, metrics):
    count = data.get("iterations", 0)
    temperatures = metrics.get("temperature_history")
    content = _fields([
        ("Stuck frequency", metrics.get("stuck_frequency")),
        ("Iterations at a local optimum", metrics.get("stuck_iterations")),
        ("Completed iterations (frequency denominator)", count),
        ("Frequency definition", metrics.get("stuck_frequency_definition")),
        ("Final state is a local optimum", metrics.get("stuck_at_local_optimum")),
        ("Rejection rate", metrics.get("rejection_rate")),
        ("Accepted moves", metrics.get("accepted_moves")),
        ("Accepted worse moves", metrics.get("accepted_worse_moves")),
        ("Rejected moves", metrics.get("rejected_moves")),
        ("Improving moves", metrics.get("improving_moves")),
        ("Initial temperature", _at(temperatures, 0)),
        ("Final temperature", _at(temperatures, count)),
    ])
    table = _table(
        ["Iteration", "Temperature used", "Raw exp(delta E / T)", "Acceptance probability", "Local optimum before move"],
        [
            [index + 1, _at(temperatures, index), _raw_exponential(metrics, index),
             _at(metrics.get("acceptance_probability_history"), index),
             _at(metrics.get("local_optimum_history"), index)]
            for index in range(count)
        ],
    )
    explanation = (
        "The exponential and probability columns are the tabular form of the SA probability plot.\n"
        "Acceptance probability = min(1, exp(delta E / T)). Raw exponentials can exceed 1.\n"
        "For worse proposals the recorded probability is the raw exponential. For other proposals,\n"
        "the raw exponential is reconstructed from the accepted objective change and temperature.\n"
        "Underflow is identified explicitly; missing inputs are shown as Not recorded.\n"
        "Temperatures are sampled before each proposal is accepted or rejected."
    )
    return [_section("SIMULATED ANNEALING MEASUREMENTS", content), _section("SA EXPONENTIAL / PROBABILITY TABLE", f"{explanation}\n\n{table}")]


def _history_sections(data, metrics):
    algorithm = data.get("algorithm")
    history = data.get("objective_history") or []
    if algorithm == "Genetic Algorithm":
        maximum = metrics.get("maximum_fitness_history") or history
        average = metrics.get("average_fitness_history") or []
        content = "Each row describes a population generation, including generation 0.\n\n" + _table(
            ["Generation / iteration", "Maximum objective", "Average objective"],
            [[index, _at(maximum, index), _at(average, index)] for index in range(max(len(maximum), len(average)))],
        )
        return [_section("GA POPULATION OBJECTIVE TABLE", content)]
    if algorithm == "Hill Climbing - Random Restart":
        counts = metrics.get("iterations_per_restart") or []
        coordinates = metrics.get("objective_history_iterations")
        raw = (
            isinstance(coordinates, list)
            and len(coordinates) == len(history)
            and sum(counts) + len(counts) == len(history)
        )
        run_rows = []
        samples = []
        offset = 0
        for run, count in enumerate(counts):
            run_rows.append([
                run + 1, run, count,
                _at(history, offset) if raw else None,
                _at(history, offset + count) if raw else None,
            ])
            if raw:
                for index in range(offset, offset + count + 1):
                    samples.append([index, run + 1, _at(coordinates, index), history[index]])
            offset += count + 1
        if not raw:
            samples = [[index, None, None, value] for index, value in enumerate(history)]
        measurements = _fields([
            ("Maximum restarts", metrics.get("configured_max_restarts", data.get("algorithm_parameters", {}).get("max_restarts"))),
            ("Completed restarts", metrics.get("completed_restarts")),
            ("Total climbing iterations", metrics.get("total_search_iterations", data.get("iterations"))),
        ])
        measurements += "\n\nRun 1 is the initial run; subsequent runs are restarts.\n"
        if raw:
            measurements += "Only climbing steps increase the iteration count.\n"
        measurements += "The returned final state is the best state across all runs, so it may differ from the last history row.\n\n"
        measurements += _table(["Run", "Restart number", "Climbing iterations", "Start objective", "End objective"], run_rows)
        note = "Every run start is retained, including repeated values and zero-step runs."
        if not raw:
            note = "Climbing coordinates were not recorded. History samples are preserved without assigning them to restarts."
        content = note + "\n\n" + _table(["Sample", "Run", "Climbing iteration", "Recorded objective"], samples)
        return [_section("RANDOM RESTART MEASUREMENTS", measurements), _section("OBJECTIVE HISTORY TABLE", content)]
    if algorithm == "Simulated Annealing":
        current = metrics.get("current_objective_history") or []
        best = metrics.get("best_objective_history") or []
        if not best:
            running = None
            for value in history:
                running = max(running, value) if running is not None else value
                best.append(running)
        return [_section("OBJECTIVE HISTORY TABLE", _table(
            ["Iteration", "Current objective", "Best so far"],
            [[index, _at(current, index), _at(best, index)] for index in range(max(len(current), len(best)))],
        )), *_sa_sections(data, metrics)]
    return [_section("OBJECTIVE HISTORY TABLE", _table(
        ["Iteration", "Current objective"], [[index, value] for index, value in enumerate(history)],
    ))]


def experiment_report(data):
    metrics = data.get("metrics") or {}
    parameters = data.get("algorithm_parameters") or {}
    objective_number = data.get("objective_number", metrics.get("objective_number", 1))
    objective, formula = OBJECTIVES.get(objective_number, ("Unknown objective", MISSING))
    sections = [_section("IF3170 LOCAL SEARCH EXPERIMENT REPORT", _fields([
        ("Experiment", data.get("experiment_name")),
        ("Job ID", data.get("id")),
        ("Saved run ID", data.get("run_id")),
        ("Run number", data.get("run_number")),
        ("Algorithm", data.get("algorithm")),
        ("Status", data.get("status")),
        ("Saved", data.get("saved")),
        ("Created at", data.get("created_at")),
        ("Completed at", data.get("completed_at")),
    ]))]
    sections.append(_section("CONFIGURATION", _fields([
        ("Objective function", f"{objective_number} - {objective}"),
        ("Objective definition (maximize)", formula),
        ("Seed", data.get("seed") if data.get("seed") is not None else "Random (None)"),
        ("Package count", data.get("package_count")),
        ("Truck count", data.get("truck_count")),
        ("Configured maximum climbing iterations per run" if data.get("algorithm") == "Hill Climbing - Random Restart" else "Configured maximum iterations", data.get("max_iterations")),
    ]) + "\n\n" + (_table(["Algorithm parameter", "Value"], [[key.replace("_", " ").capitalize(), value] for key, value in parameters.items()]) if parameters else "No additional algorithm parameters.")))
    if data.get("status") != "completed":
        sections.append(_section("RESULT AVAILABILITY", _fields([
            ("Status", data.get("status")), ("Error", data.get("error")),
        ]) + "\nThis run has no completed result. Final states, search duration, and history tables are unavailable."))
        return "\n".join(sections)
    results = [
        ("Initial objective value", data.get("initial_value")),
        ("Final objective value", data.get("final_value")),
        ("Best objective value", data.get("best_value")),
        ("Completed iterations", data.get("iterations")),
        ("Search duration (seconds)", data.get("execution_time")),
        ("Termination reason", data.get("termination_reason")),
    ]
    if data.get("algorithm") == "Genetic Algorithm":
        results.append(("Population size", metrics.get("population_size", parameters.get("population_size"))))
    sections.append(_section("SEARCH RESULTS", _fields(results)))
    if data.get("algorithm") == "Hill Climbing - Sideways Move":
        sections.append(_section("SIDEWAYS MOVE MEASUREMENTS", _fields([
            ("Maximum sideways moves", metrics.get("configured_max_sideways", parameters.get("max_sideways"))),
            ("Sideways moves performed", metrics.get("sideways_moves")),
        ])))
    trucks = data.get("trucks") or []
    sections.append(_section("TRUCKS AND COORDINATES", (
        "X = width, Y = length, Z = height. Coordinates refer to the lower package corner.\n"
        "Package dimensions below are already oriented along these axes.\n"
        "Orientation codes list the original dimensions along X, Y, Z (W = width, L = length, H = height).\n"
        "Outside packages have no truck coordinates. Interior coordinates outside the listed boxes are empty.\n\n"
        + _table(["Truck", "Width", "Length", "Height", "Maximum weight"], [
            [truck.get(key) for key in ("id", "width", "length", "height", "max_capacity")] for truck in trucks
        ])
    )))
    for title, key, value in (
        ("INITIAL STATE", "initial_state", "initial_value"),
        ("FINAL STATE", "final_state", "final_value"),
        ("BEST STATE", "best_state", "best_value"),
    ):
        sections.append(_state_section(title, data.get(key), data.get(value), trucks))
    sections.extend(_history_sections(data, metrics))
    sections.append(_section("NUMERIC PRECISION", "Values retain their recorded precision; small nonzero values are not rounded to zero for export."))
    return "\n".join(sections)


def report_filename(data):
    def safe(value):
        return re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "experiment")).strip("._-")[:70] or "experiment"
    return f"{safe(data.get('experiment_name'))}-{safe(data.get('algorithm'))}-{safe(data.get('id'))}.txt"
