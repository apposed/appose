"""
Shared helpers for the API stub postprocessing scripts: parsing a stub file
into a tree of lines by indentation, and splitting parameter lists.
"""


class Node:
    def __init__(self, line: str, children: list["Node"] | None = None):
        self.line = line
        self.children = children or []

    @property
    def indent(self) -> str:
        return self.line[: len(self.line) - len(self.line.lstrip(" "))]


def parse(text: str) -> list[Node]:
    """Parse stub text into a forest of nodes, nesting lines by indentation."""
    roots: list[Node] = []
    stack: list[tuple[int, Node]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        node = Node(line)
        depth = len(node.indent)
        while stack and stack[-1][0] >= depth:
            stack.pop()
        (stack[-1][1].children if stack else roots).append(node)
        stack.append((depth, node))
    return roots


def render(nodes: list[Node]) -> str:
    lines: list[str] = []

    def walk(ns: list[Node]) -> None:
        for n in ns:
            lines.append(n.line)
            walk(n.children)

    walk(nodes)
    return "\n".join(lines) + "\n" if lines else ""


def split_params(params_str: str) -> list[str]:
    """Split a parameter list on top-level commas."""
    params, current, depth = [], [], 0
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
    if "".join(current).strip():
        params.append("".join(current).strip())
    return params
