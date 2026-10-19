"""LeetCode 4084: Last Visited Cell in a Directional Grid."""


class Solution:
    """Simulate the path until the next move is invalid."""

    def lastVisitedCell(self, grid: list[list[str]]) -> list[int]:
        rows, cols = len(grid), len(grid[0])
        directions = {
            "L": (0, -1),
            "R": (0, 1),
            "U": (-1, 0),
            "D": (1, 0),
        }
        visited = [[False] * cols for _ in range(rows)]
        row = col = 0

        while True:
            visited[row][col] = True
            delta_row, delta_col = directions[grid[row][col]]
            next_row = row + delta_row
            next_col = col + delta_col

            if not (0 <= next_row < rows and 0 <= next_col < cols):
                return [row, col]
            if visited[next_row][next_col]:
                return [row, col]

            row, col = next_row, next_col
