#!/usr/bin/env python3
"""Refresh the generated featured-editorials table in the root README."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
START = "<!-- INDEX:START -->"
END = "<!-- INDEX:END -->"


def scalar(metadata: str, key: str, default: str = "—") -> str:
    match = re.search(rf"^{re.escape(key)}:\s*[\"']?(.+?)[\"']?\s*$", metadata, re.MULTILINE)
    return match.group(1).strip('"\'') if match else default


def topics(metadata: str) -> str:
    match = re.search(r"^topics:\s*\[(.*?)\]\s*$", metadata, re.MULTILINE)
    if not match:
        return "—"
    return ", ".join(item.strip().replace("-", " ").title() for item in match.group(1).split(","))


def build_table() -> str:
    rows = ["| Problem | Core pattern | Solutions |", "|---|---|---|"]
    for metadata_path in sorted(ROOT.glob("contests/**/metadata.yaml")):
        problem_dir = metadata_path.parent
        metadata = metadata_path.read_text(encoding="utf-8")
        title = scalar(metadata, "title")
        problem_id = scalar(metadata, "problem_id")
        relative = problem_dir.relative_to(ROOT).as_posix()
        links = []
        if (problem_dir / "brute_force.py").exists():
            links.append(f"[`Brute force`](./{relative}/brute_force.py)")
        if (problem_dir / "solution.py").exists():
            links.append(f"[`Optimized`](./{relative}/solution.py)")
        rows.append(f"| [{problem_id} — {title}](./{relative}/README.md) | {topics(metadata)} | {' · '.join(links)} |")
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail instead of rewriting a stale index")
    args = parser.parse_args()

    readme_path = ROOT / "README.md"
    original = readme_path.read_text(encoding="utf-8")
    if START not in original or END not in original:
        raise SystemExit("README.md is missing index markers")
    before, remainder = original.split(START, 1)
    _, after = remainder.split(END, 1)
    updated = f"{before}{START}\n{build_table()}\n{END}{after}"

    if updated == original:
        print("README index is current")
        return 0
    if args.check:
        print("README index is stale; run python3 scripts/update_indexes.py")
        return 1
    readme_path.write_text(updated, encoding="utf-8")
    print("Updated README index")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
