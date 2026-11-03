# Clean Architecture: bản đồ cấu trúc và pattern có lý do cho mọi project omi

Trạng thái: đề xuất từ spike TASK-169, chờ PO quyết (adopt, adjust, drop). Chưa có code sản phẩm nào được đổi.

## Người dùng
- PO: muốn nhìn đường dẫn của một file là biết lớp, module và việc của nó; không muốn trả tiền và quota cho "một bãi rác code có thể vận hành".
- Coordinator: lập task, duyệt bản đồ cấu trúc, commit thay đổi bản đồ.
- Agent (architect, engineer, reviewer): đọc bản đồ trước khi viết, ghi kế hoạch file và lý do chọn pattern.

## Vấn đề
Code do agent viết bị trôi: file phình ra, thư mục không còn nói lên file là gì. Giới hạn số dòng không giúp, và refactor cả repo đốt thời gian và quota. Cần một quy ước cấu trúc dùng cho mọi ngôn ngữ và stack (frontend, backend, database, docs), được kiểm tra bằng code không tốn token, và agent phải tìm hiểu pattern trước khi viết.

## Nguồn nghiên cứu
Nguồn lấy từ báo cáo research của TASK-169 (2026-11-03). Độ tin cậy của researcher: trung bình; WebFetch bị chặn nên các nhận định đến từ đoạn trích tìm kiếm của các URL chính, không phải đọc toàn trang.

- Quy tắc phụ thuộc: "source code dependencies can only point inwards"; code bên trong không được nhắc tên gì từ vòng ngoài; luồng điều khiển đi ra ngoài băng qua ranh giới bằng đa hình [https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html, 2012-08-13].
- Ports and adapters: ứng dụng có thể được "driven by users, programs, automated test or batch scripts" và test tách khỏi thiết bị và DB [https://alistair.cockburn.us/hexagonal-architecture/, 2005].
- Module trước, lớp sau: "package by component" gom một thành phần thô sau một interface công khai, trình biên dịch ép ranh giới; là chương 34 của *Clean Architecture* [https://simonbrown.je/modular-monolith/, bài 2016].
- Screaming Architecture (chương 21 của sách, qua bài điểm sách) [https://reflectoring.io/book-review-clean-architecture/, không rõ ngày].
- Công cụ lint kiến trúc:
  - import-linter (Python): contract `layers` với `containers`, nên cùng bộ lớp lặp lại cho từng module; kiểm cả import gián tiếp [https://import-linter.readthedocs.io/en/stable/contract_types.html, v1.x].
  - dependency-cruiser (JS/TS) [https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md, main].
  - ArchUnit (Java, phân tích bytecode): có `layeredArchitecture` và `onionArchitecture` [https://www.archunit.org/userguide/html/000_Index.html, 1.x].
  - go-arch-lint (Go): YAML với `components` và `deps.mayDependOn` theo glob [https://github.com/fe3dback/go-arch-lint/blob/master/docs/syntax/README.md, v3].
  - NetArchTest (.NET): kiểm phụ thuộc namespace bằng `ShouldNot().HaveDependencyOn`; repo gốc được ghi là không còn bảo trì [https://github.com/BenMorris/NetArchTest, 1.3.2].
  - deptrac (PHP): kiểm lớp [https://github.com/qossmic/deptrac/blob/2.0.x/docs/formatters.md, 2.0.x].
- Baseline và ratchet:
  - dependency-cruiser: `--baseline` ghi `.dependency-cruiser-known-violations.json`, `--ignore-known` bỏ qua các vi phạm đó [https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md, >=18.3.0].
  - ArchUnit: `FreezingArchRule.freeze()` giữ một ViolationStore chỉ co lại, có chế độ strict cho CI [https://www.archunit.org/userguide/html/000_Index.html, >=0.12.0].
  - deptrac: `--formatter=baseline` ghi `skip_violations` [https://github.com/qossmic/deptrac/blob/2.0.x/docs/formatters.md, 2.0.x].
- Chọn pattern: YAGNI nói về tính năng đoán trước (chi phí build, delay, carry, repair) và "does not apply to effort to make the software easier to modify" [https://martinfowler.com/bliki/Yagni.html, 2015].
- Kết luận của researcher: nguồn chính ủng hộ hướng nháp (phụ thuộc hướng vào trong, module trước lớp sau, một pattern cần lý do nêu rõ); không tìm thấy công cụ nào kiểm hướng import nhiều ngôn ngữ bằng regex, nên phần đó của omi chưa có tiền lệ.

## Chưa xác minh
Các điểm còn lại ghi là "chưa kiểm" trong báo cáo research; coi là giả định cho đến khi có nguồn.
- Baseline của go-arch-lint và import-linter: chưa kiểm (không nguồn nào ở trên nói có). NetArchTest không có chế độ baseline trong báo cáo.
- NetArchTest hay nhánh fork eNhancedEdition: chưa rõ dùng cái nào.
- Hướng dẫn chọn pattern theo GoF (tiêu đề "Applicability/Consequences"): chưa kiểm tiêu đề thật.
- URL bài Screaming Architecture gốc (có thể 2011): chưa kiểm.
- Phiên bản công cụ cụ thể: chưa ghim; các nhãn phiên bản ở trên chỉ là phiên bản nguồn nêu.
- Thuật toán kiểm và bảng regex là thiết kế của omi, chưa có tiền lệ ở nguồn nào.

## Thiết kế

### 1. Bố cục: module trước, lớp sau
```
<app>/
  modules/<module>/
    domain/              # thực thể, quy tắc nghiệp vụ, port (interface); không biết framework
    application/         # use case, API công khai của module; chỉ gọi domain và port
    adapters/inbound/    # HTTP handler, CLI, UI route, job: gọi application
    adapters/outbound/   # repository, client ngoài, file: cài đặt port
  platform/              # framework, config, nối DB, composition root
  shared/                # kernel nhỏ dùng chung (kiểu, lỗi, tiện ích thuần)
database/{migrations,seeds,schema}
docs/{adr,guides,modules}
tests/                   # phản chiếu cây code: tests/<module>/<layer>/...
```
Mỗi ngôn ngữ đổi tên gốc theo thông lệ nhưng giữ đủ các lớp:

| Stack | Gốc | Ví dụ |
|---|---|---|
| Python | `src/<pkg>/` | `src/shop/modules/orders/domain/order.py` |
| Go | `internal/` | `internal/orders/domain/order.go` |
| Java/Kotlin | package | `com.acme.shop.orders.domain.Order` (đường dẫn theo package) |
| .NET | project theo lớp hoặc thư mục theo module | `Shop.Orders.Domain/Order.cs` |
| Backend web | `modules/<m>/adapters/inbound/http/` | handler chỉ dịch request sang use case |
| Frontend (Next.js, React) | `src/` | route của framework nằm ở `platform/` hoặc `adapters/inbound/` (vd `app/` chỉ re-export); `modules/<m>/domain` là kiểu và quy tắc thuần, `application` là hook/use case, `adapters/outbound` là client API; component thuần hiển thị nằm trong `adapters/inbound/ui/` |
| Database | `database/` | `migrations/0007_add_orders.sql`; schema và seed theo module trong tên file; SQL không có import nên chỉ kiểm bằng đường dẫn |
| Docs | `docs/` | `adr/` quyết định, `guides/` cách làm, `modules/<m>.md` mô tả module |

### 2. Quy tắc
- Phụ thuộc hướng vào trong: `adapters -> application -> domain`; `platform` được import tất cả; `shared` không import gì ngoài `shared`.
- Module chỉ gọi module khác qua `application` của nó (API công khai). Không import `domain` hay `adapters` của module khác.
- Một khái niệm một file; tên file là khái niệm (`order.py`, không `utils.py`, `helpers.py`, `common.py`); dòng đầu file là một dòng mô tả trách nhiệm.
- File mới phải nằm trong thư mục đã có trong bản đồ.
- Dogfood: omi hiện có quy tắc `omi-modules` (thứ tự lớp theo subpackage, ~600 dòng). Bản đồ của chính omi được tạo bằng `omi structure init` và baseline ghi nợ hiện tại; không refactor cả repo.

### 3. Bản đồ `.omi/structure.md`
Một dòng cho mỗi glob, đọc bằng stdlib Python (cùng kiểu `meta()`/`parse()` đang dùng). Frontmatter `id: structure`, `summary`. Mỗi dòng: `- <glob> | <layer> | <responsibility> | imports: <layer>[, <layer>]`. Tên lớp cố định: `domain`, `application`, `adapter-in`, `adapter-out`, `platform`, `shared`, `data`, `docs`, `test`, `config`. `*` đầu tiên trong `modules/*/...` là tên module.

```
- src/shop/modules/*/domain/**          | domain       | entities, rules, ports            | imports: domain, shared
- src/shop/modules/*/application/**     | application  | use cases, module public API      | imports: application, domain, shared
- src/shop/modules/*/adapters/inbound/** | adapter-in  | HTTP, CLI, UI entry points        | imports: application, domain, shared
- src/shop/modules/*/adapters/outbound/**| adapter-out | DB, external clients, files       | imports: application, domain, shared
- src/shop/platform/**                  | platform     | framework, config, wiring         | imports: domain, application, adapter-in, adapter-out, shared, platform
- src/shop/shared/**                    | shared       | small kernel                      | imports: shared
- database/**                           | data         | migrations, seeds, schema         | imports: -
- docs/**, README.md                    | docs         | documentation                     | imports: -
- tests/**                              | test         | mirrors the code tree             | imports: domain, application, adapter-in, adapter-out, platform, shared
- pyproject.toml, .omi/**, .github/**   | config       | tooling and CI config             | imports: -
```
Khớp: dòng đầu tiên khớp thắng. Ngoài ra luật cố định, không cấu hình: import vào module khác chỉ hợp lệ khi đích nằm trong `modules/<khác>/application/`.

### 4. Kiểm tra không cần parser theo ngôn ngữ
Lệnh `python -m omi structure check [--changed] [--baseline]`, không tốn token, chạy trong hook `post-run` (container offline, không token) và trong CI. Thuật toán:
1. Liệt kê file đã theo dõi bởi git (hoặc chỉ file đổi so với `development` khi có `--changed`).
2. Kiểm đường dẫn: mỗi file phải khớp một dòng bản đồ, nếu không là vi phạm `unmapped`.
3. Với mỗi file nguồn có regex import cho ngôn ngữ của nó (theo đuôi file), rút chuỗi import.
4. Đổi chuỗi import thành đường dẫn nội bộ (tương đối, hoặc tiền tố package của project cấu hình trong bản đồ). Import không đổi được sang file đã ánh xạ coi là bên ngoài và bỏ qua.
5. So lớp của file nguồn với lớp của đích: đích không nằm trong `imports:` của nguồn là vi phạm `direction`; đích ở module khác ngoài `application` là vi phạm `cross-module`.
6. In `<path>: <rule>: <import>`, exit khác 0 nếu có vi phạm không nằm trong baseline.

Bảng regex import (thiết kế của omi, cần fixture thật cho từng ngôn ngữ khi cài đặt):

| Ngôn ngữ | Đuôi | Regex (nhóm 1 là chuỗi import) |
|---|---|---|
| Python | `.py` | `^\s*(?:from\s+(\.*[\w.]*)\s+import\b\|import\s+([\w.]+))` |
| JS/TS | `.js .jsx .ts .tsx .mjs .cjs` | `(?:\bfrom\s*\|\bimport\s*\(?\s*\|\brequire\s*\(\s*)['"]([^'"]+)['"]` |
| Go | `.go` | dòng trong khối `import (...)` hoặc sau `import`: `^\s*(?:import\s+)?(?:[\w.]+\s+)?"([^"]+)"` |
| Java/Kotlin | `.java .kt` | `^\s*import\s+(?:static\s+)?([\w.]+)` |
| C# | `.cs` | `^\s*using\s+(?:static\s+)?([\w.]+)\s*;` |
| PHP | `.php` | `^\s*use\s+(?:function\s+\|const\s+)?([\\\w]+)` và `(?:require\|include)(?:_once)?\s*\(?\s*['"]([^'"]+)['"]` |
| Rust | `.rs` | `^\s*(?:pub\s+)?use\s+((?:crate\|super\|self)(?:::\w+)*)` |
| Ruby | `.rb` | `^\s*require(?:_relative)?\s+['"]([^'"]+)['"]` |
| C/C++ | `.c .h .cc .cpp .hpp` | `^\s*#\s*include\s+"([^"]+)"` |
| SQL | `.sql` | n/a: chỉ kiểm đường dẫn |

Giới hạn đã biết: regex không hiểu import trong chuỗi/comment nhiều dòng, alias của bundler (`@/...`), re-export; C# và Java ánh xạ namespace sang thư mục theo quy ước nên có thể sai. Khi dự án có công cụ gốc (import-linter, dependency-cruiser, ArchUnit, deptrac, go-arch-lint, NetArchTest), bản đồ chỉ nêu tên công cụ trong `config` và `omi structure check` chạy lệnh đó thay cho regex. Bản đồ không sinh cấu hình công cụ gốc ở v1 (câu hỏi mở).

### 5. Ratchet cho repo có sẵn
- `omi structure init`: đề xuất bản đồ cho repo hiện có từ cây thư mục, in ra để PO/architect sửa; không ghi đè bản đồ đã có.
- `omi structure check --baseline`: ghi vi phạm hiện tại vào `.omi/structure-baseline.json` (khóa là `path|rule|import`, không có số dòng). Chỉ PO chạy lệnh này (như `rule_limits`).
- `omi structure check`: vi phạm trong baseline được bỏ qua; vi phạm mới làm fail. Mục baseline không còn xảy ra được báo "đã sửa, xóa khỏi baseline".
- Task chạm file nào thì phải sửa vi phạm của file đó: với `--changed`, baseline không áp cho file nằm trong diff của task.

### 6. Kế hoạch file trước khi build
- Bước plan/architect ghi mục `## File plan` trong task: mỗi dòng `- edit|create <path> (<layer>)`. Đường dẫn phải khớp bản đồ.
- `omi run` đọc file plan và bản đồ từ state hoặc `development`, không đọc bản sao trong worktree (agent sửa được), như `scope.task_scope` hiện làm.
- Sau khi engineer chạy, cùng chỗ in `OUT OF SCOPE` (`worker/run.py`, `scope.out_of_scope`) thêm hai loại và exit 3: `OUT OF PLAN: <path>` (file đổi nhưng không có trong file plan) và `UNMAPPED: <path>` (không khớp bản đồ).
- Thư mục mới cần bước architect và cập nhật bản đồ. Bản nháp ghi "cùng PR"; vì bản đồ được đọc từ `development`/state chứ không từ worktree, thay đổi bản đồ phải do Coordinator commit trước bước engineer (câu hỏi mở 3).
- Task không có `## File plan` (task cũ, docs, spike): chỉ kiểm `scope` như hiện nay.

### 7. Pattern có lý do và thư viện tham khảo
- Bước design ghi trong task: `Pattern: <tên> - <lực cần giải ở đây> - <vì sao phương án đơn giản hơn chưa đủ>`. Code chỉ kiểm dạng dòng (đủ ba phần, không rỗng); chất lượng lý do do reviewer đánh giá.
- Thư viện `.omi/references/patterns/<tên>.md`: mỗi file có "khi nào dùng", "khi nào không dùng", dấu hiệu nên bỏ. Bắt đầu với Repository, Strategy, Adapter, Factory, State, CQRS; mục anti-pattern theo stack (vd god module, `utils` hố đen, framework lọt vào domain, vòng import giữa module).
- `load_references` hiện chỉ glob `.omi/references/*.md`, nên thư mục con cần sửa catalog (task 5 dưới đây).
- Agent nghiên cứu pattern trước khi code: bước architect phải đọc file pattern liên quan (qua `refs`) trước khi viết `Pattern:`; không nạp vào budget rule.

### Reviewer
Reviewer FAIL khi: (a) thiếu cấu trúc cần thiết (file nhiều trách nhiệm, tên file không nói khái niệm, logic nghiệp vụ nằm ở adapter); (b) pattern thừa (có `Pattern:` mà không có lực thật, lớp bọc một lần dùng, interface chỉ có một cài đặt và không có ranh giới cần đảo ngược). Over-engineering cũng là rác.

## Kiểm bằng code, kiểm bằng reviewer

| Kiểm bằng code (không token) | Reviewer đánh giá |
|---|---|
| Mọi file khớp bản đồ | Tên file có nói đúng khái niệm |
| Hướng import và gọi chéo module | File có đúng một trách nhiệm |
| File chạm có nằm trong file plan | Lý do của dòng `Pattern:` có thật |
| Dòng `Pattern:` đủ ba phần | Pattern thừa hoặc thiếu |
| Vi phạm mới so với baseline | Header một dòng có đúng nội dung |

## Rủi ro
- Regex bỏ sót hoặc báo nhầm (alias, re-export, namespace): giảm bằng fixture thật theo ngôn ngữ, bỏ qua import không ánh xạ được, và ưu tiên công cụ gốc khi có. Rủi ro còn lại: vi phạm lọt qua mà không báo.
- Bản đồ sai làm chặn việc hợp lệ: `init` chỉ đề xuất, PO/architect duyệt; `UNMAPPED` nói rõ dòng nào thiếu.
- Baseline thành chỗ giấu nợ: chỉ PO ghi, mục đã sửa được báo, `--changed` buộc sửa file đang chạm.
- Thêm bước architect và file plan tăng chi phí mỗi task: bỏ qua cho task không có `## File plan`; chỉ dùng cho flow feature/refactor.
- Quá khuôn khổ cho project nhỏ: bản đồ có thể chỉ vài dòng; reviewer FAIL cả pattern thừa.
- Ép kiểu bố cục lên framework có quy ước riêng (Next.js `app/`): bản đồ ánh xạ thư mục của framework vào `platform`/`adapter-in`.

## Câu hỏi mở
1. NetArchTest hay nhánh eNhancedEdition cho .NET; nguồn và phiên bản của từng công cụ gốc.
2. `.omi/structure.md` có nên sinh cấu hình công cụ gốc (import-linter, dependency-cruiser...) hay chỉ trỏ tới nó.
3. Thay đổi bản đồ: Coordinator commit trước bước engineer (đề xuất) hay cho phép trong cùng PR và chạy check bằng bản đồ của nhánh.
4. `omi run` có cần chặn sớm trong guard hook (`scope.guard`) khi agent ghi file không khớp bản đồ, hay chỉ kiểm sau khi chạy.
5. Cách dò gốc package cho Go/Java/C# khi regex trả về tên package chứ không phải đường dẫn.

## Ràng buộc
- Chỉ stdlib Python 3.13, không thêm dependency; chạy được trên Windows và trong Docker worker (như `template-kinds.md`).
- Mỗi module `src/omi` dưới ~600 dòng (quy tắc `omi-modules`): code mới đặt ở module riêng, vd `src/omi/project/structure.py`.
- Hook chạy offline, không token; bản đồ, baseline, file plan đọc từ state/`development`.

## Tiêu chí thành công
- `omi structure init` trên repo có sẵn in ra bản đồ đề xuất mà `check` chấp nhận.
- `omi structure check` fail khi có file không khớp bản đồ hoặc import sai hướng, pass khi chỉ có vi phạm trong baseline.
- Task có `## File plan` đổi file ngoài plan hoặc ngoài bản đồ: `omi run` in `OUT OF PLAN`/`UNMAPPED` và exit 3.
- Mỗi regex ở bảng trên có test với fixture thật.
- Test tự động cho từng điểm trên đều pass (`python3 tests/test_omi.py`).

## PLAN-008: tách thành task cỡ engineer
Mỗi task một scope; thứ tự theo phụ thuộc. Scope viết theo bố cục hiện tại của repo omi. Test của omi chia theo vùng (`tests/test_<vùng>.py`, gom bởi `tests/test_omi.py`): `tests/test_omi.py` trong các scope dưới đây nghĩa là file test mới `tests/test_structure.py` cộng dòng import trong `tests/test_omi.py`; task 6 và 8 thêm test vào `tests/test_worker.py` và `tests/test_tasks.py` thay vì file mới.

1. **Bản đồ và đọc bản đồ** (nền): parse `.omi/structure.md`, khớp glob, tên module, chọn dòng đầu khớp, báo lỗi định dạng. Scope: `src/omi/project/structure.py`, `tests/test_omi.py`.
2. **Kiểm đường dẫn và hướng import**: bảng regex, đổi import thành đường dẫn, luật `direction` và `cross-module`, lệnh `omi structure check`, đăng ký trong CLI. Scope: `src/omi/project/structure.py`, `src/omi/app/cli.py`, `tests/test_omi.py`. Phụ thuộc: 1.
3. **Baseline và `--changed`**: `.omi/structure-baseline.json`, chỉ vi phạm mới fail, báo mục đã sửa. Scope: `src/omi/project/structure.py`, `src/omi/app/cli.py`, `tests/test_omi.py`. Phụ thuộc: 2.
4. **`omi structure init`**: đề xuất bản đồ từ cây thư mục, không ghi đè. Scope: `src/omi/project/structure.py`, `src/omi/app/cli.py`, `tests/test_omi.py`. Phụ thuộc: 1.
5. **Hook và mẫu**: gọi `omi structure check` trong mẫu `post-run`, bản đồ mẫu trong template, catalog nhận `.omi/references/patterns/`. Scope: `src/omi/template/dot-omi/**`, `src/omi/project/catalogs.py`, `src/omi/setup/upgrade.py`, `src/omi/template_shas.json`, `tests/test_omi.py`. Phụ thuộc: 2.
6. **File plan và từ chối trong `omi run`**: đọc `## File plan` từ state/`development`, in `OUT OF PLAN`/`UNMAPPED`, exit 3. Scope: `src/omi/project/scope.py`, `src/omi/worker/run.py`, `tests/test_omi.py`. Phụ thuộc: 1.
7. **Thư viện pattern**: `.omi/references/patterns/*.md` (Repository, Strategy, Adapter, Factory, State, CQRS, anti-pattern theo stack) với nguồn cho từng pattern. Cần researcher cấp nguồn trước. Scope: `src/omi/template/dot-omi/references/patterns/**`. Phụ thuộc: 5.
8. **Vai trò và flow**: architect ghi `## File plan` và `Pattern:`, reviewer có luật FAIL cấu trúc thiếu/pattern thừa, kiểm dạng dòng `Pattern:`. Scope: `src/omi/template/dot-omi/agents/omi-agent-architect.md`, `src/omi/template/dot-omi/agents/omi-agent-reviewer.md`, `src/omi/template/dot-omi/workflows/omi-flow-feature.md`, `src/omi/project/tasks.py`, `tests/test_omi.py`. Phụ thuộc: 6, 7.
9. **Tài liệu**: README/hướng dẫn dùng `omi structure`. Scope: `README.md`, `docs/**`. Phụ thuộc: 2-4.
