---
id: omi-modules
summary: src/omi subpackages: responsibilities, imports, layer order, package surface, test patches
applies: src/omi/**/*.py, src/omi/*.py
---
# omi-modules

- `board/data.py`: read-only JSON-ready views of detached state for the board.
- `board/server.py`: GET-only localhost HTTP handler (route allowlist, static files from `board/web/`); imports only `board.data`; `app/cli.py` owns the pull, browser and serve loop.
- `app/cli.py`: command dispatch and status presentation.
- `setup/`: `install` handles user integration; `upgrade` handles init, template updates and hashes; `attach` registers detached projects and warns about in-repo files.
- `worker/`: `run`, `hooks`, `docker` execute agents; `pr` posts step results as PR comments; `tools` builds/parses agent commands; `session` keeps the per-task engineer session cache and the task's `Session:` line; `creds` manages authentication.
- `project/`: `tasks`, `workflows`, `catalogs`, `scope`, `github` manage project content, task state, write boundaries and GitHub configuration.
- `state/`: `resolve` locates project state and validates its registry; `sync` handles detached-state git transport.
- `common/core.py`: shared paths, parsing, version and git helpers.
- Call across modules through module imports: `from . import x` within a subpackage or `from ..project import tasks` across subpackages, then `tasks.name(...)`. Import `state.resolve as state` and `state.sync as state_sync` where needed; never import individual functions except at the package surface.
- Import only downward in this module layer order (packages may span layers): app.cli > board.server > board.data > setup.attach / setup.install / worker.run > worker.hooks > worker.pr / worker.docker / setup.upgrade / project.tasks > project.workflows > project.catalogs > worker.tools / worker.session / worker.creds / project.scope / state.sync > state.resolve > common.core / project.github.
- No import inside a function to dodge a cycle; fix the layering instead.
- Keep each module under ~600 lines; a new responsibility gets a new module.
- Root `__init__.py` only re-exports `main`, `version`; `__main__.py` delegates to `main` for `python -m omi`. Subpackage initializers contain no logic.
- Tests patch the defining module (`omi.<subpackage>.<module>.<name>`), never the re-export. Keep template assets and `template_shas.json` at the package root; resource paths must work from source and installed packages.
