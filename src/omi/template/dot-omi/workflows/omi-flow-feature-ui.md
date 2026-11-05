---
id: omi-flow-feature-ui
summary: Feature with a UI change: static HTML mockups with designer/UI review PASS first, then implement, review, browser QA with screenshots, automatic acceptance on review PASS. Use when screens or interaction change; plain feature is enough for backend or non-visual work.
steps:
- id: plan | role: coordinator | skills: omi-skill-task-brief | input: PO idea | output: task file with scope including .omi/tasks/<ID>-mockup/ and acceptance criteria | gate: none | stop: task file complete and PO picked it
- id: design | role: omi-agent-designer-ui | skills: omi-skill-ui-direction, omi-skill-ui-a11y-review | input: task file | output: UI spec and mockup-match criterion in the task file, self-contained HTML in .omi/tasks/<ID>-mockup/ | gate: none | stop: one mockup per screen plus a phone-width mockup covers states, a11y and layout
- id: approve-mockup | role: coordinator | skills: | input: UI spec and .omi/tasks/<ID>-mockup/ | output: designer/UI review PASS on mockups checked against the UI spec and a11y review, recorded in ## Steps | gate: none | stop: designer/UI review passed on the repo HTML mockups before build
- id: build | role: omi-agent-engineer | skills: omi-skill-lean-implementation, omi-skill-ui-direction | input: task file with UI spec and .omi/tasks/<ID>-mockup/ with designer/UI review PASS | output: diff, tests passing, Checkpoint updated | gate: none | stop: every criterion has a passing test
- id: review | role: omi-agent-reviewer | skills: omi-skill-verify-evidence, omi-skill-simplify-review | input: task file, diff, .omi/tasks/<ID>-mockup/ with designer/UI review PASS | output: VERDICT PASS or FAIL | gate: review | stop: VERDICT PASS
- id: qa | role: omi-agent-qa-tester | skills: omi-skill-web-qa, omi-skill-verify-evidence, omi-skill-simplify-review | input: task file, running build, .omi/tasks/<ID>-mockup/ with designer/UI review PASS | output: pass/fail per criterion with side-by-side screenshots per screen | gate: review | stop: all criteria pass
- id: accept | role: coordinator | skills: | input: PASS verdict, QA report | output: `Auto accept: review PASS` line in ## Steps | gate: auto | stop: every review-type step passed or an explicit PO approval line
---
# Feature with UI

**When to use:** the change alters what a user sees or does. Why not `omi-flow-feature`: it has no mockup with designer/UI review PASS and no browser check, so layout, a11y and visual regressions slip through.
**Use instead:** for a UI change in a sensitive area (auth, data, secrets) run `omi-flow-feature-sensitive`; the Coordinator also runs `omi run omi-agent-designer-ui <ID>` before build and `omi run omi-agent-qa-tester <ID>` after security.

## Models
- plan: Coordinator, sonnet/low.
- design: designer-ui, sonnet/medium.
- approve-mockup: Coordinator; proceeds after the designer/UI review PASS, before build.
- build: engineer, sonnet/medium.
- review: reviewer, sonnet/medium, fresh each round.
- qa: qa-tester, sonnet/medium.
- accept: Coordinator; automatic after review PASS.

## Review-fail rule
A FAIL at review or qa goes back to build with the findings. Enforced in code: after `max_fix_rounds` (2) failed rounds `omi step <ID> back` and `omi run` refuse with `ROUND LIMIT` until the PO's words for this task and round are given (`--po "<words>"`, one more round; pick-list: rescope, change approach, drop). From round 2 a FAIL whose report ends `ROOT: same` prints `REPLAN: same root cause`; this workflow has no architect step, so `back` needs `--po`.

## Mockup contract
The repo files in `.omi/tasks/<ID>-mockup/` are the only source of truth: plain self-contained `.html`, one per screen plus a phone-width mockup. They open directly in any browser without an account, network or external tool; no Figma or hosted canvas is required. Use only what the target stack allows; no CDN or web fonts unless the task explicitly allows them.

The designer adds the acceptance criterion "pages match the mockup with designer/UI review PASS in `.omi/tasks/<ID>-mockup/`" to the task. Build follows those reviewed files. The reviewer checks the code against the mockup and the designer/UI review PASS recorded under `## Steps`, and FAILs on clear mismatches or a missing mockup or missing designer/UI review PASS; the render comparison is not available at review, so the reviewer marks it `QA <criterion>`, which does not block PASS. The qa-tester owns the screenshot comparison: it captures mockup and build screenshots side by side per screen, including phone width, and FAILs on mismatch.

## PO gates
`approve-mockup` has no gate: the Coordinator proceeds after the designer/UI review PASS on the repo HTML files; the PO is asked only when the mockups add operating cost. If the mockups change, redo the review before implementing the change.

`accept` is automatic: `omi step <ID> done` records `Auto accept: review PASS` under `## Steps` when every review-type step passed (or an explicit `PO approval accept:` line exists), and refuses otherwise. Use `omi-flow-feature-sensitive` for security-sensitive work. Merge to staging/main stays with the PO.
