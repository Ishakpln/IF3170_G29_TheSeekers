from .res import Result


def simulated_annealing(
    state,
    max_iterations=1000,
    seed=42,
    objective_number=1,
    initial_temperature=100.0,
    cooling_rate=0.99,
    minimum_temperature=0.01,
):
    return Result(
        "Simulated Annealing",
        state.copy(),
        state,
        best_state=state,
        iterations=0,
        objective_history=[state.value],
        termination_reason="placeholder return",
    )
