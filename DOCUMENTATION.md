# Appose Documentation

This is an overview of the Appose ReadTheDocs site in the `docs/` directory.

## What's Included

### Documentation Pages

1. **index.rst** - Main landing page with quick examples
2. **getting-started.rst** - Installation and first programs with language tabs
3. **core-concepts.rst** - Architecture overview and key concepts (Builder, Environment, Service, Task, Worker)
4. **examples.rst** - Comprehensive examples from basic to advanced with language tabs
5. **worker-protocol.rst** - Detailed protocol specification for custom workers
6. **faq.rst** - Frequently asked questions
7. **alternatives.rst** - Comparison with alternatives (Arrow, NATS, gRPC, etc.)

### Features

- **sphinx_tabs** - Language-specific examples in tabs (Java/Python side-by-side)
- **sphinx_copybutton** - Copy buttons for all code blocks
- **myst_parser** - Support for both Markdown and reStructuredText
- **sphinx_rtd_theme** - Clean, responsive Read the Docs theme
- **uv dependency management** - Modern, fast dependency management using PEP 735 dependency groups

### Configuration Files

- **pyproject.toml** - Project metadata and dependency groups (following pyimagej pattern)
- **docs/conf.py** - Sphinx configuration
- **docs/Makefile** - Build commands using `uv run --group docs`
- **docs/make.bat** - Windows build commands
- **.readthedocs.yaml** - ReadTheDocs hosting configuration

## Building Locally

### Prerequisites

Install uv if you don't have it:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Build

```bash
cd docs
make html
```

The built documentation will be in `docs/_build/html/`. Open `docs/_build/html/index.html` to view.

### Other formats

```bash
make latexpdf  # PDF (requires LaTeX)
make epub      # EPUB
make linkcheck # Check for broken links
```

## Deploying to ReadTheDocs

1. Connect your repository to ReadTheDocs
2. ReadTheDocs will automatically use `.readthedocs.yaml` configuration
3. Documentation builds automatically on each commit

## Key Design Decisions

1. **Language tabs throughout** - Java and Python examples side-by-side for easy comparison
2. **Comprehensive examples** - From "Hello World" to complex ML pipelines
3. **Protocol documentation** - Full specification enabling custom worker implementations
4. **uv-based builds** - Following the pyimagej project pattern for consistency
5. **Both .rst and .md support** - Flexibility via MyST Parser

## Next Steps

- Review the built documentation in your browser
- Customize the theme/styling if desired in `docs/_static/`
- Add any project-specific content
- Set up ReadTheDocs hosting
- Consider adding API autodoc if desired (currently focused on conceptual docs)
