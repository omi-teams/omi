---
id: omi-modules
summary: src/omi module structure: imports, layer order, size, package surface, test patches
applies: src/omi/*.py
---
# omi-modules

- Call across modules as `from . import x`, then `x.name(...)`; never `from .x import name`.
- Import only downward in the layer order: cli > install/run > hooks > docker > tasks/upgrade > workflows > catalogs > tools/creds/scope > state > core/github.
- No import inside a function to dodge a cycle; fix the layering instead.
- Keep each module under ~600 lines; a new responsibility gets a new module.
- `__init__.py` stays the package surface: only re-exports the public names (`main`, `version`); no logic there.
- Tests patch the defining module (`omi.<module>.<name>`), never the re-export.
