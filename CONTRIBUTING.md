# Contributing to KatalCode

Thanks for helping make an explanation more accurate or easier to learn from.

## Principles

- Keep one canonical editorial per problem; topic pages should link to it.
- Explain the intuitive or brute-force route before the optimization.
- Derive complexity instead of stating it without justification.
- Use original wording and cite any external material that materially shaped an explanation.
- Add visuals only when they clarify state, structure, or transitions.
- Never commit copied contest solutions, credentials, generated caches, or personal data.

## Add a problem

```bash
python3 scripts/new_problem.py <parent-directory> <slug> "<Problem title>"
```

Complete every applicable section in the generated README, add executable code and tests, then link the editorial from relevant topic indexes.

## Validate a change

```bash
python3 scripts/validate_repo.py
```

The command compiles Python files, runs all `tests.py` files, checks local Markdown links and image references, and smoke-tests publication generation.

## Pull requests

Keep each pull request focused. Include:

- the problem or documentation area changed;
- the insight or correction being introduced;
- commands used to verify the change; and
- screenshots when the visual site changed.
