# Editorial guidelines

## Reader promise

Write for a learner who understands basic data structures but has not yet seen the key observation. Be friendly without hiding technical details. Use original language and do not reproduce a platform's statement at length.

## Required narrative

Each complete problem editorial should include:

1. Problem overview in our own words
2. Intuition and first thoughts
3. Brute-force code and explanation
4. The brute-force bottleneck
5. Key observation
6. Optimized approach, step by step
7. A teaching visual when it adds clarity
8. Detailed dry run with intermediate state
9. Final accepted Python 3 code
10. Time-complexity derivation
11. Space-complexity derivation
12. Edge cases and common mistakes
13. FAQ and conceptual clarifications
14. Reusable patterns and takeaways
15. The command for producing a publication-ready version

If a truly separate brute force does not exist, explain why the direct method is already optimal and show the most literal inefficient representation before improving it.

## Visuals

- Put local assets in the problem's `assets/` directory.
- Prefer SVG for diagrams: it is sharp, accessible, diffable, and small.
- Give every SVG a `<title>` and `<desc>`.
- Keep labels readable on a narrow screen and never encode meaning by color alone.
- A Mermaid diagram that must publish outside GitHub needs a checked-in fallback:

  ````markdown
  <!-- publication-image: assets/example.svg -->
  ```mermaid
  flowchart LR
      A --> B
  ```

  ![Explanation of the same diagram](./assets/example.svg)
  ````

  The publication generator removes the Mermaid block and keeps one public image.

## Code

- Match the target platform's signature in `solution.py`.
- Keep teaching/reference implementations in clearly named files such as `brute_force.py`.
- Use type hints supported by the platform's current Python 3 runtime.
- Test examples, smallest inputs, structural edge cases, and the failure mode that motivated the optimization.
- Differentially test brute-force and optimized solutions when practical.

## Canonical source and publication

The problem README is canonical. Do not maintain a second hand-edited LeetCode copy. Run:

```bash
python3 scripts/generate_publication.py path/to/problem/README.md
```

Generated files belong in `build/publications/` and are ignored by Git. The generator rewrites local images to raw GitHub URLs and local repository links to GitHub blob URLs.
