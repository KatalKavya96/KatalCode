#!/usr/bin/env python3
"""Run repository syntax, tests, links, frontend, and publication checks."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StrictEnoughHTMLParser(HTMLParser):
    """Parse HTML to catch gross tokenization errors using the standard library."""


def run(command: list[str], cwd: Path = ROOT) -> None:
    print("+", " ".join(command))
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    subprocess.run(command, cwd=cwd, env=environment, check=True)


def validate_python_syntax() -> None:
    files = sorted(
        path for path in ROOT.rglob("*.py")
        if ".git" not in path.parts and "build" not in path.parts
    )
    for path in files:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    print(f"Compiled {len(files)} Python sources in memory")


def run_tests() -> None:
    tests = sorted(ROOT.glob("**/tests.py"))
    for test_file in tests:
        run([sys.executable, test_file.name, "-v"], cwd=test_file.parent)
    print(f"Ran {len(tests)} test modules")


def validate_frontend() -> None:
    run([sys.executable, str(ROOT / "scripts" / "build_solution_sources.py"), "--check"])
    parser = StrictEnoughHTMLParser()
    parser.feed((ROOT / "dist" / "index.html").read_text(encoding="utf-8"))
    required = (ROOT / "dist" / "styles.css", ROOT / "dist" / "app.js")
    if not all(path.is_file() and path.stat().st_size for path in required):
        raise RuntimeError("Frontend assets are missing or empty")
    node = shutil.which("node")
    if node:
        for script in sorted((ROOT / "dist").glob("*.js")):
            run([node, "--check", str(script)])
    print("Parsed frontend entry point and checked static assets")


def validate_publications() -> None:
    sources = sorted(ROOT.glob("contests/**/metadata.yaml"))
    with tempfile.TemporaryDirectory(prefix="katalcode-publications-") as temporary:
        temporary_path = Path(temporary)
        for metadata in sources:
            source = metadata.parent / "README.md"
            output = temporary_path / f"{metadata.parent.name}.md"
            run([sys.executable, str(ROOT / "scripts" / "generate_publication.py"), str(source), "--output", str(output)])
            content = output.read_text(encoding="utf-8")
            if "raw.githubusercontent.com" not in content:
                raise RuntimeError(f"Publication has no public image URL: {source}")
            if "```mermaid" in content:
                raise RuntimeError(f"Publication still contains Mermaid: {source}")
    print(f"Generated {len(sources)} publication previews")


def main() -> int:
    validate_python_syntax()
    run_tests()
    run([sys.executable, str(ROOT / "scripts" / "check_links.py")])
    run([sys.executable, str(ROOT / "scripts" / "update_indexes.py"), "--check"])
    validate_frontend()
    validate_publications()
    print("All repository checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
