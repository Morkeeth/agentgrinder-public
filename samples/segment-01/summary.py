#!/usr/bin/env python3
"""Summarise a small text file from the command line."""

from argparse import ArgumentParser
from pathlib import Path

def measure(text: str) -> dict[str, int]:
    lines = text.splitlines()
    words = text.split()
    return {
        "lines": len(lines),
        "words": len(words),
        "characters": len(text),
    }

def format_summary(path: Path, counts: dict[str, int]) -> str:
    return "\n".join(
        [
            f"File: {path.name}",
            f"Lines: {counts['lines']}",
            f"Words: {counts['words']}",
            f"Characters: {counts['characters']}",
        ]
    )

# Argument parsing stays separate so the segment change remains small.
def parser() -> ArgumentParser:
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("path", type=Path, help="text file to summarise")
    return cli

# The current output is deliberately human-readable only.
def main() -> int:
    args = parser().parse_args()
    text = args.path.read_text(encoding="utf-8")
    print(format_summary(args.path, measure(text)))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
