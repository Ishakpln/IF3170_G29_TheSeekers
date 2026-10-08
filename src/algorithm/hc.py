from .res import Result


def hill_climbing(
    state,
    max_iterations=1000,
    seed=42,
    objective_number=1,
    max_restarts=5,
):
    return Result(
        "Hill Climbing",
        state.copy(),
        state,
        best_state=state,
        iterations=0,
        objective_history=[state.value],
        termination_reason="placeholder return",
    )
