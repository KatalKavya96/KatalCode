# Learning and publishing workflow

## 1. Solve and preserve the reasoning

Record the first correct idea, including mistakes and uncertainty. A brute-force attempt is valuable evidence: it tells us what information matters and which work repeats.

## 2. Find the bottleneck

Name the expensive operation precisely. Replace “it is slow” with an operation count: repeated membership scans, a traversal per candidate, overlapping subproblems, or a state space that grows exponentially.

## 3. Extract the invariant

Ask what stays true after every transition, which choice is forced, and what earlier work can be reused. Turn the answer into both an optimization and a correctness argument.

## 4. Build the canonical editorial

Scaffold the directory:

```bash
python3 scripts/new_problem.py <parent> <slug> "<title>"
```

Write the README, executable implementations, tests, metadata, and focused visual assets together. Link topic indexes back to this one editorial.

## 5. Validate

```bash
python3 scripts/validate_repo.py
```

Fix code, tests, links, accessibility text, and publication errors before committing. For visual-site changes, also run `python3 -m http.server 8000 --directory dist` and test the narrow and wide layouts.

## 6. Commit with intent

A useful commit message explains the learning unit, for example:

```text
feat: add colored-tree orientation editorial
```

## 7. Publish without rewriting

Generate the platform copy from the canonical source:

```bash
python3 scripts/generate_publication.py path/to/problem/README.md
```

Review the generated Markdown in `build/publications/`, then paste it into LeetCode. Public raw-image URLs work after the corresponding source commit is pushed to GitHub.

## 8. Revisit by pattern

Link the editorial from every relevant topic page. Add a short note describing why it represents that pattern rather than duplicating code or prose.
