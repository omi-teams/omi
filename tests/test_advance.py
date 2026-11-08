"""Advance stage ordering, trust boundaries, failure stops and restart recovery (fake git/gh)."""
import contextlib
import datetime
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import helpers
from omi.app import cli
from omi.state import resolve as state
from omi.worker import advance

TID = "TASK-218"
ROLE = "omi-agent-engineer"
STAMP = datetime.datetime(2026, 11, 6, 11, 20)


class Handoff:
    def __init__(self, root):
        self.project = state.Project(root, root)
        self.task = root / 'task.md'
        self.run_dir = root / 'run'
        self.run_dir.mkdir()
        self.text = ("---\nid: TASK-218\nstep: build\nworkflow: flow\n---\n## Steps\n"
                     "- build started 2026-11-06 11:18\n\n## Reports\n"
                     "2026-11-06 11:21 omi-agent-engineer (codex):\n> DONE\n> Suggested commit: feat(worker): advance task\n")
        self.task.write_text(self.text, encoding='utf-8')
        self.rec = dict(tid=TID, role=ROLE, rc=0, running=False, started=STAMP, dir=self.run_dir)
        self.recs = [self.rec]
        self.steps = [dict(id='build', role=ROLE), dict(id='security', role='omi-agent-security-reviewer')]
        self.remote = 'git@github.com:org/repo.git'
        self.calls = []
        self.fail = None
        self.dirty = True
        self.head = 'aaa'
        self.pr = []
        self.bad = []

    def run(self, argv, **kwargs):
        assert isinstance(argv, list) and not kwargs.get('shell'), argv
        assert kwargs['capture_output'] and kwargs['encoding'] == 'utf-8'
        self.calls.append(argv)
        args = argv[1:] if argv[0] == 'git' else argv[2:] if argv[0] == 'gh' else argv[3:]
        name = ('pr' if argv[0] == 'gh' else args[0])
        if name == 'step':
            name = 'step-' + args[-1]
        if name == self.fail or (argv[0] == 'gh' and 'pr-' + args[0] == self.fail):
            return subprocess.CompletedProcess(argv, 1, '', 'secret credential must not be printed' if name in ('push', 'pr') else 'action failed with a useful diagnostic')
        out = ''
        if argv[0] == 'git':
            if args[0] == 'branch': out = 'task/TASK-218'
            elif args[0] == 'status':
                out = (' M app.py\0' if '-z' in args else ' M app.py') if self.dirty else ''
            elif args[0] == 'rev-parse': out = self.head
            elif args[0] == 'commit': self.dirty = False
            elif args == ['rebase', 'development']: self.head = 'bbb'
            elif args == ['remote']: out = 'origin' if self.remote else ''
            elif args[:2] == ['remote', 'get-url']: out = self.remote
        elif argv[0] == 'gh':
            if args[0] == 'list': out = json.dumps(self.pr)
            elif args[0] == 'create':
                body = Path(args[args.index('--body-file') + 1]).read_text(encoding='utf-8')
                assert '## Summary' in body and TID in body and '--draft' in args
                self.pr = [{'number': 1}]
        elif args[:1] == ['step']:
            text = self.task.read_text(encoding='utf-8')
            if args[-1] == 'done':
                text = text.replace('\n## Reports', '- build done 2026-11-06 11:22\n\n## Reports')
            else:
                text = text.replace('step: build', 'step: security')
            self.task.write_text(text, encoding='utf-8')
        return subprocess.CompletedProcess(argv, 0, out, '')

    def invoke(self, message=None, reject=None, why=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            try:
                advance.advance(self.project, TID, message, reject, why)
            except SystemExit as exc:
                return str(exc), output.getvalue()
        return '', output.getvalue()


@contextlib.contextmanager
def handoff():
    with tempfile.TemporaryDirectory() as d, contextlib.ExitStack() as stack:
        h = Handoff(Path(d))
        stack.enter_context(patch.object(advance.dispatch, 'records', side_effect=lambda _: h.recs))
        stack.enter_context(patch.object(advance.state, 'task_file', return_value=h.task))
        stack.enter_context(patch.object(advance.catalogs, 'get_role', side_effect=lambda _, role: {'access': 'write' if role == ROLE else 'read'}))
        stack.enter_context(patch.object(advance.workflows, 'get_workflow', side_effect=lambda *_: h.steps))
        stack.enter_context(patch.object(advance.core, 'task_worktrees', return_value={TID: h.project.code}))
        stack.enter_context(patch.object(advance.scope, 'out_of_scope', side_effect=lambda *_a, **_kw: h.bad))
        stack.enter_context(patch.object(advance.subprocess, 'run', side_effect=h.run))
        yield h


def test_all_stages_and_rerun() -> None:
    with handoff() as h:
        error, out = h.invoke()
        assert not error, error
        assert out.splitlines() == ['eligibility: DONE write run for build', 'scope: checked',
                                    'commit: committed', 'rebase: done', 'push: done', 'pr: done',
                                    'host-test: done', 'step-done: done', 'step-next: done', 'dispatch: done'], out
        assert ['git', 'commit', '-m', 'feat(worker): advance task'] in h.calls
        assert any(c[-3:] == ['dispatch', 'omi-agent-security-reviewer', TID] for c in h.calls)
        assert any('--title' in c and '[TASK-218] feat(worker): advance task' in c for c in h.calls)
        h.calls.clear()
        error, out = h.invoke()
        assert not error and out.count('already done') == 8, (error, out)
        assert not any(c[0] == 'gh' or c[1] in ('add', 'commit', 'rebase', 'push') or c[0] != 'git' for c in h.calls)


def test_each_stage_failure_and_retry() -> None:
    for failure, stage in [('status', 'scope'), ('diff', 'scope'), ('add', 'commit'), ('commit', 'commit'),
                           ('rebase', 'rebase'), ('remote', 'remote'), ('push', 'push'), ('pr', 'pr'),
                           ('pr-create', 'pr'), ('host-test', 'host-test'), ('step-done', 'step-done'), ('step-next', 'step-next'), ('dispatch', 'dispatch')]:
        with handoff() as h:
            h.fail = failure
            error, out = h.invoke()
            assert f'advance {stage} FAILED' in error, (failure, error)
            assert 'secret' not in error + out
            if failure not in ('push', 'pr', 'pr-create'):
                assert 'useful diagnostic' in error, (failure, error)
            failed_at = next(i for i, c in enumerate(h.calls) if (c[1:2] == [failure] or
                              (failure == 'pr' and c[0] == 'gh') or (failure == 'pr-create' and c[:3] == ['gh', 'pr', 'create']) or c[-1:] == [failure.removeprefix('step-')] and failure.startswith('step-') or failure in ('host-test', 'dispatch') and failure in c))
            later = h.calls[failed_at + 1:]
            assert later == ([['git', 'rebase', '--abort']] if failure == 'rebase' else []), later
            h.fail = None
            error, _ = h.invoke()
            assert not error, (failure, error)
            assert sum(c[1:2] == ['commit'] for c in h.calls) <= (2 if failure == 'commit' else 1)


def test_eligibility_refuses_without_mutations() -> None:
    for change, why in [('none', 'no finished'), ('rc', 'exit 0'), ('verdict', 'DONE'), ('read', 'write role'),
                        ('stale', 'stale'), ('step', 'current write step'), ('running', 'running'), ('next', 'reviewer')]:
        with handoff() as h:
            if change == 'none': h.recs = []
            elif change == 'rc': h.rec['rc'] = 1
            elif change == 'verdict': h.task.write_text(h.text.replace('> DONE', '> BLOCKED'), encoding='utf-8')
            elif change == 'read':
                h.rec['role'] = 'omi-agent-reviewer'
                h.task.write_text(h.text.replace(ROLE, h.rec['role']), encoding='utf-8')
            elif change == 'stale': h.rec['started'] = STAMP.replace(hour=10)
            elif change == 'step': h.task.write_text(h.text.replace('step: build', 'step: security'), encoding='utf-8')
            elif change == 'running': h.recs.append({**h.rec, 'running': True})
            else: h.steps[1]['role'] = 'coordinator'
            error, _ = h.invoke()
            assert 'eligibility FAILED' in error and why in error, (change, error)
            assert not (h.run_dir / 'advance.json').exists()
            assert not any(c[0] != 'git' or c[1] not in ('branch',) for c in h.calls)


def test_reproduce_and_fix_in_one_run() -> None:
    for reproduced in (True, False):
        with handoff() as h:
            h.steps = [dict(id='reproduce', role=ROLE), dict(id='fix', role=ROLE), dict(id='security', role=REVIEWER)]
            h.text = h.text.replace('step: build', 'step: reproduce').replace('- build started', '- reproduce started')
            if reproduced:
                h.text = h.text.replace('> DONE\n', '> DONE\n> Reproduced: test_x failed before the fix\n')
            h.task.write_text(h.text, encoding='utf-8')
            plain = h.run

            def run(argv, **kwargs):
                args = argv[3:]
                if argv[0] != 'git' and argv[0] != 'gh' and args[:1] == ['step']:
                    h.calls.append(argv)
                    text = h.task.read_text(encoding='utf-8')
                    cur = text.split('step: ')[1].split('\n')[0]
                    if args[-1] == 'done':
                        text = text.replace('\n## Reports', f'- {cur} done 2026-11-06 11:22\n\n## Reports')
                    else:
                        nxt = {'reproduce': 'fix', 'fix': 'security'}[cur]
                        text = text.replace(f'step: {cur}', f'step: {nxt}').replace('\n## Reports', f'- {nxt} started 2026-11-06 11:23\n\n## Reports')
                    h.task.write_text(text, encoding='utf-8')
                    return subprocess.CompletedProcess(argv, 0, '', '')
                return plain(argv, **kwargs)
            with patch.object(advance.subprocess, 'run', side_effect=run):
                error, out = h.invoke()
            if reproduced:
                assert not error, error
                assert [c[-1] for c in h.calls if c[0] not in ('git', 'gh') and c[3] == 'step'] == ['done', 'next', 'done', 'next']
                assert any(c[-3:] == ['dispatch', REVIEWER, TID] for c in h.calls)
            else:
                assert 'the next workflow step is not a reviewer' in error, error


def test_scope_stops_before_staging() -> None:
    with handoff() as h:
        h.bad = ['outside.py', '.github/workflows/ci.yml']
        error, out = h.invoke()
        assert 'scope FAILED' in error and all('OUT OF SCOPE: ' + p in out for p in h.bad)
        assert not any(c[1] in ('add', 'commit', 'checkout', 'restore') for c in h.calls)


def test_scope_git_path_exact_match() -> None:
    # Exercise the real scope helper with fake git reads, including committed paths.
    from omi.project import scope
    with tempfile.TemporaryDirectory() as d:
        wt = Path(d)
        with patch.object(scope.state, 'resolve', return_value=state.Project(wt, wt, True)), \
                patch.object(scope, 'task_scope', return_value=['.github/**', 'app.py']) as globs, \
                patch.object(scope, 'changed_paths', return_value=(['.github/workflows/ci.yml', 'app.py'], set())):
            assert scope.out_of_scope(wt, TID, committed=True) == ['.github/workflows/ci.yml']
            globs.return_value = ['.github/workflows/ci.yml', 'app.py']
            assert scope.out_of_scope(wt, TID, committed=True) == []


def test_commit_messages() -> None:
    for value in ['', 'update things', 'fix: x\ny', 'fix: x\rx', 'fix: x\x00', 'fix: x\x7f', 'fix: x\u0085', 'fix: x\u2028x']:
        with handoff() as h:
            error, _ = h.invoke(value)
            assert '--message "<msg>"' in error and not h.calls, (value, error)
    for report in ['DONE', 'DONE\nSuggested commit: bad', 'DONE\nSuggested commit: fix: x\nSuggested commit: fix: y']:
        try:
            advance.commit_message(report, None)
        except state.StateError:
            pass
        else:
            raise AssertionError(report)
    try:
        advance.commit_message('DONE\n**Commit message:** `feat(x): y`', None)
    except state.StateError:
        pass
    else:
        raise AssertionError('free-form commit line accepted')
    assert advance.commit_message('Suggested commit: `fix(a): b`', None) == 'fix(a): b'
    # TASK-251: a bullet, bold or backticks around the line still count; a short fix-round report reuses the earlier line
    for report in ['DONE\n- Suggested commit: fix(a): b', 'DONE\n* **Suggested commit:** `fix(a): b`', 'DONE\n  Suggested commit: fix(a): b']:
        assert advance.commit_message(report, None) == 'fix(a): b', report
    earlier = ['DONE\nfixed\nSuggested commit: fix(a): newest', 'DONE\nSuggested commit: fix(a): older']
    assert advance.commit_message('DONE\nfixed the finding', None, earlier) == 'fix(a): newest'
    assert advance.commit_message('DONE\nSuggested commit: feat(b): own', None, earlier) == 'feat(b): own'
    try:
        advance.commit_message('DONE\nfixed the finding', None, ['DONE\nno line here'])
    except state.StateError as exc:
        assert '--message' in str(exc)
    else:
        raise AssertionError('missing Suggested commit everywhere was accepted')
    with handoff() as h:
        error, _ = h.invoke('fix(worker)!: handle `$(literal)` safely')
        assert not error and ['git', 'commit', '-m', 'fix(worker)!: handle `$(literal)` safely'] in h.calls


def test_non_github_and_existing_pr() -> None:
    for remote in ['', '/tmp/local-origin.git', 'https://example.org/repo.git']:
        with handoff() as h:
            h.remote = remote
            error, out = h.invoke()
            assert not error and out.count('skipped (no GitHub remote)') == 2, (error, out)
            assert not any(c[0] == 'gh' or c[1] == 'push' for c in h.calls)
    with handoff() as h:
        h.pr = [{'number': 23}]
        error, _ = h.invoke()
        assert not error and not any(c[:3] == ['gh', 'pr', 'create'] for c in h.calls)


def test_head_change_and_launch_recovery() -> None:
    with handoff() as h:
        h.fail = 'host-test'
        assert 'host-test FAILED' in h.invoke()[0]
        h.head = 'ccc'
        h.fail = None
        assert 'HEAD changed' in h.invoke()[0]
    with handoff() as h:
        h.fail = 'dispatch'
        assert 'dispatch FAILED' in h.invoke()[0]
        h.recs.append(dict(tid=TID, role='omi-agent-security-reviewer', rc=None, running=True, started=STAMP))
        # Simulate launch completing just before the parent died, leaving no marker.
        h.fail = None
        # A running reviewer is recoverable only after step-next completed.
        error, _ = h.invoke()
        assert not error, error
        assert sum(c[-3:] == ['dispatch', 'omi-agent-security-reviewer', TID] for c in h.calls) == 1


def test_cli_and_windows_no_console() -> None:
    with handoff() as h, patch.object(cli.state, 'resolve', return_value=h.project), \
            patch.object(cli.core, 'main_checkout', return_value=h.project.code), \
            patch.object(cli.advance, 'advance') as call:
        cli.dispatch(['advance', TID, '--message', 'fix: task'])
        call.assert_called_once_with(h.project, TID, 'fix: task', None, None)
        call.reset_mock()
        cli.dispatch(['advance', TID, '--reject', '1,3', '--why', 'not a bug'])
        call.assert_called_once_with(h.project, TID, None, [1, 3], 'not a bug')
    with handoff() as h, patch.object(advance.core, 'WINDOWS', True), \
            patch.object(advance.subprocess, 'CREATE_NO_WINDOW', 0x08000000, create=True):
        with patch.object(advance.subprocess, 'run', wraps=h.run) as run:
            assert not h.invoke()[0]
            assert all(c.kwargs['creationflags'] == 0x08000000 for c in run.call_args_list)


def test_real_git_local_origin() -> None:
    # Host smoke test: real temp git repositories; external omi stages stay fake.
    # Runs on Windows too, exercising command()'s CREATE_NO_WINDOW path there.
    real_run = subprocess.run
    real_command = advance.command
    with handoff() as h:
        root = h.project.code
        repo, bare = root / 'repo', root / 'local-origin.git'
        repo.mkdir()

        def git(*args):
            result = real_run(['git', '-C', str(repo), *args], capture_output=True, encoding='utf-8',
                              **({'creationflags': subprocess.CREATE_NO_WINDOW} if advance.core.WINDOWS else {}))
            assert result.returncode == 0, result.stderr
            return result.stdout.strip()

        git('init', '-q', '-b', 'development')
        git('init', '--bare', '-q', str(bare))
        git('remote', 'add', 'origin', str(bare))
        (repo / 'app.py').write_text('value = 1\n', encoding='utf-8')
        git('add', '.')
        git('commit', '-qm', 'chore: base')
        git('branch', 'task/TASK-218')
        (repo / 'base.txt').write_text('new development commit\n', encoding='utf-8')
        git('add', '.')
        git('commit', '-qm', 'chore: advance development')
        development = git('rev-parse', 'HEAD')
        git('checkout', '-q', 'task/TASK-218')
        (repo / 'app.py').write_text('value = 2\n', encoding='utf-8')

        def command(cwd, argv):
            if argv[0] in ('git', 'gh'):
                assert argv[0] == 'git', 'a local remote must never call gh'
                return real_command(cwd, argv)
            result = h.run(argv, cwd=cwd, capture_output=True, encoding='utf-8')
            return result.stdout

        with patch.object(advance.core, 'task_worktrees', return_value={TID: repo}), \
                patch.object(advance, 'command', side_effect=command), \
                patch.object(advance.subprocess, 'run', side_effect=real_run):
            error, out = h.invoke()
            assert not error, error
            assert 'push: skipped (no GitHub remote)' in out and 'pr: skipped (no GitHub remote)' in out
            assert git('log', '-1', '--format=%s') == 'feat(worker): advance task'
            assert git('rev-parse', 'HEAD^') == development
            assert git('status', '--porcelain') == ''
            assert (repo / 'base.txt').exists()
            assert git('ls-remote', 'origin') == '', 'local bare origin must stay untouched'


def test_commit_stage_reports_clean_and_committed() -> None:
    for dirty, expected in [(True, 'committed'), (False, 'nothing to commit')]:
        with handoff() as h:
            h.dirty = dirty
            error, output = h.invoke()
            assert not error, error
            assert 'commit: ' + expected in output
            assert any(c[1:2] == ['commit'] for c in h.calls) == dirty


def test_task_branch_push_uses_lease() -> None:
    with handoff() as h:
        assert not h.invoke()[0]
        pushes = [c for c in h.calls if c[1:2] == ['push']]
        assert pushes == [['git', 'push', '--force-with-lease', '-u', 'origin', 'task/TASK-218']], pushes


def test_failure_output_tail_and_auth_suppression() -> None:
    output = '\n'.join(f'line {i}' for i in range(15)) + '\n\x1b[31museful\x00 detail\x7f\x85\x1b[0m'
    safe = [['git', 'status'], ['git', 'rebase', 'development'], [sys.executable, '-m', 'omi', 'host-test', TID]]
    hidden = [['gh', 'pr', 'list'], ['git', 'push', '--force-with-lease', 'origin', 'task/' + TID]]
    for argv in safe + hidden:
        for stream in ('stdout', 'stderr'):
            result = subprocess.CompletedProcess(argv, 1, output if stream == 'stdout' else '', output if stream == 'stderr' else '')
            with patch.object(advance.subprocess, 'run', return_value=result):
                try:
                    advance.command(Path('.'), argv)
                except state.StateError as exc:
                    error = str(exc)
                else:
                    raise AssertionError('command failure was swallowed')
            assert error.startswith('command exited 1')
            if argv in hidden:
                assert error == 'command exited 1', error
            else:
                assert 'useful detail' in error and 'line 5\n' not in error and 'line 6\n' in error, repr(error)
                assert not any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in error if c != '\n'), repr(error)
                assert '[31m' not in error and len(error.splitlines()) <= 11, repr(error)


def test_real_git_push_after_rebase_keeps_lease() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        repo, origin = root / 'repo', root / 'origin.git'
        repo.mkdir()

        def git(*args):
            return advance.command(repo, ['git', *args])

        git('init', '-q', '-b', 'development')
        git('init', '--bare', '-q', str(origin))
        git('remote', 'add', 'origin', str(origin))
        (repo / 'app.py').write_text('value = 1\n', encoding='utf-8')
        git('add', '.')
        git('commit', '-qm', 'chore: base')
        git('checkout', '-qb', 'task/' + TID)
        (repo / 'app.py').write_text('value = 2\n', encoding='utf-8')
        git('commit', '-qam', 'fix: task change')
        git('push', '-u', 'origin', 'task/' + TID)
        git('checkout', '-q', 'development')
        (repo / 'base.txt').write_text('development moved\n', encoding='utf-8')
        git('add', '.')
        git('commit', '-qm', 'chore: development change')
        git('push', 'origin', 'development')
        development = git('rev-parse', 'HEAD')
        git('checkout', '-q', 'task/' + TID)
        git('rebase', 'development')
        ctx = advance.Context(state.Project(repo, repo), TID, {}, {})
        ctx.wt, ctx.target = repo, 'origin'
        advance.push(ctx)
        head = git('rev-parse', 'HEAD')
        assert git('--git-dir', str(origin), 'rev-parse', 'refs/heads/task/' + TID) == head
        assert git('--git-dir', str(origin), 'rev-parse', 'refs/heads/development') == development
        # An unseen remote change must still block the next task-branch push.
        git('--git-dir', str(origin), 'update-ref', 'refs/heads/task/' + TID, development)
        try:
            advance.push(ctx)
        except state.StateError as exc:
            assert str(exc) == 'command exited 1', str(exc)
        else:
            raise AssertionError('push ignored a changed remote lease')
        assert git('--git-dir', str(origin), 'rev-parse', 'refs/heads/task/' + TID) == development
        assert git('--git-dir', str(origin), 'rev-parse', 'refs/heads/development') == development


REVIEWER = 'omi-agent-security-reviewer'


class ReviewFail(Handoff):
    """A security review FAIL for the `security` step; `omi step back` is faked on the task file."""
    def __init__(self, root):
        super().__init__(root)
        self.text = ("---\nid: TASK-218\nstep: security\nworkflow: flow\n---\n## Checkpoint\nDone: build\nNext: review\n\n## Steps\n"
                     "- build done 2026-11-06 11:10\n- security started 2026-11-06 11:18\n\n## Reports\n"
                     "2026-11-06 11:21 omi-agent-security-reviewer (codex):\n> VERDICT: FAIL\n"
                     "> Review round 1 FAIL: quoted by the reviewer\n> - a.py:1 quotes Review round 1 FAIL:\n"
                     "> - b.py:2 see ## Steps\n> ## Steps\n> - c.py:3 control\x07 char\n> ROOT: new\n")
        self.task.write_text(self.text, encoding='utf-8')
        self.rec.update(role=REVIEWER)
        self.steps = [dict(id='build', role=ROLE), dict(id='security', role=REVIEWER)]
        self.pr = [{'number': 7, 'isDraft': False}]
        self.back_out = 'TASK-218: step security failed; back to build'

    def run(self, argv, **kwargs):
        if argv[0] not in ('git', 'gh') and argv[3:5] == ['step', TID]:
            self.calls.append(argv)
            if self.fail == 'step-back':
                return subprocess.CompletedProcess(argv, 1, '', 'ROUND LIMIT: TASK-218 failed 2 review rounds; the Coordinator decides')
            self.why = argv[argv.index('--why') + 1] if '--why' in argv else None
            self.task.write_text(self.task.read_text(encoding='utf-8').replace('step: security', 'step: build'), encoding='utf-8')
            return subprocess.CompletedProcess(argv, 0, self.back_out, '')
        return super().run(argv, **kwargs)

    def invoke(self, *args, **kwargs):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            try:
                advance.advance(self.project, TID, *args, **kwargs)
            except SystemExit as exc:
                return str(exc), output.getvalue()
        return '', output.getvalue()


@contextlib.contextmanager
def review_fail():
    with tempfile.TemporaryDirectory() as d, contextlib.ExitStack() as stack:
        h = ReviewFail(Path(d))
        h.recs[0].update(role=REVIEWER)
        stack.enter_context(patch.object(advance.dispatch, 'records', side_effect=lambda _: h.recs))
        stack.enter_context(patch.object(advance.state, 'task_file', return_value=h.task))
        stack.enter_context(patch.object(advance.workflows, 'get_workflow', side_effect=lambda *_: h.steps))
        stack.enter_context(patch.object(advance.core, 'task_worktrees', return_value={TID: h.project.code}))
        stack.enter_context(patch.object(advance.subprocess, 'run', side_effect=h.run))
        yield h


USAGE = "\n## Usage\n| role | model |\n|---|---|\n| omi-agent-security-reviewer | m | high | 1 | 1 | 1 | 1s | - | FAIL |\n"


def checkpoint_of(h):
    return h.task.read_text(encoding='utf-8').partition('\n## Checkpoint\n')[2].split('\n## ', 1)[0]


def test_review_fail_path_and_rerun() -> None:
    with review_fail() as h:
        h.task.write_text(h.text + USAGE, encoding='utf-8')
        error, out = h.invoke()
        assert not error, (error, out)
        assert out.splitlines()[1:] == ['findings: 3 finding(s) under Review round 1 FAIL:', 'step-back: done',
                                        'pr-draft: back to draft', f'dispatch: {ROLE} dispatched'], out
        text = h.task.read_text(encoding='utf-8')
        # Placed between ## Checkpoint and ## Steps; the quoted marker and heading in findings do not confuse it.
        assert text.index('## Checkpoint') < text.index('\nReview round 1 FAIL:\n- a.py:1') < text.index('\n## Steps\n')
        assert checkpoint_of(h).endswith('Next: review\nReview round 1 FAIL:\n- a.py:1 quotes Review round 1 FAIL:\n'
                                         '- b.py:2 see ## Steps\n- c.py:3 control char\n'), repr(checkpoint_of(h))
        assert [c for c in h.calls if c[:2] == ['gh', 'pr'] and 'ready' in c] == [['gh', 'pr', 'ready', '--undo', '7', '--repo', 'org/repo']]
        assert any(c[-3:] == ['dispatch', ROLE, TID] for c in h.calls)
        h.calls.clear()
        h.recs.append(dict(tid=TID, role=ROLE, rc=None, running=True, started=STAMP.replace(minute=30)))
        error, out = h.invoke()
        assert not error and out.count('already done') == 4 and not h.calls, (error, out, h.calls)
        assert h.task.read_text(encoding='utf-8').count('\nReview round 1 FAIL:\n') == 1


def test_review_fail_resume_does_not_duplicate() -> None:
    with review_fail() as h:
        h.task.write_text(h.text + USAGE, encoding='utf-8')
        h.fail = 'dispatch'
        assert 'dispatch FAILED' in h.invoke()[0]
        h.fail = None
        assert not h.invoke()[0]
        assert h.task.read_text(encoding='utf-8').count('\nReview round 1 FAIL:\n') == 1


def test_review_fail_reject() -> None:
    with review_fail() as h:
        error, out = h.invoke(None, [2], 'not a defect')
        assert not error, error
        cp = checkpoint_of(h)
        assert '- b.py:2' not in cp and '- a.py:1' in cp and '- c.py:3' in cp
        assert 'Coordinator rejected finding 2: not a defect' in cp and h.why == 'not a defect'
    with review_fail() as h:
        error, out = h.invoke(None, [1, 2, 3], 'all noise')
        assert error == '1' and 'the Coordinator decides' in out and '--po' in out, (error, out)
        assert h.task.read_text(encoding='utf-8') == h.text and not h.calls
    with review_fail() as h:
        assert '--reject needs --why' in h.invoke(None, [1])[0] and 'finding(s)' in h.invoke(None, [9], 'x')[0]
        assert h.task.read_text(encoding='utf-8') == h.text and not h.calls


def test_review_fail_stops_and_refusals() -> None:
    with review_fail() as h:
        h.fail = 'step-back'
        error, out = h.invoke()
        assert error == '1' and 'ROUND LIMIT: TASK-218' in out and not any(c[0] == 'gh' for c in h.calls), (error, out)
    with review_fail() as h:
        h.back_out = 'TASK-218: step security failed; back to build\nREPLAN: same root cause'
        error, out = h.invoke()
        assert error == '1' and 'REPLAN: same root cause' in out and not any(c[-3:-1] == ['dispatch', ROLE] for c in h.calls)
    with review_fail() as h:
        h.back_out = 'REPLAN: same root cause'
        h.steps.insert(0, dict(id='plan', role='omi-agent-architect'))
        h.task.write_text(h.text.replace('step: security', 'step: security'), encoding='utf-8')
        real = h.run

        def back_to_plan(argv, **kw):
            result = real(argv, **kw)
            if argv[0] not in ('git', 'gh') and argv[3:5] == ['step', TID]:
                h.task.write_text(h.task.read_text(encoding='utf-8').replace('step: build', 'step: plan'), encoding='utf-8')
            return result
        with patch.object(advance.subprocess, 'run', side_effect=back_to_plan):
            error, out = h.invoke()
        assert not error and any(c[-3:] == ['dispatch', 'omi-agent-architect', TID] for c in h.calls), (error, out)
    for change, why in [('pass', 'current review step'), ('rc', 'FAIL'), ('done', 'step'), ('stale', 'stale'), ('nofinding', 'finding'), ('running', 'running')]:
        with review_fail() as h:
            if change == 'pass': h.task.write_text(h.text.replace('VERDICT: FAIL', 'VERDICT: PASS'), encoding='utf-8')
            elif change == 'rc': h.rec['rc'] = 1
            elif change == 'done': h.task.write_text(h.text.replace('- security started 2026-11-06 11:18', '- security done 2026-11-06 11:30'), encoding='utf-8')
            elif change == 'stale': h.rec['started'] = STAMP.replace(hour=10)
            elif change == 'nofinding': h.task.write_text(h.text.replace('> - ', '> * '), encoding='utf-8')
            else: h.recs.append({**h.rec, 'running': True})
            error, _ = h.invoke()
            assert 'eligibility FAILED' in error and why in error, (change, error)
            assert not h.calls and not (h.run_dir / 'advance.json').exists()
    with review_fail() as h:
        h.remote = 'https://example.org/repo.git'
        error, out = h.invoke()
        assert not error and 'pr-draft: skipped (no GitHub remote)' in out and not any(c[0] == 'gh' for c in h.calls)
    with review_fail() as h:
        h.pr = [{'number': 7, 'isDraft': True}]
        error, out = h.invoke()
        assert not error and 'skipped (no open non-draft PR)' in out and not any(c[:3] == ['gh', 'pr', 'ready'] for c in h.calls)
    with handoff() as h:
        assert '--reject and --why apply only after a review FAIL' in h.invoke(None, [1], 'x')[0]


def test_rebase_regenerates_generated_conflicts() -> None:
    """TASK-251: a rebase that conflicts only in `generated` files finishes by regenerating them; any other conflict still aborts."""
    from types import SimpleNamespace
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        repo, cfg = root / "repo", root / "state"
        (cfg / ".omi").mkdir(parents=True)
        regen = root / "regen.py"  # gen.txt lists every src file: both branches add one, so both edit gen.txt
        regen.write_text("from pathlib import Path\nPath('gen.txt').write_text(''.join(sorted(p.name + '\\n' for p in Path('src').glob('*.txt'))))\n")
        (cfg / ".omi" / "config.json").write_text(json.dumps({"generated": ["gen.txt"], "regenerate": f'"{sys.executable}" "{regen}"'}))
        run = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True).stdout.strip()
        repo.mkdir()
        run("init", "-q", "-b", "development")
        run("config", "user.email", "t@t"); run("config", "user.name", "t")
        (repo / "src").mkdir()
        (repo / "src" / "a.txt").write_text("a\n")
        (repo / "shared.txt").write_text("base\n")
        subprocess.run([sys.executable, str(regen)], cwd=repo, check=True)
        run("add", "-A"); run("commit", "-qm", "base")
        run("checkout", "-qb", "task/TASK-900")
        (repo / "src" / "b.txt").write_text("b\n")
        subprocess.run([sys.executable, str(regen)], cwd=repo, check=True)
        run("add", "-A"); run("commit", "-qm", "task adds b")
        run("checkout", "-q", "development")
        (repo / "src" / "c.txt").write_text("c\n")
        subprocess.run([sys.executable, str(regen)], cwd=repo, check=True)
        run("add", "-A"); run("commit", "-qm", "development adds c")
        run("checkout", "-q", "task/TASK-900")
        ctx = SimpleNamespace(wt=repo, project=SimpleNamespace(state=cfg), progress={})
        advance.rebase(ctx)
        assert (repo / "gen.txt").read_text() == "a.txt\nb.txt\nc.txt\n" and run("status", "--porcelain") == ""
        assert run("log", "--format=%s", "-3").splitlines() == ["task adds b", "development adds c", "base"]
        assert ctx.progress["head"] == run("rev-parse", "HEAD")
        # a conflict outside `generated` is not resolved: the rebase is aborted as before
        run("checkout", "-q", "development")
        (repo / "shared.txt").write_text("development\n"); run("commit", "-qam", "dev edits shared")
        run("checkout", "-q", "task/TASK-900")
        (repo / "shared.txt").write_text("task\n"); run("commit", "-qam", "task edits shared")
        head = run("rev-parse", "HEAD")
        try:
            advance.rebase(ctx)
        except state.StateError as exc:
            assert "rebase failed; aborted" in str(exc)
        else:
            raise AssertionError("a real conflict was resolved")
        assert run("rev-parse", "HEAD") == head and run("status", "--porcelain") == ""


def main():
    test_rebase_regenerates_generated_conflicts()
    test_commit_stage_reports_clean_and_committed()
    test_task_branch_push_uses_lease()
    test_real_git_push_after_rebase_keeps_lease()
    test_failure_output_tail_and_auth_suppression()
    test_all_stages_and_rerun()
    test_each_stage_failure_and_retry()
    test_eligibility_refuses_without_mutations()
    test_reproduce_and_fix_in_one_run()
    test_scope_stops_before_staging()
    test_scope_git_path_exact_match()
    test_commit_messages()
    test_non_github_and_existing_pr()
    test_head_change_and_launch_recovery()
    test_cli_and_windows_no_console()
    test_real_git_local_origin()
    test_review_fail_path_and_rerun()
    test_review_fail_resume_does_not_duplicate()
    test_review_fail_reject()
    test_review_fail_stops_and_refusals()


if __name__ == '__main__':
    main()
    print('advance: ok')
