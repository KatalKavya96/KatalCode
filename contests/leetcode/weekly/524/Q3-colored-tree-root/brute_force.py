"""Reference O(n^2) solution for LeetCode 4085."""

from collections import deque


COLOR_AFTER = {"R": "B", "B": "W", "W": "R"}


def find_colored_root_brute_force(edges: list[list[int]], colors: str) -> int:
    """Try every node as root and validate the rooted tree with BFS."""
    node_count = len(colors)
    adjacency = [[] for _ in range(node_count)]
    for first, second in edges:
        adjacency[first].append(second)
        adjacency[second].append(first)

    for root in range(node_count):
        # This state belongs to one candidate root and must not leak into the
        # next attempt.
        visited = [False] * node_count
        visited[root] = True
        queue = deque([(root, colors[root])])
        valid = True

        while queue and valid:
            node, expected_color = queue.popleft()
            if colors[node] != expected_color:
                valid = False
                break

            child_count = 0
            for neighbor in adjacency[node]:
                if visited[neighbor]:
                    continue
                visited[neighbor] = True
                child_count += 1
                queue.append((neighbor, COLOR_AFTER[expected_color]))

            if child_count > 2:
                valid = False

        if valid:
            return root

    return -1


class Solution:
    """LeetCode-compatible wrapper around the teaching implementation."""

    def findColoredRoot(self, edges: list[list[int]], colors: str) -> int:
        return find_colored_root_brute_force(edges, colors)
