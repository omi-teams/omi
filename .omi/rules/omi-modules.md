---
id: omi-modules
summary: src/omi module structure: imports, layer order, size, package surface, test patches
applies: src/omi/*.py
---
# omi-modules

- Call across modules as `from . import x`, then `x.name(...)`; never `from .x import name`.
- Import only downward in the layer order: cli > run > hooks > docker > tasks/upgrade > workflows > catalogs > tools/creds/scope > core/github.
- No import inside a function to dodge a cycle; fix the layering instead.
- Keep each module under ~600 lines; a new responsibility gets a new module.
- `__init__.py` stays the package surface; do not re-export names from it.
- Tests patch the defining module (`omi.<module>.<name>`), never the re-export.
