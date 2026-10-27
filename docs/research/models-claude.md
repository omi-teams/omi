# Model và effort của Claude Code (TASK-080)

## Phạm vi và nguồn

Ghi nhận ngày 2026-10-27, Claude Code CLI 2.1.302, đăng nhập phiên của PO. Đây là ảnh chụp khả năng dùng trong phiên này, không phải danh sách model cho mọi tài khoản.

- **[H]** `.omi/tasks/TASK-080.md`, mục Reports: researcher đã đọc `claude --help`. `--model` nhận alias hoặc tên model đầy đủ; help nêu `fable`, `opus`, `sonnet`, không nêu `haiku`. `--effort` nhận `low`, `medium`, `high`, `xhigh`, `max`.
- **[C]** Cùng mục Reports: chạy trong container với tám alias/ID bên dưới đều nhận `is_error:true`, `Not logged in · Please run /login`, `terminal_reason:api_error`, không token hay chi phí. Kết quả này không xác nhận quyền dùng model.
- **[M]** Mục Checkpoint của task: Coordinator chạy trên host bằng phiên PO, lệnh `claude -p --model <m> --effort low --output-format json "say ok"`. Bảng bên dưới chép kết quả đã được ghi trong task; lượt viết tài liệu không chạy lại.
- **[E]** Cùng Checkpoint: probe effort trên host bằng `claude -p --model haiku --effort <e> "What is 17*23? Answer with the number only."`.
- **[R]** `.omi/agents/CATALOG.md` và các role; `.omi/workflows/CATALOG.md` và phần Models của workflow: căn cứ cho các khuyến nghị bên dưới. Đây là nội dung repo, không phải benchmark chất lượng model.

## Model dùng được trong phiên

Cột fits và avoid for là **khuyến nghị theo [R]**, chưa được đo trên các loại công việc đó. Effort ngoài `low` chỉ được probe trên alias `haiku`; chưa kiểm chứng từng tổ hợp model × effort.

| model id | alias | effort levels | fits | avoid for | relative cost/speed | evidence |
|---|---|---|---|---|---|---|
| `claude-haiku-5-5` | `haiku` | Alias: cả 5 mức [E]; ID: `low` [M] | Docs cơ học, đổi tên, config cơ học có yêu cầu rõ | Kiến trúc, review bảo mật phức tạp chưa có đánh giá chất lượng | Rẻ nhất trong probe; 1,6–2,2 giây | [M]: cả alias và ID trả `ok`; alias ghi `modelUsage: claude-haiku-5-5` |
| `claude-sonnet-5-5` | `sonnet` | `low` [M]; 4 mức còn lại chỉ có help [H], chưa probe | Feature thường, bugfix, refactor, review, nghiên cứu, docs kỹ thuật | Chưa có bằng chứng đủ để giao quyết định rủi ro cao chỉ dựa vào probe này | Khoảng 16–19 lần chi phí Haiku trong probe; 2,4–5,8 giây | [M]: cả alias và ID trả `ok`; alias ghi `modelUsage: claude-sonnet-5-5` |
| `claude-opus-5-5` | `opus` | `low` [M]; 4 mức còn lại chỉ có help [H], chưa probe | Kiến trúc, phân tích khó, hỗ trợ sau nhiều vòng review thất bại | Tác vụ cơ học khi chi phí là ưu tiên | Khoảng 2 lần Sonnet, 35–38 lần Haiku trong probe; 1,3–6,5 giây | [M]: cả alias và ID trả `ok`; alias ghi `modelUsage: claude-opus-5-5` |
| `claude-fable-5-1` | `fable` | Chỉ thử `low`, không có câu trả lời thành công | Chưa đề xuất dùng với phiên hiện tại | Mọi task cho tới khi xác nhận quyền dùng | Khoảng 0,630 s, chi phí ghi 0 do lỗi | [M]: cả hai trả `is_error`, `Fable 5.1 requires usage credits. Switch to another model`; không có `modelUsage` |

Số liệu gốc [M], mỗi đầu vào một lượt:

| `--model` | Kết quả | `duration_ms` | `total_cost_usd` |
|---|---|---|---|
| `opus` | `ok` | 6493 | 0.1459 |
| `claude-opus-5-5` | `ok` | 1280 | 0.1281 |
| `sonnet` | `ok` | 5845 | 0.0727 |
| `claude-sonnet-5-5` | `ok` | 2354 | 0.0640 |
| `haiku` | `ok` | 1617 | 0.0039 |
| `claude-haiku-5-5` | `ok` | 2224 | 0.0034 |

Các tỷ lệ so cùng kiểu đầu vào (alias với alias, ID với ID), làm tròn. Prompt rất nhỏ, phần lớn chi phí là system prompt đã cache theo ghi chú host [M]. Không suy ra giá niêm yết, tiền thực trả của gói đăng nhập, hay tốc độ trên task thật. Opus ID nhanh hơn Sonnet ID trong lượt này; số mẫu không đủ để xếp hạng tốc độ ổn định.

## Effort

Help chấp nhận năm mức [H]. Probe Haiku [E] đều trả `391`:

| `--effort` | `output_tokens` |
|---|---|
| `low` | 29 |
| `medium` | 57 |
| `high` | 61 |
| `xhigh` | 67 |
| `max` | 207 |

Checkpoint chỉ ghi khoảng chi phí 0.0034–0.0036 USD và thời gian 1,9–2,6 giây cho cả nhóm, không có số riêng từng mức. Trong probe này, effort cao hơn đi cùng nhiều output token hơn. Task diễn giải đó là token suy nghĩ, nhưng không cung cấp breakdown thinking riêng: chưa xác minh ngân sách thinking cụ thể hoặc cơ chế tăng ngân sách. Chưa đo lợi ích độ đúng, tốc độ, chi phí trên bài khó, hoặc tác động trên Opus/Sonnet. Không có căn cứ để mặc định `xhigh` hay `max` cho task omi.

## Khuyến nghị theo role

Đây là lựa chọn khởi điểm để Coordinator ghi **model và effort cụ thể cho từng task**, không phải fallback tự động hay kết luận benchmark. Bảng giữ mapping hiện có trong catalog [R]; các mức `medium`/`high` trên Sonnet/Opus chưa được probe trong [M]. Các ID tương ứng nằm trong bảng model.

| Role (`omi-agent-…`) | Model / effort khởi điểm | Khi điều chỉnh (khuyến nghị [R]) |
|---|---|---|
| `architect` | `opus/high` | Phù hợp câu hỏi cấu trúc hoặc sau hai vòng review thất bại |
| `designer-ui` | `sonnet/medium` | Giữ cho spec và review UI có nhiều trạng thái |
| `devops` | `sonnet/medium` | `haiku/low` cho đổi version/path cơ học; hành vi mới giữ Sonnet |
| `docs-writer` | `haiku/low` | `sonnet/medium` cho tài liệu dài hoặc kỹ thuật |
| `engineer` | `sonnet/medium` | `opus/high` khi cần phân tích khó sau review thất bại |
| `qa-tester` | `sonnet/medium` | Chưa có benchmark để đề xuất hạ model |
| `researcher` | `sonnet/medium` | Chưa có benchmark để đề xuất tăng effort thường xuyên |
| `reviewer` | `sonnet/medium` | Giữ lượt review độc lập theo workflow |
| `security-reviewer` | `sonnet/medium` | `opus/high` cho auth, payment hoặc secrets, theo workflow feature-sensitive |

## Khuyến nghị theo loại bước workflow

Các tên bước và mapping dựa trên workflow repo [R]; hiệu quả lựa chọn chưa đo. Bảng này không thay đổi cấu hình workflow hay quyền phê duyệt của PO.

| Loại bước | Model / effort đề xuất | Áp dụng |
|---|---|---|
| Lập task (`plan`) | `sonnet/low` | Coordinator lập phạm vi và tiêu chí |
| Kiến trúc, phân tích thay đổi (`architect`, `impact`, `options`, `replan`) | `opus/high` | Phân tích phương án và rủi ro |
| Thiết kế UI (`design`) | `sonnet/medium` | Spec trước build |
| Triển khai (`build`, `reproduce`, `fix`, `baseline`, `refactor`, `hotfix`) | `sonnet/medium` | Feature, bugfix, refactor; tăng lên Opus khi cần xử lý thất bại lặp lại |
| Kiểm tra (`review`, `qa`) | `sonnet/medium` | Review độc lập, kiểm tiêu chí |
| Bảo mật (`security`) | `sonnet/medium`; `opus/high` khi auth/payment/secrets | Theo feature-sensitive |
| Nghiên cứu (`research`) | `sonnet/medium` | Thu thập bằng chứng cho spike |
| Viết (`write`, `postmortem`) | `haiku/low`; `sonnet/medium` nếu dài hoặc kỹ thuật | Tóm tắt bằng chứng đã có |
| Vận hành (`contain`, `diagnose`) | `sonnet/medium` | Incident cần đánh giá hành vi và nguyên nhân |
| Chuẩn bị release/promote/tag (`candidate`, `pr`, `promote`, `tag`) | `haiku/low` nếu cơ học; `sonnet/medium` nếu cần phân tích | Khuyến nghị phân theo độ phức tạp; chưa đo |
| Quyết định/phê duyệt (`accept`, `decide`, `merge-staging`, `merge-main`, `merge-prod`) | PO quyết định; nếu cần soạn nội dung: `sonnet/low` | Model không thay quyền quyết định của PO |

## Chưa kiểm chứng và bước tiếp theo

- Chưa có log JSON đầy đủ trong report; bằng chứng host được chép từ Checkpoint, chưa tái chạy độc lập.
- Chưa thử các model ngoài tám alias/ID đã nêu; help nhận tên đầy đủ không chứng minh mọi ID đều dùng được.
- Chưa đo tổ hợp Sonnet/Opus với `medium`, `high`, `xhigh`, `max`, task thật hoặc chất lượng theo role. Cần probe riêng trước khi coi các tổ hợp này đã được xác nhận.
- PO chọn giữ hay điều chỉnh khuyến nghị ở bước `decide` của spike. Không thay đổi role/workflow trong lượt viết này.
