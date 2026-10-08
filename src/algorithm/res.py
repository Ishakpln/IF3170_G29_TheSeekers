class Result:
    def __init__(
        self,
        algorithm,
        initial_state,
        final_state,
        best_state=None,
        iterations=0,
        objective_history=None,
        execution_time=0,
        termination_reason=None,
        metrics=None,
    ):
        self.algorithm = algorithm
        self.initial_state = initial_state
        self.final_state = final_state
        self.best_state = best_state if best_state is not None else final_state
        self.iterations = iterations
        self.objective_history = (
            objective_history if objective_history is not None else []
        )
        self.execution_time = execution_time
        self.termination_reason = termination_reason
        self.metrics = metrics if metrics is not None else {}
