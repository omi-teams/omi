"""Host-side review PASS acceptance and gated merge; report text is never executed."""

import datetime
import json
import re
import sys
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any

from ..common import core
from ..project import tasks, workflows
from ..state import resolve as state
from . import dispatch, pr, run


def section(text: str, heading: str) -> str:
    return text.partition('\n## ' + heading + '\n')[2].split('\n## ', 1)[0]


def marked_criteria(text: str, report: str, worktree: Path | None = None) -> str:
    """Accept complete ordered AC statuses, otherwise require exact criterion text."""
    criteria = section(text, 'Acceptance criteria')
    marked = {re.sub(r'^\s*(?:[-*] )?(?:\[[ xX]\] )?✓\s*', '', line).strip()
              for line in report.splitlines() if re.match(r'^\s*(?:[-*] )?(?:\[[ xX]\] )?✓\s*', line)}
    rows = re.findall(r'^- \[[ xX]\] (.+)$', criteria, re.M)
    ac_lines = re.findall(r'^[ \t]*(?:[-*] )?AC: ?.*$', report, re.M)
    statuses = []
    for line in ac_lines:
        body = re.sub(r'^[ \t]*(?:[-*] )?AC: ?', '', line)
        criterion = max((row for row in rows if body.startswith(row)), key=len, default='')
        statuses.append(re.search(r'[ \t]+(✓|✗|UNVERIFIED|QA)(?:[ \t]|$)', body[len(criterion):]))
    ordered = len(ac_lines) == len(rows) and all(status and status[1] == '✓' for status in statuses)
    missing = [row for row in rows if not ordered and row not in marked and not re.search(
        rf'^[ \t]*(?:[-*] )?(?:AC: )?{re.escape(row)}[ \t]+✓(?:[ \t]|$)', report, re.M)]
    if not rows or missing:
        raise state.StateError('criteria not marked ✓: ' + '; '.join(missing or ['no acceptance criteria']))
    check_hosts(text, report, worktree)
    return text.replace('\n## Acceptance criteria\n' + criteria,
                        '\n## Acceptance criteria\n' + re.sub(r'^- \[ \]', '- [x]', criteria, flags=re.M), 1)


HOST_LINE = re.compile(r'^Host: (.+?) \[(host|container|ci)\] -> (PASS|FAIL)\b')  # command, environment, result


def check_hosts(text: str, report: str, worktree: Path | None = None) -> None:
    """Accept explicit host results (`Host: <command> [host|container|ci] -> PASS`) or the latest host-test PASS on current HEAD."""
    checkpoint = section(text, 'Checkpoint')
    hosts = [h for h in re.findall(r'^\s*(?:[-*] )?HOST:?[ \t]+(.+)$', report, re.M)
             if not re.match(r'(?:none|n/a|-)\s*(?:[;:]|$)', h.strip(), re.I)]  # `HOST: none; <why>` is no host check, `HOST: - X` is one
    lines = re.findall(r'^Host:.*$', checkpoint, re.M)
    bad = [line for line in lines if not HOST_LINE.match(line)]
    if bad:
        raise state.StateError('Host lines need a command and an environment, `Host: <command> [host|container|ci] -> PASS|FAIL`: '
                               + '; '.join(bad))
    passed = [m[1].strip('` ') for m in map(HOST_LINE.match, lines) if m[3] == 'PASS']
    pending = [h for h in hosts if h.strip('` ') not in passed and h not in passed]
    host_tests = [h for h in pending if re.match(r'host[- ]test\b', h, re.I)]
    if host_tests and worktree is not None:
        head = core.git(worktree, 'rev-parse', '--short=7', 'HEAD')
        rows = [r[-1] for r in tasks.usage_rows(text) if r[0] == 'host-test']
        if head and rows and rows[-1] == f'PASS {head}':
            pending = [h for h in pending if h not in host_tests]
    if pending:
        raise state.StateError('HOST checks need a passing Host: line under ## Checkpoint; after running each check, record: '
                               + '; '.join(f'Host: {item} [host] -> PASS' for item in pending))


def passed_on_head(ctx: Any, role: str, command: Callable) -> bool:
    """True when `role`'s newest Usage verdict is PASS on the task worktree's current HEAD (TASK-241: no second review of it)."""
    wt = core.task_worktrees(ctx.project.code).get(ctx.tid)
    try:
        head = command(Path(wt), ['git', 'rev-parse', '--short=7', 'HEAD']) if wt else ''
    except state.StateError:
        head = ''
    rows = [r[-1] for r in tasks.usage_rows(core.read_task(task_file(ctx))) if r[0] == role]
    return bool(head and rows and rows[-1].split()[:2] == ['PASS', head])


def eligible(ctx: Any) -> bool:
    """Validate the current review and all report evidence before any mutation."""
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
    first = workflows.stage_of(steps, sid)[0]['id']  # a stage's reviewers all ran from its first step's start
    starts = re.findall(rf'^- {re.escape(first)} started (\d{{4}}-\d\d-\d\d \d\d:\d\d)', section(text, 'Steps'), re.M)
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
    worktree = core.task_worktrees(ctx.project.code).get(ctx.tid)
    check_hosts(text, ctx.report, worktree)
    next_review = following.get('gate') == 'review'
    if not next_review and (following.get('gate') != 'auto' or at + 2 != len(steps)):
        raise state.StateError('PASS requires a next reviewer or a final auto acceptance gate')
    if not next_review:
        marked_criteria(text, ctx.report, worktree)  # all untrusted-input checks precede mutation
    ctx.step, ctx.following = steps[at], following
    ctx.review_roles = tuple(s['role'] for s in steps if s.get('gate') == 'review')
    ctx.progress['step'] = sid
    return next_review


def task_file(ctx: Any) -> Path:
    return state.task_file(ctx.project, ctx.tid)


def omi(ctx: Any, command: Callable, *args: str) -> str:
    return command(ctx.project.code, [sys.executable, '-m', 'omi', *args])


def gh(ctx: Any, command: Callable, *args: str, allowed: tuple[int, ...] = (0,)) -> str:
    # The main checkout survives --delete-branch and supplies host authentication.
    return command(ctx.project.code, ['gh', 'pr', *args, '--repo', ctx.progress['repository']], allowed=allowed)


def stage(ctx: Any, perform: Callable, command: Callable, name: str, action: Callable) -> None:
    perform(ctx, name, partial(action, command=command))


def tick_criteria(ctx: Any, command: Callable) -> None:
    task = task_file(ctx)
    core.write_text(task, tasks.set_front(marked_criteria(core.read_task(task), ctx.report, core.task_worktrees(ctx.project.code).get(ctx.tid)), 'status', 'done'))


def step_done(ctx: Any, command: Callable) -> None:
    if tasks.step_states(core.read_task(task_file(ctx))).get(ctx.step['id']) != 'done':
        omi(ctx, command, 'step', ctx.tid, 'done')


def step_next(ctx: Any, command: Callable) -> None:
    if core.meta(task_file(ctx)).get('step') != ctx.following['id']:
        omi(ctx, command, 'step', ctx.tid, 'next')


def reviewer(ctx: Any, command: Callable) -> str | None:
    if ctx.following.get('stage') and ctx.following.get('stage') == ctx.step.get('stage'):
        return 'skipped (ran with its stage)'
    if ctx.following['role'] == ctx.rec['role'] or passed_on_head(ctx, ctx.following['role'], command):
        return f"skipped ({ctx.following['role']} PASS on this HEAD already)"
    if not any(r['tid'] == ctx.tid and r['role'] == ctx.following['role'] and r['started'] >= ctx.rec['started']
               for r in dispatch.records(ctx.project.code)):
        omi(ctx, command, 'dispatch', ctx.following['role'], ctx.tid)


def accept_done(ctx: Any, command: Callable) -> None:
    if tasks.step_states(core.read_task(task_file(ctx))).get(ctx.following['id']) != 'done':
        omi(ctx, command, 'step', ctx.tid, 'done')


def pre_merge(ctx: Any, command: Callable) -> None:
    omi(ctx, command, 'hook', 'pre-merge', ctx.tid)


def accept_review(ctx: Any, perform: Callable, command: Callable, next_review: bool) -> None:
    """Tick final criteria and finish acceptance, or hand off to the next reviewer."""
    if not next_review:
        stage(ctx, perform, command, 'criteria', tick_criteria)
    stage(ctx, perform, command, 'step-done', step_done)
    stage(ctx, perform, command, 'step-next', step_next)
    if next_review:
        stage(ctx, perform, command, 'dispatch', reviewer)
    else:
        stage(ctx, perform, command, 'accept-done', accept_done)
        stage(ctx, perform, command, 'pre-merge', pre_merge)


def remote(ctx: Any, command: Callable) -> None:
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


def development(ctx: Any, command: Callable) -> None:
    if command(ctx.project.code, ['git', 'branch', '--show-current']) != 'development':
        raise state.StateError('main checkout must be on development')
    if command(ctx.project.code, ['git', 'status', '--porcelain']):
        raise state.StateError('main checkout must be clean')


def commit(ctx: Any, command: Callable) -> None:
    wt = Path(ctx.progress['worktree'])
    if command(wt, ['git', 'status', '--porcelain', '--', '.', f':(exclude).omi/tasks/{ctx.tid}.md']):
        raise state.StateError('worktree has changes beyond the acceptance task file')
    if not ctx.project.detached:
        relative = str(task_file(ctx).relative_to(wt))
        if command(wt, ['git', 'status', '--porcelain', '--', relative]):
            command(wt, ['git', 'add', '--', relative])
            command(wt, ['git', 'commit', '-m', f'chore({ctx.tid}): accept review PASS'])


def title(ctx: Any, command: Callable) -> None:
    ctx.progress['pr-title'] = (json.loads(gh(ctx, command, 'view', 'task/' + ctx.tid, '--json', 'title'))['title']
                                if ctx.progress.get('repository') else f'[{ctx.tid}] {ctx.meta.get("title", ctx.tid)}')


def push(ctx: Any, command: Callable) -> None:
    command(Path(ctx.progress['worktree']), ['git', 'push', '-u', ctx.progress['target'], 'task/' + ctx.tid])


def update_body(ctx: Any, command: Callable) -> None:
    path = ctx.rec['dir'] / 'pr-body.md'
    core.write_text(path, pr.acceptance_body(ctx.tid, core.read_task(task_file(ctx)), ctx.review_roles))
    gh(ctx, command, 'edit', 'task/' + ctx.tid, '--body-file', str(path))


def ready(ctx: Any, command: Callable) -> None:
    gh(ctx, command, 'ready', 'task/' + ctx.tid)


def checks(ctx: Any, command: Callable, *args: str) -> None:
    """Only actual failed/cancelled checks reopen; missing or pending CI blocks merge."""
    try:
        gh(ctx, command, 'checks', 'task/' + ctx.tid, *args)
    except state.StateError as exc:
        try:
            rows = json.loads(gh(ctx, command, 'checks', 'task/' + ctx.tid, '--json', 'name,state,bucket', allowed=(0, 1, 8)))
            if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
                raise ValueError('invalid check list')
            names = [r['name'] for r in rows if r.get('bucket') in ('fail', 'cancel')]
            if any(not isinstance(name, str) for name in names):
                raise ValueError('invalid check name')
        except (state.StateError, ValueError, KeyError) as query_error:
            raise state.StateError('CI status unavailable; merge blocked; retry advance') from query_error
        if not rows:
            raise state.StateError('no checks reported; merge blocked; configure CI and rerun advance') from exc
        if not names:
            raise state.StateError('CI not passing; merge blocked; retry advance') from exc
        reason = 'CI failed: ' + ', '.join(re.sub(r'[^\w .:/()-]', '', n)[:120] for n in names)
        ctx.progress['ci-failed'] = True
        omi(ctx, command, 'step', ctx.tid, 'reopen', '--why', reason)
        raise state.StateError(reason + '; finish a fresh review') from exc


def watch_ci(ctx: Any, command: Callable) -> None:
    checks(ctx, command, '--watch', '--fail-fast')


def merge(ctx: Any, command: Callable) -> str | None:
    if json.loads(gh(ctx, command, 'view', 'task/' + ctx.tid, '--json', 'state'))['state'] == 'MERGED':
        return 'already merged'
    development(ctx, command)
    checks(ctx, command)  # Never journal this guard separately from the irreversible merge.
    gh(ctx, command, 'merge', 'task/' + ctx.tid, '--squash', '--delete-branch', '--subject', ctx.progress['pr-title'])


def pull(ctx: Any, command: Callable) -> None:
    development(ctx, command)
    command(ctx.project.code, ['git', 'pull'])


def local_squash(ctx: Any, command: Callable) -> None:
    development(ctx, command)
    command(ctx.project.code, ['git', 'merge', '--squash', 'task/' + ctx.tid])


def local_commit(ctx: Any, command: Callable) -> None:
    command(ctx.project.code, ['git', 'commit', '-m', ctx.progress['pr-title']])


def clean(ctx: Any, command: Callable) -> None:
    omi(ctx, command, 'clean', ctx.tid)


def post_test(ctx: Any, command: Callable) -> str | None:
    if command(ctx.project.code, ['git', 'branch', '--show-current']) != 'development':
        raise state.StateError('post-merge test requires development; no revert')
    cmd = tasks.host_test_command(ctx.project.state)
    if not cmd:
        return 'skipped (host_test is empty)'
    try:
        argv = run.shell_command(cmd)
        # run.shell_command returns a list, or a cmd command string on Windows
        # without Git Bash. Preserve that fallback using explicit argv (no shell=True).
        if isinstance(argv, str):
            argv = ['cmd', '/d', '/s', '/c', cmd]
        command(ctx.project.code, argv)
    except state.StateError as exc:
        raise state.StateError('POST-MERGE TEST FAILED; no revert: ' + str(exc)) from exc
    return None


def merge_task(ctx: Any, perform: Callable, command: Callable) -> None:
    """Prepare the reviewed branch, enforce CI, merge, clean and test development."""
    for name, action in [('remote', remote), ('commit', commit), ('title', title)]:
        stage(ctx, perform, command, name, action)
    if ctx.progress.get('repository'):
        actions = [('push', push), ('pr-body', update_body), ('ready', ready), ('ci', watch_ci), ('merge', merge), ('pull', pull)]
    else:
        actions = [('local-squash', local_squash), ('merge', local_commit)]
    for name, action in [*actions, ('clean', clean), ('post-merge-test', post_test)]:
        stage(ctx, perform, command, name, action)


def advance_pass(ctx: Any, perform: Callable, command: Callable) -> None:
    """Run the validated review handoff or final acceptance and merge stages."""
    next_review = eligible(ctx)
    print('eligibility: review PASS for ' + ctx.step['id'])
    accept_review(ctx, perform, command, next_review)
    if not next_review:
        merge_task(ctx, perform, command)
