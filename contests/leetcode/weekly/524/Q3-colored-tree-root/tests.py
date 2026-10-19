"""Tests and differential checks for both colored-tree implementations."""

import itertools
import random
import unittest

from brute_force import find_colored_root_brute_force
from solution import find_colored_root


class ColoredTreeRootTests(unittest.TestCase):
    def assert_agree(self, edges: list[list[int]], colors: str) -> None:
        self.assertEqual(
            find_colored_root(edges, colors),
            find_colored_root_brute_force(edges, colors),
        )

    def test_two_nodes(self) -> None:
        self.assertEqual(find_colored_root([[0, 1]], "RB"), 0)

    def test_balanced_binary_tree(self) -> None:
        edges = [[0, 1], [0, 2], [1, 3], [1, 4]]
        self.assertEqual(find_colored_root(edges, "RBBWW"), 0)

    def test_multiple_root_candidates_are_invalid(self) -> None:
        self.assertEqual(find_colored_root([[0, 1], [1, 2]], "RBR"), -1)

    def test_equal_colored_neighbors_are_invalid(self) -> None:
        self.assertEqual(find_colored_root([[0, 1]], "RR"), -1)

    def test_root_cannot_have_three_children(self) -> None:
        edges = [[0, 1], [0, 2], [0, 3]]
        self.assertEqual(find_colored_root(edges, "RBBB"), -1)

    def test_implementations_agree_exhaustively_on_small_paths(self) -> None:
        for node_count in range(2, 7):
            edges = [[node, node + 1] for node in range(node_count - 1)]
            for colors in map("".join, itertools.product("RBW", repeat=node_count)):
                self.assert_agree(edges, colors)

    def test_implementations_agree_on_random_degree_bounded_trees(self) -> None:
        randomizer = random.Random(524)
        checked = 0
        while checked < 150:
            node_count = randomizer.randint(2, 10)
            edges: list[list[int]] = []
            degree = [0] * node_count
            valid_tree = True
            for node in range(1, node_count):
                choices = [parent for parent in range(node) if degree[parent] < 3]
                if not choices:
                    valid_tree = False
                    break
                parent = randomizer.choice(choices)
                edges.append([parent, node])
                degree[parent] += 1
                degree[node] += 1
            if not valid_tree:
                continue
            colors = "".join(randomizer.choice("RBW") for _ in range(node_count))
            self.assert_agree(edges, colors)
            checked += 1


if __name__ == "__main__":
    unittest.main()
