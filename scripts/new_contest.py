#!/usr/bin/env python3
"""Create a contest directory from the repository template."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", choices=("leetcode", "codeforces", "codechef"))
    parser.add_argument("contest_type", help="For example: weekly, biweekly, round, starters")
    parser.add_argument("contest_id", help="Platform contest number or code")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.platform == "leetcode":
        destination = ROOT / "contests" / args.platform / args.contest_type / args.contest_id
    else:
        destination = ROOT / "contests" / args.platform / args.contest_id

    if destination.exists():
        raise SystemExit(f"Refusing to overwrite existing directory: {destination.relative_to(ROOT)}")

    destination.mkdir(parents=True)
    template = (ROOT / "templates" / "contest-readme.md").read_text(encoding="utf-8")
    rendered = (
        template.replace("{{ platform }}", args.platform.title())
        .replace("{{ contest_type }}", args.contest_type.title())
        .replace("{{ contest_id }}", args.contest_id)
    )
    (destination / "README.md").write_text(rendered, encoding="utf-8")
    print(f"Created {destination.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
