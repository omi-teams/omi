---
id: ci-workflow-audit
group: quality
description: Use when adding or reviewing GitHub Actions workflows, especially those that run AI agents or act on pull requests from forks or issues.
tokens: 652
tools: Read, Grep
source_repo: https://github.com/trailofbits/skills
source_ref: 196a9073ab10d35bacf111f945e02c00b2c6883a
source_file: plugins/agentic-actions-auditor/skills/agentic-actions-auditor/SKILL.md
source_license: CC-BY-SA-4.0
source_use: rewrite
---
<!-- Own wording, ideas only from Trail of Bits "agentic-actions-auditor" (https://github.com/trailofbits/skills, CC-BY-SA-4.0, commit 196a9073ab10d35bacf111f945e02c00b2c6883a). No text copied. -->
# CI workflow audit

Source: ideas only (Trail of Bits agentic-actions-auditor).

## When to use
- A file in `.github/workflows/` is added or changed, above all when a step runs an AI agent or shell code with data from PRs, issues or comments.

## When not to use
- Workflows of other CI systems; general application code (use diff-security-review).

## Inputs
- All workflow files and any composite actions they call; the repo settings the PO can describe.

## Steps
1. List workflow files and their triggers. Mark triggers that run with secrets or write tokens on untrusted input (`pull_request_target`, `issue_comment`, `workflow_run`, issues).
2. Find steps that start an AI agent or an action that executes prompts. Note what text reaches it: PR title, body, branch name, comments, changed files.
3. For each, record the token permissions, the secrets in scope, the tools granted to the agent, and who can trigger it.
4. Check attack paths: attacker text steering the agent (prompt injection); `${{ }}` expressions placed straight into `run:` scripts; checkout of the PR head in a privileged job; broad `permissions`; unpinned actions (tag instead of SHA); secrets echoed to logs; agent allowed to run any shell command.
5. Prove each finding from the file: quote the line numbers and the chain trigger, input, sink. If you cannot trace the chain, list it as a question.
6. Report `file:line | severity | reason | how verified`.
7. Never excuse a risk because "only maintainers trigger it" without finding the check that enforces that.

## Outputs and evidence
- Findings with location, reason and verification; workflows reviewed; a list of what was not checked.

## Stop and escalate
- A privileged trigger fed by untrusted text with secrets or write access: report at once and propose no deployment until fixed.
- Settings you cannot see (repo or org policy): ask the PO; do not assume.

## Tools needed
- Read, Grep (no network needed).
