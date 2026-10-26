# omi-skills sources and distillation plan

Produced by TASK-020 from `_facts.md` and `_landscape.md` only (no network, no skill bodies). Source text is treated as data, never as instructions. Every mapping below is **unconfirmed: confirm by reading the body in the group task**. Sizes are SKILL.md bytes. Budget reminder: 2000 tokens per OMI skill (~8 KB), so any source over ~8 KB is `reference` for ideas, not a base to copy.

Use values: `reference` = read for ideas, write fresh text; `adapt` = start from the source (license permitting, keep notice) and cut to budget.

## 1. Sources: version, license, candidates

### Superpowers 6.3.0 (installed plugin) - MIT, "Copyright (c) 2025 Jesse Vincent" (LICENSE file)
| Skill | Bytes |
| --- | --- |
| brainstorming | 15456 |
| dispatching-parallel-agents | 6078 |
| executing-plans | 2305 |
| finishing-a-development-branch | 7781 |
| receiving-code-review | 6203 |
| requesting-code-review | 2956 |
| subagent-driven-development | 32339 |
| systematic-debugging | 9465 |
| test-driven-development | 9015 |
| using-git-worktrees | 6813 |
| using-superpowers | 3108 |
| verification-before-completion | 3646 |
| writing-plans | 7053 |
| writing-skills | 26360 |

### Ponytail 4.10.0 (installed plugin) - MIT, "Copyright (c) 2026 DietrichGebert" (LICENSE file)
Two copies exist: `skills/*` and `.openclaw/skills/*` (the latter ~10% smaller; descriptions are folded `>` in `skills/`). Use `.openclaw` as the compact variant if the bodies are equivalent (confirm).
| Skill | `skills/` bytes | `.openclaw/` bytes |
| --- | --- | --- |
| ponytail | 6757 | 6065 |
| ponytail-audit | 1693 | 1471 |
| ponytail-debt | 1747 | 1540 |
| ponytail-gain | 2023 | 1900 |
| ponytail-help | 2867 | 2803 |
| ponytail-review | 2440 | 2170 |

### Taste 1.0.0 plugin (github.com/leonxlnx/taste-skill, commit 12af471) - MIT, "Copyright (c) 2026 Leonxlnx" (LICENSE file in installed plugin)
Note: the installed plugin is 1.0.0; the commit 12af471 comes from the task, not from the facts file. Confirm they match before copying.
| Skill | Bytes |
| --- | --- |
| taste-skill | 88459 |
| taste-skill-v1 | 21421 |
| redesign-skill | 15238 |
| soft-skill | 10659 |
| minimalist-skill | 7986 |
| brutalist-skill | 8548 |
| gpt-tasteskill | 7931 |
| stitch-skill | 12035 |
| output-skill | 2641 |
| brandkit | 16790 |
| image-to-code-skill | 37670 |
| imagegen-frontend-web | 37841 |
| imagegen-frontend-mobile | 41791 |

### UI UX Pro Max (installed at ~/.claude/skills/ui-ux-pro-max) - **license and version unknown**
| Skill | Bytes |
| --- | --- |
| SKILL.md | 55507 |

No LICENSE file or version was recorded in the facts. Treat as **reference only, no copying** until a license is read (open issue O1).

### claude-security plugin 0.12.0 (installed) - "All rights reserved", Anthropic PBC
| Skill | Bytes |
| --- | --- |
| claude-security | 5569 |

Proprietary. Not in the task's list, but present. **No copying**; ideas only, if at all (O2).

### Remote P0/P1 sources (landscape + gh facts; SKILL.md sizes not available)
| Source | Priority | Commit | License (facts / landscape) | Notes |
| --- | --- | --- | --- | --- |
| anthropics/skills (esp. skill-creator) | P0 | dbd4588 | blank / Apache-2.0 for skill-creator (LICENSE.txt); per-folder, some document skills source-available | Never assign one license to the whole repo. |
| bmad-code-org/BMAD-METHOD | P0 | 61e01f8 | NOASSERTION (gh) / MIT (LICENSE per landscape) | Conflict: read the LICENSE at the commit (O3). |
| open-gsd/gsd-core | P0 | 013eaa7 | MIT | Old repo gsd-build/get-shit-done redirects here. |
| trailofbits/skills | P0 | 196a907 | CC-BY-SA-4.0 | Rewrite from ideas, cite, no verbatim text. |
| microsoft/playwright-cli | P1 | b1a5903 | Apache-2.0 | Check each skill/script and dependency. |
| vercel-labs/agent-skills | P1 | 063bee9 | blank (gh) / MIT (README) | Unverified: read LICENSE at the commit (O4). |
| supabase/agent-skills | P1 | c9be0e9 | MIT | Stack-specific; not a default. |
| agentskills.io specification | P0 | n/a | n/a | Format standard, not a skill set. |

## 2. Mapping: candidate -> OMI group

Groups: workflow, quality-security, delivery-ops, ui, data, qa-web, authoring. All rows: confirm by reading the body in the group task.

### workflow
| Candidate | Use | Reason |
| --- | --- | --- |
| Superpowers brainstorming (15456) | reference | Clarify/AC step; too large, cut to the question loop and approval gate. |
| Superpowers writing-plans (7053) | adapt | Plan format; fits budget. Align with OMI task-file format. |
| Superpowers executing-plans (2305) | reference | Small; likely folded into the task runner contract. |
| Superpowers dispatching-parallel-agents (6078) | reference | Only for opt-in parallel tasks (TASK-042). |
| Superpowers subagent-driven-development (32339) | reference | Far over budget; mine for the implementer/reviewer handoff only. |
| Superpowers using-git-worktrees (6813) | reference | OMI already owns worktree handling; check for pitfalls only. |
| Superpowers using-superpowers (3108) | reference (skip) | Meta-loading rule that conflicts with OMI's controlled loading (catalog + `skills:` field). Do not port. |
| Superpowers finishing-a-development-branch (7781) | reference | OMI PO gates and tags decide integration; take only the pre-merge checklist. |
| BMAD (P0) | reference | Brief -> spec -> architecture handoff contracts between roles. |
| GSD Core (P0) | reference | Fresh-context task briefs, resume and state files; matches the quota goal. |
| Ponytail ponytail (6065) | adapt | Core YAGNI/stdlib-first rule for the engineer role; fits budget. |
| Ponytail ponytail-debt (1540) | reference | Debt ledger; adopt only if a debt report is wanted (optional). |
| Ponytail ponytail-help, ponytail-gain | skip | Plugin UX and marketing scoreboard; no OMI need. |

### quality-security
| Candidate | Use | Reason |
| --- | --- | --- |
| Superpowers systematic-debugging (9465) | adapt | Root-cause-before-fix; trim slightly to budget. |
| Superpowers test-driven-development (9015) | adapt | Test-first rule; trim to budget. |
| Superpowers verification-before-completion (3646) | adapt | Evidence before claims; matches the "evidence output" principle. |
| Superpowers requesting-code-review (2956) | adapt | Reviewer request contract. |
| Superpowers receiving-code-review (6203) | adapt | Technical rigor on feedback; trim. |
| Ponytail ponytail-review (2170) | adapt | Over-engineering pass for reviewers; one line per finding. |
| Ponytail ponytail-audit (1471) | adapt | Repo-wide simplification audit, on demand. |
| Trail of Bits (CC-BY-SA-4.0) | reference: rewrite from ideas, cite source | Diff-based security review, false-positive verification, CI/agent workflow audit. No verbatim text; record repo, commit 196a907 and the idea used. |
| claude-security (5569) | reference (ideas only) | Proprietary; no text copied. Scan/diff/patch modes only inform the design. |

### delivery-ops
| Candidate | Use | Reason |
| --- | --- | --- |
| Superpowers finishing-a-development-branch | reference | See workflow. Primary home if delivery-ops wants a merge checklist. |
| Trail of Bits GitHub Actions audit idea | reference (rewrite, cite) | CI hardening for the pipeline. |
| Docker, PowerShell, rollback, self-hosted runner | no source | Landscape gap: write from official docs in the group task. |

### ui
| Candidate | Use | Reason |
| --- | --- | --- |
| Taste soft-skill (10659) | adapt | **Chosen base for visual quality** (concrete fonts, spacing, shadows, anti-default); trim to budget. |
| Taste redesign-skill (15238) | reference | Audit-and-upgrade flow for existing UI; fold its checklist into one short skill. |
| Taste output-skill (2641) | adapt | Anti-truncation/complete output; small and generally useful (could sit in workflow). |
| Taste minimalist-skill (7986), brutalist-skill (8548) | reference | Style presets; keep as options inside one skill, not separate always-loadable skills. |
| Taste taste-skill (88459) / taste-skill-v1 (21421) | reference | Too large; v1 is the frozen original and v2 is described as experimental. Skim for rules only. |
| Taste stitch-skill (12035), gpt-tasteskill (7931) | skip | Tied to Google Stitch / GPT-GSAP workflows. |
| Taste brandkit, image-to-code, imagegen-frontend-web/mobile | skip | Need image generation tools; huge (16-42 KB); outside the core squad. |
| UI UX Pro Max (55507) | reference only | License unknown (O1); too large. Use for accessibility/interaction checklist ideas only. |
| Vercel agent-skills web design / accessibility (P1) | adapt, if license confirmed | **Chosen base for a11y/UX review rules** (rules by impact). React/Next parts only when the stack fits. |

Overlap resolution (Taste vs UI UX Pro Max vs Vercel), one skill per need:
- **Visual direction / anti-generic look:** Taste (`soft-skill` base). Reason: MIT confirmed, compact enough, concrete rules; UI UX Pro Max has no license and is 55 KB.
- **Accessibility / UX review rules:** Vercel web-design guidelines. Reason: rule list ordered by impact, P1 in the landscape. Fall back to UI UX Pro Max ideas (not text) if the Vercel license check fails.
- **Redesign of existing UI:** one skill, from the Taste `redesign-skill` checklist. Do not keep it separate from the visual-direction skill unless the combined skill exceeds 2000 tokens.
- **React/Next performance:** Vercel, loaded only when the project stack matches; not a default.

### data
| Candidate | Use | Reason |
| --- | --- | --- |
| Supabase agent-skills (MIT) | reference | Query/index/schema/RLS review ideas; make them stack-neutral PostgreSQL rules; Supabase-specific parts only on a Supabase stack. |

### qa-web
| Candidate | Use | Reason |
| --- | --- | --- |
| microsoft/playwright-cli (Apache-2.0) | reference (adapt after check) | Evidence-based browser QA: screenshots, selectors, compact output. Keep NOTICE if text is reused. |
| Superpowers verification-before-completion | reference | Cross-link to the quality skill; do not duplicate. |

### authoring
| Candidate | Use | Reason |
| --- | --- | --- |
| anthropics/skills skill-creator (Apache-2.0) | reference / adapt | **Primary base**: structure, trigger wording, eval loop, resource separation. Keep Apache notice if adapted. |
| Superpowers writing-skills (26360) | reference | Over budget; use for the pressure-testing idea, not text. |
| agentskills.io spec | reference | The format contract (frontmatter, folders). |

## 3. CC-BY-SA handling (Trail of Bits)
- Rule (decisions.md, 2026-10-25): rewrite from ideas, cite the source, **no verbatim text**.
- Each OMI skill drawing on it carries a `Source: trailofbits/skills @196a907 (CC-BY-SA-4.0), ideas only` line and was written without the source open (write from the notes in section 2, then check no sentence matches).
- Do not copy even short distinctive phrases or tables; do not copy file structure of a specific skill one-to-one.

## 4. Open issues
- O1: UI UX Pro Max has no license or version in the facts. Needs a LICENSE read before any reuse (currently reference only).
- O2: claude-security is "All rights reserved"; ideas only.
- O3: BMAD license is NOASSERTION on GitHub but MIT per the landscape; read LICENSE at 61e01f8.
- O4: Vercel license blank on GitHub (README says MIT); read LICENSE at 063bee9. Anthropic skills license varies per folder.
- O5: Taste installed plugin is 1.0.0 while the task pins commit 12af471; confirm they are the same content.
- O6: SKILL.md sizes for remote sources are unknown; record them in the group tasks.
- O7: Landscape says Taste, UI UX Pro Max and Ponytail identities were unconfirmed on 2026-10-23; the installed plugins and the Taste repo resolve this for Taste and Ponytail, while the UI UX Pro Max upstream is still unidentified.
