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
