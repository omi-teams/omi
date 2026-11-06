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



def test_marked_criteria_real_paraphrased_reports() -> None:
    # TASK-230 16:56 and TASK-233 19:46 reviewer reports, including their fences.
    fixtures = [
        ('\n## Acceptance criteria\n- [ ] Reproduce first: a test with one in-progress task (no running worker, no running dispatch record) and one ready planned task shows `omi status` printing `next:` with only the planned task.\n- [ ] `next:` names in-progress tasks with no running worker or running dispatch record first, marked `(resume)` (several: all of them, space-separated), then the first ready planned task; an in-progress task whose worker is running is not listed there.\n- [ ] When finished runs are not yet reported by `omi watch`, `omi status` prints one line `finished runs not handled: <N>; run python -m omi watch`.\n- [ ] The omi-status SKILL template resumes every `(resume)` task from `next:` (omi-task step 2, `omi-task <ID> <ID>` for several) before the next planned task, and runs `omi watch` first when status names unhandled runs; tests/test_content.py asserts it; template_shas regenerated.\n- [ ] `python tests/test_omi.py` passes.\n\n## Checkpoint\n',
         "```\nVERDICT: PASS\n- src/omi/app/cli.py:147 `resume` marks any in-progress top-level task with no worker as `(resume)`, including a task whose run has finished but not been reported (`omi watch` handles it). The criteria allow this and status prints the unhandled-runs line first, so nothing to fix. -> none\nAC: Reproduce first: a test shows `next:` with only the planned task ✓ The old code printed `next: {nxt}` with planned tasks only. The reproduce-first step was never run against the old code (the engineer's own report says so), but the diff makes the old behaviour clear, so this does not block PASS.\nAC: `next:` names orphaned in-progress tasks first as `(resume)`, then the first ready planned task; a task with a running worker is not listed ✓ cli.py:140-150 builds `busy` from running dispatch records plus `docker.running_workers`. `test_status_next_resumes_orphaned_and_flags_unhandled` covers several orphans, a task busy by record, a task busy by container, and the all-idle case.\nAC: `finished runs not handled: <N>; run python -m omi watch` ✓ cli.py:151-153 counts records that are not running and not reported, the same filter `dispatch.watch` uses (dispatch.py:174). The test asserts the exact line, and that it is absent when nothing is unhandled.\nAC: omi-status SKILL resumes `(resume)` tasks, runs `omi watch` first, test_content asserts it, shas regenerated ✓ SKILL.md has the new text and the `Bash(python -m omi watch)` allowed-tool. `test_status_skill_resumes_orphans` is added and registered in `main()`. The `.claude/skills/omi-status/SKILL.md` entry in template_shas.json was updated. The full suite passes, so the sha and content checks hold.\nAC: `python tests/test_omi.py` passes ✓ I ran `python3 tests/test_omi.py` here. It exited 0 and printed `ok`. The only skip was `test_wheel_ships_web` (pip missing). The Coordinator also recorded `host-test PASS 37fae12`.\nKnown issues: none\nHOST: none\nROOT: n/a\n```"),
        ('\n## Acceptance criteria\n- [ ] Reproduce first: a test where `gh pr merge` succeeds but the merge stage is not saved (crash before save, or gh exits non-zero after merging on --delete-branch) shows the rerun stopping at the CI guard.\n- [ ] Before the final CI guard the merge stage checks `gh pr view task/<TID> --json state`; `MERGED` marks the stage done (prints `merge: already merged`) and continues with pull, clean and the post-merge test; any other state keeps the guard unchanged.\n- [ ] `python tests/test_omi.py` passes.\n\n## Checkpoint\n',
         '```\nVERDICT: PASS\nAC: Reproduce first: a test shows the rerun stopping at the CI guard after gh merges but the stage isn\'t saved (save crash, or non-zero exit after merging on --delete-branch) ✓ `test_pass_merged_pr_resumes_unsaved_merge` (tests/test_accept.py) runs both failure modes. It asserts \'merge FAILED\', a merged PR and progress without `merge`. On the rerun, `gh pr checks` fails on the merged PR, so without the fix it stops at the guard. I did not re-run it against the unfixed code. The engineer\'s report says the regression was reproduced before the fix.\nAC: Before the final CI guard, merge checks `gh pr view task/<TID> --json state`; MERGED marks the stage done, prints `merge: already merged`, and continues with pull, clean and the post-merge test; any other state keeps the guard ✓ src/omi/worker/accept.py `merge()` returns \'already merged\' on MERGED, and `perform` records the stage and prints `merge: already merged`. The test asserts the view call comes first, no `checks` or `merge` calls follow, and the order pull < clean < post-merge test with all stages saved. `test_pass_unmerged_pr_keeps_final_ci_guard` covers OPEN and CLOSED: the guard still runs and no merge happens.\nAC: `python tests/test_omi.py` passes ✓ I ran it and it exited 0, printing "ok". `test_wheel_ships_web` was skipped because pip is missing, which is unrelated to this change. `tests/test_accept.py` also exited 0.\nKnown issues: `merge()` does not catch a malformed `gh pr view` JSON reply. A bad reply raises `JSONDecodeError` or `KeyError` instead of a `StateError`. This is minor, since gh output is trusted.\nHOST: none\nROOT: n/a\n```'),
    ]
    for text, report in fixtures:
        for fenced in (False, True):
            body = report.removeprefix('```\n').removesuffix('\n```')
            if fenced:
                body = '```\n' + body + '\n```'
            marked = advance.accept.marked_criteria(text, body)
            assert '- [ ]' not in marked
            assert marked.count('- [x]') == text.count('- [ ]')


def test_marked_criteria_ordered_status_guards() -> None:
    text = '\n## Acceptance criteria\n- [ ] handles input\n- [ ] rejects invalid input\n\n## Checkpoint\n'
    good = 'AC: accepts values ✓ input test\nAC: refuses bad values ✓ invalid test'
    for fenced in (False, True):
        for report in (good, good.replace('AC: refuses bad values', 'AC: rejects invalid input')):
            body = 'VERDICT: PASS\n' + report
            if fenced:
                body = '```\n' + body + '\n```'
            assert '- [ ]' not in advance.accept.marked_criteria(text, body)
        invalid = [good.splitlines()[0], good + '\nAC: extra ✓ evidence',
                   good.replace('AC: refuses bad values ✓ invalid test', 'AC: malformed'),
                   good.replace('✓ invalid test', '✓bogus')]
        invalid += [good.replace('✓ invalid test', status + ' evidence mentions ✓')
                    for status in ('✗', 'UNVERIFIED', 'QA')]
        for report in invalid:
            body = 'VERDICT: PASS\n' + report
            if fenced:
                body = '```\n' + body + '\n```'
            try:
                advance.accept.marked_criteria(text, body)
            except advance.state.StateError as exc:
                assert 'criteria not marked ✓' in str(exc)
            else:
                raise AssertionError(body)
        # A disabled fallback preserves the existing exact-text rule.
        for extra in ('', '\nAC: extra ✓ evidence', '\nAC: deferred QA evidence'):
            body = 'AC: handles input ✓ test\nAC: rejects invalid input ✓ test' + extra
            if fenced:
                body = '```\n' + body + '\n```'
            assert '- [ ]' not in advance.accept.marked_criteria(text, body)
        body = 'AC: handles input ✓ test\n✓ rejects invalid input'
        assert '- [ ]' not in advance.accept.marked_criteria(text, body)
    try:
        advance.accept.marked_criteria('\n## Acceptance criteria\n\n', 'VERDICT: PASS')
    except advance.state.StateError as exc:
        assert 'no acceptance criteria' in str(exc)
    else:
        raise AssertionError('empty criteria accepted')


def test_pass_post_merge_config_command() -> None:
    cmd = 'python check.py && echo ok'
    cases = [(False, None, ['sh', '-c', cmd]),
             (True, r'C:\Program Files\Git\bin\bash.exe',
              [r'C:\Program Files\Git\bin\bash.exe', '-c', cmd]),
             (True, None, ['cmd', '/d', '/s', '/c', cmd])]
    for windows, bash_path, expected in cases:
        with accepted() as h, patch.object(advance.core, 'WINDOWS', windows), \
                patch.object(advance.accept.run, 'host_bash', return_value=bash_path), \
                patch.object(advance.accept.run.shutil, 'which', return_value=None), \
                patch.object(advance.accept.run, 'shell_command', wraps=advance.accept.run.shell_command) as shell, \
                patch.object(advance.subprocess, 'CREATE_NO_WINDOW', 0x08000000, create=True), \
                patch.object(advance.subprocess, 'run', wraps=advance.subprocess.run) as run:
            config = h.project.state / '.omi' / 'config.json'
            config.parent.mkdir()
            config.write_text(json.dumps({'host_test': cmd}), encoding='utf-8')
            error, _ = h.invoke()
            assert not error, (windows, bash_path, error)
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
    for bash_path, expected in [(r'C:\Program Files\Git\bin\bash.exe',
                                 [r'C:\Program Files\Git\bin\bash.exe', '-c', cmd]),
                                (None, ['cmd', '/d', '/s', '/c', cmd])]:
        with accepted() as h, patch.object(advance.core, 'WINDOWS', True), \
                patch.object(advance.accept.run, 'host_bash', return_value=bash_path), \
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
    # Missing checks block merge without falsely reopening a completed task.
    with accepted() as h:
        original = advance.subprocess.run
        def run(argv, **kw):
            if argv[:3] == ['gh', 'pr', 'checks']:
                h.calls.append(argv)
                return subprocess.CompletedProcess(argv, 1, '[]' if '--json' in argv else '', 'no checks reported')
            return original(argv, **kw)
        with patch.object(advance.subprocess, 'run', side_effect=run):
            error, _ = h.invoke()
        assert 'no checks reported' in error, error
        assert not any('reopen' in c for c in h.calls)
        assert not json.loads((h.run_dir / 'advance.json').read_text(encoding='utf-8')).get('ci-failed')
        assert not any(c[:3] == ['gh', 'pr', 'merge'] for c in h.calls)


def test_pass_pr_body_filters_reports_and_describes_changes() -> None:
    with accepted() as h:
        text = h.text.replace('workflow: flow', 'workflow: flow\nfiles: src/input.py, tests/test_input.py')
        text = text.replace('## Acceptance criteria', '## Goal\nValidate incoming requests.\n\n## Acceptance criteria')
        text = text.replace('## Usage', '2026-11-06 11:22 hook post-run passed:\n> Conflict. The container name /tmp/private-token\n'
                            '> VERDICT: PASS\n> Known issues: /tmp/private-token\n\n## Usage')
        text = text.replace('> ✓ handles input', '> /tmp/private-token\n> ✓ handles input')
        h.task.write_text(text, encoding='utf-8')
        error, _ = h.invoke()
        assert not error, error
        body = (h.run_dir / 'pr-body.md').read_text(encoding='utf-8')
        assert '/tmp/private-token' not in body and 'Conflict.' not in body and 'hook post-run' not in body
        assert 'Validate incoming requests.' in body
        assert '- src/input.py' in body and '- tests/test_input.py' in body
        assert 'Changes outside the task scope' in body
        assert '- [x] handles input' not in body
        assert 'omi-agent-reviewer' in body and 'VERDICT: PASS' in body


def test_pass_host_error_prints_recordable_line() -> None:
    with accepted() as h:
        request = 'native Windows check: run python check.py on the host'
        text = h.text.replace('HOST: python check.py', 'HOST: ' + request)
        h.task.write_text(text, encoding='utf-8')
        error, _ = h.invoke()
        assert f'Host: {request} -> PASS' in error, error
        assert not h.calls and h.task.read_text(encoding='utf-8') == text
        h.task.write_text(text.replace('Host: python check.py -> PASS', f'Host: {request} -> PASS'), encoding='utf-8')
        assert not h.invoke()[0]


def test_pass_ci_classifies_check_results() -> None:
    for final in (False, True):
        for bucket in ('pending', 'pass', 'fail', 'cancel', 'empty', 'invalid'):
            with accepted() as h:
                original = advance.subprocess.run
                def run(argv, **kw):
                    if argv[:3] != ['gh', 'pr', 'checks']:
                        return original(argv, **kw)
                    h.calls.append(argv)
                    if '--json' in argv:
                        rows = [] if bucket == 'empty' else [{'name': 'unit', 'bucket': bucket}]
                        return subprocess.CompletedProcess(argv, 1, 'invalid JSON' if bucket == 'invalid' else json.dumps(rows), '')
                    return subprocess.CompletedProcess(argv, int(not final or '--watch' not in argv), '', '')
                with patch.object(advance.subprocess, 'run', side_effect=run):
                    error, _ = h.invoke()
                assert ('merge FAILED' if final else 'ci FAILED') in error, error
                reopens = [c for c in h.calls if 'reopen' in c]
                assert bool(reopens) == (bucket in ('fail', 'cancel')), (bucket, error)
                assert not any(c[:3] == ['gh', 'pr', 'merge'] for c in h.calls)
                if bucket in ('fail', 'cancel'):
                    assert reopens[0][-1] == 'CI failed: unit'
                else:
                    assert not json.loads((h.run_dir / 'advance.json').read_text(encoding='utf-8')).get('ci-failed')
                if bucket == 'empty':
                    assert 'no checks reported' in error
                if bucket == 'invalid':
                    assert 'CI status unavailable' in error


def main():
    test_pass_every_stage_stops_and_resumes()
    test_pass_review_guards_and_windows()
    test_pass_templates()
    test_pass_real_auto_gate_steps()
    test_pass_post_merge_config_command()
    test_pass_windows_post_merge_failure()
    test_pass_real_report_format()
    test_marked_criteria_real_paraphrased_reports()
    test_marked_criteria_ordered_status_guards()
    test_pass_merge_and_resume()
    test_pass_refusals_do_not_change_task()
    test_pass_next_reviewer()
    test_pass_stage_failures_and_retry()
    test_pass_ci_red_reopens()
    test_pass_no_ci_checks_blocks_merge()
    test_pass_pr_body_filters_reports_and_describes_changes()
    test_pass_host_error_prints_recordable_line()
    test_pass_ci_classifies_check_results()
    test_pass_local_and_post_merge_failure()


if __name__ == '__main__':
    main()
