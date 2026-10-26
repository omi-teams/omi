---
name: omi-upgrade
description: Upgrade omi in this project - install a newer omi, update unmodified template files, resolve the modified ones with the PO.
disable-model-invocation: true
---
1. Run `python -m omi upgrade --check`. Read `omi_repo` from `.omi/config.json` (default: `https://github.com/omi-teams/omi-squad2`). `up to date` -> tell the PO and stop.
2. Ask the PO (pick-list) which version: the latest shown, or another `vX.Y.Z` tag. Show the repo URL with each choice. For a non-default repo, ask the PO to explicitly confirm that URL before installing.
3. Run `python -m omi upgrade --to <tag>`; for a confirmed non-default repo, add `--repo <url>` with the exact configured URL. Show the summary verbatim.
4. For each `<path>.omi-new` (listed as `kept (modified)`), show the diff against `<path>` and ask the PO (pick-list): keep (delete the `.omi-new`), take new (replace the file, delete the `.omi-new`), or merge (edit `<path>`, delete the `.omi-new`).
5. Commit on `development` (`chore: upgrade omi to <version>`), then run the project's tests.

Never edit `.omi/tasks`, `.omi/decisions.md` or other plans by hand during an upgrade.
