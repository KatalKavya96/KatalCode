<div align="center">

# KatalCode

### Think. Break. Optimize.

**DSA • Algorithms • LeetCode • Competitive Programming • Visual Editorials**

[Visual Lab](https://katalkavya96.github.io/KatalCode/) · [Contest archive](./contests/) · [Topic guides](./topics/) · [Editorial workflow](./docs/learning-workflow.md)

</div>

---

KatalCode is Kavya Katal's learning-first algorithm handbook: tested solutions paired with the intuition, failed attempts, bottlenecks, proofs, dry runs, and reusable patterns that make them useful long after submission day.

This repository favors understanding over answer collection. Every complete editorial moves through:

> **Intuition → Brute Force → Bottleneck → Optimization → Proof**

## Visual Lab

The [`dist/`](./dist/) site lets readers choose LeetCode, Codeforces, or CodeChef, then browse documented contests and questions. Questions include concise visual explanations and interactive simulations where available. The current archive has two questions from LeetCode Weekly Contest 524; empty platform archives are shown honestly rather than listing undocumented contests.

Run it locally with no dependencies:

```bash
python3 -m http.server 8000 --directory dist
```

Then open `http://localhost:8000`. GitHub Pages publishes `dist/`. For Vercel, import this repository with the repository root as the Root Directory; [`vercel.json`](./vercel.json) selects the static `dist/` output and the Other framework preset. No build command is needed.

Solutions open as a phone- and tablet-friendly book: problem, approach, explained Python source pages, simulation, and proof. Previous/Next controls and the contents menu navigate the pages; the URL preserves the current page. The source pages use the actual solution files. After editing a solution, refresh the static source bundle with `python3 scripts/build_solution_sources.py`; repository validation checks that it stays current.

## Featured visual editorials

<!-- INDEX:START -->
| Problem | Core pattern | Solutions |
|---|---|---|
| [4084 — Last Visited Cell in a Directional Grid](./contests/leetcode/weekly/524/Q2-last-visited-cell/README.md) | Simulation, Matrix | [`Optimized`](./contests/leetcode/weekly/524/Q2-last-visited-cell/solution.py) |
| [4085 — Find Root of a Colored Tree](./contests/leetcode/weekly/524/Q3-colored-tree-root/README.md) | Trees, Graph Orientation, Indegree, Bfs | [`Brute force`](./contests/leetcode/weekly/524/Q3-colored-tree-root/brute_force.py) · [`Optimized`](./contests/leetcode/weekly/524/Q3-colored-tree-root/solution.py) |
<!-- INDEX:END -->

## Repository map

```text
KatalCode/
├── contests/              # Contest-first archive: LeetCode, Codeforces, CodeChef
├── problems/              # Non-contest problems grouped by platform and difficulty
├── topics/                # Pattern indexes pointing to canonical editorials
├── templates/             # Editorial, contest, and metadata starters
├── scripts/               # Scaffolding, validation, indexing, and publication tools
├── docs/                  # Writing standards and learning workflow
├── dist/                  # Interactive visual learning site
└── .github/workflows/     # Continuous validation and GitHub Pages deployment
```

Start with [Weekly Contest 524](./contests/leetcode/weekly/524/README.md), browse by [topic](./topics/), or use the [repository workflow](./docs/learning-workflow.md) to add a solution.

## Browse by source

| Source | Weekly | Biweekly / Other |
|---|---|---|
| LeetCode | [Weekly contests](./contests/leetcode/weekly/) | [Biweekly contests](./contests/leetcode/biweekly/) |
| Codeforces | [Contest archive](./contests/codeforces/) | — |
| CodeChef | [Contest archive](./contests/codechef/) | — |

Non-contest LeetCode practice: [Easy](./problems/leetcode/easy/) · [Medium](./problems/leetcode/medium/) · [Hard](./problems/leetcode/hard/)

## Browse by topic

[Arrays](./topics/arrays/) · [Binary Search](./topics/binary-search/) · [Graphs](./topics/graphs/) · [Trees](./topics/trees/) · [Dynamic Programming](./topics/dynamic-programming/) · [Greedy](./topics/greedy/) · [Strings](./topics/strings/)

Topic pages link to one canonical problem editorial rather than copying the solution.

## Build and publish once

The repository keeps each source editorial canonical. Create a LeetCode-ready version with rewritten public image URLs:

```bash
python3 scripts/generate_publication.py \
  contests/leetcode/weekly/524/Q3-colored-tree-root/README.md
```

Pre-rendered SVGs marked with `publication-image` replace Mermaid blocks for publishing targets that cannot render Mermaid. See the [editorial guidelines](./docs/editorial-guidelines.md).

## Lightweight tooling

```bash
# Create a contest folder
python3 scripts/new_contest.py leetcode weekly 525

# Create a problem from the standard template
python3 scripts/new_problem.py contests/leetcode/weekly/525 Q1-example "Example Problem"

# Refresh the generated featured-editorials table
python3 scripts/update_indexes.py

# Run syntax checks, unit tests, link checks, and publication smoke tests
python3 scripts/validate_repo.py
```

The tools use only the Python standard library.

## Profiles

- [GitHub — KatalKavya96](https://github.com/KatalKavya96)
- [LeetCode — KavyaKatal96](https://leetcode.com/u/KavyaKatal96/)
- [Codeforces](https://codeforces.com/) — profile handle not added until verified
- [CodeChef](https://www.codechef.com/) — profile handle not added until verified

No rankings or activity statistics are mirrored here; the linked platforms remain the source of truth.

## Contributing

This is a personal learning archive, but corrections and clearer explanations are welcome. Read [`CONTRIBUTING.md`](./CONTRIBUTING.md) before opening a change.

## License

Code and original documentation are available under the [MIT License](./LICENSE).
