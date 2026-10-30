# Pilot omi board (TASK-116): omi-pilot-splitbill

2026-10-30. Coordinator chạy trên Windows 11 host, omi ở development `478f894`,
state thật `~/.omi/state`, dự án `omi-pilot-splitbill`, task TASK-003.

Bằng chứng dưới đây được chép từ checkpoint TASK-116 của Coordinator; docs-writer
không có quyền đọc state thật nên không chạy lại các lệnh.

## Tiêu chí 1-4

| # | Tiêu chí | Lệnh hoặc thao tác | Kết quả trên state pilot |
|---|---|---|---|
| 1 | Board đọc đúng state thật | `omi board` (cổng 8801); gọi `/api/projects/omi-pilot-splitbill` và `/api/projects/omi-pilot-splitbill/tasks/TASK-003` | Dự án trả plan PLAN-000, kanban done=[TASK-003]. Phần Steps và Reports của task khớp từng byte với file; Usage có 2 dòng như file (engineer + reviewer PASS 98f8665). |
| 2 | Sửa file state, board cập nhật không cần restart | Bản sao state, `OMI_STATE=<bản sao>` (cổng 8802); sửa `title:` của TASK-003 | Request API kế tiếp trả title mới, server không restart. |
| 3 | An toàn đầu vào | `title: <script>alert(1)</script>`; `curl --path-as-is` tới `/../../etc/passwd`, `/%2e%2e/%2e%2e/README.md`, `/api/projects/..%2f..%2f/tasks/x`, `/api/projects/omi-pilot-splitbill/tasks/..%2fTASK-003` | Title trả về là JSON text thuần, UI chỉ chèn bằng `textContent` (test tĩnh TASK-115). Cả 4 đường dẫn trả 404. Header CSP là `default-src 'self'`. |
| 4 | Chạy trên Windows và Linux | Windows: C1-C3 ở trên và `python tests/test_omi.py`. Linux: CI `ubuntu-latest` và worker Docker | Windows: test `ok` (chỉ bỏ qua test browser Playwright). Linux: CI development `478f894` success; worker Docker (Linux) chạy `tests/test_omi.py` `ok` trong mọi lần chạy TASK-115/134. QA browser Chrome thật ở 360/390/768/1280 px ghi trong TASK-115. |

## Gap cho plan sau

- Chưa có Playwright trên host và worker nên test browser bị bỏ qua (TASK-128).
- Board chỉ hiện dự án trong registry; repo omi không có trong danh sách.
- Task đã done vẫn hiện bước cuối là bước hiện tại; Usage cuộn bên trong thẻ của nó (TASK-125).
