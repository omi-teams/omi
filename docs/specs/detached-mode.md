# Chế độ độc lập (detached mode)

Trạng thái: PO duyệt 2026-10-28; thực hiện ở PLAN-004.

Tầm nhìn: omi (repo `omi-teams/omi`, trước đây là omi-squad2) là công cụ hỗ trợ toàn diện cho việc phát triển dự án bằng các agent, dùng được cho bất kỳ repo nào. Chế độ độc lập là bước đầu tiên; `omi board` là bước tiếp theo.

## Người dùng
PO dùng omi trên nhiều máy và nhiều repo, kể cả repo không muốn có file hay commit nào của omi.

## Vấn đề
Hiện omi cài vào chính repo: `.omi/`, `AGENTS.md`, `.claude/`, `docker/`, kèm các commit `chore: start TASK-...`. Repo của người khác hoặc của khách hàng không chấp nhận được việc này. State cũng chỉ nằm trong repo đó, không có chỗ chung cho nhiều project.

## Tính năng v1
- **Cài global:** `pip install` omi, rồi chạy `omi install-user` một lần trên mỗi máy. Lệnh này đặt skill omi vào `~/.claude/skills`, hook SessionStart cấp user và `~/.codex/AGENTS.md`. Hook chỉ bật vai Coordinator khi repo hiện tại đã được attach; repo khác vẫn như bình thường.
- **Repo state chung:** một repo git private `omi-state` clone về `~/.omi/state`, mỗi project là một thư mục `projects/<tên>/` chứa `.omi/`, `docker/` và hooks như chế độ in-repo.
- **`omi attach [<repo>]`:** tạo thư mục project trong omi-state và nhận diện repo code qua URL remote, nên máy khác tự khớp mà không cần cấu hình lại.
- **Tách state root khỏi git root:** mọi lệnh (`status`, `step`, `run`, `plans`, `hook`...) đọc state từ omi-state và thao tác git (branch `task/*`, worktree, PR) trên repo code.
- **Đồng bộ:** `omi status` tự pull đầu phiên; mỗi lần state đổi thì tự commit và push omi-state. Có thêm `omi sync` để chạy tay (pull, commit, push).
- **Worktree** đặt ở `../<repo>.wt/<ID>` như hiện nay, nằm ngoài repo code.

## Ngoài phạm vi v1
- Chuyển project in-repo sang chế độ độc lập (`omi detach`).
- `omi board` (thay cho omi-board): làm ở plan sau, chỉ đọc omi-state, không dùng DB.
- File CI trong repo code: chế độ độc lập dựa vào CI sẵn có của repo, hoặc test local.

## Ràng buộc
- Chế độ in-repo giữ nguyên hành vi, test hiện có vẫn phải qua.
- Không tốn tiền: omi-state là repo GitHub private miễn phí.
- Không lưu token: agent dùng đăng nhập trên host như hiện nay.
- Python stdlib, giống phần còn lại của omi.

## Tiêu chí thành công
Pilot trên một bản clone sạch của `omi-pilot-splitbill`:
1. `omi attach`, rồi chạy một task thật từ đầu đến merge. Repo code không có file hay commit nào của omi, chỉ có commit code của task.
2. Clone omi-state ở thư mục thứ hai (giả máy khác), `omi status` cho ra cùng kết quả.
3. Chế độ in-repo vẫn qua hết test (Linux worker và Windows host).

## Lựa chọn kỹ thuật
- Repo git cho state: có lịch sử và đồng bộ được nhiều máy, PO đã quen git.
- Một repo chung: mỗi máy chỉ cần clone một lần.
- Hook SessionStart cấp user: Claude Code tự nạp, không cần file trong repo.
- Nhận diện qua URL remote: ổn định giữa các máy, khác với đường dẫn local.


## State root contract (TASK-097)

The registry lives at `$OMI_STATE/projects/<name>/project.json`, defaulting to
`~/.omi/state/projects/<name>/project.json`. Each manifest contains:

```json
{"remote": "https://github.com/owner/repo.git"}
```

`omi.state.resolve(cwd)` returns `Project(state, code, detached)`. The code root
is the main checkout, including when invoked from a task worktree. Matching uses
`origin`: HTTPS, SSH and scp URLs share `host/owner/repo` form, the host is
lowercase, and a trailing `.git` or slash is ignored. Repository path case is
preserved. A normalized remote string is also accepted. Invalid manifests and
multiple matching projects fail explicitly; an unmatched or absent origin keeps
in-repo mode. `OMI_STATE` is read on each resolution.

The matched project directory owns `.omi/`, `docker/`, configuration, catalogs,
workflow steps, hooks, reports and usage. Git operations and scope checks still
use the code worktree (`../<repo>.wt/<TASK-ID>`); commands use the existing
`task/<TASK-ID>` worktree registration. Detached scope is read from the state task
file, never from a task copy in the code worktree. Step changes do not commit to
the code repository. Registry creation and state synchronization belong to the
separate attach/sync tasks.

Workers mount the project directory at `/state:ro` alongside `/work`. Task,
skill, rule and reference paths in both Claude and Codex prompts point to
`/state`; hooks receive the same read-only mount and `OMI_PROJECT_STATE=/state`.
The shipped post-run hook reads configuration from that root (defaulting to `.`
when the variable is unset or empty) and keeps `/work` as the test cwd. Engineers report checkpoint
updates in their final response. The host records reports and usage in the state
task file; the engineer cannot edit state. Read roles also validate the state
catalogs, while tests and diffs run against the code worktree. In-repo workers
retain their `/work/.omi/` paths and existing task commit behavior.

Validation: `python3 tests/test_omi.py` includes temporary registry resolution,
a full real-git step cycle with clean code status, authoritative scope and guard
checks, and Docker argv tests for both tools and hooks. Docker execution is
mocked in these tests; Windows host execution must be recorded separately.

