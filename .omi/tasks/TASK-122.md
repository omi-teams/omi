---
id: TASK-122
title: UI workflow - PO-approved mockup before build
status: planned
depends:
plan:
scope: src/omi/template/dot-omi/workflows/omi-flow-feature-ui.md, src/omi/template/dot-omi/agents/omi-agent-designer-ui.md, src/omi/template/dot-omi/agents/omi-agent-reviewer.md, src/omi/template/dot-omi/agents/omi-agent-qa-tester.md, src/omi/template/dot-omi/skills/ui/**, src/omi/template_shas.json, .omi/workflows/**, .omi/agents/**, .omi/skills/**, tests/test_content.py, .omi/tasks/TASK-122.md
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature
step:
---
## Goal
In every omi project, a UI task gets a visual mockup the PO approves before the engineer builds, and the build is checked against it, so a text-only spec can no longer produce a bare UI (TASK-115: PO "không có chút UIUX nào").

## Acceptance criteria
- [ ] `omi-flow-feature-ui` has a `po` gate after `design`: the designer delivers static HTML mockup files (one per screen plus a phone-width one) under `.omi/tasks/<ID>-mockup/`, built only from what the target stack allows (no CDN or web fonts unless the task allows them), and the PO approves them before `build`. The repo files are the only source of truth: plain self-contained `.html` that opens in any browser with no account, network or external tool (no Figma, no hosted canvas required).
- [ ] The `build` step gets `omi-skill-ui-direction` besides `omi-skill-lean-implementation`, and the designer adds the criterion "pages match the PO-approved mockup in `.omi/tasks/<ID>-mockup/`" to the task.
- [ ] Reviewer and qa-tester compare the result with the mockup (qa: screenshots side by side per screen) and FAIL on clear mismatches in layout, components or colours.
- [ ] The repo's own `.omi` copies match the template; generated catalogs regenerated; `template_shas.json` updated if needed; tests cover the new step and skills; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
