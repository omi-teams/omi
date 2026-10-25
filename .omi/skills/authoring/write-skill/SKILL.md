---
id: write-skill
group: authoring
description: Use when creating or revising an omi-skill; gives the contract, trigger wording and acceptance test.
tokens: 900
tools: Read, Write, Edit, Bash
source_repo: https://github.com/anthropics/skills
source_ref: dbd4588f9e1033efb41dad4bef2f7947c8993d44
source_file: skills/skill-creator/SKILL.md
source_license: Apache-2.0
source_use: adapt
---
<!-- Adapted from Anthropic skill-creator (https://github.com/anthropics/skills), Apache-2.0, pinned at dbd4588f9e1033efb41dad4bef2f7947c8993d44.
     Copyright Anthropic, PBC (see upstream LICENSE.txt at the pinned commit).
     Licensed under the Apache License 2.0, https://www.apache.org/licenses/LICENSE-2.0 ; changes: condensed to the omi skill contract. -->
# Write a skill

## When to use
- A task needs a repeatable procedure that agents keep reinventing.
- An existing skill misfires, is too long, or is not found when needed.

## When not to use
- One-off facts: put them in the task file or `.omi/decisions.md`.
- Anything that needs wider permissions or scope than the task grants: escalate instead.

## Inputs
- The procedure to capture, 2-3 real example tasks, and the source it comes from (repo, tag, file, license).

## Steps
1. Baseline first: run the example tasks without the skill and note where the agent fails or wastes tokens.
2. Write frontmatter: `id`, `group`, `description`, `tokens`, `tools`, `source_*` (use = reference, adapt or rewrite).
3. Trigger wording: `description` says when to use it, in the words a task would use ("Use when ..."), not what the skill is.
4. Keep the body short: imperative steps, no background the model already knows, one example at most. Hard cap 2000 tokens including references.
5. Split detail out: long tables, templates or API notes go in `references/*.md`, listed in `references:` and read only when a step says so.
6. Fill every section: when to use / not to use, inputs, steps, outputs and evidence, stop and escalate, tools needed.
7. Keep the license notice of adapted sources at the top of the body.
8. Run `python -m omi skills --check`, then `python -m omi skills` to refresh the catalog.
9. Compare against the baseline: rerun the examples with the skill. Accept only if it is clearly better (fewer errors or tokens); otherwise cut or rewrite it.

## Outputs and evidence
- `.omi/skills/<group>/<id>/SKILL.md` (+ references), a refreshed `CATALOG.md`.
- Evidence: `skills --check` output and a baseline vs. with-skill note in the task checkpoint.

## Stop and escalate
- The skill would need tools, network or write access beyond the task scope: stop, report NEEDS SCOPE.
- The source license is unknown or incompatible: stop and ask the PO.
- No measurable gain over the baseline: do not add the skill.

## Tools needed
- Read, Write, Edit, and Bash for `python -m omi skills --check`.
