import pickle
from pathlib import Path


REQUIRED_METRICS = {
    "Hill Climbing - Sideways Move": {
        "configured_max_sideways",
        "sideways_moves",
    },
    "Hill Climbing - Random Restart": {
        "configured_max_restarts",
        "completed_restarts",
        "iterations_per_restart",
    },
    "Simulated Annealing": {
        "acceptance_probability_history",
        "current_objective_history",
        "temperature_history",
        "stuck_frequency",
    },
    "Genetic Algorithm": {
        "population_size",
        "maximum_fitness_history",
        "average_fitness_history",
    },
}


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
        run_id=None,
        run_number=None,
        experiment_name=None,
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
        self.run_id = run_id
        self.run_number = run_number
        self.experiment_name = experiment_name


class ResultContainer:
    def __init__(self, results=None):
        self.results = []

        if results is not None:
            self.addAllRes(results)

    def addRes(self, result, experiment_name=None):
        if not isinstance(result, Result):
            raise TypeError("result must be a Result")

        if experiment_name is not None:
            result.experiment_name = experiment_name
        if result.experiment_name is None:
            result.experiment_name = result.algorithm
        if result.run_number is None:
            existing_run_numbers = [
                saved.run_number
                for saved in self.results
                if saved.algorithm == result.algorithm
                and saved.experiment_name == result.experiment_name
                and saved.run_number is not None
            ]
            result.run_number = max(existing_run_numbers, default=0) + 1
        if result.run_id is None:
            existing_ids = [
                saved.run_id
                for saved in self.results
                if saved.run_id is not None
            ]
            result.run_id = max(existing_ids, default=0) + 1

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

    def getByExperiment(self, experiment_name):
        return [
            result
            for result in self.results
            if result.experiment_name == experiment_name
        ]

    def clearRes(self):
        self.results.clear()

    def countRes(self):
        return len(self.results)

    def saveToFile(self, file_path):
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("wb") as file:
            pickle.dump(self, file)

    @classmethod
    def loadFromFile(cls, file_path):
        path = Path(file_path)

        with path.open("rb") as file:
            container = pickle.load(file)

        if not isinstance(container, cls):
            raise TypeError("file does not contain a ResultContainer")

        return container

    def __len__(self):
        return len(self.results)

    def __iter__(self):
        return iter(self.results)

    def __getitem__(self, index):
        return self.results[index]
