#!/usr/bin/env python3
"""
Sort the members of API stub files into a canonical order.

The implementations declare the same functions, classes and methods in
different orders, which makes a line diff report each moved member as a
removal plus an addition. This script sorts module-level functions and
classes by name, and the methods of each class by name and then arity, so
that only real differences remain. Overloads of the same arity keep their
relative order, as do enum values, which come first in their class.

Normalization can make overloads identical (e.g. str and Path parameters both
become str), so duplicate members within the same scope are also dropped.

Usage:
    sort-api.py <api-directory>
"""

import re
import sys
from pathlib import Path

from apitree import Node, parse, render, split_params

NAME_RE = re.compile(r"^\s*(?:abstract )?(def|class) (\w+)(?:\((.*)\) ->)?")


def sort_key(node: Node) -> tuple[int, int, str, int]:
    m = NAME_RE.match(node.line)
    if not m:
        # Non-def lines (e.g. enum values) keep their place, ahead of the rest.
        return (0, 0, "", 0)
    kind, name, params = m.groups()
    dunder = name.startswith("__") and name.endswith("__")
    arity = len([p for p in split_params(params or "") if p != "self"])
    return (1 if kind == "def" else 2, 0 if dunder else 1, name.lstrip("_"), arity)


def sort_nodes(nodes: list[Node]) -> list[Node]:
    """Sort nodes recursively, dropping duplicate siblings."""
    seen: set[str] = set()
    unique = []
    for node in nodes:
        if node.line in seen and not node.children:
            continue
        seen.add(node.line)
        node.children = sort_nodes(node.children)
        unique.append(node)
    return sorted(unique, key=sort_key)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: sort-api.py <api-directory>", file=sys.stderr)
        sys.exit(1)
    for api_file in Path(sys.argv[1]).rglob("*.api"):
        nodes = parse(api_file.read_text(encoding="utf-8"))
        api_file.write_text(render(sort_nodes(nodes)), encoding="utf-8")


if __name__ == "__main__":
    main()
