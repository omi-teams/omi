# Đánh giá omi: skill, role và workflow so với baseline (TASK-057)

## Tóm tắt

- Đã chạy 7 cặp so sánh trên sandbox Python (`omi init`), mỗi biến thể một lần (n=1). Kết quả chỉ mang tính định hướng.
- Tất cả biến thể đều đúng ở các bài nhỏ. Không có biến thể nào sai, nên chất lượng không phân biệt được ở các bài này.
- Hai skill tốn thêm token mà không cho thấy lợi ích: `omi-skill-debug-root-cause` và `omi-agent-security-reviewer` (đề xuất rút gọn).
- Các skill còn lại: giữ tạm thời, vì chưa đủ bằng chứng để bỏ hoặc vì bài thử chưa kiểm tra được quy tắc phạm vi và an toàn của chúng.
- Context mặc định omi thêm vào: **3402 token** (AGENTS.md 1297, skills CATALOG 889, workflows CATALOG 830, agents CATALOG 386).
- Release workflow không được đo (chỉ có bước của Coordinator, không có lần chạy agent).

Nguồn: `TASK-057 ## Results` (bảng kết quả) và `TASK-057 ## Plan` (kế hoạch và giả thuyết).

## Cách đo

- **Sandbox:** một repo Python nhỏ tạo bằng `omi init`, cùng commit bắt đầu cho mọi bài.
- **Bài (scenario):** mỗi bài là một task trong sandbox. Các họ workflow được phủ: feature, bugfix, docs-only, change-request, incident. Họ security được thêm vào để kiểm tra security-reviewer trên một lỗi được cài sẵn. Họ release không đo.
- **Baseline:** cùng bài, nhưng chỉ dùng role thường (không skill, không workflow). Kế hoạch có 8 baseline, bảng kết quả có 7 cặp hợp lệ, cộng một baseline architect không hợp lệ (xem bên dưới).
- **Chỉ số:**
  - đúng: test pass, lỗi được cài sẵn được tìm thấy, hoặc tiêu chí đạt;
  - token output và token cache-read, lấy từ mục `## Usage` của mỗi task;
  - thời gian (giây);
  - số vòng review.
- **Giới hạn của cách đo:** n=1 cho mỗi biến thể, nên chênh lệch vài phần trăm là nhiễu. Một số cặp khác model hoặc effort (xem bảng), nên chênh lệch còn lẫn yếu tố model.

## Bảng kết quả

| Cặp | Biến thể | Đúng | Output | Cache | Giây |
|---|---|---|---|---|---|
| feature: engineer + lean-implementation | đầy đủ | có (3/3 tiêu chí) | 813 | 70714 | 13 |
| feature: engineer, không skill bước | không skill | có | 769 | 67358 | 13 |
| feature: role thường | thường | có | 780 | 66638 | 13 |
| bugfix: engineer + debug-root-cause | đầy đủ | có (cả hai trang đúng) | 1157 | 108690 | 16 |
| bugfix: engineer, không skill bước | không skill | có | 858 | 84531 | 14 |
| docs: docs-writer (haiku/low) | đầy đủ | có | 1422 | 90592 | 16 |
| docs: role thường (sonnet) | thường | có | 953 | 65907 | 14 |
| change-request: architect (opus/high) + change-request | đầy đủ | có: 2 phương án + 1 khuyến nghị, phát hiện code đã đánh số từ 0 | 1645 | 52991 | 31 |
| change-request: role đọc thường | thường | **baseline không hợp lệ**: prompt là prompt review nên agent đã review thay vì làm | 639 | 32581 | 9 |
| incident contain: devops + incident | đầy đủ | có, thêm bước tái hiện và "vì sao cổng kiểm tra bỏ sót" | 1859 | 92031 | 22 |
| incident contain: devops, không skill | không skill | có | 1605 | 87463 | 19 |
| review lỗi off-by-one được cài: reviewer | đầy đủ | tìm ra lỗi + thiếu test | 669 | 33518 | 11 |
| review lỗi off-by-one được cài: đọc thường | thường | tìm ra lỗi + thiếu test | 658 | 33078 | 9 |
| security được cài shell=True + rò rỉ token: security-reviewer | đầy đủ | tìm ra injection + 2 rò rỉ, đã kiểm chứng bằng cách chạy | 830 | 51467 | 13 |
| security được cài: đọc thường | thường | tìm ra injection + rò rỉ + token gửi tới host bất kỳ | 578 | 32812 | 10 |

Chênh lệch so với baseline (cùng cặp, đã làm tròn):

- **debug-root-cause:** output +35%, cache +29%, không có lợi ích về đúng/sai ở bài này.
- **security-reviewer:** output +44%, cache +57%, baseline role thường tìm được cùng các lỗi.
- **lean-implementation:** output +6%, cache +5%, đều đúng.
- **incident:** output +16%, cache +5%, biến thể đầy đủ có thêm phần tái hiện và phân tích cổng kiểm tra (chất lượng báo cáo tốt hơn, nhưng chưa đo bằng chỉ số).
- **docs-writer:** output +49% so với baseline sonnet, nhưng khác model và effort, nên không thể tách yếu tố skill ra khỏi yếu tố model.
- **reviewer và engineer (không skill bước):** ngang nhau về đúng và gần bằng nhau về token. Quy tắc phạm vi và an toàn của chúng không được bài thử kiểm tra.

## Context mặc định

| Thành phần | Token |
|---|---|
| AGENTS.md | 1297 |
| skills CATALOG | 889 |
| workflows CATALOG | 830 |
| agents CATALOG | 386 |
| **Tổng** | **3402** |

Ngoài ra, mỗi role có 239–632 token và mỗi skill có 528–1107 token (chỉ tính khi được nạp).

## Lỗi omi tìm thấy

Sandbox (một project `omi init` mới) phát hiện ba lỗi:

1. `omi init` không tạo `.omi/skills/CATALOG.md`. Mọi task có workflow đều lỗi cho đến khi chạy `omi skills`.
2. Lệnh test mặc định là `python -m pytest -q`. Với project có script test thường và không dùng pytest, role đọc từ chối bắt đầu. Cần khai báo `"test"` trong config, nhưng mẫu template không ghi điều này.
3. Template không có `.gitignore`. `__pycache__` do chính agent sinh ra khi chạy test bị báo là OUT OF SCOPE (exit 3).

Ghi chú về fixture: các diff review được cài có kèm một file `.pyc` của máy host (lỗi chuẩn bị fixture của Coordinator). Mọi reviewer đều đánh dấu đây là vấn đề nhỏ.

## Đề xuất

Quyết định thuộc về PO.

1. **Rút gọn `omi-skill-debug-root-cause`.** Chi phí cao hơn (+35% output, +29% cache) và không cải thiện kết quả ở bài này.
2. **Rút gọn `omi-agent-security-reviewer`.** Chi phí cao hơn (+44% output, +57% cache) và baseline role thường tìm được cùng lỗi.
3. **Giữ tạm thời:**
   - `lean-implementation` (chi phí thêm nhỏ, không sai);
   - `incident` (có lợi ích nhỏ về nội dung báo cáo);
   - `docs-writer` (dùng haiku, cần kiểm tra lại khi tách yếu tố model);
   - `reviewer` và `engineer` (ngang baseline, nhưng chưa kiểm tra quy tắc phạm vi và an toàn);
   - `architect` (baseline không hợp lệ, cần đo lại).
4. **Tạo task mới cho ba lỗi omi** ở mục trên.

## Giới hạn

- n=1 cho mọi biến thể. Chênh lệch dưới khoảng 10% không đáng tin.
- Bài nhỏ, một repo đồ chơi. Không đại diện cho dự án thật.
- Baseline architect không hợp lệ (prompt baseline là prompt review). Cần chạy lại.
- Một số cặp khác model hoặc effort (docs-writer dùng haiku/low so với sonnet; architect dùng opus/high). Chênh lệch không tách được yếu tố skill khỏi yếu tố model.
- Họ release không được đo: chỉ có bước của Coordinator, không có lần chạy agent.
- Chưa đo số vòng review trong bảng này; chỉ số thời gian và token có đủ.
