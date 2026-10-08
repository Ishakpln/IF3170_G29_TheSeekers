class Result:
    def __init__(
        self,
        algorithm,
        initial_state,
        final_state,
        best_state=None,
        initial_value=None,
        final_value=None,
        best_value=None,
        iterations=0,
        objective_history=None,
        execution_time=0,
        termination_reason=None,
        metrics=None,
        problem=None,
    ):
        self.algorithm = algorithm
        self.problem = problem
        self.initial_state = initial_state
        self.final_state = final_state
        self.best_state = best_state if best_state is not None else final_state
        self.initial_value = initial_value
        self.final_value = final_value
        self.best_value = best_value if best_value is not None else final_value
        self.iterations = iterations
        self.objective_history = (
            objective_history if objective_history is not None else []
        )
        self.execution_time = execution_time
        self.termination_reason = termination_reason
        self.metrics = metrics if metrics is not None else {}


class ResultContainer:
    def __init__(self, results=None):
        self.results = []

        if results is not None:
            self.addAllRes(results)

    def addRes(self, result):
        if not isinstance(result, Result):
            raise TypeError("result must be a Result")

        self.results.append(result)
        return result

    def addAllRes(self, results):
        for result in results:
            self.addRes(result)

    def removeRes(self, result_or_index):
        if isinstance(result_or_index, int):
            return self.results.pop(result_or_index)

        self.results.remove(result_or_index)
        return result_or_index

    def getRes(self, index):
        return self.results[index]

    def getAllRes(self):
        return self.results.copy()

    def getByAlgorithm(self, algorithm):
        return [
            result
            for result in self.results
            if result.algorithm == algorithm
        ]

    def clearRes(self):
        self.results.clear()

    def countRes(self):
        return len(self.results)

    def __len__(self):
        return len(self.results)

    def __iter__(self):
        return iter(self.results)

    def __getitem__(self, index):
        return self.results[index]
