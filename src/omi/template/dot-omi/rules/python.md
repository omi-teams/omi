---
id: python
summary: Python code: typing, errors, tests, packaging
applies: **/*.py, pyproject.toml
---
# python

- Python 3.13; type-hint public functions.
- Standard library first; add no dependency the task does not ask for.
- Read and write text files with `encoding="utf-8"`; build paths with `pathlib`.
- Raise specific exceptions; never use a bare `except:`.
- No mutable default arguments; no global state that tests cannot reset.
- One small test per behavior (pytest or plain asserts); run the project's test command.
