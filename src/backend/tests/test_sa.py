import unittest
from math import exp
from unittest.mock import patch

from ..algorithm.sa import simulated_annealing
from ..core import (
    Dimensions,
    Orientation,
    Package,
    Placement,
    Position,
    Problem,
    State,
    Truck,
    move,
)


class SimulatedAnnealingStuckMetricTest(unittest.TestCase):
    def setUp(self):
        self.truck = Truck("T1", Dimensions(2, 1, 1), 100)
        self.low = Package("low", Dimensions(1, 1, 1), 1, 1, False, 1)

    def run_rejected_move(self, problem, state):
        worse_neighbor = move(problem, state, "low", None, None)

        with patch(
            "src.backend.algorithm.sa.generate_random_neighbor",
            return_value=worse_neighbor,
        ):
            return simulated_annealing(
                problem,
                state,
                max_iterations=1,
                seed=0,
                initial_temperature=0.1,
                cooling_rate=0.5,
                minimum_temperature=0.01,
            )

    def test_rejection_is_not_stuck_when_improving_neighbor_exists(self):
        high = Package("high", Dimensions(1, 1, 1), 10, 1, False, 1)
        problem = Problem([self.truck], [self.low, high])
        state = State(
            [
                Placement(
                    "low",
                    Position(0, 0, 0),
                    Orientation.WLH,
                    "T1",
                ),
                Placement("high"),
            ]
        )

        result = self.run_rejected_move(problem, state)

        self.assertEqual(result.metrics["rejection_rate"], 1.0)
        self.assertFalse(result.metrics["stuck_at_local_optimum"])
        self.assertEqual(result.metrics["stuck_frequency"], 0.0)

    def test_rejection_is_stuck_at_true_local_optimum(self):
        problem = Problem([self.truck], [self.low])
        state = State(
            [
                Placement(
                    "low",
                    Position(0, 0, 0),
                    Orientation.WLH,
                    "T1",
                )
            ]
        )

        result = self.run_rejected_move(problem, state)

        self.assertEqual(result.metrics["rejection_rate"], 1.0)
        self.assertTrue(result.metrics["stuck_at_local_optimum"])
        self.assertEqual(result.metrics["stuck_frequency"], 1.0)

    def test_worse_move_uses_exponential_acceptance_probability(self):
        problem = Problem([self.truck], [self.low])
        state = State(
            [
                Placement(
                    "low",
                    Position(0, 0, 0),
                    Orientation.WLH,
                    "T1",
                )
            ]
        )
        worse_neighbor = move(problem, state, "low", None, None)

        with patch(
            "src.backend.algorithm.sa.generate_random_neighbor",
            return_value=worse_neighbor,
        ):
            result = simulated_annealing(
                problem,
                state,
                max_iterations=1,
                seed=0,
                initial_temperature=10,
                cooling_rate=0.5,
                minimum_temperature=0.01,
            )

        probability = result.metrics["acceptance_probability_history"][0]
        self.assertAlmostEqual(probability, exp(-1 / 10))
        self.assertEqual(result.metrics["accepted_worse_moves"], 1)
        self.assertEqual(result.final_value, 0)


if __name__ == "__main__":
    unittest.main()
