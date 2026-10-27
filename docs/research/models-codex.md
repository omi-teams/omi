# Model và effort của Codex CLI (TASK-081)

## Phạm vi và nguồn

Ghi nhận ngày 2026-10-27, Codex CLI 0.164.0, đăng nhập ChatGPT của PO, trên máy host (Windows). Đây là ảnh chụp khả năng dùng với phiên đăng nhập này, không phải danh sách model cho mọi tài khoản.

- **[H]** `codex exec --help` (0.164.0): `-m, --model <MODEL>` chỉ mô tả "Model the agent should use"; không liệt kê ID hay effort. Trong container, `codex login status` in "Not logged in" và proxy chặn `api.openai.com`, nên không có probe nào chạy được ở đó (Reports của researcher).
- **[C]** `~/.codex/models_cache.json` trên host, `fetched_at` 2026-10-27T02:25Z, client 0.164.0. Đây là cache do CLI tải về; cho biết model nào CLI cho là hiển thị và mức effort nào được khai báo, không chứng minh model đó chạy được (việc đó do [M] xác nhận).
- **[M]** Lệnh chạy trên host bởi Coordinator, đã ghi trong Checkpoint của task: `codex exec --skip-git-repo-check --json -s read-only -m <id> -c model_reasoning_effort=<e> "say ok"`. Lượt viết tài liệu này không chạy lại lệnh nào.
- **[F]** `~/.codex/config.toml` trên host: `model = "gpt-6.1-sol"`, `model_reasoning_effort = "medium"`, `service_tier = "priority"`.
- **[R]** `.omi/config.json` (mục `codex_models`) và `README.md` mục liên quan: căn cứ cho mapping hiện tại và cho lý do `codex-default` xuất hiện. Đây là nội dung repo, không phải benchmark.

## Model dùng được

Bảng dưới lấy danh sách từ cache [C] và trạng thái đã chạy từ [M]. Cột `fits` và `avoid for` là **khuyến nghị theo mô tả trong cache**, chưa đo trên loại công việc nào. Cột chi phí và tốc độ là số đo thô, không phải giá.

| model id | effort levels (cache [C]) | fits (khuyến nghị) | avoid for (khuyến nghị) | relative cost/speed | evidence |
|---|---|---|---|---|---|
| `gpt-6.1-sol` | low, medium, high, xhigh, max, ultra; mặc định cache `low` | Mặc định của "everyday work" theo cache; feature thường, bugfix, refactor | Chưa đo đủ để giao việc rủi ro cao chỉ dựa vào probe này | 9685 ms, input 19532 tok (cache 13440) [M] | [M] `-m gpt-6.1-sol -c model_reasoning_effort=low`: `ok`. Cũng là model trong `config.toml` [F] |
| `gpt-6-astra` | low..ultra; mặc định `low` | "Frontier intelligence" theo cache: kiến trúc, phân tích khó | Tác vụ cơ học khi chi phí là ưu tiên | 10898 ms, input 18922 (cache 13312) [M] | [M] `ok` ở `low` |
| `gpt-6.1-terra` | low..ultra; mặc định `low` | Chưa có mô tả thực dụng ngoài "Codex model" | Chưa có bằng chứng | 8558 ms, input 18922 (cache 8320) [M] | [M] `ok` ở `low` |
| `gpt-6-sol` | low..ultra; mặc định `medium` | Thế hệ trước của workhorse; dự phòng cho `gpt-6.1-sol` | Chưa có bằng chứng so sánh | 7515 ms, input 18473 (cache 12928) [M] | [M] `ok` ở `low` |
| `gpt-6-luna` | low..max; mặc định `medium` (cache) | "Fast and affordable model for easier tasks": docs cơ học, đổi tên, việc đơn giản | Kiến trúc, review bảo mật | 7521 ms, input 18294 (cache 12672) [M] | [M] `OK` ở `low`; `ultra` được chấp nhận dù cache không liệt kê; `minimal` bị từ chối (xem effort) |
| `gpt-5.6-sol` | low..ultra; mặc định `low` | Thế hệ cũ, dự phòng | Chưa có bằng chứng | 8127 ms, input 18650 (cache 12416) [M] | [M] `ok` ở `low` |
| `gpt-5.6-terra` | low..ultra; mặc định `medium` | Thế hệ cũ, việc đơn giản theo mô tả cache | Chưa có bằng chứng | 9084 ms, input 18104 (cache 12032) [M] | [M] `ok` ở `low` |
| `gpt-5.6-luna` | low..max; mặc định `medium` | Thế hệ cũ, nhanh và rẻ theo mô tả cache | Chưa có bằng chứng | 10126 ms, input 17123 (cache 11392) [M] | [M] `ok` ở `low` |
| `gpt-reserve` | low..max; mặc định `medium`; cache ẩn (`visibility: hide`) | Không đề xuất: không hiển thị, không có mô tả chọn việc | Mọi việc cho tới khi PO xác nhận | 9385 ms, input 16577 (cache 11392) [M] | [M] `ok` ở `low`, dù bị ẩn trong cache |
| `codex-auto-review` | không rõ | Dành cho bước duyệt tự động của Codex | Không dùng cho omi | Không đo | [C] chỉ có trong cache, `visibility: hide`; không probe |

Ghi chú về số liệu [M]:

- Các probe đều trả "say ok" (đầu ra 5 token). Input token gần như bằng nhau vì prompt rất nhỏ và phần lớn là prompt hệ thống; lệch giữa các model chủ yếu là phần cached.
- Thời gian 7,5–11 giây gần như toàn là khởi động CLI. Không dùng để so tốc độ trên task thật.
- Output JSON không ghi tên model. Trong lượt không có `-m`, trả về cùng số input token với lượt `-m gpt-6.1-sol`; đây là bằng chứng gián tiếp, không phải xác nhận trực tiếp.
- Chi phí theo gói ChatGPT không đo được từ JSON (chỉ có token, không có giá). Không suy ra mức trừ hạn mức từ bảng này.
- `-m foo-model` trả lỗi `turn.failed`, 400, `invalid_request_error`: "The 'foo-model' model is not supported when using Codex with a ChatGPT account". Đây là cách xác nhận một ID không dùng được với đăng nhập này.

## Mặc định của `codex exec`

- **Trên host [F] + [M]:** không có `-m` thì dùng `gpt-6.1-sol` ở effort `medium`, theo `config.toml`. Lượt không `-m` cho cùng input token với lượt `-m gpt-6.1-sol`, nên hợp lý nhưng chưa được chứng minh tuyệt đối.
- **Trong container worker:** không có `config.toml` của host. Mặc định ở đó **chưa được kiểm chứng**. Suy đoán: model ưu tiên 1 trong cache là `gpt-6.1-sol`, với effort `default_reasoning_level` là `low`. Đây là suy đoán, không phải kết quả đo.
- Vì vậy không để `model` hoặc `effort` trống khi gọi omi. Trống là nguyên nhân của nhãn `codex-default` / `none` trong log.

## Effort

Effort được đọc qua `-c model_reasoning_effort=<e>`. Cache [C] và probe [M] cho thấy:

- **Giá trị được cache khai báo:** `low`, `medium`, `high`, `xhigh`, `max`, `ultra` (sol và astra, terra cũng có `ultra`); luna và reserve chỉ có đến `max`.
- **`none` [M]:** được chấp nhận trên `gpt-6-luna` (output 5, không reasoning).
- **`minimal` [M]:** bị từ chối trên `gpt-6-luna`: "Unsupported value: 'minimal' is not supported with the 'gpt-6-luna' model. Supported values are: 'none', 'low', 'medium', 'high', 'xhigh', and 'max'."
- **`ultra` trên luna [M]:** được chấp nhận (23 token output, 16 reasoning) dù cache không liệt kê cho luna. Chưa xác minh CLI ép xuống `max` hay truyền nguyên giá trị.

Probe effort trên `gpt-6.1-sol`, prompt bat-and-ball (cả sáu mức đều trả `5`) [M]:

| effort | output tok | reasoning tok | wall ms |
|---|---|---|---|
| low | 5 | 0 | 8975 |
| medium | 5 | 0 | 7323 |
| high | 17 | 10 | 8183 |
| xhigh | 20 | 13 | 9276 |
| max | 25 | 18 | 8896 |
| ultra | 17 | 10 | 8533 |

Trên prompt này, `low` và `medium` không sinh reasoning token; `high` trở lên sinh. `ultra` không sinh nhiều token hơn `high` trong lượt này. Đây là một prompt, một lần chạy: không đủ để kết luận `ultra` khác `high` về chất lượng. Chưa đo chất lượng, độ đúng, hay chi phí trên task khó. Không có căn cứ để mặc định `xhigh`, `max` hay `ultra` cho omi.

## Khuyến nghị

Phần này là đề xuất của Coordinator dựa trên cache và mô tả, không phải kết quả benchmark. Chưa được PO phê duyệt.

**Mapping `codex_models` đề xuất:**

| alias | model | effort mặc định | lý do |
|---|---|---|---|
| `haiku` | `gpt-6-luna` | `low` | Mô tả cache "fast and affordable"; chạy được [M] |
| `sonnet` | `gpt-6.1-sol` | `medium` | Mô tả cache "everyday work"; là model trong config host [F] |
| `opus` | `gpt-6-astra` | `high` | Mô tả cache "frontier intelligence"; chưa có probe chất lượng |

Lưu ý với mapping hiện tại trong `.omi/config.json` [R]: cả ba alias đang trỏ về `gpt-6.1-sol`. Điều này chạy được [M] nhưng không tách mức theo role. Đổi mapping là quyết định của PO.

**Mặc định theo role (khởi điểm, chưa đo):**

| role | alias / effort | ghi chú |
|---|---|---|
| `architect` | `opus` / `high` | Câu hỏi cấu trúc, sau hai vòng review thất bại |
| `engineer` | `sonnet` / `medium` | Feature và bugfix thường |
| `reviewer` | `sonnet` / `medium` | Giữ review độc lập |
| `security-reviewer` | `sonnet` / `medium`; `opus` / `high` khi auth, payment, secrets | Theo feature-sensitive |
| `researcher` | `sonnet` / `medium` | Thu thập bằng chứng |
| `docs-writer` | `haiku` / `low` | `sonnet` / `medium` cho tài liệu dài hoặc kỹ thuật |
| `devops` | `sonnet` / `medium`; `haiku` / `low` cho đổi cấu hình cơ học | |

Không có role nào được đề xuất `ultra` hay `max` mặc định.

## Chưa xác minh

- Mặc định của `codex exec` trong container worker (không có `config.toml` của host).
- Cách CLI xử lý `ultra` trên `gpt-6-luna` (ép xuống hay truyền nguyên).
- Model thật sự chạy trong các lượt không `-m`: JSON không ghi tên model; chỉ suy ra từ số input token.
- Chi phí theo gói ChatGPT của từng model.
- Tốc độ và chất lượng trên task thật (bugfix, refactor, review, security review, kiến trúc). Mọi cột "fits" và "avoid for" là khuyến nghị.
- Các model `codex-auto-review` và `gpt-reserve`: không dùng cho omi, không probe chất lượng.
- Kết quả trên gói hoặc đăng nhập khác với phiên PO.
