from .res import Result


def simulated_annealing(state, max_iterations=1000, seed=42, objective_number=1):
    return Result(
        "Simulated Annealing",
        state.copy(),
        state,
        best_state=state,
        iterations=0,
        objective_history=[state.value],
        termination_reason="placeholder return",
    )
