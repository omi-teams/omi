# OMI Squad

Điều hành một squad AI coding agent ngay trong dự án, ưu tiên **tiết kiệm quota**. Ý tưởng gốc: [project-overview.md](project-overview.md).

## Cài và dùng

Phiên bản (SemVer 0.x) chỉ ghi ở `pyproject.toml`; `omi init` ghi nó vào `.omi/version`, `omi status` báo khi dự án cũ hơn omi đang cài.

```sh
python -m pip install --user "git+https://github.com/omi-teams/omi@v0.4.0"     # cài từ tag
python -m omi upgrade [--check|--to vX.Y.Z]   # nâng cấp omi rồi cập nhật file khung chưa bị sửa (file đã sửa: giữ nguyên, bản mới ở <file>.omi-new); trong Claude Code: /omi-upgrade
omi --version             # omi 0.4.0
# Mỗi Python trên máy có một omi (hook và AGENTS.md gọi `python -m omi`); người phát triển omi dùng `pip install -e .` thay cho lệnh trên.
mkdir my-app && cd my-app
omi init                  # cài khung squad, không ghi đè file sẵn có
omi github [--po]         # (PO, quyền admin; --po: đăng nhập PO trên browser, xong tự logout + quay lại tài khoản squad) tạo staging + ruleset: squad chỉ merge vào development
# Coordinator mặc định chạy model sonnet ("model" trong .claude/settings.json); đổi: sửa key đó hoặc /model trong phiên
# Worker: alias haiku/sonnet/opus đổi thành model ID đầy đủ qua "models" trong .omi/config.json (PO sửa được); tên container <repo>-<task>-<role>-<tool>-<model>-<effort>-<HHMMSS> (vd. omi-TASK-055-reviewer-claude-sonnet-5.5-medium-143205), agent và proxy cùng một nhóm compose (com.docker.compose.project) để Docker Desktop gom lại, label omi-role/task/model/effort/started; omi status liệt kê worker đang chạy
claude                    # rồi gõ /omi-idea, /omi-task TASK-001, /omi-status
```

Để giữ repo code nguyên vẹn, dùng `omi attach [<repo path>]` (mặc định: thư mục hiện tại, cần remote `origin`). Lệnh tạo và commit `projects/<tên-repo>/project.json`, `.omi/`, `docker/` và hooks trong repo state `~/.omi/state` (đổi bằng `OMI_STATE`), không tạo `AGENTS.md` hay `.claude` ở đó. Tên đã tồn tại bị từ chối trừ khi cùng URL origin; HTTPS và SSH của cùng repo được nhận diện như nhau.

Lần đầu dùng `omi attach --state <git url>` để clone repo state riêng tư; không có URL thì omi khởi tạo repo state và in lệnh thêm private remote. Git cần có `user.name` và `user.email` để commit. Attach tự push commit lên remote state (thiết lập upstream nếu remote trống); push lỗi giữ commit local và in `STATE NOT PUSHED: run omi sync`. Nếu có `origin/development` mà chưa có nhánh local `development`, attach tạo nhánh tracking và in một dòng; nhánh local đã có được giữ nguyên, repo code không nhận commit hay file mới. Khi chưa có remote state, thêm private remote rồi chạy `omi sync`; trên máy khác clone nó vào `OMI_STATE` rồi clone repo code: omi nhận diện dự án theo URL origin, không phụ thuộc đường dẫn checkout. Manifest lỗi hoặc URL trùng trong registry khiến mọi lệnh dừng với thông báo `OMI:` nêu file cần sửa.

Chạy `omi install-user` một lần trên mỗi máy để cài skills vào `~/.claude/skills/`, thêm SessionStart hook vào `~/.claude/settings.json` và luật Coordinator vào block `<!-- omi -->` trong `~/.codex/AGENTS.md`. Hook `python -m omi session-start` chỉ in luật và status trong repo đã attach; Codex chạy lệnh này theo luật đầu phiên. Các đường dẫn `.omi/` trong luật trỏ tới repo state; skills dùng đường dẫn user. Lệnh giữ settings và nội dung AGENTS khác, chạy lại không nhân đôi; lần sửa settings đầu tiên có backup `settings.json.omi-bak`. `omi install-user --remove` hoàn tác phần đã cài theo manifest `~/.omi/install-user.json`, giữ skills đã sửa và nội dung user thêm sau đó. In-repo mode vẫn dùng `omi init` như trước.

Trong detached mode, `omi status` tự pull repo state bằng `git pull --rebase`; offline hoặc chưa có remote thì in một dòng và vẫn hiển thị state local. Các lệnh thay đổi state (step, catalogs, run reports/usage, hooks) tự commit đúng các file chúng sửa với message `chore(<project>): <what>` rồi push. Push lỗi giữ commit local và in `STATE NOT PUSHED: run omi sync`. Chạy `omi sync` để pull, commit các thay đổi còn lại (task start/done, decisions, plans sửa bằng tay) và push toàn bộ repo state. Nếu rebase conflict, omi liệt kê file và dừng; giải quyết bằng git rồi chạy lại `omi sync`. In-repo mode giữ nguyên.

Trên Windows, tìm thư mục Python `Scripts` bằng `python -c "import sysconfig; print(sysconfig.get_path('scripts'))"` rồi thêm vào `PATH`, hoặc gọi `python -m omi`. Dự án đã attach cần đặt lệnh kiểm thử `"test": "python tests/test_omi.py"` trong `.omi/config.json` của bản state (`~/.omi/state/projects/<tên>/.omi/config.json`, hoặc dưới `OMI_STATE`), không phải repo code.
Worker tự cho phép API host của tool được chọn (Claude: `api.anthropic.com`, Codex: `api.openai.com`); đăng nhập Codex bằng ChatGPT cũng thêm `chatgpt.com`. Khai host bổ sung trong `network_allow` của `.omi/config.json`.
Nếu repo code có `.omi/`, `AGENTS.md` hoặc `.claude/` được Git theo dõi, `omi attach`/`omi status` báo `WARN: in-repo omi files ignored (detached): <paths>`; omi không tự di chuyển các file này. PO duyệt bước bằng `omi step <ID> approve --why "<lời PO>"`; mở lại workflow đã hoàn tất bằng `omi step <ID> reopen --why "<lý do>"`.


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

Cache tải xuống (Go modules, npm, pip) nằm trong `.omi-cache/` của worktree (được gitignore) để hook và reviewer dùng lại dependency của engineer; cache build vẫn ở tmpfs `/cache`.

## Lấy và lưu key

- **Claude (mặc định theo đăng nhập Claude Code):** agent dùng tài khoản của phiên Claude Code hiện tại. Thứ tự: biến môi trường `CLAUDE_CODE_OAUTH_TOKEN` (ghi đè rõ ràng), rồi đăng nhập phiên (`accessToken` trong `~/.claude/.credentials.json` hoặc `$CLAUDE_CONFIG_DIR/.credentials.json`, đọc lúc chạy, không lưu, không ghi log; refresh token không rời máy host), rồi token đã lưu. Token phiên hết hạn thì mở Claude Code một lần để làm mới; `omi run` in `claude auth: env|session|stored`.
- **Claude (token lưu sẵn):** chạy `claude setup-token` và copy token. Lưu bằng `python -m omi token set`; trên Windows token nằm trong Credential Manager với target `omi/CLAUDE_CODE_OAUTH_TOKEN`. OS khác: đặt biến môi trường `CLAUDE_CODE_OAUTH_TOKEN`.
- **OpenAI (Codex):** vào platform.openai.com và tạo tài khoản. API tính tiền riêng với gói ChatGPT: nạp credit, đặt giới hạn chi tiêu hàng tháng. Vào API keys → Create new secret key; key chỉ hiện một lần. Lưu bằng `python -m omi token set --tool codex` (target `omi/OPENAI_API_KEY`; OS khác: biến môi trường `OPENAI_API_KEY`). `api.openai.com` được cho phép tự động khi chạy codex.
- **ChatGPT (Codex, không cần API key):** nếu CLI Codex trên máy host đã "Logged in using ChatGPT" (chạy `codex` một lần, hoặc `codex login`), `omi run --tool codex` tự dùng đăng nhập đó khi không có khóa lưu và không có biến `OPENAI_API_KEY` (thứ tự: khóa đã lưu, biến môi trường, đăng nhập ChatGPT). omi chỉ đọc `access_token` từ `~/.codex/auth.json` (hoặc `$CODEX_HOME/auth.json`) lúc chạy, không lưu, không ghi log, truyền vào container theo tên biến `OMI_CODEX_AUTH`; refresh token không bao giờ vào container. `chatgpt.com` được thêm tự động vào allowlist ở chế độ này. Token hết hạn thì chạy `codex` một lần trên host rồi thử lại.
- **CLI lồng trong worker:** lệnh `codex` gọi từ agent trong worker Codex dùng chính đăng nhập của lần chạy đó; `~/.codex/auth.json` nằm trong tmpfs, chỉ mang access token (không có refresh token thật). Ví dụ: `codex exec -m gpt-6-luna -c model_reasoning_effort=low "say ok"`. Lệnh `claude` lồng trong worker không được đăng nhập theo thiết kế: Claude Code loại thông tin xác thực khỏi môi trường subprocess. Chạy các phép thử model Claude trên host; giữ nguyên cơ chế bảo vệ này.
- **Kiểm tra / xóa (Windows):** `cmdkey /list:omi/CLAUDE_CODE_OAUTH_TOKEN`, `cmdkey /delete:omi/CLAUDE_CODE_OAUTH_TOKEN` (tương tự với `omi/OPENAI_API_KEY`).
- Khi nhập key, màn hình không hiện gì, đó là bình thường. Không dán key vào chat, issue hay file nào.
- Tên menu trên platform.openai.com có thể thay đổi theo thời gian.

## Cách tiết kiệm quota

- **Việc gì script làm được thì không dùng LLM:** `omi status` (đọc file + git), `omi guard` (kiểm tra scope), CI.
- **Context luôn nạp nhỏ nhất có thể:** `AGENTS.md` ngắn; quy trình chi tiết nằm trong skills, chỉ nạp khi gọi.
- **File hướng dẫn cho agent viết tiếng Anh** (tiếng Việt tốn token gấp 2–3 lần). Agent vẫn trao đổi với PO bằng tiếng Việt.
- **3 vai trò thay vì 17:** Coordinator, omi-agent-engineer, omi-agent-reviewer. Mặc định dùng `sonnet`, việc cơ học dùng `haiku`, chỉ dùng `opus` khi thật cần.
- **Mỗi lần một task.** Không review với thay đổi chỉ ở docs/`.omi`. Tối đa 2 vòng sửa, sau đó hỏi PO.
- **Lệnh test** (`"test"` trong `.omi/config.json`, nếu có); không có thì: `tests/test_omi.py` nếu tồn tại, rồi pytest nếu import được, cuối cùng chạy từng `tests/test_*.py` như script (lỗi nếu có file nào thất bại).
- **Agent nhận đường dẫn task file,** không nhận context dán sẵn. Báo cáo không quá 10 dòng.

## Giới hạn đã biết

- Mẫu nhận diện hết quota (`QUOTA_PATTERNS`) chưa được kiểm thử với output giới hạn thật được ghi lại (không thể ghi lại nếu không chạm giới hạn thật); chỉ kiểm thử với mẫu dựng theo định dạng sự kiện của từng CLI. `omi run` chỉ xét sự kiện lỗi cuối của chính CLI (claude `result` lỗi, codex `error`/`turn.failed`), không xét output của công cụ.
- `omi guard` chặn Edit/Write của Coordinator và reviewer trên host. Engineer chạy trong Docker (`omi worker`): hệ điều hành chặn mọi thao tác ghi ngoài worktree, kể cả qua shell; thay đổi ngoài scope bị liệt kê sau khi chạy và Coordinator loại bỏ trước khi commit.
- `omi worker` cần Docker đang chạy và token từ `claude setup-token` (`omi token set` lưu vào Windows Credential Manager; OS khác dùng biến môi trường `CLAUDE_CODE_OAUTH_TOKEN`). Không có phương án chạy omi-agent-engineer trên host.
- Mạng của worker: mỗi lần chạy `omi worker`/`omi run` tạo một network Docker `--internal` và một proxy CONNECT (`docker/proxy.py`, chỉ stdlib, không giải mã TLS nên không thấy token). Container chỉ ra ngoài qua `HTTPS_PROXY`; mặc định chỉ `api.anthropic.com`, sửa bằng `"network_allow": ["host", "*.suffix", "host:port"]` trong `.omi/config.json`. Host bị chặn được in ra dạng `NETWORK BLOCKED: <host> - add to "network_allow" in .omi/config.json`. Kiểm tra thủ công (cả Docker Desktop for Windows/WSL2): `python -m omi worker <wt> --prove` phải PASS cho host được phép (200), host bị chặn (403 nêu host và key) và TCP trực tiếp tới 1.1.1.1:443 (thất bại). `omi clean` xóa cả proxy và network còn sót. Còn lại: DNS có thể vẫn phân giải được trên một số engine (không có đường dữ liệu ra ngoài).
- Phiên bản CLI trong image được ghim (Dockerfile và `cli_versions` trong `.omi/config.json`): Claude Code 2.1.302, Codex CLI 0.164.0. `omi run <role> <TASK> --tool codex` chạy `codex exec -m <model> -c model_reasoning_effort=<level>` trong container, khóa `OPENAI_API_KEY` chỉ truyền theo tên (`omi token set --tool codex` lưu khóa vào Windows Credential Manager, target `omi/OPENAI_API_KEY` riêng với token Claude; `omi run` đọc kho trước, rồi mới tới biến môi trường `OPENAI_API_KEY`); `api.openai.com` được thêm tự động cho tool codex (không cần khai trong `network_allow`). `omi worker <wt> --prove` đặt tên container như một lần chạy thật và kiểm tra cả hai CLI tới được API qua proxy (khóa giả, mong đợi lỗi xác thực, không phải lỗi DNS/mạng).
- Thiết lập theo bước: `step_settings: architect=codex/opus/high, security=claude/opus/high, review=claude//`; phần trống kế thừa; thứ tự ưu tiên: CLI `--tool/--model/--effort` > thiết lập bước hiện tại (chỉ vai trò của bước đó) > task `tool/model/effort` (vai trò ghi hoặc vai trò của task) > file vai trò > mặc định.
- Chọn công cụ theo vai trò/task: `tool: claude|codex` trong file role, `tool:` trong task (ghi đè role), `omi run --tool` (ghi đè cả hai); alias model của Codex nằm ở `codex_models` trong `.omi/config.json`. `codex_models` mặc định ánh xạ haiku/sonnet/opus tới gpt-6-luna/gpt-6.1-sol/gpt-6-astra; PO có thể sửa ID model, và alias thiếu ánh xạ sẽ dừng lần chạy. Khi CLI dừng vì hết quota, `omi run` tự chạy lại (nếu `--model` là ID đầy đủ của một tool thì tool kia dùng alias của role) cùng role bằng công cụ còn lại trong cùng worktree (ghi vào `## Usage` và `## Checkpoint`); nếu cả hai hết quota hoặc thiếu token thì thoát mã 5 với dòng `QUOTA:`, không mất gì. Báo cáo cuối của agent được ghi vào `## Reports` trong file task (quá dài thì giữ dòng đầu và dòng cuối, cắt phần giữa); `omi status` in `resume: omi-task <ID>` cho task đang làm để phiên Claude Code hoặc Codex mới tiếp tục.
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
