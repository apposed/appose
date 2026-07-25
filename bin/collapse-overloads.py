#!/usr/bin/env python3
"""
Collapse overload families in API stub files to their minimal- and
maximal-arity signatures.

The postprocess-api.py expansion turns each optional/default parameter into
the full power set of signatures, to mirror the way Java exposes overloads.
When two implementations do not declare exactly the same overload subset,
this produces large combinatorial diffs that are pure noise (e.g. process.run,
Task.__init__, TaskEvent.__init__, Task.update).

For cross-implementation comparison, only the endpoints matter: the simplest
call (fewest parameters) and the fullest call (most parameters). This script
keeps, for each group of same-named "def" signatures in the same class scope,
only the lines whose parameter count equals the group minimum or maximum. All
other lines pass through untouched and original ordering is preserved.

Usage:
    collapse-overloads.py <api-directory>
"""

import sys
from pathlib import Path


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def param_count(line: str) -> int:
    """Count parameters in a 'def name(...)' line, ignoring 'self'."""
    open_paren = line.find("(")
    if open_paren < 0:
        return 0
    # Find the matching close paren for the parameter list.
    depth = 0
    close_paren = -1
    for i in range(open_paren, len(line)):
        c = line[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                close_paren = i
                break
    if close_paren < 0:
        return 0
    params_str = line[open_paren + 1 : close_paren].strip()
    if not params_str:
        return 0
    # Split on top-level commas.
    params = []
    depth = 0
    current = []
    for c in params_str:
        if c in "[(":
            depth += 1
        elif c in "])":
            depth -= 1
        if c == "," and depth == 0:
            params.append("".join(current).strip())
            current = []
        else:
            current.append(c)
    if current:
        params.append("".join(current).strip())
    return sum(1 for p in params if p and p != "self")


def def_name(line: str) -> str:
    s = line.lstrip()
    rest = s[len("def ") :]
    paren = rest.find("(")
    return rest[:paren].strip() if paren >= 0 else rest.strip()


def scope_key(lines, idx: int) -> str:
    """Identify the enclosing class for the def at lines[idx] (or 'module')."""
    my_indent = indent_of(lines[idx])
    for j in range(idx - 1, -1, -1):
        prev = lines[j]
        if not prev.strip():
            continue
        if prev.lstrip().startswith("class ") and indent_of(prev) < my_indent:
            return f"{indent_of(prev)}:{prev.strip()}"
    return "module"


def process_file(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()

    # First pass: compute min/max param count per (scope, name) group.
    bounds: dict[tuple[str, str], list[int]] = {}
    for idx, line in enumerate(lines):
        if line.lstrip().startswith("def "):
            key = (scope_key(lines, idx), def_name(line))
            n = param_count(line)
            if key not in bounds:
                bounds[key] = [n, n]
            else:
                bounds[key][0] = min(bounds[key][0], n)
                bounds[key][1] = max(bounds[key][1], n)

    # Second pass: keep only endpoint signatures for each group.
    out = []
    for idx, line in enumerate(lines):
        if line.lstrip().startswith("def "):
            key = (scope_key(lines, idx), def_name(line))
            lo, hi = bounds[key]
            n = param_count(line)
            if n != lo and n != hi:
                continue
        out.append(line)

    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: collapse-overloads.py <api-directory>", file=sys.stderr)
        sys.exit(1)
    api_dir = Path(sys.argv[1])
    for api_file in api_dir.rglob("*.api"):
        process_file(api_file)


if __name__ == "__main__":
    main()
