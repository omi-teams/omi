# OMI Squad — Ý tưởng và mục tiêu dự án

Ngày tổng hợp: 2026-10-25, múi giờ Asia/Bangkok.

Tài liệu này trình bày độc lập ý tưởng, vấn đề cần giải quyết, mục tiêu, phạm vi và cách vận hành của OMI Squad. Các khả năng mô tả dưới đây là mục tiêu xây dựng; tình trạng triển khai được ghi riêng ở cuối tài liệu.

## 1. Ý tưởng cốt lõi

**OMI Squad là framework giúp một người làm sản phẩm điều hành một đội ngũ AI coding agents ngay trong từng dự án, từ ý tưởng đến phát triển, kiểm thử và phát hành có kiểm soát.**

Người dùng giữ vai trò Product Owner (PO), tập trung vào mục tiêu, nghiệp vụ, thứ tự ưu tiên và nghiệm thu. Một agent chính đóng vai Project Coordinator, làm đầu mối trao đổi với PO và điều phối các agent chuyên môn để thực hiện công việc.

OMI cung cấp quy trình, vai trò, skills, trạng thái, checkpoint và cơ chế thực thi quyền dùng chung. Claude Code hoặc Codex là công cụ thực hiện công việc trong khuôn khổ đó. Dữ liệu cần để tiếp tục dự án được lưu cùng dự án, giúp việc phát triển có thể trải qua nhiều phiên làm việc và chuyển công cụ giữa các phiên.

Trải nghiệm mong muốn bắt đầu từ một thư mục trống: cài OMI cho dự án, khởi tạo framework, trao đổi ý tưởng, duyệt tài liệu, chọn task và để squad thực hiện theo quy trình đã thống nhất.

## 2. Vấn đề cần giải quyết

Khi dùng coding agents cho một dự án dài hạn, người dùng phải tự giữ nhiều đầu việc: giải thích lại bối cảnh, phân chia nhiệm vụ, chọn công cụ, kiểm tra thay đổi, tổ chức review, theo dõi CI và nhớ phần việc đang dở. Những khó khăn này tăng lên khi có nhiều agent hoặc khi phiên làm việc bị gián đoạn.

OMI Squad tập trung giải quyết sáu vấn đề:

- **Bối cảnh bị phân tán:** mục tiêu, quyết định và tiến độ nằm trong nhiều cuộc hội thoại, khó bàn giao hoặc xác minh.
- **Phân công thiếu cấu trúc:** agent nhận việc quá lớn, chồng chéo trách nhiệm hoặc sửa vượt phần được giao.
- **Chất lượng khó kiểm soát:** kết quả do agent tự báo chưa đủ để chứng minh yêu cầu, review và kiểm thử đã đạt.
- **Gián đoạn công việc:** hết quota, đóng phiên, mất mạng hoặc đổi công cụ có thể khiến phải làm lại phần đã hoàn tất.
- **Ngân sách và tài nguyên có hạn:** model, effort, số agent và runner cần phù hợp với nhiệm vụ, quota và máy của PO.
- **Quyền tự động hóa chưa rõ:** cần xác định chính xác việc squad được tự thực hiện và các quyết định vẫn thuộc PO.

## 3. Mục tiêu tổng thể

Xây dựng một nền tảng điều phối để PO có thể phát triển sản phẩm với đội ngũ AI chuyên môn, duy trì tiến độ qua nhiều phiên, kiểm soát quyền và đánh giá kết quả bằng bằng chứng.

| Mục tiêu | Kết quả mong muốn |
| --- | --- |
| Giảm công việc điều phối thủ công | PO trao đổi qua Coordinator; squad tự tổ chức các bước thường lệ trong phạm vi được giao |
| Chuẩn hóa vòng đời phát triển | Ý tưởng, yêu cầu, thiết kế, task, review, kiểm thử và phát hành có đầu vào, đầu ra và điều kiện chuyển bước rõ ràng |
| Giữ tính liên tục | Phiên mới đọc lại trạng thái và checkpoint, xác minh thực tế rồi tiếp tục đúng phần còn dở |
| Bảo đảm phạm vi thực thi | Worker chỉ ghi được vào vùng được cấp, kể cả khi thao tác qua shell |
| Kiểm soát chất lượng | Kết quả gắn với acceptance criteria, commit, review độc lập và CI phù hợp |
| Sử dụng nguồn lực hợp lý | Chỉ khởi chạy vai trò cần thiết, chọn model/effort phù hợp và giới hạn song song theo khả năng thực tế |
| Giữ quyền quyết định của PO | Thay đổi nghiệp vụ lớn, chi phí, UAT và promotion vào staging/main có đúng chủ thể quyết định |
| Dễ cài và bảo trì theo dự án | Cấu hình, phiên bản và dữ liệu của mỗi dự án được quản lý riêng; cập nhật có kế hoạch khôi phục |

## 4. Người dùng và phạm vi phiên bản đầu

Người dùng đầu tiên là chính PO, làm sản phẩm vào thời gian rảnh và cần tiếp tục công việc sau các quãng nghỉ. Thiết kế ưu tiên một người điều hành squad với thời gian, quota và tài nguyên máy hữu hạn.

Phạm vi v1 đã được định hướng như sau:

- Windows là nền tảng ưu tiên; kiểm chứng trải nghiệm CLI trước, extension sau.
- Hỗ trợ Claude Code và Codex, sử dụng subscription trong khả năng được công cụ hỗ trợ; không tự chuyển sang API trả phí.
- Mỗi phiên squad dùng cùng một công cụ. Có thể chuyển từ Claude Code sang Codex hoặc ngược lại ở phiên tiếp theo thông qua dữ liệu bàn giao.
- Bắt đầu với dự án mới từ thư mục trống; cài đặt riêng cho từng dự án.
- Quản lý backlog, sprint, quyết định và checkpoint bằng file; v1 không dùng GitHub Projects làm nguồn trạng thái chính.
- Hướng đến repository public trong GitHub Organization, giới hạn tạo PR cho collaborators theo cấu hình đã chốt.
- Dùng Docker cho môi trường worker và các self-hosted runner trên máy PO; số lượng chạy đồng thời phụ thuộc khả năng thực tế.
- Trao đổi và viết tài liệu bằng tiếng Việt; code, API, tên file, branch và commit bằng tiếng Anh.

## 5. Mô hình tổ chức và quyền quyết định

### Product Owner

PO đưa ra ý tưởng, chốt mục tiêu và nghiệp vụ, duyệt bộ tài liệu trước triển khai, chọn task tiếp theo và quyết định các thay đổi lớn hoặc phát sinh chi phí. PO thực hiện UAT và giữ quyền merge các PR promotion vào `staging` và `main`.

### Project Coordinator

Coordinator là đầu mối duy nhất trao đổi với PO. Vai trò này làm rõ yêu cầu, lập backlog và sprint, phân rã task, giao chuyên môn, chọn model/effort, quản lý checkpoint và tổng hợp kết quả. Các câu hỏi khám phá được đặt lần lượt; khi cần quyết định, Coordinator trình phương án và một khuyến nghị có lý do.

Coordinator điều phối thông qua các dịch vụ được kiểm soát; worker chuyên môn đảm nhiệm phần sửa code sản phẩm. Khi có yêu cầu vượt phạm vi hoặc gặp bế tắc, Coordinator tổ chức giao lại việc hoặc trình PO quyết định.

### Các vai trò chuyên môn

Danh mục gồm 17 vai trò, bao gồm Coordinator và các chuyên môn phục vụ toàn bộ vòng đời sản phẩm:

| Nhóm | Vai trò |
| --- | --- |
| Điều phối và tích hợp | Project Coordinator, Tech Lead |
| Khám phá và thiết kế | Business Analyst, Product Researcher, UX/UI Designer, Solution Architect |
| Xây dựng sản phẩm | Frontend Engineer, Backend Engineer, Data Engineer, Platform/Specialist Engineer |
| Kiểm chứng chất lượng | QA/Test Engineer, Code Reviewer, Security Reviewer |
| Vận hành và duy trì | DevOps/SRE Engineer, Documentation Engineer, Agile Process Reviewer, Workspace Maintainer |

Vai trò được định nghĩa đầy đủ nhưng instance chỉ khởi chạy khi có nhiệm vụ và kết thúc sau khi bàn giao. Reviewer dùng instance khác với người viết. Mức song song phụ thuộc tính độc lập của công việc, quyền truy cập, auth, quota và tài nguyên.

## 6. Hành trình làm việc mong muốn

### Bước 1 — Cài đặt và khởi tạo

PO tạo thư mục trống và cài framework riêng cho dự án. OMI kiểm tra môi trường, trình các dependency còn thiếu và khởi tạo policy, vai trò, workflow, skills đã ghim phiên bản, adapter và trạng thái ban đầu.

Khởi tạo chỉ dựng nền tảng làm việc cho squad. Công nghệ và code ứng dụng được quyết định sau khi làm rõ ý tưởng sản phẩm.

### Bước 2 — Từ ý tưởng đến tài liệu được duyệt

Coordinator hỏi từng câu để làm rõ người dùng, vấn đề, nghiệp vụ, phạm vi, ràng buộc, công nghệ, chi phí và tiêu chí thành công. Các chuyên môn liên quan tạo tài liệu cần thiết và được review bằng instance độc lập.

PO duyệt bộ tài liệu cuối trước khi bắt đầu triển khai sản phẩm. Bản được duyệt có tham chiếu phiên bản hoặc digest để nhận diện thay đổi về sau.

### Bước 3 — Lập kế hoạch và chọn task

Squad chia công việc thành task nhỏ, mỗi task có một đầu ra rõ ràng, phụ thuộc, phạm vi và acceptance criteria. Sprint được tổ chức theo mục tiêu và điều kiện kết thúc, phù hợp nhịp làm việc của PO.

Trạng thái dự án trình bày việc đã làm, việc đang dở, điểm chặn và task được đề xuất, kèm thông tin ngân sách khi có cơ sở. PO chọn task; squad thực hiện task đó và báo lại trước khi chuyển sang task tiếp theo.

### Bước 4 — Thực hiện và tích hợp

Task sẵn sàng được cấp brief, role, skills, model/effort, branch, worktree và quyền đọc/ghi cụ thể. Worker thực hiện, kiểm thử và lưu checkpoint theo các mốc có ý nghĩa.

Thay đổi đi qua commit, push, PR, code review, security review và CI. Tech Lead được merge task vào `development` qua cổng kiểm tra khi đủ điều kiện. Task triển khai chỉ hoàn tất sau kiểm tra sau merge và cập nhật bằng chứng, trạng thái cùng việc dọn hoặc bàn giao tài nguyên.

### Bước 5 — UAT và phát hành

Luồng nhánh thống nhất là:

```text
development → task branch → PR → development
                                    ↓
                           PO merge promotion
                                    ↓
                                 staging
                                    ↓
                                 PO UAT
                                    ↓
                           PO merge promotion
                                    ↓
                                  main
                                    ↓
                     Deploy và xác minh production
```

V1 xét một candidate UAT tại một thời điểm. Bản PO kiểm thử phải truy vết được tới code, artifact và cấu hình liên quan; staging giữ ổn định trong thời gian UAT. Thay đổi làm ảnh hưởng hành vi tạo candidate mới và kiểm tra lại phần bị tác động.

Squad chuẩn bị PR promotion, hướng dẫn test, release notes và phương án rollback. Chỉ PO merge vào staging/main. Deploy cần đúng môi trường, quyền và chi phí đã được chấp thuận, sau đó có kiểm tra kết quả thực tế.

## 7. Những năng lực làm nền tảng

### Trạng thái và checkpoint thuộc về dự án

OMI lưu mục tiêu, backlog, quyết định, bằng chứng và checkpoint thành dữ liệu có cấu trúc. Checkpoint ghi việc đã làm, thay đổi chưa hoàn tất, kết quả kiểm tra, lỗi còn lại và bước tiếp theo, đủ để phiên khác tiếp tục.

Trước khi resume, hệ thống đối chiếu checkpoint với Git, PR, CI và runtime. Việc tiếp nhận lại quyền sở hữu phải bảo đảm chỉ một worker có quyền ghi cùng nhiệm vụ. Pause, cancel và dừng khẩn cấp giữ lại dữ liệu cần phục hồi và ghi rõ trạng thái còn chưa xác định.

### Quyền được thực thi bằng runtime

Worker được quản lý trong Docker, có giới hạn mount, công cụ và tài nguyên theo task. Worktree tách thay đổi Git; runtime chịu trách nhiệm chặn ghi ngoài vùng được cấp. Quyền đặc biệt, secrets, Docker và thao tác GitHub đi qua thành phần tin cậy với policy tương ứng.

Khi cần thay đổi ngoài scope, worker báo Coordinator để giao lại việc. Bảo đảm này thuộc đường thực thi do OMI quản lý; một agent chạy tự do trên host có khả năng khác và phải được báo rõ.

### Chất lượng gắn với bằng chứng

Acceptance criteria, kết quả kiểm tra, findings và review gắn với đúng đầu vào đang xét. Thay đổi code hoặc cấu hình có thể làm kết quả cũ mất hiệu lực và yêu cầu kiểm tra lại.

OMI phân biệt ba vòng đời: **task hoàn tất**, **feature được PO chấp nhận** và **release đã deploy, xác minh**. Mỗi cấp có điều kiện riêng để tránh báo tiến độ vượt quá kết quả thực tế.

### Quota và tài nguyên được quản lý minh bạch

Coordinator chọn cấu hình đủ năng lực cho từng nhiệm vụ, tính cả chi phí review và sửa sai. Skills được nạp theo nhu cầu; agent và runner chỉ chạy khi cần, với giới hạn tài nguyên máy.

Quota hiển thị nguồn và thời điểm đo khi có dữ liệu. Dự báo cần mẫu thực tế và độ tin cậy; dữ liệu thiếu hoặc cũ được báo rõ. Khi quota thấp, hệ thống đề xuất task nhỏ hoặc tạm dừng, đồng thời dành khả năng lưu checkpoint và bàn giao.

### Cài đặt và cập nhật có thể khôi phục

Installer hướng đến khả năng xem trước thay đổi, chạy lại an toàn, giữ tùy biến và sao lưu trước migration. Core, adapter, schema và skills có phiên bản tương thích rõ ràng. Cập nhật skills cần PO đồng ý và không đổi phiên bản giữa task đang chạy.

Cleanup chỉ tác động tài nguyên thuộc OMI đã xác minh quyền sở hữu. Gỡ framework giữ lại code, tài liệu và backlog. Dữ liệu nhạy cảm, auth và secrets được giữ ngoài Git public; dữ liệu local cần cơ chế sao lưu phù hợp.

## 8. Các thành phần của hệ sinh thái

| Thành phần | Mục đích |
| --- | --- |
| `omi-squad` | Core điều phối, CLI/installer, state, policy, runtime, adapter, GitHub/CI và template |
| `omi-skills` | Repository riêng cho skills có phiên bản, metadata, đánh giá chất lượng và nguồn/license rõ ràng; có thể dùng độc lập |
| Dự án sử dụng OMI | Cấu hình riêng, tài liệu sản phẩm, backlog, checkpoint, quyết định và phiên bản framework/skills đã ghim |

Baseline kỹ thuật chọn Python cho core và CLI `omi`, state dựa trên file với snapshot nguyên tử, runtime/broker tin cậy trên host và worker được quản lý trong container. Công nghệ của ứng dụng do dự án sử dụng OMI quyết định riêng.

Ba thao tác trung tâm là `omi-init`, `omi-idea` và `omi-status`. CLI tương ứng là `omi init`, `omi idea`, `omi status`; adapter dùng `/omi-*` trên Claude và `$omi-*` trên Codex. Đây là giao diện mục tiêu, cần triển khai và kiểm chứng theo phiên bản công cụ.

## 9. Tiêu chí thành công

OMI v1 cần chứng minh được một vòng đời thực tế từ cài đặt đến hoàn tất task và tiếp nối phiên làm việc:

1. Cài riêng trên Windows từ thư mục trống, khởi tạo đúng framework và báo chính xác khả năng môi trường.
2. Từ ý tưởng tạo được tài liệu đã review, ghi nhận PO duyệt trước triển khai.
3. Task nhỏ do PO chọn chạy qua branch/worktree, kiểm thử, PR, review, CI, merge development và kiểm tra sau merge.
4. Chặn được ghi ngoài scope trong đường thực thi hỗ trợ, bao gồm thao tác qua shell.
5. Resume được sau gián đoạn và chuyển công cụ giữa phiên, giữ phần việc đã xác minh và xử lý quyền sở hữu an toàn.
6. Thực thi quyền PO với promotion staging/main; UAT và release truy vết đúng candidate, cấu hình và môi trường.
7. Báo rõ chất lượng số đo quota, giới hạn dự báo và khả năng CLI/extension đã kiểm chứng.
8. Cài lại, cập nhật, gỡ và dọn tài nguyên giữ được dữ liệu cần thiết, có bằng chứng khôi phục phù hợp.

Pilot trên dự án thật sẽ cung cấp dữ liệu về mức PO phải can thiệp, khả năng resume, chi phí quota và các lỗi quy trình. Các số đo này dùng để hiệu chỉnh thiết kế; tài liệu hiện tại chưa đặt chỉ tiêu định lượng khi chưa có đủ mẫu thực tế.

## 10. Lộ trình và tình trạng hiện tại

Lộ trình đi từ xác nhận hướng sản phẩm, kiểm chứng rủi ro và review đặc tả tới xây dựng state/runtime, adapter/skills, installer, workflow, Git/CI/release, rồi pilot và nghiệm thu đầu cuối. Mỗi task có đầu ra và cổng kiểm chứng; hoàn tất một bước không tự cho phép triển khai toàn bộ backlog.

Tình trạng dự án tại ngày tổng hợp:

- Vision đã chốt; bộ đặc tả baseline 1.0 và backlog 40 task đã được lập.
- TASK-0001 đã hoàn tất review baseline trong phạm vi đặc tả.
- TASK-0002 đã hoàn tất bootstrap Python package/CLI alpha `0.1.0a1`, có help/version, review, CI, merge development và kiểm tra sau merge.
- TASK-0003 về loader/validator contracts và canonical hash là đề xuất tiếp theo, đang ở trạng thái planned trong backlog.
- Runtime và installer sản phẩm chưa được triển khai. Lab, prototype và các phép thử khả thi cung cấp bằng chứng cho từng điểm kỹ thuật; chúng chưa xác nhận OMI v1 đã hoạt động trọn vẹn.

Các cổng còn cần chứng minh gồm auth dài hạn, điều phối/runtime tích hợp, forecast quota, extension parity, installer/update đầy đủ, release/deploy theo stack thực và nghiệm thu end-to-end. Phạm vi sau v1 gồm tiếp nhận repository có sẵn, mở rộng công cụ, macOS/Linux và tích hợp hệ thống quản lý công việc khác. Lệnh `doctor` kiểm tra môi trường trong baseline hiện tại được phân biệt với khả năng tiếp nhận dự án cũ ở giai đoạn sau.

