#!/usr/bin/env python3
"""
Structurally normalize API stub files for cross-implementation comparison.

Where the sed rules in align.sh rewrite lines in isolation, this script
handles the language idioms that need context, i.e. knowledge of which class
a line belongs to:

* Decorators (@overload, @property, @staticmethod, @dataclass, ...) are
  dropped; the signatures they decorate carry the comparable information.
* "-> Self" is replaced by the enclosing class name, as Java spells it.
* Parameters and return values that stubgen could not infer are typed Any.
* Static methods and class methods are hoisted out of their class to module
  level. Python favors module-level functions where Java must use static
  methods, so where a helper lives is an implementation detail.
* Public fields become accessor methods: Python exposes attributes (e.g.
  ndarray.shape, task.outputs) where Java exposes fields or accessors (e.g.
  ndarray.shape(), task.outputs), so "name: T" becomes "def name(self) -> T".
  Private fields and ALL_CAPS constants are left alone (align.sh drops them).
* Varargs parameters move to the end of the parameter list, as Java requires
  (Python's def exec(self, *args, cwd=None) is Java's exec(cwd, args...)).
  And because varargs may be empty, a signature ending in varargs is also
  emitted without them, as Java often declares that overload explicitly.
* With --public, private members (a single leading underscore) are dropped,
  along with private classes and everything in them, to compare only the
  public API.

Usage:
    normalize-api.py [--public] <api-directory>
"""

import re
import sys
from pathlib import Path

from apitree import Node, parse, render, split_params

DEF_RE = re.compile(r"^(\s*)((?:abstract )?def )(\w+)\((.*)\)( -> .*)?(: \.\.\.)$")
FIELD_RE = re.compile(r"^(\s*)([A-Za-z_]\w*): (.+)$")
CLASS_RE = re.compile(r"^\s*class (\w+)")


def is_private(name: str) -> bool:
    return name.startswith("_") and not name.startswith("__")


def is_constant(name: str) -> bool:
    return name.upper() == name and any(c.isalpha() for c in name)


def reorder_varargs(params: list[str]) -> list[str]:
    """Move a *args parameter to the end of the list."""
    varargs = [p for p in params if p.startswith("*") and not p.startswith("**")]
    if not varargs or params[-1] == varargs[-1]:
        return params
    rest = [p for p in params if p not in varargs]
    kwargs = [p for p in rest if p.startswith("**")]
    rest = [p for p in rest if not p.startswith("**")]
    return rest + varargs + kwargs


def normalize_def(line: str, class_name: str | None) -> tuple[list[str], bool]:
    """
    Normalize one def line. Returns the resulting def lines (without
    indentation) and whether the def is static (no self parameter).
    """
    m = DEF_RE.match(line)
    if not m:
        return [line.strip()], False
    _, kw, name, params_str, ret, tail = m.groups()
    ret = ret or ""
    params = [p for p in split_params(params_str) if p not in ("*", "/")]

    # Class methods are static methods by another name.
    if params and params[0] == "cls":
        params = params[1:]
        static = True
    else:
        static = class_name is not None and (not params or params[0] != "self")

    # Note: stubgen omits annotations it cannot infer; those mean Any.
    params = [
        p if ":" in p or "=" in p or p == "self" or p.startswith("*") else f"{p}: Any"
        for p in params
    ]
    if not ret and name != "__init__":
        ret = " -> Any"

    if class_name:
        ret = re.sub(r"\bSelf\b", class_name, ret)

    params = reorder_varargs(params)
    variants = [params]
    last = params[-1] if params else ""
    if last.startswith("*") and not last.startswith("**"):
        variants.insert(0, params[:-1])

    if static and class_name:
        kw = kw.replace("abstract ", "")
    lines = [f"{kw}{name}({', '.join(v)}){ret}{tail}" for v in variants]
    return lines, static


def normalize_class(node: Node, public_only: bool) -> list[Node]:
    """Normalize a class node; returns it plus any hoisted static functions."""
    class_name = CLASS_RE.match(node.line).group(1)
    if "(unittest.TestCase)" in node.line:
        # Note: Test classes are dumped as module-level functions, as pytest
        # spells them, regardless of the framework.
        return [
            Node(line)
            for c in node.children
            if c.line.strip().startswith("def test")
            for line in normalize_def(re.sub(r"\(self(, )?", "(", c.line.strip()), None)[0]
        ]
    hoisted = []
    children = []
    for child in node.children:
        stripped = child.line.strip()
        if stripped.startswith("@"):
            continue
        if CLASS_RE.match(child.line):
            if public_only and is_private(CLASS_RE.match(child.line).group(1)):
                continue
            children.extend(normalize_class(child, public_only))
            continue
        m = DEF_RE.match(child.line)
        if m:
            if public_only and is_private(m.group(3)):
                continue
            lines, static = normalize_def(child.line, class_name)
            if static:
                hoisted.extend(Node(line) for line in lines)
            else:
                children.extend(Node(child.indent + line) for line in lines)
            continue
        m = FIELD_RE.match(child.line)
        if m and not is_private(m.group(2)) and not is_constant(m.group(2)):
            # Note: Dataclass fields with defaults read "name: T = ...".
            name, ftype = m.group(2), re.sub(r" = .*$", "", m.group(3))
            children.append(Node(f"{child.indent}def {name}(self) -> {ftype}: ..."))
            continue
        if m and public_only and is_private(m.group(2)):
            continue
        children.append(child)
    node.children = children
    return [node] + hoisted


def normalize_file(path: Path, public_only: bool) -> None:
    out = []
    for node in parse(path.read_text(encoding="utf-8")):
        stripped = node.line.strip()
        if stripped.startswith("@"):
            continue
        if CLASS_RE.match(node.line):
            if public_only and is_private(CLASS_RE.match(node.line).group(1)):
                continue
            out.extend(normalize_class(node, public_only))
            continue
        m = DEF_RE.match(node.line)
        if m:
            if public_only and is_private(m.group(3)):
                continue
            out.extend(Node(line) for line in normalize_def(node.line, None)[0])
            continue
        m = FIELD_RE.match(node.line)
        if m and public_only and is_private(m.group(2)):
            continue
        out.append(node)
    path.write_text(render(out), encoding="utf-8")


def main() -> None:
    args = sys.argv[1:]
    public_only = "--public" in args
    args = [a for a in args if a != "--public"]
    if len(args) != 1:
        print("Usage: normalize-api.py [--public] <api-directory>", file=sys.stderr)
        sys.exit(1)
    for api_file in Path(args[0]).rglob("*.api"):
        normalize_file(api_file, public_only)


if __name__ == "__main__":
    main()
