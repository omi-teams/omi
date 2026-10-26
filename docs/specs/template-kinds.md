# Rules, references, plans, hooks cho template

Trạng thái: PO đã duyệt (2026-10-26, a8df61b).

## Người dùng
- PO: viết hoặc chọn nội dung cho từng project, xem tiến độ theo plan.
- Coordinator: chọn `refs`/`plan` khi lập task, chạy hook `pre-merge`.
- Agent (engineer, reviewer...): nhận rules và refs trong prompt.

## Vấn đề
Hiện chỉ có agents, skills, workflows. Chưa có chỗ cho quy ước code theo stack, tài liệu tra cứu, nhóm task theo mục tiêu, hay bước tự động (lint/test) trước và sau khi agent chạy. Coordinator phải dán tay vào task và tốn token.

## Tính năng v1
Mỗi loại có thư mục riêng trong `.omi/`, có `CATALOG.md` sinh bằng lệnh `python -m omi <loại>` (giống skills), có kiểm tra định dạng, và có mẫu trong `src/omi/template`.

1. **Rules** — `.omi/rules/<id>.md`, frontmatter `id, summary, applies: <glob>[, ...]`.
   - `omi run` tự nạp mọi rule có `applies` khớp ít nhất một glob trong `scope` của task, đưa đường dẫn vào prompt với câu "phải tuân theo".
   - Budget riêng: `rule_limits` trong `.omi/config.json`, mặc định 2000 token mỗi lần chạy và 800 token mỗi rule. Vượt budget thì dừng và báo file nào gây vượt. Chỉ PO được nâng.
2. **References** — `.omi/references/<id>.md`, frontmatter `id, summary`.
   - Task ghi `refs: [...]`. Agent chỉ nhận đường dẫn, tự đọc khi cần, không tính vào budget.
   - Ref không có trong catalog thì `omi run` dừng.
3. **Plans** — `.omi/plans/PLAN-NNN.md`, frontmatter `id, title, status (active|done)`, gồm mục tiêu và tiêu chí hoàn thành.
   - Task ghi `plan: PLAN-NNN`.
   - `omi status` hiện mỗi plan đang active kèm `done x/y`.
   - Sau này map sang Epic/Feature của omi-board.
4. **Hooks** — `.omi/hooks/<event>.sh` hoặc `.py`, với event `pre-run`, `post-run`, `pre-merge`.
   - Chạy trong Docker, cwd là worktree. Exit code khác 0 thì chặn bước đó; output được ghi vào `## Reports`.
   - Script được đọc từ repo chính (nhánh `development`), không đọc từ worktree, để agent không sửa được hook.
   - `pre-merge` chạy qua lệnh `python -m omi hook pre-merge <TASK-ID>`, được gọi trong skill omi-task.

**Mẫu ship kèm:**
- Rules: `go`, `python`, `postgres`, `nextjs`, `docker`.
- References: `postgres-conventions`, `nextjs-app-router`.
- Plan: `PLAN-000` (mẫu).
- Hook: `post-run.sh` (chạy test của project nếu tìm thấy).

**Bổ sung sau:** nâng cấp omi rồi chạy lại `omi init`. Lệnh này chỉ thêm file còn thiếu, không ghi đè file PO đã sửa.

## Ngoài phạm vi
- Hook cho Claude Code (`.claude/settings.json`) và các event khác ngoài 3 event trên.
- Rule chọn theo role; reference là link ngoài.
- Lệnh `omi init --update` ghi đè mẫu cũ.
- UI xem plan (để dành cho omi-board).

## Ràng buộc
- Chỉ dùng stdlib Python 3.13, nằm trong `src/omi/__init__.py`, không thêm dependency.
- Chạy được trên Windows (PowerShell, Git Bash) và trong Docker worker.
- Hook không được truy cập secret của host; chạy cùng container với agent.

## Tiêu chí thành công
- `omi init` vào thư mục trống tạo đủ 4 thư mục, có mẫu và catalog.
- Một task có scope `src/**/*.go` tự nhận rule `go`, không nhận rule `python`; vượt budget thì `omi run` dừng và báo rõ.
- `omi status` hiện tiến độ của plan.
- Hook `post-run` thất bại thì task không được chuyển sang review.
- Test tự động cho từng điểm trên đều pass.

## Stack
- Python stdlib, nằm trong `omi` hiện có: giữ nguyên cách cài đặt hiện tại.
- Markdown + frontmatter: dùng lại hàm `meta()` và `parse()` đang có.
- Docker worker cho hooks: cùng mức cách ly với agent, không mở thêm quyền trên host.
