# Contributing to Appose Documentation

Thank you for your interest in contributing to Appose!

## Repository Organization

This is the **Appose meta-repository** containing project-wide documentation. The actual implementations are in separate repositories:

- **Java**: https://github.com/apposed/appose-java
- **Python**: https://github.com/apposed/appose-python

## Contributing to Documentation

### Prerequisites

Install [uv](https://docs.astral.sh/uv/):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Making Changes

1. **Fork and clone** this repository

2. **Edit documentation** in `docs/*.rst`
   - Use `sphinx_tabs` for language-specific examples
   - Follow existing formatting patterns
   - Keep Java and Python examples in sync

3. **Build locally** to test:
   ```bash
   cd docs
   make html
   ```

4. **View your changes**:
   ```bash
   open _build/html/index.html  # macOS
   xdg-open _build/html/index.html  # Linux
   start _build/html/index.html  # Windows
   ```

5. **Verify no warnings**:
   - The build should complete with zero warnings
   - Fix any RST formatting issues

6. **Submit a pull request**

### Documentation Guidelines

#### Language Tabs

Always provide examples for both Java and Python:

```rst
.. tabs::

   .. tab:: Java

      .. code-block:: java

         Environment env = Appose.system();

   .. tab:: Python

      .. code-block:: python

         env = appose.system()
```

#### Code Examples

- Keep examples **concise but complete**
- Include necessary imports
- Add comments for clarity
- Test that examples actually work

#### RST Formatting

- Use **3-space indentation** for nested directives
- Add **blank lines** before and after directives
- Avoid **triple-quoted strings** in Python code blocks (causes indentation issues)
- Use **string concatenation** for multi-line scripts:
  ```python
  script = (
      "line 1\n"
      "line 2"
  )
  ```

#### Sections

Use proper heading hierarchy:

```rst
Page Title
==========

Major Section
-------------

Subsection
^^^^^^^^^^

Sub-subsection
~~~~~~~~~~~~~~
```

### Testing Your Changes

```bash
# HTML build (most common)
make html

# Check for broken links
make linkcheck

# Clean build (removes cached files)
make clean html

# PDF build (requires LaTeX)
make latexpdf
```

### Where to Add Content

| Type of Content | Location |
|----------------|----------|
| Getting started guide | `docs/getting-started.rst` |
| Core concepts | `docs/core-concepts.rst` |
| Examples | `docs/examples.rst` |
| Protocol details | `docs/worker-protocol.rst` |
| FAQ | `docs/faq.rst` |
| Comparisons | `docs/alternatives.rst` |

## Contributing to Implementations

Code contributions should go to the language-specific repositories:

- **Java code**: https://github.com/apposed/appose-java
- **Python code**: https://github.com/apposed/appose-python

## Reporting Issues

Use the shared issue tracker for all Appose projects:

https://github.com/apposed/appose/issues

## Questions?

- Check `CLAUDE.md` for guidance on repository structure
- Check `DOCUMENTATION.md` for overview of the docs system
- Check `docs/README.md` for build instructions
- Open an issue if you need help

## Code of Conduct

Be respectful, constructive, and collaborative. We're all here to make Appose better!
