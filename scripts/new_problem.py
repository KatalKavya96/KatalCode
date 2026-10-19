#!/usr/bin/env python3
"""Create a problem editorial, solution, tests, metadata, and asset folder."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parent", help="Repository-relative parent directory")
    parser.add_argument("slug", help="Directory name, for example Q1-two-sum")
    parser.add_argument("title", help="Human-readable problem title")
    parser.add_argument("--platform", default="LeetCode")
    parser.add_argument("--difficulty", default="Unrated")
    parser.add_argument("--topics", default="Add topics")
    parser.add_argument("--problem-id", default="TBD")
    parser.add_argument("--problem-url", default="#")
    return parser.parse_args()


def safe_destination(parent: str, slug: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", slug):
        raise SystemExit("Slug may contain only letters, digits, dots, underscores, and hyphens.")
    destination = (ROOT / parent / slug).resolve()
    if ROOT not in destination.parents:
        raise SystemExit("Destination must stay inside the repository.")
    if destination.exists():
        raise SystemExit(f"Refusing to overwrite existing directory: {destination.relative_to(ROOT)}")
    return destination


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{ " + key + " }}", value)
    return template


def main() -> int:
    args = parse_args()
    destination = safe_destination(args.parent, args.slug)
    (destination / "assets").mkdir(parents=True)

    values = {
        "title": args.title,
        "platform": args.platform,
        "difficulty": args.difficulty,
        "topics": args.topics,
        "problem_id": args.problem_id,
        "problem_url": args.problem_url,
        "contest_type": "TBD",
        "contest_id": "TBD",
    }
    editorial = render((ROOT / "templates" / "editorial.md").read_text(encoding="utf-8"), values)
    metadata = render((ROOT / "templates" / "problem-metadata.yaml").read_text(encoding="utf-8"), values)
    (destination / "README.md").write_text(editorial, encoding="utf-8")
    (destination / "metadata.yaml").write_text(metadata, encoding="utf-8")
    (destination / "solution.py").write_text(
        '"""Solution for ' + args.title.replace('"', "'") + '."""\n\n\nclass Solution:\n    pass\n',
        encoding="utf-8",
    )
    (destination / "tests.py").write_text(
        '"""Tests for ' + args.title.replace('"', "'") + '."""\n\nimport unittest\n\n\nclass SolutionTests(unittest.TestCase):\n    @unittest.skip("Add representative cases")\n    def test_placeholder(self) -> None:\n        self.fail("Replace this placeholder")\n\n\nif __name__ == "__main__":\n    unittest.main()\n',
        encoding="utf-8",
    )
    (destination / "assets" / "diagram.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="240" viewBox="0 0 640 240" role="img" aria-labelledby="title desc">\n'
        '  <title id="title">Editorial diagram placeholder</title>\n'
        '  <desc id="desc">Replace this placeholder with a diagram that explains algorithm state.</desc>\n'
        '  <rect width="640" height="240" rx="20" fill="#f8fafc"/>\n'
        '  <rect x="40" y="40" width="560" height="160" rx="16" fill="none" stroke="#334155" stroke-width="3" stroke-dasharray="10 8"/>\n'
        '  <text x="320" y="125" text-anchor="middle" font-family="system-ui, sans-serif" font-size="22" fill="#334155">Replace with a teaching visual</text>\n'
        '</svg>\n',
        encoding="utf-8",
    )
    print(f"Created {destination.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
