# OMI Squad

Điều hành một squad AI coding agent ngay trong dự án, ưu tiên **tiết kiệm quota**. Ý tưởng gốc: [project-overview.md](project-overview.md).

## Cài và dùng

```sh
pip install -e .          # hoặc: pipx install .
mkdir my-app && cd my-app
omi init                  # cài khung squad, không ghi đè file sẵn có
omi github                # (PO, quyền admin) tạo staging + ruleset: squad chỉ merge vào development
claude                    # rồi gõ /omi-idea, /omi-task TASK-001, /omi-status
```

`omi init` tạo các file sau trong dự án:

| File | Vai trò |
| --- | --- |
| `AGENTS.md` (+ `CLAUDE.md` import nó) | Luật của Coordinator; Claude Code và Codex dùng chung |
| `.claude/agents/engineer.md`, `reviewer.md` | 2 vai trò chuyên môn; Coordinator là phiên chính |
| `.claude/skills/omi-*` | Quy trình `idea`, `task`, `status`, chỉ nạp khi gọi |
| `.claude/settings.json` | Hook: tự chèn `omi status` đầu phiên; `omi guard` chặn ghi ngoài scope |
| `.omi/tasks/TASK-NNN.md` | Mỗi task một file: brief, scope, acceptance criteria, checkpoint |
| `.omi/decisions.md` | Nhật ký quyết định của PO |

## Cách tiết kiệm quota

- **Việc gì script làm được thì không dùng LLM:** `omi status` (đọc file + git), `omi guard` (kiểm tra scope), CI.
- **Context luôn nạp nhỏ nhất có thể:** `AGENTS.md` ngắn; quy trình chi tiết nằm trong skills, chỉ nạp khi gọi.
- **File hướng dẫn cho agent viết tiếng Anh** (tiếng Việt tốn token gấp 2–3 lần). Agent vẫn trao đổi với PO bằng tiếng Việt.
- **3 vai trò thay vì 17:** Coordinator, engineer, reviewer. Mặc định dùng `sonnet`, việc cơ học dùng `haiku`, chỉ dùng `opus` khi thật cần.
- **Mỗi lần một task.** Không review với thay đổi chỉ ở docs/`.omi`. Tối đa 2 vòng sửa, sau đó hỏi PO.
- **Agent nhận đường dẫn task file,** không nhận context dán sẵn. Báo cáo không quá 10 dòng.

## Giới hạn đã biết

- `omi guard` chặn Edit/Write của Claude Code. Thao tác ghi qua shell **chưa** bị chặn (giai đoạn 3: worker chạy trong Docker).
- Codex chưa có hook, nên scope chỉ dựa vào hướng dẫn trong prompt.
- Hook gọi `python -m omi`: nếu `python` không chạy được hoặc chưa cài `omi`, hook không chặn được gì (fail-open).

## Lộ trình

1. ✅ Khung squad: init, status, guard, idea, task.
2. Pilot một dự án thật qua `omi-idea` → `omi-task`; thêm lệnh `omi github` để cấu hình rulesets (chỉ PO merge vào `staging`/`main`).
3. Spike Docker để chặn ghi qua shell, kèm auth subscription trong container.
4. Kiểm thử resume và đổi công cụ Claude ↔ Codex.
5. Luồng UAT/promotion staging → main.

Hoãn sang sau v1: dự báo quota, extension parity, repo `omi-skills` riêng, migration cho installer.

## Kiểm thử

```sh
python tests/test_omi.py
```
