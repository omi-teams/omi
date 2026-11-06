"""Review PASS acceptance, merge gates and restart recovery with fake argv tools."""
import contextlib
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from test_advance import handoff, STAMP, TID
from omi.worker import advance
from omi.app import cli
from omi.project import tasks

REVIEWER = 'omi-agent-reviewer'


@contextlib.contextmanager
def accepted():
    with handoff() as h:
        h.rec['role'] = REVIEWER
        h.steps = [dict(id='review', role=REVIEWER, gate='review'),
                   dict(id='accept', role='coordinator', gate='auto')]
        h.text = ('---\nid: TASK-218\ntitle: feat: accept\nstatus: in-progress\nstep: review\nworkflow: flow\n---\n'
                  '## Acceptance criteria\n- [ ] handles input\n- [ ] rejects invalid input\n\n'
                  '## Checkpoint\nHost: python check.py -> PASS\n\n## Steps\n'
                  '- review started 2026-11-06 11:18\n\n## Reports\n'
                  '2026-11-06 11:21 omi-agent-reviewer (codex):\n> VERDICT: PASS\n'
                  '> ✓ handles input\n> ✓ rejects invalid input\n> HOST: python check.py\n\n'
                  '## Usage\n| host-test | m | PASS abc1234 |\n| omi-agent-reviewer | PASS abc1234 |\n')
        h.task.write_text(h.text, encoding='utf-8')
        h.dirty = False
        original = h.run
        def run(argv, **kw):
            executable = argv[0].replace('\\', '/').rsplit('/', 1)[-1].lower()
            if executable in ('bash', 'bash.exe', 'sh', 'sh.exe', 'cmd', 'cmd.exe'):
                h.calls.append(argv)
                return subprocess.CompletedProcess(argv, 1 if h.fail == 'post-merge-test' else 0, '', '')
            if argv == ['git', 'status', '--porcelain', '--', 'task.md']:
                h.calls.append(argv)
                return subprocess.CompletedProcess(argv, 0, ' M task.md', '')
            if argv == ['git', 'branch', '--show-current']:
                h.calls.append(argv)
                return subprocess.CompletedProcess(argv, 0, 'development', '')
            args = argv[3:] if argv[0] not in ('git', 'gh') else argv[2:] if argv[0] == 'gh' else argv[1:]
            if argv[0] == 'gh' and args[0] == 'view':
                h.calls.append(argv)
                return subprocess.CompletedProcess(argv, 0, json.dumps({'title': '[TASK-218] feat: accept'}), '')
            if argv[0] == 'gh' and args[:1] == ['checks'] and '--json' in args:
                h.calls.append(argv)
                return subprocess.CompletedProcess(argv, 1, '[{"name":"unit","state":"FAILURE","bucket":"fail"}]', '')
            if argv[0] not in ('git', 'gh') and args[:1] == ['step']:
                h.calls.append(argv)
                name = 'step-' + args[2]
                if h.fail == name:
                    return subprocess.CompletedProcess(argv, 1, '', 'failed')
                text = h.task.read_text(encoding='utf-8')
                if args[2] == 'next': text = text.replace('step: review', 'step: accept')
                if args[2] == 'done':
                    sid = 'accept' if 'step: accept' in text else 'review'
                    text = text.replace('\n## Reports', f'- {sid} done 2026-11-06 11:22\n\n## Reports')
                h.task.write_text(text, encoding='utf-8')
                return subprocess.CompletedProcess(argv, 0, '', '')
            return original(argv, **kw)
        with patch.object(advance.subprocess, 'run', side_effect=run):
            yield h


def test_pass_merge_and_resume() -> None:
    with accepted() as h:
        error, out = h.invoke()
        assert not error, (error, out)
        assert '- [x] handles input' in h.task.read_text(encoding='utf-8')
        assert 'status: done' in h.task.read_text(encoding='utf-8')
        calls = h.calls
        body = (h.run_dir / 'pr-body.md').read_text(encoding='utf-8')
        for needle in ['## Summary', '## Changes', '## Not in this PR', '## Verification', '## Known issues', 'Host: python check.py -> PASS', 'PASS abc1234', 'VERDICT: PASS', '- accept done']:
            assert needle in body, (needle, body)
        edit = next(c for c in calls if c[:3] == ['gh', 'pr', 'edit'])
        assert '--body-file' in edit
        watch = next(i for i, c in enumerate(calls) if c[:3] == ['gh', 'pr', 'checks'] and '--watch' in c)
        merge = next(i for i, c in enumerate(calls) if c[:3] == ['gh', 'pr', 'merge'])
        assert '--fail-fast' in calls[watch] and calls[merge-1][:3] == ['gh', 'pr', 'checks']
        assert '--squash' in calls[merge] and '--delete-branch' in calls[merge] and '[TASK-218] feat: accept' in calls[merge]
        assert watch < merge < calls.index(['git', 'pull'])
        h.calls.clear()
        error, out = h.invoke()
        assert not error and 'already done' in out and not h.calls, (error, out, h.calls)


def test_pass_refusals_do_not_change_task() -> None:
    for old, new, expected in [('Host: python check.py -> PASS', '', 'HOST'),
                               ('Host: python check.py -> PASS', 'Host: python check.py -> FAIL', 'HOST'),
                               ('✓ handles input', 'handles input', 'handles input'),
                               ('✓ rejects invalid input', '✓ unrelated', 'rejects invalid input'),
                               ('- review started', '- review done', 'current'),
                               ('VERDICT: PASS', 'VERDICT: BLOCKED', 'FAIL')]:
        with accepted() as h:
            text = h.text.replace(old, new)
            h.task.write_text(text, encoding='utf-8')
            error, _ = h.invoke()
            assert expected in error, error
            assert h.task.read_text(encoding='utf-8') == text and not h.calls


def test_pass_next_reviewer() -> None:
    with accepted() as h:
        h.steps.insert(1, dict(id='security', role='omi-agent-security-reviewer', gate='review'))
        error, out = h.invoke()
        assert not error, (error, out)
        assert any(c[-3:] == ['dispatch', 'omi-agent-security-reviewer', TID] for c in h.calls)
        assert not any(c[0] == 'gh' for c in h.calls)
        assert 'status: in-progress' in h.task.read_text(encoding='utf-8')


def test_pass_stage_failures_and_retry() -> None:
    for failure, stage in [('step-done', 'step-done'), ('step-next', 'step-next'), ('hook', 'pre-merge'),
                           ('commit', 'commit'), ('push', 'push'), ('pr-edit', 'pr-body'),
                           ('pr-ready', 'ready'), ('pull', 'pull'), ('clean', 'clean')]:
        with accepted() as h:
            h.fail = failure
            error, _ = h.invoke()
            assert stage + ' FAILED' in error, (failure, error)
            if stage not in ('pull', 'clean'):
                assert not any(c[:3] == ['gh', 'pr', 'merge'] for c in h.calls)
            h.fail = None
            assert not h.invoke()[0]


def test_pass_ci_red_reopens() -> None:
    for final in [False, True]:
        with accepted() as h:
            original = advance.command
            def command(cwd, argv, **kw):
                if argv[:3] == ['gh', 'pr', 'checks'] and '--json' not in argv and (final == ('--watch' not in argv)):
                    raise advance.state.StateError('command exited 1')
                return original(cwd, argv, **kw)
            with patch.object(advance, 'command', side_effect=command):
                error, _ = h.invoke()
            assert 'CI failed: unit' in error, error
            assert any(c[-3:] == ['reopen', '--why', 'CI failed: unit'] for c in h.calls)
            assert not any(c[:3] == ['gh', 'pr', 'merge'] for c in h.calls)
            assert 'fresh review' in h.invoke()[0]


def test_pass_local_and_post_merge_failure() -> None:
    with accepted() as h:
        h.remote = ''
        error, _ = h.invoke()
        assert not error, error
        assert ['git', 'merge', '--squash', 'task/' + TID] in h.calls
        assert ['git', 'commit', '-m', '[TASK-218] feat: accept'] in h.calls
        assert not any(c[0] == 'gh' or c == ['git', 'pull'] for c in h.calls)
    with accepted() as h:
        config = h.project.state / '.omi' / 'config.json'
        config.parent.mkdir()
        config.write_text('{"host_test": "python check.py"}', encoding='utf-8')
        original = advance.command
        def command(cwd, argv, **kw):
            if argv[-2:] == ['-c', 'python check.py']:
                raise advance.state.StateError('test failed')
            return original(cwd, argv, **kw)
        with patch.object(advance, 'command', side_effect=command), \
                patch.object(advance.accept.run, 'shell_command', return_value=['sh', '-c', 'python check.py']):
            error, _ = h.invoke()
        assert 'post-merge-test FAILED' in error and 'no revert' in error, error



def test_pass_every_stage_stops_and_resumes() -> None:
    stages = ['criteria', 'step-done', 'step-next', 'accept-done', 'pre-merge', 'remote',
              'commit', 'title', 'push', 'pr-body', 'ready', 'ci', 'merge', 'pull', 'clean', 'post-merge-test']
    for failed in stages:
        with accepted() as h:
            real = advance.perform
            def perform(ctx, name, action, remember=True):
                def fail(_):
                    raise OSError('injected stage failure')
                return real(ctx, name, fail if name == failed else action, remember)
            with patch.object(advance, 'perform', side_effect=perform):
                error, out = h.invoke()
            assert failed + ' FAILED' in error, (failed, error)
            assert not any(line.startswith(failed + ': done') for line in out.splitlines())
            error, _ = h.invoke()
            assert not error, (failed, error)
    with accepted() as h:
        h.remote = ''
        h.fail = 'merge'
        assert 'local-squash FAILED' in h.invoke()[0]
        assert not any(c[:2] == ['git', 'commit'] and '[TASK-218] feat: accept' in c for c in h.calls)


def test_pass_review_guards_and_windows() -> None:
    for mode in ['stale', 'running', 'rc', 'wrong-role', 'po', 'reject', 'host-next']:
        with accepted() as h:
            if mode == 'stale': h.rec['started'] = STAMP.replace(hour=10)
            elif mode == 'running': h.recs.append({**h.rec, 'running': True})
            elif mode == 'rc': h.rec['rc'] = 1
            elif mode == 'wrong-role': h.steps[0]['role'] = 'omi-agent-security-reviewer'
            elif mode == 'po': h.steps[1]['gate'] = 'po'
            elif mode == 'host-next':
                h.steps.insert(1, dict(id='security', role='omi-agent-security-reviewer', gate='review'))
                h.task.write_text(h.text.replace('Host: python check.py -> PASS', ''), encoding='utf-8')
            before = h.task.read_text(encoding='utf-8')
            error, _ = h.invoke(reject=[1] if mode == 'reject' else None)
            assert 'eligibility FAILED' in error and not h.calls, (mode, error)
            assert h.task.read_text(encoding='utf-8') == before
    with accepted() as h, patch.object(advance.core, 'WINDOWS', True), \
            patch.object(advance.subprocess, 'CREATE_NO_WINDOW', 0x08000000, create=True), \
            patch.object(advance.subprocess, 'run', wraps=advance.subprocess.run) as run:
        assert not h.invoke()[0]
        assert all(c.kwargs['creationflags'] == 0x08000000 for c in run.call_args_list)
    with accepted() as h:
        h.steps.insert(1, dict(id='qa', role='omi-agent-qa-tester', gate='review'))
        assert not h.invoke()[0]
        assert any(c[-3:] == ['dispatch', 'omi-agent-qa-tester', TID] for c in h.calls)


def test_pass_templates() -> None:
    root = advance.core.TEMPLATE
    for path in [root / 'AGENTS.md', root / 'dot-claude/skills/omi-task/SKILL.md']:
        text = path.read_text(encoding='utf-8')
        for marker in ['advance', 'PASS', '--fail-fast', 'Host:', 'post-merge', 'clean']:
            assert marker in text, (path, marker)
    assert 'after review PASS' in cli.USAGE



def test_pass_real_report_format() -> None:
    with accepted() as h:
        text = h.text.replace('✓ handles input', 'AC: handles input ✓ tests exercise input')
        text = text.replace('✓ rejects invalid input', 'AC: rejects invalid input ✓ test_invalid')
        text = text.replace('HOST: python check.py', 'HOST: none')
        h.task.write_text(text, encoding='utf-8')
        error, _ = h.invoke()
        assert not error, error
        assert '- [x] rejects invalid input' in h.task.read_text(encoding='utf-8')
    with accepted() as h:
        h.task.write_text(h.text.replace('✓ handles input', 'AC: handles input extra ✓ bogus'), encoding='utf-8')
        error, _ = h.invoke()
        assert 'handles input' in error and not h.calls



def test_pass_post_merge_config_command() -> None:
    cmd = 'python check.py && echo ok'
    cases = [(False, ['sh', '-c', cmd], ['sh', '-c', cmd]),
             (True, [r'C:\Program Files\Git\bin\bash.exe', '-c', cmd],
              [r'C:\Program Files\Git\bin\bash.exe', '-c', cmd]),
             (True, f'cmd /d /s /c "{cmd}"', ['cmd', '/d', '/s', '/c', cmd])]
    for windows, shell_output, expected in cases:
        with accepted() as h, patch.object(advance.core, 'WINDOWS', windows), \
                patch.object(advance.accept.run, 'shell_command', return_value=shell_output) as shell, \
                patch.object(advance.subprocess, 'CREATE_NO_WINDOW', 0x08000000, create=True), \
                patch.object(advance.subprocess, 'run', wraps=advance.subprocess.run) as run:
            config = h.project.state / '.omi' / 'config.json'
            config.parent.mkdir()
            config.write_text(json.dumps({'host_test': cmd}), encoding='utf-8')
            error, _ = h.invoke()
            assert not error, (windows, shell_output, error)
            shell.assert_called_once_with(cmd)
            test_calls = [call for call in run.call_args_list if call.args[0] == expected]
            assert len(test_calls) == 1, (expected, h.calls)
            options = test_calls[0].kwargs
            assert options['cwd'] == h.project.code and not options.get('shell')
            assert options.get('creationflags', 0) == (0x08000000 if windows else 0)
            assert h.calls.index(expected) > next(i for i, c in enumerate(h.calls) if c[-2:] == ['clean', TID])


def test_pass_real_auto_gate_steps() -> None:
    with accepted() as h:
        h.steps[1].update(input='review', output='accept', stop='done', skills='')
        original = advance.subprocess.run
        def run(argv, **kw):
            if argv[0] not in ('git', 'gh') and argv[3:5] == ['step', TID]:
                h.calls.append(argv)
                tasks.step(h.project.code, TID, argv[5])
                return subprocess.CompletedProcess(argv, 0, '', '')
            return original(argv, **kw)
        with patch.object(advance.state, 'resolve', return_value=h.project), \
                patch.object(advance.subprocess, 'run', side_effect=run):
            error, _ = h.invoke()
        assert not error, error
        text = h.task.read_text(encoding='utf-8')
        assert 'Auto accept: review PASS' in text
        assert tasks.step_states(text) == {'review': 'done', 'accept': 'done'}


def test_pass_windows_post_merge_failure() -> None:
    cmd = 'python check.py'
    for shell_output, expected in [([r'C:\Program Files\Git\bin\bash.exe', '-c', cmd],
                                   [r'C:\Program Files\Git\bin\bash.exe', '-c', cmd]),
                                  (f'cmd /d /s /c "{cmd}"', ['cmd', '/d', '/s', '/c', cmd])]:
        with accepted() as h, patch.object(advance.core, 'WINDOWS', True), \
                patch.object(advance.accept.run, 'shell_command', return_value=shell_output), \
                patch.object(advance.subprocess, 'CREATE_NO_WINDOW', 0x08000000, create=True):
            config = h.project.state / '.omi' / 'config.json'
            config.parent.mkdir()
            config.write_text(json.dumps({'host_test': cmd}), encoding='utf-8')
            h.fail = 'post-merge-test'
            error, _ = h.invoke()
            assert 'post-merge-test FAILED' in error and 'no revert' in error, error
            assert expected in h.calls
            assert not any(c[:2] == ['git', 'revert'] for c in h.calls)


def test_pass_no_ci_checks_blocks_merge() -> None:
    # The task requires a final checks exit 0, even for repositories without CI.
    with accepted() as h:
        original = advance.subprocess.run
        def run(argv, **kw):
            if argv[:3] == ['gh', 'pr', 'checks']:
                h.calls.append(argv)
                return subprocess.CompletedProcess(argv, 1, '[]' if '--json' in argv else '', 'no checks reported')
            return original(argv, **kw)
        with patch.object(advance.subprocess, 'run', side_effect=run):
            error, _ = h.invoke()
        assert 'CI failed: unknown check' in error, error
        assert any(c[-3:] == ['reopen', '--why', 'CI failed: unknown check'] for c in h.calls)
        assert not any(c[:3] == ['gh', 'pr', 'merge'] for c in h.calls)


def main():
    test_pass_every_stage_stops_and_resumes()
    test_pass_review_guards_and_windows()
    test_pass_templates()
    test_pass_real_auto_gate_steps()
    test_pass_post_merge_config_command()
    test_pass_windows_post_merge_failure()
    test_pass_real_report_format()
    test_pass_merge_and_resume()
    test_pass_refusals_do_not_change_task()
    test_pass_next_reviewer()
    test_pass_stage_failures_and_retry()
    test_pass_ci_red_reopens()
    test_pass_no_ci_checks_blocks_merge()
    test_pass_local_and_post_merge_failure()


if __name__ == '__main__':
    main()
