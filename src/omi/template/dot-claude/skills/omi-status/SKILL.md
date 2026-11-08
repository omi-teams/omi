---
name: omi-status
description: Show OMI project status.
disable-model-invocation: true
allowed-tools: Bash(python -m omi status), Bash(python -m omi watch)
---
!`python -m omi status`

Show the status above to the PO verbatim in a code block. If status says `finished runs not handled`, run `python -m omi watch` first and act only on its `DECIDE:` lines: `omi drive` runs the `NEXT:` ones (advance, dispatch next) by itself; start it with `omi dispatch next` when it is not running. Then resume every `(resume)` task from `next:` yourself (omi-task step 2; `omi-task <ID> <ID>` for several) before the next planned task, then run `omi-task <ID>` for that planned task; no PO question.
