# OMI Squad

Điều hành một squad AI coding agent ngay trong dự án, ưu tiên **tiết kiệm quota**. Ý tưởng gốc: [project-overview.md](project-overview.md).

## Cài và dùng

```sh
pip install -e .          # hoặc: pipx install .
mkdir my-app && cd my-app
omi init                  # cài khung squad, không ghi đè file sẵn có
omi github [--po]         # (PO, quyền admin; --po: đăng nhập PO trên browser, xong tự logout + quay lại tài khoản squad) tạo staging + ruleset: squad chỉ merge vào development
# Coordinator mặc định chạy model sonnet ("model" trong .claude/settings.json); đổi: sửa key đó hoặc /model trong phiên
# Worker: alias haiku/sonnet/opus đổi thành model ID đầy đủ qua "models" trong .omi/config.json (PO sửa được); tên container omi-<repo>-<task>-<role>-<model-id>-<effort>-<HHMMSS>, label omi-role/task/model/effort/started; omi status liệt kê worker đang chạy
claude                    # rồi gõ /omi-idea, /omi-task TASK-001, /omi-status
```

`omi init` tạo các file sau trong dự án:

| File | Vai trò |
| --- | --- |
| `AGENTS.md` | Luật của Coordinator; Claude Code và Codex dùng chung |
| `.omi/agents/*.md` | Vai trò (omi-agent-engineer, omi-agent-reviewer) là prompt file, chỉ nạp khi task gọi; `omi agents` sinh `CATALOG.md`; `omi run <role> <TASK-ID>` chạy trong Docker (role `read`: worktree mount read-only, chỉ chạy sau khi test/scope/skills pass) |
| `.claude/skills/omi-*` | Quy trình `idea`, `task`, `status`, chỉ nạp khi gọi |
| `docker/` | Image cho worker: omi-agent-engineer chạy `claude -p` trong container, chỉ ghi được vào worktree |
| `.claude/settings.json` | Hook: tự chèn `omi status` đầu phiên; `omi guard` chặn ghi ngoài scope |
| `.omi/tasks/TASK-NNN.md` | Mỗi task một file: brief, scope, acceptance criteria, checkpoint |
| `.omi/decisions.md` | Nhật ký quyết định của PO |

## Cách tiết kiệm quota

- **Việc gì script làm được thì không dùng LLM:** `omi status` (đọc file + git), `omi guard` (kiểm tra scope), CI.
- **Context luôn nạp nhỏ nhất có thể:** `AGENTS.md` ngắn; quy trình chi tiết nằm trong skills, chỉ nạp khi gọi.
- **File hướng dẫn cho agent viết tiếng Anh** (tiếng Việt tốn token gấp 2–3 lần). Agent vẫn trao đổi với PO bằng tiếng Việt.
- **3 vai trò thay vì 17:** Coordinator, omi-agent-engineer, omi-agent-reviewer. Mặc định dùng `sonnet`, việc cơ học dùng `haiku`, chỉ dùng `opus` khi thật cần.
- **Mỗi lần một task.** Không review với thay đổi chỉ ở docs/`.omi`. Tối đa 2 vòng sửa, sau đó hỏi PO.
- **Agent nhận đường dẫn task file,** không nhận context dán sẵn. Báo cáo không quá 10 dòng.

## Giới hạn đã biết

- `omi guard` chặn Edit/Write của Coordinator và reviewer trên host. Engineer chạy trong Docker (`omi worker`): hệ điều hành chặn mọi thao tác ghi ngoài worktree, kể cả qua shell; thay đổi ngoài scope bị liệt kê sau khi chạy và Coordinator loại bỏ trước khi commit.
- `omi worker` cần Docker đang chạy và token từ `claude setup-token` (`omi token set` lưu vào Windows Credential Manager; OS khác dùng biến môi trường `CLAUDE_CODE_OAUTH_TOKEN`). Không có phương án chạy omi-agent-engineer trên host.
- Mạng của worker: mỗi lần chạy `omi worker`/`omi run` tạo một network Docker `--internal` và một proxy CONNECT (`docker/proxy.py`, chỉ stdlib, không giải mã TLS nên không thấy token). Container chỉ ra ngoài qua `HTTPS_PROXY`; mặc định chỉ `api.anthropic.com`, sửa bằng `"network_allow": ["host", "*.suffix", "host:port"]` trong `.omi/config.json`. Host bị chặn được in ra dạng `NETWORK BLOCKED: <host> - add to "network_allow" in .omi/config.json`. Kiểm tra thủ công (cả Docker Desktop for Windows/WSL2): `python -m omi worker <wt> --prove` phải PASS cho host được phép (200), host bị chặn (403 nêu host và key) và TCP trực tiếp tới 1.1.1.1:443 (thất bại). `omi clean` xóa cả proxy và network còn sót. Còn lại: DNS có thể vẫn phân giải được trên một số engine (không có đường dữ liệu ra ngoài).
- Phiên bản CLI trong image được ghim (Dockerfile và `cli_versions` trong `.omi/config.json`): Claude Code 2.1.302, Codex CLI 0.164.0. `omi run <role> <TASK> --tool codex` chạy `codex exec -m <model> -c model_reasoning_effort=<level>` trong container, khóa `OPENAI_API_KEY` chỉ truyền theo tên; `api.openai.com` được thêm tự động cho tool codex (không cần khai trong `network_allow`). `omi worker <wt> --prove` đặt tên container như một lần chạy thật và kiểm tra cả hai CLI tới được API qua proxy (khóa giả, mong đợi lỗi xác thực, không phải lỗi DNS/mạng).
- Codex chưa có hook, nên scope chỉ dựa vào hướng dẫn trong prompt.
- Hook gọi `python -m omi`: nếu `python` không chạy được hoặc chưa cài `omi`, hook không chặn được gì (fail-open).

## Lộ trình

1. ✅ Khung squad: init, status, guard, idea, task.
2. Pilot một dự án thật qua `omi-idea` → `omi-task`; thêm lệnh `omi github` để cấu hình rulesets (chỉ PO merge vào `staging`/`main`).
3. ✅ Engineer chạy trong Docker worker (`omi worker`), auth subscription qua token.
4. Kiểm thử resume và đổi công cụ Claude ↔ Codex.
5. Luồng UAT/promotion staging → main.

Hoãn sang sau v1: dự báo quota, extension parity, repo `omi-skills` riêng, migration cho installer.

## Kiểm thử

```sh
python tests/test_omi.py
```
