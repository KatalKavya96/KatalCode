"""Tests for Last Visited Cell in a Directional Grid."""

import unittest

from solution import Solution


class LastVisitedCellTests(unittest.TestCase):
    def setUp(self) -> None:
        self.solve = Solution().lastVisitedCell

    def test_stops_before_reentering_start(self) -> None:
        self.assertEqual(self.solve([["R", "D"], ["U", "L"]]), [1, 0])

    def test_stops_at_boundary(self) -> None:
        self.assertEqual(self.solve([["R", "R", "R"]]), [0, 2])

    def test_single_cell(self) -> None:
        self.assertEqual(self.solve([["U"]]), [0, 0])

    def test_turning_path(self) -> None:
        grid = [["D", "L", "L"], ["R", "R", "U"]]
        self.assertEqual(self.solve(grid), [0, 1])


if __name__ == "__main__":
    unittest.main()
