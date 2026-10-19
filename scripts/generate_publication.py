#!/usr/bin/env python3
"""Generate copy-ready Markdown with public GitHub asset and source links."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import quote, unquote


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OWNER = "KatalKavya96"
DEFAULT_REPOSITORY = "KatalCode"

MARKDOWN_LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\)")
PUBLISH_MERMAID = re.compile(
    r"<!--\s*publication-image:\s*(?P<path>[^\s]+)\s*-->\s*```mermaid\s*.*?```",
    re.DOTALL,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Canonical problem README")
    parser.add_argument("--output", type=Path, help="Output path; defaults to build/publications/<problem>.md")
    parser.add_argument("--owner", default=DEFAULT_OWNER)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--ref", default="main", help="Git ref used in public URLs")
    parser.add_argument("--stdout", action="store_true", help="Print instead of writing a file")
    return parser.parse_args()


def repository_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError as error:
        raise SystemExit(f"Path must stay inside {ROOT}") from error


def convert_target(
    target: str,
    source_dir: Path,
    is_image: bool,
    owner: str,
    repository: str,
    ref: str,
) -> str:
    if target.startswith(("http://", "https://", "mailto:", "#", "data:")):
        return target
    clean_target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    absolute = (source_dir / clean_target).resolve()
    relative = repository_relative(absolute)
    encoded = quote(relative, safe="/")
    if is_image:
        return f"https://raw.githubusercontent.com/{owner}/{repository}/{ref}/{encoded}"
    return f"https://github.com/{owner}/{repository}/blob/{ref}/{encoded}"


def collapse_duplicate_images(markdown: str) -> str:
    output: list[str] = []
    previous_image_target: str | None = None
    blanks_after_image: list[str] = []
    image_line = re.compile(r"^!\[[^\]]*\]\(([^)]+)\)\s*$")

    for line in markdown.splitlines():
        match = image_line.match(line)
        if not line.strip() and previous_image_target:
            blanks_after_image.append(line)
            continue
        if match and match.group(1) == previous_image_target:
            blanks_after_image.clear()
            continue
        output.extend(blanks_after_image)
        blanks_after_image.clear()
        output.append(line)
        previous_image_target = match.group(1) if match else None
    output.extend(blanks_after_image)
    return "\n".join(output) + "\n"


def generate(source: Path, owner: str, repository: str, ref: str) -> str:
    source = source.resolve()
    if not source.is_file():
        raise SystemExit(f"Source does not exist: {source}")
    repository_relative(source)
    markdown = source.read_text(encoding="utf-8")

    # The source keeps the authoring command; the generated post does not need it.
    markdown = re.split(r"^## LeetCode-ready version\s*$", markdown, maxsplit=1, flags=re.MULTILINE)[0].rstrip()
    markdown = PUBLISH_MERMAID.sub(lambda match: f"![Algorithm diagram]({match.group('path')})", markdown)

    def replace_link(match: re.Match[str]) -> str:
        marker, label, target = match.groups()
        converted = convert_target(target, source.parent, marker == "!", owner, repository, ref)
        return f"{marker}[{label}]({converted})"

    markdown = MARKDOWN_LINK.sub(replace_link, markdown)
    generated_note = (
        "<!-- Generated from the canonical KatalCode editorial. "
        "Edit the source README, not this publication copy. -->\n\n"
    )
    return generated_note + collapse_duplicate_images(markdown)


def main() -> int:
    args = parse_args()
    content = generate(args.source, args.owner, args.repository, args.ref)
    if args.stdout:
        print(content, end="")
        return 0

    output = args.output
    if output is None:
        output = ROOT / "build" / "publications" / f"{args.source.resolve().parent.name}.md"
    elif not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"Generated {output.relative_to(ROOT) if ROOT in output.resolve().parents else output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
