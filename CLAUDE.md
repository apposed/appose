# CLAUDE.md

This file provides guidance to Claude Code when working with the Appose meta-repository.

## Project Overview

This is the **Appose meta-repository** - it contains the overarching project documentation, protocol specification, and links to language-specific implementations. **This repository does not contain code** - it is purely documentation.

**What is Appose?**

Appose is a library for interprocess cooperation with shared memory. It enables easy execution of code in different programming languages without copying large data structures (especially tensors for deep learning).

**Key principles:**
- **Simplicity** - Minimal dependencies, straightforward API
- **Efficiency** - Zero-copy tensor sharing via shared memory

**Architecture:**
- Each language has its **own implementation** (separate repositories)
- All implementations follow the **same worker protocol** (JSON over stdin/stdout)
- Workers can be written in any language that implements the protocol

## Repository Structure

```
appose/                          # Meta-repository (THIS REPO)
├── README.md                    # Main project README with protocol spec
├── CLAUDE.md                    # This file
├── DOCUMENTATION.md             # Guide to the Sphinx documentation
├── pyproject.toml               # Dependency groups for docs building
├── .readthedocs.yaml            # ReadTheDocs configuration
├── docs/                        # Comprehensive Sphinx documentation
│   ├── conf.py                  # Sphinx configuration
│   ├── Makefile                 # Build commands (uses uv)
│   ├── make.bat                 # Windows build commands
│   ├── requirements.txt         # Docs dependencies (legacy, use pyproject.toml)
│   ├── README.md                # How to build the docs
│   ├── index.rst                # Documentation landing page
│   ├── getting-started.rst      # Installation and first steps
│   ├── core-concepts.rst        # Architecture and key concepts
│   ├── examples.rst             # Comprehensive examples
│   ├── worker-protocol.rst      # Protocol specification
│   ├── faq.rst                  # FAQ
│   ├── alternatives.rst         # Comparison with alternatives
│   ├── _static/                 # Static assets
│   └── _templates/              # Custom templates
└── openmoji-svg-color/          # SVG icons (not part of docs)
```

## Related Repositories

The actual implementations are in separate repositories:

- **appose-java**: Java implementation at `../appose-java/`
  - See `../appose-java/CLAUDE.md` for Java-specific guidance
- **appose-python**: Python implementation at `../appose-python/`
  - See `../appose-python/README.md` for Python-specific docs

## Core Concepts

### Architecture Layers

```
Builder → Environment → Service → Task
```

1. **Builder**: Creates environments with dependencies (Pixi, Mamba, UV, System)
2. **Environment**: Configured environment with executables
3. **Service**: Access to a worker process
4. **Task**: Asynchronous operation (like a Future/Promise)
5. **Worker**: Separate process that executes scripts

### Worker Protocol

Communication is via **JSON over stdin/stdout**:

**Request Types:**
- `EXECUTE` - Run a script
- `CANCEL` - Cancel a running task

**Response Types:**
- `LAUNCH` - Task started
- `UPDATE` - Progress update
- `COMPLETION` - Task finished successfully
- `CANCELATION` - Task canceled
- `FAILURE` - Task failed
- `CRASH` - Worker crashed

See `README.md` or `docs/worker-protocol.rst` for full specification.

## Documentation System

### Technology Stack

- **Sphinx** - Documentation generator
- **sphinx_rtd_theme** - Read the Docs theme
- **sphinx_tabs** - Language-specific examples in tabs (Java/Python)
- **sphinx_copybutton** - Copy buttons for code blocks
- **myst_parser** - Markdown support alongside RST
- **uv** - Dependency management (following pyimagej pattern)

### Build Commands

```bash
# Build HTML documentation
cd docs
make html

# Other formats
make latexpdf  # PDF (requires LaTeX)
make epub      # EPUB
make linkcheck # Check for broken links

# Clean build
make clean
```

The Makefile uses `uv run --group docs sphinx-build`, which automatically:
1. Creates a virtual environment in `.venv/`
2. Installs dependencies from `pyproject.toml` `[dependency-groups]` section
3. Runs sphinx-build

### Dependency Management

Dependencies are managed in **pyproject.toml** using PEP 735 dependency groups:

```toml
[dependency-groups]
docs = [
    "myst-parser>=2.0.0",
    "sphinx>=7.0.0",
    "sphinx-copybutton>=0.5.0",
    "sphinx-rtd-theme>=2.0.0",
    "sphinx-tabs>=3.4.0",
]
```

This follows the same pattern as `~/code/imagej/pyimagej/pyproject.toml`.

### Documentation Pages

1. **index.rst** - Landing page with quick examples
2. **getting-started.rst** - Installation, prerequisites, first program
3. **core-concepts.rst** - Deep dive into architecture
4. **examples.rst** - From basic to advanced use cases
5. **worker-protocol.rst** - Complete protocol specification
6. **faq.rst** - Frequently asked questions
7. **alternatives.rst** - Comparison with Arrow, NATS, gRPC, etc.

### Language Tabs Pattern

Throughout the docs, examples are shown side-by-side using `sphinx_tabs`:

```rst
.. tabs::

   .. tab:: Java

      .. code-block:: java

         Environment env = Appose.system();
         Service python = env.python();

   .. tab:: Python

      .. code-block:: python

         env = appose.system()
         python = env.python()
```

This makes it easy for users to compare implementations across languages.

## Common Tasks

### Adding New Documentation

1. **Create or edit .rst files** in `docs/`
2. **Use sphinx_tabs** for language-specific examples
3. **Test locally**: `cd docs && make html`
4. **Check for warnings** - build should have zero warnings
5. **Add to toctree** in `index.rst` if new page

### Updating the Protocol

The worker protocol is documented in **two places**:
1. `README.md` - Main specification (canonical)
2. `docs/worker-protocol.rst` - Detailed Sphinx version

Keep them in sync when updating.

### Adding Examples

Add examples to `docs/examples.rst`:
- Use tabs for Java/Python side-by-side
- Include both simple and advanced examples
- Group by topic (basic, progress, environments, real-world)
- Keep examples concise but complete

### Formatting Guidelines

**Code blocks:**
- Always specify language: `.. code-block:: java`
- Use tabs for multi-language examples
- Keep indentation consistent (3 spaces for nested content in RST)

**Avoid triple-quoted strings in Python examples within RST:**
- They cause indentation parsing errors
- Use string concatenation instead:
  ```python
  script = (
      "line 1\n"
      "line 2\n"
  )
  ```

## Important Notes

### This is a Documentation-Only Repo

- **No code implementation** - see appose-java and appose-python for code
- **No tests to run** - documentation builds are the "tests"
- **No releases** - implementations are released independently
- **Shared issue tracker**: https://github.com/apposed/appose/issues

### ReadTheDocs Hosting

Configuration in `.readthedocs.yaml`:
- Uses Python 3.11
- Builds Sphinx docs from `docs/conf.py`
- Installs dependencies from `docs/requirements.txt`
- Generates PDF and EPUB in addition to HTML

### Relationship to Implementations

```
appose/              # THIS REPO - Documentation
├── README.md        # Protocol spec + overview
└── docs/            # Full documentation site

appose-java/         # Java implementation
├── src/main/java/   # Java code
├── README.md        # Java-specific README
└── CLAUDE.md        # Java-specific guidance

appose-python/       # Python implementation
├── src/appose/      # Python code
└── README.md        # Python-specific README
```

Changes to the protocol require coordinating across all implementations.

### Version Numbers

- This repo doesn't have releases
- Documentation version is set in `docs/conf.py`: `release = '0.3.0'`
- Should match the latest stable release of implementations
- Update when implementations release new versions

## Troubleshooting

### Build warnings about indentation

RST is whitespace-sensitive. Common issues:
- Triple-quoted Python strings in code blocks
- Inconsistent indentation in nested directives
- Missing blank lines before/after directives

### "document isn't included in any toctree"

Either:
1. Add to a `.. toctree::` directive (usually in `index.rst`)
2. Add to `exclude_patterns` in `conf.py` (for files like README.md)

### Theme option warnings

Check `html_theme_options` in `conf.py` against current sphinx_rtd_theme version. Deprecated options should be removed.

### uv not found

Install uv:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Reference Links

- **Main site**: https://apposed.org (when launched)
- **Issue tracker**: https://github.com/apposed/appose/issues
- **Java implementation**: https://github.com/apposed/appose-java
- **Python implementation**: https://github.com/apposed/appose-python
- **Sphinx docs**: https://www.sphinx-doc.org/
- **Read the Docs**: https://docs.readthedocs.io/
- **uv**: https://docs.astral.sh/uv/

## Quick Reference

### File Locations

| What | Where |
|------|-------|
| Protocol specification | `README.md` |
| Documentation source | `docs/*.rst` |
| Sphinx config | `docs/conf.py` |
| Build commands | `docs/Makefile` |
| Dependencies | `pyproject.toml` |
| ReadTheDocs config | `.readthedocs.yaml` |
| Java implementation docs | `../appose-java/CLAUDE.md` |

### Common Commands

```bash
# Build docs
cd docs && make html

# Clean build
cd docs && make clean html

# Check links
cd docs && make linkcheck

# View built docs
open docs/_build/html/index.html

# Check for uncommitted changes
git status
```

## Philosophy

Appose prioritizes **simplicity** over features:

- ✅ Simple JSON protocol, not Protocol Buffers
- ✅ Pipes (stdin/stdout), not network sockets
- ✅ One self-contained library per language
- ✅ Minimal dependencies
- ❌ No plugin architecture (keeps codebase small)
- ❌ No cross-machine communication (keeps it simple)
- ❌ No alternative transport layers (keeps it focused)

See `README.md` FAQ section for rationale on these decisions.
