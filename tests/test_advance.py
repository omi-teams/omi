"""Advance stage ordering, trust boundaries, failure stops and restart recovery (fake git/gh)."""
import contextlib
import datetime
import io
import json
import subprocess
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
            return subprocess.CompletedProcess(argv, 1, '', 'secret credential must not be printed')
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

    def invoke(self, message=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            try:
                advance.advance(self.project, TID, message)
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
                                    'commit: done (clean worktree)', 'rebase: done', 'push: done', 'pr: done',
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
        call.assert_called_once_with(h.project, TID, 'fix: task')
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


def main():
    test_all_stages_and_rerun()
    test_each_stage_failure_and_retry()
    test_eligibility_refuses_without_mutations()
    test_scope_stops_before_staging()
    test_scope_git_path_exact_match()
    test_commit_messages()
    test_non_github_and_existing_pr()
    test_head_change_and_launch_recovery()
    test_cli_and_windows_no_console()
    test_real_git_local_origin()


if __name__ == '__main__':
    main()
    print('advance: ok')
