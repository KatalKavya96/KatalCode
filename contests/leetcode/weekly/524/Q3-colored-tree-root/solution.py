"""O(n) solution for LeetCode 4085: Find Root of a Colored Tree."""


COLOR_AFTER = {"R": "B", "B": "W", "W": "R"}


def find_colored_root(edges: list[list[int]], colors: str) -> int:
    """Orient color-compatible edges and return the unique indegree-zero node."""
    node_count = len(colors)
    indegree = [0] * node_count
    degree = [0] * node_count

    for first, second in edges:
        degree[first] += 1
        degree[second] += 1

        if COLOR_AFTER[colors[first]] == colors[second]:
            indegree[second] += 1
        elif COLOR_AFTER[colors[second]] == colors[first]:
            indegree[first] += 1
        else:
            # Equal-colored endpoints can never occupy adjacent depths.
            return -1

    roots = [node for node, incoming in enumerate(indegree) if incoming == 0]
    if len(roots) != 1:
        return -1

    root = roots[0]
    if degree[root] > 2:
        return -1
    if any(indegree[node] != 1 for node in range(node_count) if node != root):
        return -1

    return root


class Solution:
    """LeetCode-compatible entry point."""

    def findColoredRoot(self, edges: list[list[int]], colors: str) -> int:
        return find_colored_root(edges, colors)
