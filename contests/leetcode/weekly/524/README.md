# LeetCode Weekly Contest 524

Held on October 18, 2026.

This first KatalCode contest chapter focuses on how a literal simulation reveals a better state representation, and how repeated BFS validation can collapse into one edge-orientation pass.

| Problem | Difficulty | Pattern | Code |
|---|---|---|---|
| [Q2 — Last Visited Cell in a Directional Grid](./Q2-last-visited-cell/) | Medium | Simulation, visited matrix | [`solution.py`](./Q2-last-visited-cell/solution.py) |
| [Q3 — Find Root of a Colored Tree](./Q3-colored-tree-root/) | Medium | Tree orientation, indegree | [`brute_force.py`](./Q3-colored-tree-root/brute_force.py) · [`solution.py`](./Q3-colored-tree-root/solution.py) |

## Run the tests

```bash
python3 -m unittest discover -s contests/leetcode/weekly/524/Q2-last-visited-cell -p 'tests.py' -v
python3 -m unittest discover -s contests/leetcode/weekly/524/Q3-colored-tree-root -p 'tests.py' -v
```

Or validate the whole repository with `python3 scripts/validate_repo.py`.
