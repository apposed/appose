# Appose Documentation

This directory contains the source files for the Appose documentation, built with [Sphinx](https://www.sphinx-doc.org/).

**📖 For detailed guidance, see:**
- [`../CLAUDE.md`](../CLAUDE.md) - Complete guide to this repository
- [`../DOCUMENTATION.md`](../DOCUMENTATION.md) - Overview of the documentation system
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) - How to contribute

## Building Locally

### Prerequisites

Install [uv](https://docs.astral.sh/uv/) if you don't have it:

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Dependencies are managed in `pyproject.toml` under the `[dependency-groups]` section. uv will automatically install them when building.

### Build HTML

```bash
# On Linux/Mac
make html

# On Windows
make.bat html
```

The HTML documentation will be generated in `_build/html/`. Open `_build/html/index.html` in your browser to view it.

### Build PDF

```bash
# On Linux/Mac
make latexpdf

# On Windows
make.bat latexpdf
```

Note: This requires LaTeX to be installed on your system.

### Other Formats

```bash
make epub       # EPUB format
make singlehtml # Single-page HTML
make linkcheck  # Check for broken links
```

## Documentation Structure

- `index.rst` - Main landing page
- `getting-started.rst` - Installation and first steps
- `core-concepts.rst` - Architecture and key concepts
- `examples.rst` - Comprehensive examples with language tabs
- `worker-protocol.rst` - Detailed protocol specification
- `faq.rst` - Frequently asked questions
- `alternatives.rst` - Alternative tools and complements
- `conf.py` - Sphinx configuration
- `requirements.txt` - Python dependencies for building docs

## ReadTheDocs

The documentation is automatically built and hosted on [Read the Docs](https://readthedocs.org/) when changes are pushed to the repository.

Configuration is in `.readthedocs.yaml` at the repository root.

## Features

- **sphinx_tabs** - Language-specific examples in tabs (Java/Python)
- **sphinx_copybutton** - Copy button for code blocks
- **myst_parser** - Support for Markdown files alongside RST
- **sphinx_rtd_theme** - Clean, responsive Read the Docs theme

## Contributing

When adding new documentation:

1. Use `sphinx_tabs` for language-specific examples
2. Follow the existing structure and style
3. Test locally before committing
4. Check for broken links with `make linkcheck`
5. Keep examples concise but complete
