# omi board

Trạng thái: chờ PO duyệt; thực hiện ở PLAN-006 sau PLAN-005.

## Người dùng
PO theo dõi nhiều project đã attach vào omi-state, trên nhiều máy.

## Vấn đề
`omi status` chỉ in một project, dạng text. Repo omi-board cũ (Go, React, PostgreSQL) cần DB và build riêng, và không đọc omi-state.

## Tính năng v1
- **`omi board [--port N] [--no-open]`:** server `http.server` của stdlib, chỉ bind `127.0.0.1` (mặc định cổng 8765), tự mở trình duyệt. Pull omi-state một lần lúc khởi động như `omi status`. Mỗi lần tải trang đọc lại file state, không cache, không DB.
- **Trang chủ:** danh sách project trong `$OMI_STATE/projects/*`, mỗi project kèm plan đang active (done/total), số task theo trạng thái và việc đang chờ PO.
- **Dashboard project:**
  - Việc cần PO: task đang ở gate `po`, task `blocked`, next task gợi ý, dòng `Next:` của task in-progress.
  - Plan và tiến độ.
  - Kanban: planned / in-progress / review / blocked / done.
  - Hoạt động gần đây: lấy từ `## Steps` và `## Reports` (bước, task, thời điểm, thời lượng).
  - Decisions mới nhất.
  - Usage: token theo task, tổng theo model, số vòng review.
  - Sync: omi-state ahead/behind remote, commit cuối, thay đổi chưa commit.
- **Chi tiết task:** frontmatter, Goal, tiêu chí kèm dấu tick, Checkpoint, Steps, Reports, Usage.
- Giao diện tiếng Việt, frontend tĩnh trong package, không JS hay CDN bên ngoài, tự refresh mỗi 30 giây (tắt được).

## Ngoài phạm vi v1
- Ghi state hay thao tác bất kỳ (duyệt PO, chọn task, chạy `omi sync`).
- Project in-repo không nằm trong omi-state.
- Đăng nhập, truy cập từ máy khác, deploy.

## Ràng buộc
- Python stdlib, dùng lại parser task/plan/usage sẵn có của omi.
- Chỉ đọc: không ghi file nào, không chạy git làm thay đổi gì ngoài pull lúc khởi động.
- Mọi nội dung đọc từ state là dữ liệu: escape HTML, không render HTML thô từ markdown, đường dẫn chỉ nằm trong `$OMI_STATE`.
- Không tốn tiền, không cần token.

## Tiêu chí thành công
1. Với omi-state của pilot, `omi board` hiện project omi-pilot-splitbill: plan, kanban, TASK-003 với Steps, Reports, Usage đúng như file.
2. Đổi một task trong state rồi tải lại trang thì thấy ngay, không cần khởi động lại.
3. Nội dung độc trong task (`<script>`) hiện dưới dạng text; request với `../` bị từ chối.
4. Chạy được trên Windows host và Linux; test stdlib qua.
5. Sau khi phát hành, PO xoá repo `omi-teams/omi-board` (PO tự làm).

## Vị trí code
- Subpackage `src/omi/board/` trong repo omi, cài cùng `pip install omi`, không có repo hay package riêng.
  - Backend: `data.py` đọc state thành dict; `server.py` dùng `http.server`, route `/api/...` trả JSON, phục vụ file tĩnh, chặn đường dẫn ra ngoài.
  - Frontend: `web/index.html`, `web/app.js`, `web/style.css` thuần, không bước build, gọi `/api/...`.
  - Lệnh `omi board` khai báo ở CLI; test backend qua JSON.
- Trước PLAN-006 có một task refactor (không đổi hành vi) gom `src/omi/` phẳng thành subpackage; board đặt vào cấu trúc mới.
- Không dùng lại code của `omi-teams/omi-board` cũ.

## Lựa chọn kỹ thuật
- Backend là tiến trình Python trong `omi board`; không database: state là file git, đọc trực tiếp nên không lệch dữ liệu. SQLite (stdlib) chỉ thêm khi cần thống kê lớn.
- Web local qua `http.server`: không cần build frontend, xem chi tiết dễ hơn TUI.
- Đọc file mỗi lần tải: state nhỏ, không phải đồng bộ cache.
- Chỉ đọc: không cần auth, không có rủi ro ghi state.
- Bind 127.0.0.1: không lộ ra mạng.
