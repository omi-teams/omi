# Bản đồ cấu trúc (`omi structure`)

Bản đồ cấu trúc cho omi biết mỗi file thuộc lớp nào, module nào, chịu trách nhiệm gì và được import từ lớp nào. Bản đồ nằm ở `.omi/structure.md`, đọc bằng Python stdlib, không tốn token. Thiết kế đầy đủ và lý do: [docs/specs/clean-architecture.md](../specs/clean-architecture.md).

## Các lớp

| Lớp | Nội dung |
|---|---|
| `domain` | thực thể, quy tắc nghiệp vụ, port (interface); không biết framework |
| `application` | use case, API công khai của module |
| `adapter-in` | HTTP handler, CLI, UI route, job: gọi `application` |
| `adapter-out` | repository, client ngoài, file: cài đặt port |
| `platform` | framework, config, nối DB (composition root); được import mọi lớp |
| `shared` | kernel nhỏ dùng chung (kiểu, lỗi, tiện ích thuần) |
| `data` | migration, seed, schema |
| `docs` | tài liệu |
| `test` | test, phản chiếu cây code |
| `config` | cấu hình công cụ và CI |

## Định dạng bản đồ

Mỗi dòng là một luật, dòng khớp đầu tiên thắng:

```
- <glob>[, <glob>] | <layer> | <responsibility> | imports: <layer>[, <layer>]
```

- `imports: -` nghĩa là không import gì ngoài chính lớp đó.
- `**` khớp qua dấu `/`; `*` không khớp qua `/`. `*` đầu tiên sau `modules/` là tên module.
- Luật cố định, không cấu hình: import sang module khác chỉ hợp lệ khi đích nằm trong `application` của module đó.
- Dòng sai định dạng, lớp không có trong danh sách, hoặc `imports:` rỗng làm `omi structure check` báo lỗi kèm số dòng.

### Ví dụ backend (Python)

```
- src/shop/modules/*/domain/**           | domain       | entities, rules, ports            | imports: domain, shared
- src/shop/modules/*/application/**      | application  | use cases, module public API      | imports: application, domain, shared
- src/shop/modules/*/adapters/inbound/** | adapter-in   | HTTP, CLI, UI entry points        | imports: application, domain, shared
- src/shop/modules/*/adapters/outbound/**| adapter-out  | DB, external clients, files       | imports: application, domain, shared
- src/shop/platform/**                   | platform     | framework, config, wiring         | imports: domain, application, adapter-in, adapter-out, shared, platform
- src/shop/shared/**                     | shared       | small kernel                      | imports: shared
- database/**                            | data         | migrations, seeds, schema         | imports: -
- docs/**, README.md                     | docs         | documentation                     | imports: -
- tests/**                               | test         | mirrors the code tree             | imports: domain, application, adapter-in, adapter-out, platform, shared
- pyproject.toml, .omi/**, .github/**    | config       | tooling and CI config             | imports: -
```

Với `src/shop/modules/orders/adapters/inbound/http/order_routes.py`, `omi` ghi nhận lớp `adapter-in`, module `orders`. Import `from ..domain.order import Order` được phép; import `src/shop/modules/billing/domain/...` từ module `orders` là vi phạm `cross-module`.

### Ví dụ frontend (Next.js / React)

`app/` là quy ước của framework, nên các route chỉ re-export từ `src/modules`:

```
- src/app/**                             | adapter-in   | Next.js routes, re-export only    | imports: application, domain, shared
- src/modules/*/domain/**                | domain       | types and pure rules              | imports: domain, shared
- src/modules/*/application/**           | application  | hooks, use cases, module API      | imports: application, domain, shared
- src/modules/*/adapters/inbound/**      | adapter-in   | UI components, route handlers     | imports: application, domain, shared
- src/modules/*/adapters/outbound/**     | adapter-out  | API clients                       | imports: application, domain, shared
- src/platform/**                        | platform     | config, providers, wiring         | imports: domain, application, adapter-in, adapter-out, shared, platform
- src/shared/**                          | shared       | small kernel                      | imports: shared
- tests/**                               | test         | mirrors the code tree             | imports: domain, application, adapter-in, adapter-out, platform, shared
- package.json, *.config.*, .github/**   | config       | tooling and CI config             | imports: -
```

## Các lệnh

### `omi structure init`

In ra bản đồ đề xuất từ các file đang được git theo dõi; không ghi file nào. Thư mục đã biết được gán lớp (ví dụ `docs` → `docs`, `migrations` → `data`); thư mục chưa biết có responsibility `TODO: assign a layer and responsibility`, phải sửa trước khi dùng. Nếu `.omi/structure.md` đã có, lệnh dừng và không đổi gì.

Không ghi trực tiếp bằng `> .omi/structure.md`: shell tạo file rỗng trước, rồi `init` báo file đã tồn tại. Ghi ra file tạm, duyệt, rồi chuyển vào:

```sh
python -m omi structure init > /tmp/structure.md
# sửa /tmp/structure.md cho đúng với repo
mv /tmp/structure.md .omi/structure.md
```

### `omi structure check`

Kiểm mọi file đang được git theo dõi. Mỗi vi phạm in một dòng `<path>: <rule>: <import>`:

| Rule | Nghĩa |
|---|---|
| `unmapped` | file không khớp dòng nào của bản đồ |
| `direction` | import sang lớp không nằm trong `imports:` của lớp nguồn |
| `cross-module` | import vào module khác, không qua `application` |
| `tool` | lệnh công cụ gốc khai bằng `tool:` trong bản đồ trả lỗi |

Exit 0 khi không có vi phạm mới; exit 1 khi có vi phạm không nằm trong baseline. Vi phạm đã ghi trong baseline bị bỏ qua. Mục baseline không còn xảy ra được in dạng `fixed, remove from .omi/structure-baseline.json: <key>` (không làm lệnh fail).

Với dự án có lệnh gốc (import-linter, dependency-cruiser, ArchUnit, deptrac, go-arch-lint, NetArchTest...), đặt lệnh đó làm `responsibility` của dòng `config` theo dạng `tool: <lệnh>`; `check` chạy lệnh và báo khi nó thoát khác 0.

### `omi structure check --baseline`

Ghi mọi vi phạm hiện tại vào `.omi/structure-baseline.json` (khóa là `path|rule|import`, không có số dòng) rồi exit 0. Đây là ratchet cho repo có sẵn nợ: vi phạm cũ được chấp nhận, vi phạm mới làm fail. Theo quy ước của dự án, chỉ PO chạy lệnh này, vì baseline là nơi giấu nợ nếu ai cũng ghi được.

### `omi structure check --changed`

Chỉ kiểm các file trong `git diff development...HEAD` và bỏ qua baseline. Task chạm file nào thì phải sửa vi phạm của file đó; file không đổi không bị kiểm. Cần nhánh `development` tồn tại.

`--baseline` và `--changed` không dùng chung trong một lệnh.

## File plan và `Pattern:` trong task

### `## File plan` (đã có trong `omi run`)

Task làm feature hoặc refactor ghi mục `## File plan`, mỗi file một dòng:

```
## File plan
- create src/shop/modules/orders/domain/order.py (domain)
- edit src/shop/modules/orders/application/place_order.py (application)
```

Đường dẫn phải khớp bản đồ. Khi engineer chạy xong, `omi run` so danh sách file đã đổi với file plan và bản đồ (đọc từ `development`, không đọc bản sao trong worktree). Nó in:

- `OUT OF PLAN: <path>`: file bị đổi nhưng không có trong file plan;
- `UNMAPPED: <path>`: file không khớp bản đồ (hoặc bản đồ không đọc được).

Khi có một trong hai dòng này, `omi run` thoát mã 3. Task không có mục `## File plan` không bị kiểm thêm ngoài `scope`.

### `Pattern:` (quy ước, chưa có lệnh kiểm)

Bước thiết kế ghi lý do dùng pattern theo dạng:

```
Pattern: <tên> - <lực cần giải quyết ở đây> - <vì sao phương án đơn giản hơn chưa đủ>
```

Ví dụ: `Pattern: Repository - đổi DB từ Postgres sang SQLite cho test - hai nơi gọi SQL trực tiếp, đổi là sửa cả hai`.

Hiện omi chưa có lệnh tự kiểm dòng này; reviewer đánh giá lý do có thật hay không. Kiểm tự động dạng dòng là việc còn trong lộ trình ([clean-architecture.md](../specs/clean-architecture.md), PLAN-008).

## Quy trình đề xuất khi áp dụng cho một repo

1. `omi structure init > /tmp/structure.md`, sửa các dòng `TODO`, rồi chuyển thành `.omi/structure.md`.
2. `omi structure check`; sửa các vi phạm mới của chính việc viết bản đồ.
3. PO chạy `omi structure check --baseline` để ghi nợ hiện có.
4. Từ đó, mọi task chạm file có vi phạm phải sửa vi phạm đó (`--changed`).
5. Đưa `.omi/structure.md` vào `development` trước khi engineer bắt đầu task mới: `omi run` đọc bản đồ từ `development` (hoặc state ở chế độ detached), không đọc bản sao trong worktree. Cách này là đề xuất, chưa được PO chốt.
