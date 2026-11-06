"""Host-side review PASS acceptance and gated merge; report text is never executed."""

import datetime
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..common import core
from ..project import tasks, workflows
from ..state import resolve as state
from . import dispatch, run


def section(text: str, heading: str) -> str:
    return text.partition('\n## ' + heading + '\n')[2].split('\n## ', 1)[0]


def marked_criteria(text: str, report: str) -> str:
    """Require exact criterion text after a check marker, never execute report commands."""
    criteria = section(text, 'Acceptance criteria')
    marked = {re.sub(r'^\s*(?:[-*] )?(?:\[[ xX]\] )?✓\s*', '', line).strip()
              for line in report.splitlines() if re.match(r'^\s*(?:[-*] )?(?:\[[ xX]\] )?✓\s*', line)}
    rows = re.findall(r'^- \[[ xX]\] (.+)$', criteria, re.M)
    missing = [row for row in rows if row not in marked and not re.search(
        rf'^(?:AC: )?{re.escape(row)}[ \t]+✓(?:[ \t]|$)', report, re.M)]
    if not rows or missing:
        raise state.StateError('criteria not marked ✓: ' + '; '.join(missing or ['no acceptance criteria']))
    check_hosts(text, report)
    return text.replace('\n## Acceptance criteria\n' + criteria,
                        '\n## Acceptance criteria\n' + re.sub(r'^- \[ \]', '- [x]', criteria, flags=re.M), 1)


def check_hosts(text: str, report: str) -> None:
    """Only an explicit passing host result satisfies a report's HOST request."""
    checkpoint = section(text, 'Checkpoint')
    hosts = [h for h in re.findall(r'^\s*(?:[-*] )?HOST:?[ \t]+(.+)$', report, re.M)
             if h.strip().lower().rstrip('.') not in ('none', 'n/a', '-')]
    passed = set(re.findall(r'^Host: (.+?) -> (?:PASS(?:\b.*)?|passed(?:\b.*)?|0|exit 0)$', checkpoint, re.M))
    pending = [h for h in hosts if h not in passed]
    if pending:
        raise state.StateError('HOST checks need a passing Host: line under ## Checkpoint: ' + '; '.join(pending))


def advance_pass(ctx: Any, perform: Callable, command: Callable) -> None:
    """Reuse advance's context, atomic stage journal and console-free argv runner."""
    task = state.task_file(ctx.project, ctx.tid)
    text = core.read_task(task)
    ctx.report = dispatch.last_report(text, ctx.rec['role'], ctx.rec['started'])
    if ctx.rec['rc'] != 0 or dispatch.verdict(ctx.report) != 'PASS':
        raise state.StateError('newest finished review must exit 0 with verdict PASS')
    if ctx.reject or ctx.why:
        raise state.StateError('--reject and --why apply only after a review FAIL')
    if ctx.progress.get('ci-failed'):
        raise state.StateError('CI failed; finish a fresh review before advancing again')
    ctx.meta = core.parse(text)
    steps = workflows.get_workflow(ctx.project.state, ctx.meta.get('workflow') or workflows.DEFAULT_WORKFLOW)
    sid = ctx.progress.get('step', ctx.meta.get('step'))
    at = next((i for i, s in enumerate(steps) if s['id'] == sid), -1)
    if at < 0 or steps[at]['role'] != ctx.rec['role'] or steps[at].get('gate') != 'review':
        raise state.StateError('run role does not match the current review step')
    starts = re.findall(rf'^- {re.escape(sid)} started (\d{{4}}-\d\d-\d\d \d\d:\d\d)', section(text, 'Steps'), re.M)
    if not starts or datetime.datetime.strptime(starts[-1], '%Y-%m-%d %H:%M') > ctx.rec['started'].replace(second=0, microsecond=0):
        raise state.StateError('finished run is stale for the current step')
    following = steps[at + 1] if at + 1 < len(steps) else {}
    if not ctx.progress.get('step-done') and (ctx.meta.get('step') != sid or tasks.step_states(text).get(sid) != 'started'):
        raise state.StateError('finished run is not for the current review step')
    if ctx.progress.get('step-done') and ctx.meta.get('step') not in (sid, following.get('id')):
        raise state.StateError('finished run is not for the current review step')
    if any(r['running'] and not (ctx.progress.get('step-next') and r['role'] == following.get('role'))
           for r in dispatch.records(ctx.project.code) if r['tid'] == ctx.tid):
        raise state.StateError('task has a running worker')
    check_hosts(text, ctx.report)
    next_review = following.get('gate') == 'review'
    if not next_review and (following.get('gate') != 'auto' or at + 2 != len(steps)):
        raise state.StateError('PASS requires a next reviewer or a final auto acceptance gate')
    if not next_review:
        marked_criteria(text, ctx.report)  # all untrusted-input checks precede mutation
    ctx.progress['step'] = sid
    print('eligibility: review PASS for ' + sid)

    def omi(*args):
        return command(ctx.project.code, [sys.executable, '-m', 'omi', *args])

    def done(_):
        if tasks.step_states(core.read_task(task)).get(sid) != 'done':
            omi('step', ctx.tid, 'done')

    def next_step(_):
        if core.meta(task).get('step') != following['id']:
            omi('step', ctx.tid, 'next')

    if next_review:
        perform(ctx, 'step-done', done)
        perform(ctx, 'step-next', next_step)
        def reviewer(_):
            if not any(r['tid'] == ctx.tid and r['role'] == following['role'] and r['started'] >= ctx.rec['started']
                       for r in dispatch.records(ctx.project.code)):
                omi('dispatch', following['role'], ctx.tid)
        perform(ctx, 'dispatch', reviewer)
        return

    def criteria(_):
        core.write_text(task, tasks.set_front(marked_criteria(core.read_task(task), ctx.report), 'status', 'done'))

    perform(ctx, 'criteria', criteria)
    perform(ctx, 'step-done', done)
    perform(ctx, 'step-next', next_step)
    def accept_done(_):
        if tasks.step_states(core.read_task(task)).get(following['id']) != 'done':
            omi('step', ctx.tid, 'done')
    perform(ctx, 'accept-done', accept_done)
    perform(ctx, 'pre-merge', lambda _: omi('hook', 'pre-merge', ctx.tid) and None)

    # Persist remote and title before merging: gh may remove the worktree/branch.
    def remote(_):
        wt = core.task_worktrees(ctx.project.code).get(ctx.tid)
        if not wt:
            raise state.StateError('task worktree is missing')
        if command(ctx.project.code, ['git', 'branch', '--show-current']) != 'development':
            raise state.StateError('main checkout must be on development')
        ctx.progress['worktree'] = str(wt)
        for name in sorted(command(Path(wt), ['git', 'remote']).splitlines(), key=lambda n: n != 'origin'):
            url = state.normalise_url(command(Path(wt), ['git', 'remote', 'get-url', name]))
            if url.startswith('github.com/'):
                ctx.progress.update(target=name, repository=url.removeprefix('github.com/'))
                break
    perform(ctx, 'remote', remote)
    wt = Path(ctx.progress['worktree'])
    repository = ctx.progress.get('repository')
    branch = 'task/' + ctx.tid

    def gh(*args, allowed=(0,)):
        # Main checkout survives --delete-branch and supplies host authentication.
        return command(ctx.project.code, ['gh', 'pr', *args, '--repo', repository], allowed=allowed)

    def development():
        if command(ctx.project.code, ['git', 'branch', '--show-current']) != 'development':
            raise state.StateError('main checkout must be on development')
        if command(ctx.project.code, ['git', 'status', '--porcelain']):
            raise state.StateError('main checkout must be clean')

    def commit(_):
        if command(wt, ['git', 'status', '--porcelain', '--', '.', f':(exclude).omi/tasks/{ctx.tid}.md']):
            raise state.StateError('worktree has changes beyond the acceptance task file')
        if not ctx.project.detached:
            relative = str(task.relative_to(wt))
            if command(wt, ['git', 'status', '--porcelain', '--', relative]):
                command(wt, ['git', 'add', '--', relative])
                command(wt, ['git', 'commit', '-m', f'chore({ctx.tid}): accept review PASS'])
    perform(ctx, 'commit', commit)

    def title(_):
        ctx.progress['pr-title'] = (json.loads(gh('view', branch, '--json', 'title'))['title'] if repository
                                 else f'[{ctx.tid}] {ctx.meta.get("title", ctx.tid)}')
    perform(ctx, 'title', title)
    subject = ctx.progress['pr-title']
    if repository:
        perform(ctx, 'push', lambda _: command(wt, ['git', 'push', '-u', ctx.progress['target'], branch]) and None)
        def body(_):
            current = core.read_task(task)
            verification = '\n'.join([section(current, 'Usage'),
                                      '\n'.join(l for l in section(current, 'Checkpoint').splitlines() if l.startswith('Host:')),
                                      section(current, 'Steps'), section(current, 'Reports')])
            path = ctx.rec['dir'] / 'pr-body.md'
            known = section(current, 'Known issues') or '\n'.join(
                line.removeprefix('>').strip() for line in section(current, 'Reports').splitlines()
                if line.removeprefix('>').strip().startswith('Known issues:')) or 'None reported.'
            core.write_text(path, tasks.clean_text(f'## Summary\n{ctx.tid}: {ctx.meta.get("title", subject)}\n\n'
                f'## Changes\n{section(current, "Acceptance criteria")}\n## Not in this PR\nNone.\n\n'
                f'## Verification\n{verification}\n## Known issues\n{known}\n'))
            gh('edit', branch, '--body-file', str(path))
        perform(ctx, 'pr-body', body)
        perform(ctx, 'ready', lambda _: gh('ready', branch) and None)

        def checks(*args):
            try:
                gh('checks', branch, *args)
            except state.StateError as exc:
                names = []
                try:
                    rows = json.loads(gh('checks', branch, '--json', 'name,state,bucket', allowed=(0, 1, 8)))
                    names = [r['name'] for r in rows if r.get('bucket') != 'pass']
                except (state.StateError, ValueError, KeyError):
                    pass
                reason = 'CI failed: ' + ', '.join(re.sub(r'[^\w .:/()-]', '', n)[:120] for n in names or ['unknown check'])
                # Save a terminal marker even when reopen itself fails.
                ctx.progress['ci-failed'] = True
                omi('step', ctx.tid, 'reopen', '--why', reason)
                raise state.StateError(reason + '; finish a fresh review') from exc
        perform(ctx, 'ci', lambda _: checks('--watch', '--fail-fast'))
        def merge(_):
            development()
            checks()  # never journal this guard separately from the irreversible merge
            gh('merge', branch, '--squash', '--delete-branch', '--subject', subject)
        perform(ctx, 'merge', merge)
        def pull(_):
            development()
            command(ctx.project.code, ['git', 'pull'])
        perform(ctx, 'pull', pull)
    else:
        def squash(_):
            development()
            command(ctx.project.code, ['git', 'merge', '--squash', branch])
        perform(ctx, 'local-squash', squash)
        perform(ctx, 'merge', lambda _: command(ctx.project.code, ['git', 'commit', '-m', subject]) and None)
    perform(ctx, 'clean', lambda _: omi('clean', ctx.tid) and None)

    def post_test(_):
        if command(ctx.project.code, ['git', 'branch', '--show-current']) != 'development':
            raise state.StateError('post-merge test requires development; no revert')
        cmd = tasks.host_test_command(ctx.project.state)
        if not cmd:
            return 'skipped (host_test is empty)'
        try:
            argv = run.shell_command(cmd)
            if not isinstance(argv, list):
                argv = ['cmd', '/d', '/s', '/c', cmd]
            command(ctx.project.code, argv)
        except state.StateError as exc:
            raise state.StateError('POST-MERGE TEST FAILED; no revert: ' + str(exc)) from exc
    perform(ctx, 'post-merge-test', post_test)
