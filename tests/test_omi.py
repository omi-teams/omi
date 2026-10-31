"""Runs every area test file in one process: python tests/test_omi.py"""
import json
from pathlib import Path

import helpers  # noqa: F401
import test_upgrade
import test_init
import test_github
import test_worker
import test_creds
import test_tools
import test_hooks
import test_tasks
import test_content
import test_cli
import test_attach
import test_detached
import test_install
import test_board
import test_board_server
import test_board_web

from omi.project import tasks
from omi.setup import upgrade
import omi.common.core


def test_release_0_5_0():
    assert omi.common.core.version() == "0.5.0"
    assert upgrade.template_shas() == json.loads(upgrade.SHAS.read_text(encoding="utf-8"))["0.5.0"]


def test_phase():
    wf = [{"id": "plan", "role": "coordinator"}, {"id": "design", "role": "omi-agent-architect"},
          {"id": "build", "role": "omi-agent-engineer"}, {"id": "docs", "role": "omi-agent-docs-writer"},
          {"id": "ops", "role": "omi-agent-devops"}, {"id": "ui", "role": "omi-agent-designer-ui"},
          {"id": "res", "role": "omi-agent-researcher"}, {"id": "review", "role": "omi-agent-reviewer"},
          {"id": "sec", "role": "omi-agent-security-reviewer"}, {"id": "qa", "role": "omi-agent-qa-tester"},
          {"id": "odd", "role": "mystery"}, {"id": "accept", "role": "coordinator", "gate": "po"}]
    ph = lambda status, step, steps=wf, text="": tasks.phase({"status": status, "step": step, "_text": text}, steps)
    assert ph("planned", "build")["label"] == "Chưa bắt đầu" and ph("planned", "build")["key"] == "not_started"
    assert ph("blocked", "build")["label"] == "Bị chặn" and ph("done", "accept")["label"] == "Xong"
    for step, key, label in (("accept", "po", "Chờ PO"), ("plan", "planning", "Lên kế hoạch"), ("design", "design", "Thiết kế"),
                             ("ui", "design", "Thiết kế"), ("res", "design", "Thiết kế"), ("build", "working", "Đang làm"),
                             ("docs", "working", "Đang làm"), ("ops", "working", "Đang làm"), ("review", "review", "Đang review"),
                             ("sec", "review", "Đang review"), ("qa", "qa", "Đang QA"), ("odd", "working", "Đang làm"),
                             ("", "working", "Đang làm"), ("nope", "working", "Đang làm")):
        got = ph("in-progress", step)
        assert (got["key"], got["label"]) == (key, label), (step, got)
    assert ph("in-progress", "build", [])["label"] == "Đang làm" and ph("in-progress", "build", [])["step_count"] == 0
    got = ph("in-progress", "review")
    assert (got["step_index"], got["step_count"], got["step"]) == (8, 12, "review") and got["review_round"] == 1
    assert ph("in-progress", "build")["review_round"] is None
    usage = ("\n## Usage\n| role | model | effort | input | output | cache | duration | skills read | verdict |\n|---|---|---|---|---|---|---|---|---|\n"
             "| omi-agent-reviewer | m | high | 1 | 1 | 1 | 1s | - | FAIL abc1234 |\n"
             "| omi-agent-reviewer | m | high | 1 | 1 | 1 | 1s | - | QUOTA->x |\n"
             "| omi-agent-engineer | m | high | 1 | 1 | 1 | 1s | - | FAIL |\n"
             "| omi-agent-reviewer | m | high | 1 | 1 | 1 | 1s | - | PASS |\n")
    assert ph("in-progress", "review", text=usage)["review_round"] == 2
    assert ph("in-progress", "qa", text=usage)["review_round"] == 2
    m = {"status": "in-progress", "step": "design", "_text": ""}
    assert tasks.step_strip(m, wf[:4]) == "plan ✓ [design] build docs"
    assert tasks.step_strip({**m, "status": "done"}, wf[:2]) == "plan ✓ design ✓"


if __name__ == "__main__":
    test_phase()
    test_release_0_5_0()
    test_upgrade.main()
    test_init.main()
    test_github.main()
    test_worker.main()
    test_creds.main()
    test_tools.main()
    test_hooks.main()
    test_tasks.main()
    test_content.main()
    test_cli.main()
    test_attach.main()
    test_detached.main()
    test_install.main()
    test_board.main()
    test_board_server.main()
    test_board_web.main()
    print("ok")
