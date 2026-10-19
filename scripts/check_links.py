#!/usr/bin/env python3
"""Check repository-local Markdown links and image references."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\)")
SKIP_DIRECTORIES = {".git", "build", "templates"}


def markdown_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*.md")
        if not any(part in SKIP_DIRECTORIES for part in path.relative_to(ROOT).parts)
    ]


def main() -> int:
    failures: list[str] = []
    checked = 0
    for markdown in markdown_files():
        content = markdown.read_text(encoding="utf-8")
        fence: str | None = None
        for line_number, line in enumerate(content.splitlines(), start=1):
            stripped = line.lstrip()
            if stripped.startswith(("```", "~~~~")):
                marker = stripped[:3]
                if fence is None:
                    fence = marker
                elif marker == fence:
                    fence = None
                continue
            if fence is not None:
                continue
            for match in LINK.finditer(line):
                target = match.group(1)
                if target.startswith(("http://", "https://", "mailto:", "#", "data:")):
                    continue
                clean = unquote(target.split("#", 1)[0].split("?", 1)[0])
                if not clean or "{{" in clean:
                    continue
                checked += 1
                resolved = (markdown.parent / clean).resolve()
                try:
                    resolved.relative_to(ROOT)
                except ValueError:
                    failures.append(f"{markdown.relative_to(ROOT)}:{line_number}: escapes repository: {target}")
                    continue
                if not resolved.exists():
                    failures.append(f"{markdown.relative_to(ROOT)}:{line_number}: missing: {target}")

    if failures:
        print("Broken local links:")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print(f"Checked {checked} local Markdown links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
