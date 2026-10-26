---
name: omi-status
description: Show OMI project status.
disable-model-invocation: true
allowed-tools: Bash(python -m omi status)
---
!`python -m omi status`

Show the status above to the PO verbatim in a code block. Then ask what next with the AskUserQuestion pick-list: start the `next` task (recommended), another planned task, or stop. On a pick, run `omi-task <ID>` yourself; the pick is the approval.
