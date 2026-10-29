# Pilot chế độ độc lập (TASK-101): omi-pilot-splitbill

2026-10-29. Coordinator chạy trên Windows host, omi 0.3.2, bản development
`181b31c`, cài bằng `pip install -e .`.
Repo code: [omi-teams/omi-pilot-splitbill](https://github.com/omi-teams/omi-pilot-splitbill).
Repo state private: [omi-teams/omi-state](https://github.com/omi-teams/omi-state).

Bằng chứng dưới đây được chép từ checkpoint TASK-101 của Coordinator; đây là
các lệnh và trích đoạn kết quả đã ghi nhận, không phải transcript đầy đủ hay một
lần chạy lại của docs-writer. Với thao tác chưa có nguyên lệnh hoặc stdout trong
checkpoint, báo cáo chỉ ghi kết quả được cung cấp.

## Kết quả

| Tiêu chí | Kết quả | Bằng chứng |
|---|---|---|
| Clone mới, `omi install-user`, `omi attach`, một task thật từ đầu đến merge; task chỉ thêm commit code, không thêm file omi | Đạt trong lần pilot; repo đã có file omi từ trước, xem G4 | E1–E7 |
| Clone state sang thư mục thứ hai, đổi `OMI_STATE`, `omi status` giống nhau | Đạt trên cùng Windows host, giả lập máy khác | E8 |
| Ghi lệnh, kết quả và mọi gap bằng tiếng Việt | Đã ghi trong tài liệu này | E1–E9, G1–G8 |
| Chế độ in-repo qua toàn bộ test trên Linux worker và Windows host | Đạt: Windows host và Linux worker | E9 |

## Cài đặt và attach (E1–E5)

| Mốc | Lệnh đã chạy | Kết quả được ghi nhận |
|---|---|---|
| E1 | `omi --version` | `omi 0.3.2` |
| E1 | `omi install-user` | `installed omi user integration`, exit 0 |
| E2 | `gh repo create omi-teams/omi-state --private` | `https://github.com/omi-teams/omi-state` |
| E3 | `git clone https://github.com/omi-teams/omi-pilot-splitbill.git` | Clone mới trong `E:/Github/Orgs/omi-teams/pilot/`; checkpoint không lưu stdout |
| E4 | `omi attach --state https://github.com/omi-teams/omi-state.git` | Tạo `docker/`, `.omi/` (agents, skills, rules, workflows, catalogs) trong `~/.omi/state/projects/omi-pilot-splitbill`; `tools: git ok, gh ok, docker ok, claude ok, codex ok`; `attached: ...`; exit 0 |
| E4 | `git status` trong repo code | `nothing to commit, working tree clean` |
| E5 | `omi status` | `state pull skipped: offline or remote unavailable (check remote/upstream)`; checkpoint tóm tắt phần task là `no tasks yet` |
| E5 | `omi sync` | `state synced`; trạng thái repo state sau đó: `## main...origin/main` |

Manifest `~/.omi/state/projects/omi-pilot-splitbill/project.json` sau attach:

```json
{"remote": "https://github.com/omi-teams/omi-pilot-splitbill.git"}
```

E4 ghi nhận repo state có một commit `omi: attach omi-pilot-splitbill`, chưa push,
và trạng thái `## main...origin/main [gone]`. Sau E5, state đã được đồng bộ.
Các chuỗi trạng thái branch trên là bằng chứng trong checkpoint; checkpoint
không lưu nguyên lệnh kiểm tra repo state.

## Task thật từ đầu đến merge (E6–E7)

TASK-003, `Add --tip percentage`, được tạo trong state bằng cách chép từ plan
in-repo của splitbill, dùng workflow `omi-flow-feature`. Engineer dùng codex
`gpt-6.1-sol`/medium; reviewer dùng `claude-sonnet-5-5`/medium.

| Thao tác hoặc lệnh đã ghi nhận | Kết quả |
|---|---|
| `omi step` qua plan/build/review/accept (checkpoint không lưu từng nguyên lệnh) | Mỗi bước commit và push state với message `chore(omi-pilot-splitbill): step state`; các bước này không sửa repo code |
| Chạy engineer (checkpoint không lưu nguyên lệnh) | `DONE`, 10 tests passed, `hook post-run passed`; 50 giây; 88.818 input / 1.571 output tokens |
| Chạy reviewer (checkpoint không lưu nguyên lệnh) | `VERDICT PASS`, 21 giây; ghi chú không chặn merge về `--tip 1e9999999` (G8) |
| `omi step accept done` (dạng ghi tắt trong checkpoint) | Bị từ chối cho đến khi chuyển dòng `PO approval accept: ...` vào ngay dưới `## Steps` |
| `omi hook pre-merge` (checkpoint không ghi TASK-ID trong lệnh) | `no pre-merge hook` |
| [PR #5](https://github.com/omi-teams/omi-pilot-splitbill/pull/5) | CI của splitbill trên ubuntu/macos/windows đều pass; squash-merged |

Các dạng ghi tắt ở trên không phải cú pháp để sao chép chạy lại. CLI yêu cầu
`omi step <TASK-ID> next|done|back|skip --why <reason>` và
`omi hook pre-run|post-run|pre-merge <TASK-ID>`. PO gate đọc dòng approval có nội
dung trong mục `## Steps`, trước heading cấp hai tiếp theo; không bắt buộc dòng
đó phải nằm ngay sau heading.

Sau merge, các lệnh kiểm tra repo code được ghi nhận như sau:

```text
git log --oneline -3
f79b518 feat: add tip percentage before splitting bills (#5)
4afcd6f feat: equal split ... (TASK-002) (#2)
2dcd07e chore: start TASK-002

git show --stat HEAD
src/split_bill/cli.py | 13
tests/test_cli.py | 37

git diff --name-only 4afcd6f HEAD
src/split_bill/cli.py
tests/test_cli.py

git status
nothing to commit, working tree clean
```

Đây là trích đoạn; dấu `...` trong commit cũ là phần rút gọn của checkpoint.
Task chỉ thêm commit `f79b518`, thay đổi hai file code/test, không thêm file hay
commit omi. Repo vẫn chứa các file và commit omi có sẵn từ trước pilot (G4).

## Clone state thứ hai (E8)

Lệnh clone đã chạy:

```text
git clone https://github.com/omi-teams/omi-state.git E:/Github/Orgs/omi-teams/pilot/state2
```

Coordinator chạy `omi status` với state mặc định, rồi với biến môi trường
`OMI_STATE=E:/Github/Orgs/omi-teams/pilot/state2`. Checkpoint không lưu cú pháp
đặt biến trên shell Windows hay nguyên lệnh `diff`; kết quả so sánh được ghi là
giống nhau. Các dòng status được lưu cho cả hai lần:

```text
branch: development
omi 0.3.2 (project 0.3.2)
done: 1/1
next: none ready
```

Đây là hai clone trên cùng host, chưa phải bằng chứng chạy trên máy vật lý khác.

## Test chế độ in-repo (E9)

| Môi trường | Lệnh | Kết quả |
|---|---|---|
| Windows host, worktree omi của task này | `python tests/test_omi.py` | `ok`, exit 0, theo Coordinator |
| Linux worker (Docker, hook post-run của lần chạy docs-writer) | `python3 tests/test_omi.py` | `ok`, `hook post-run passed` (ghi trong `## Reports` của TASK-101) |
| CI của PR omi này | `python tests/test_omi.py` | Chờ kết quả; `.github/workflows/ci.yml` cấu hình `ubuntu-latest`, Python 3.13, cài package bằng `pip install .` trước khi test |

CI ba hệ điều hành của PR splitbill #5 kiểm tra sản phẩm splitbill, không thay cho test của omi.

## Gap cần quyết định ở plan sau

| Gap | Hiện tượng trong pilot | Điểm còn mở |
|---|---|---|
| G1 | Sau `pip install -e .`, `omi.exe` nằm trong thư mục Python `Scripts` chưa có trên PATH; phải gọi bằng đường dẫn đầy đủ | Cách hướng dẫn hoặc kiểm tra PATH khi cài |
| G2 | `omi attach` commit state nhưng không push; `omi status` đầu tiên với remote mới rỗng báo `state pull skipped` cho đến khi chạy `omi sync` | Hành vi đồng bộ và thông báo sau attach |
| G3 | Clone mới checkout `main`; phải chạy tay `git checkout -b development origin/development` trước khi tạo worktree task | Chuẩn bị branch cho repo vừa attach |
| G4 | Splitbill đã có `.omi/`, `AGENTS.md`, `.claude/`; sau attach, state in-repo bị bỏ qua mà không cảnh báo, task cũ không được import. TASK-003 được chép tay và bỏ `depends: TASK-002` | Cảnh báo khi hai nguồn state cùng tồn tại; `omi detach`/migration ngoài phạm vi v1 |
| G5 | Chưa có lệnh ghi approval của PO; dòng thêm cuối file sau `## Usage` bị PO gate từ chối, chuyển vào `## Steps` thì được chấp nhận | Cách ghi approval đúng mục, có thể kiểm tra được |
| G6 | Squash title là `feat: add tip percentage before splitting bills (#5)`, thiếu task ID như commit in-repo có `(TASK-002)` | Quy ước liên kết commit code với task trong state |
| G7 | Config mặc định của project attach có `"test": ""` khiến status cảnh báo; `network_allow` chỉ có `api.anthropic.com`, nhưng engineer codex vẫn chạy được | Cấu hình test của project và lý do đường chạy codex thành công; chưa xác minh nguyên nhân mạng |
| G8 | Reviewer ghi nhận `--tip 1e9999999` gây traceback `ValueError` thay vì exit 2; không chặn merge | Follow-up của splitbill: giới hạn số mũ `--tip` quá lớn |

Các gap trên được ghi lại để quyết định sau; task tài liệu này không sửa hành vi.
