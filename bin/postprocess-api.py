#!/usr/bin/env python3
"""
Post-processes API stub files for cross-implementation comparison.

This script performs two key transformations:
1. Normalizes '| None' unions to '?' nullable syntax (Kotlin/TypeScript-style)
2. Expands optional parameters (with default values) into all possible signatures

This makes it easier to compare APIs across Appose implementations (Java, Python, etc.)
despite their different conventions (Java uses overloads, Python uses default parameters).

Example transformations:
    Input:  def pixi(source: str | Path | None = None) -> PixiBuilder: ...

    After normalization:
            def pixi(source: str? | Path? = None) -> PixiBuilder: ...

    After expansion:
            def pixi() -> PixiBuilder: ...
            def pixi(source: str?) -> PixiBuilder: ...
            def pixi(source: Path?) -> PixiBuilder: ...

Usage:
    postprocess-api.py <api-directory>
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple
from itertools import product


def parse_parameter(param_str: str) -> Tuple[str, str, bool, bool]:
    """
    Parse a parameter string into its components.

    Returns:
        (name, type, has_default, is_varargs)
    """
    param_str = param_str.strip()

    # Handle *args syntax
    is_varargs = param_str.startswith('*') and not param_str.startswith('**')
    if is_varargs:
        param_str = param_str[1:]

    # Split on = to detect default values
    has_default = '=' in param_str
    if has_default:
        param_str = param_str.split('=')[0].strip()

    # Split on : to get name and type
    if ':' in param_str:
        name, type_str = param_str.split(':', 1)
        return name.strip(), type_str.strip(), has_default, is_varargs
    else:
        # No type annotation (like 'self')
        return param_str.strip(), '', has_default, is_varargs


def split_union(type_str: str) -> List[str]:
    """
    Split a union type into its components, handling nested types.

    Example: 'str | Path | None' -> ['str', 'Path', 'None']
    Example: 'list[str] | dict[str, int]' -> ['list[str]', 'dict[str, int]']
    """
    if '|' not in type_str:
        return [type_str]

    # Track bracket depth to avoid splitting inside generic types
    parts = []
    current = []
    depth = 0

    for char in type_str:
        if char == '[':
            depth += 1
            current.append(char)
        elif char == ']':
            depth -= 1
            current.append(char)
        elif char == '|' and depth == 0:
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(char)

    if current:
        parts.append(''.join(current).strip())

    return parts


def expand_signature(line: str) -> List[str]:
    """
    Expand a function/method signature with union types into multiple signatures.

    Example:
        Input:  'def pixi(source: str | Path | None = None) -> PixiBuilder: ...'
        Output: ['def pixi() -> PixiBuilder: ...',
                 'def pixi(source: str) -> PixiBuilder: ...',
                 'def pixi(source: Path) -> PixiBuilder: ...']
    """
    # Check if this is a function/method definition
    if not line.strip().startswith('def '):
        return [line]

    # Extract function signature parts
    match = re.match(r'^(\s*def\s+\w+\s*\()(.*)(\)\s*->\s*.*?:\s*\.\.\.)$', line)
    if not match:
        return [line]

    prefix, params_str, suffix = match.groups()

    # Handle empty parameter list
    if not params_str.strip() or params_str.strip() == 'self':
        return [line]

    # Parse parameters
    params = []
    current_param = []
    depth = 0

    for char in params_str + ',':
        if char == '[':
            depth += 1
            current_param.append(char)
        elif char == ']':
            depth -= 1
            current_param.append(char)
        elif char == ',' and depth == 0:
            param_str = ''.join(current_param).strip()
            if param_str:
                params.append(param_str)
            current_param = []
        else:
            current_param.append(char)

    # Parse each parameter
    parsed_params = []
    for param_str in params:
        name, type_str, has_default, is_varargs = parse_parameter(param_str)
        parsed_params.append((name, type_str, has_default, is_varargs))

    # Check if any parameter needs expansion (has union type or default value)
    needs_expansion = False
    for name, type_str, has_default, is_varargs in parsed_params:
        if name != 'self' and not is_varargs:
            if '|' in type_str or has_default:
                needs_expansion = True
                break

    if not needs_expansion:
        return [line]

    # Expand unions
    # For each parameter with a union, split it into options
    param_options = []
    for name, type_str, has_default, is_varargs in parsed_params:
        if name == 'self':
            param_options.append([(name, '', False, False)])
        elif is_varargs:
            # Keep varargs as-is
            param_options.append([(name, type_str, has_default, is_varargs)])
        elif '|' in type_str:
            # Split union types (after | None has been converted to ?)
            types = split_union(type_str)
            options = []
            for t in types:
                options.append((name, t, False, False))
            # If parameter has default value, add omission option at the end
            # (product() iterates rightmost fastest, so None at end gives correct order)
            if has_default:
                options.append(None)
            param_options.append(options)
        else:
            # No union
            if has_default:
                # Parameter with default value can be omitted or included
                # Put type first, then None, for correct iteration order
                options = [(name, type_str, False, is_varargs), None]
                param_options.append(options)
            else:
                # Required parameter, must be included
                param_options.append([(name, type_str, False, is_varargs)])

    # Generate all combinations
    results = []
    for combination in product(*param_options):
        # Filter out None values (represent omitted parameters)
        combo_params = [p for p in combination if p is not None]

        # Build parameter string
        param_strs = []
        for name, type_str, has_default, is_varargs in combo_params:
            if name == 'self':
                param_strs.append('self')
            elif is_varargs:
                param_strs.append(f'*{name}: {type_str}')
            elif type_str:
                param_strs.append(f'{name}: {type_str}')
            else:
                param_strs.append(name)

        result_line = prefix + ', '.join(param_strs) + suffix
        results.append(result_line)

    # Deduplicate first - keep only unique signatures
    seen = set()
    unique_results = []
    for result in results:
        if result not in seen:
            seen.add(result)
            unique_results.append(result)

    # Sort by complexity: zero-arg variants first, then by parameter count,
    # then left-to-right natural ordering in the same order they were unioned.
    # This matches Java convention of simplest to most complex overloads.
    def signature_complexity(line):
        # Extract parameter list (everything between first '(' and last ')')
        match = re.search(r'\(([^)]*)\)', line)
        if not match:
            return (999, '', line)  # Fallback for malformed lines

        params = match.group(1).strip()

        # Count parameters (ignoring 'self')
        if not params or params == 'self':
            return (0, '', line)  # Zero params (or only self)

        # Count commas to estimate parameter count
        param_count = params.count(',') + 1
        if 'self' in params.split(',')[0]:
            param_count -= 1  # Don't count 'self' as a parameter

        # Sort by parameter count as described above
        return (param_count,)

    unique_results.sort(key=signature_complexity)

    return unique_results


def normalize_none_to_nullable(line: str) -> str:
    """
    Convert '| None' syntax to '?' nullable syntax.

    Examples:
        'foo: str | None' -> 'foo: str?'
        'foo: str | Path | None' -> 'foo: str? | Path?'
        'Builder[Any] | None' -> 'Builder[Any]?'
        '-> BuilderFactory | None:' -> '-> BuilderFactory?:'
    """
    import re

    # Strategy: Find all type annotations and process them
    def process_type_annotation(match):
        param_name = match.group(1)
        type_annotation = match.group(2)

        # Check if it contains | None
        if ' | None' in type_annotation or '| None' in type_annotation:
            # Remove | None
            cleaned = type_annotation.replace(' | None', '').replace('| None', '')

            # Split into individual types and add ? to each
            types = split_union(cleaned)
            nullable_types = [t.strip() + '?' for t in types if t.strip()]
            return param_name + ': ' + ' | '.join(nullable_types)

        return match.group(0)  # No change needed

    # Process return type annotations: -> return_type:
    def process_return_type(match):
        type_annotation = match.group(1)

        # Check if it contains | None
        if ' | None' in type_annotation or '| None' in type_annotation:
            # Remove | None
            cleaned = type_annotation.replace(' | None', '').replace('| None', '')

            # Split into individual types and add ? to each
            types = split_union(cleaned)
            nullable_types = [t.strip() + '?' for t in types if t.strip()]
            return '-> ' + ' | '.join(nullable_types) + ':'

        return match.group(0)  # No change needed

    # First, match return type annotations: -> return_type:
    result = re.sub(
        r'-> ([^:]+):',
        process_return_type,
        line
    )

    # Then match parameter type annotations: param_name: type_annotation
    # where type_annotation can contain nested brackets and ends before a comma, paren, or =
    result = re.sub(
        r'(\w+): ([^:,)=]+(?:\[[^\]]*\][^:,)=]*)?)',
        process_type_annotation,
        result
    )

    # Fix spacing: "Type?=" -> "Type? ="
    result = re.sub(r'\?=', '? =', result)

    return result


def convert_abstractmethod_to_keyword(line: str) -> tuple[str, bool]:
    """
    Convert @abstractmethod decorator to abstract keyword prefix.

    Examples:
        '    @abstractmethod' -> ('', True)  # Mark for removal, flag next line
        '    def build(self) -> Environment: ...' (if flagged) -> '    abstract def build(self) -> Environment: ...'

    Returns:
        (processed_line, is_abstractmethod_decorator)
    """
    stripped = line.strip()
    if stripped == '@abstractmethod':
        return ('', True)  # Remove decorator line, flag next line
    return (line, False)


def add_abstract_keyword(line: str) -> str:
    """Add 'abstract' keyword before 'def' in a method signature."""
    # Match indentation + def
    match = re.match(r'^(\s*)def\s+', line)
    if match:
        indent = match.group(1)
        rest = line[len(indent):]
        return f'{indent}abstract {rest}'
    return line


def strip_abc_from_class(line: str) -> str:
    """
    Strip ABC and metaclass=abc.ABCMeta from class declarations.

    Examples:
        'class Builder(ABC):' -> 'class Builder:'
        'class Builder(ABC, metaclass=abc.ABCMeta):' -> 'class Builder:'
        'class BaseBuilder(Builder, ABC):' -> 'class BaseBuilder(Builder):'
        'class SimpleBuilder(BaseBuilder):' -> 'class SimpleBuilder(BaseBuilder):'  # unchanged
    """
    # Match class declarations with base classes
    match = re.match(r'^(\s*class\s+\w+)\(([^)]+)\)(\s*:.*)$', line)
    if not match:
        return line

    prefix = match.group(1)  # e.g., "class Builder"
    bases_str = match.group(2)  # e.g., "ABC, metaclass=abc.ABCMeta" or "Builder, ABC"
    suffix = match.group(3)  # e.g., ":"

    # Split bases by comma, handling nested generics
    bases = []
    current = []
    depth = 0

    for char in bases_str + ',':
        if char == '[':
            depth += 1
            current.append(char)
        elif char == ']':
            depth -= 1
            current.append(char)
        elif char == ',' and depth == 0:
            base = ''.join(current).strip()
            if base:
                bases.append(base)
            current = []
        else:
            current.append(char)

    # Filter out ABC and metaclass arguments
    filtered_bases = []
    for base in bases:
        # Skip ABC
        if base == 'ABC':
            continue
        # Skip metaclass arguments
        if base.startswith('metaclass='):
            continue
        filtered_bases.append(base)

    # Reconstruct class declaration
    if filtered_bases:
        return f'{prefix}({", ".join(filtered_bases)}){suffix}'
    else:
        return f'{prefix}{suffix}'


def process_file(file_path: Path):
    """Process a single API file, expanding union types in signatures."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    output_lines = []
    abstract_next = False

    for line in lines:
        # First normalize | None to ? syntax
        normalized = normalize_none_to_nullable(line.rstrip('\n'))

        # Strip ABC from class declarations
        normalized = strip_abc_from_class(normalized)

        # Check for @abstractmethod decorator
        processed, is_abstractmethod = convert_abstractmethod_to_keyword(normalized)

        if is_abstractmethod:
            # This line was @abstractmethod - skip it and flag next line
            abstract_next = True
            continue

        # If previous line was @abstractmethod, add abstract keyword
        if abstract_next and processed.strip().startswith('def '):
            processed = add_abstract_keyword(processed)
            abstract_next = False

        # Then expand unions
        expanded = expand_signature(processed)
        output_lines.extend(expanded)

    # Deduplicate across all lines (handles cases where Java overloads map to same Python signature)
    seen = set()
    unique_lines = []
    for line in output_lines:
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)

    with open(file_path, 'w') as f:
        for line in unique_lines:
            f.write(line + '\n')


def process_directory(api_dir: Path):
    """Process all .api files in a directory tree."""
    count = 0
    for api_file in api_dir.rglob('*.api'):
        process_file(api_file)
        count += 1

    return count


def main():
    if len(sys.argv) < 2:
        print("Usage: dump-api.py <api-directory>", file=sys.stderr)
        print("", file=sys.stderr)
        print("Post-processes Java API dump files to expand union types.", file=sys.stderr)
        sys.exit(1)

    api_dir = Path(sys.argv[1])
    if not api_dir.exists():
        print(f"Error: Directory '{api_dir}' does not exist", file=sys.stderr)
        sys.exit(1)

    count = process_directory(api_dir)
    print(f"Processed {count} API file(s)", file=sys.stderr)


if __name__ == '__main__':
    main()
