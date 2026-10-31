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

## Chuyển repo omi sang chế độ độc lập (TASK-135)

2026-10-31. Repo omi tự dùng chế độ độc lập: plan, task và decision của omi nằm ở
`projects/omi/` trong [omi-teams/omi-state](https://github.com/omi-teams/omi-state), nên
hiện trên board như mọi dự án khác. Phương án đã chọn (architect, option A): gỡ
`.omi/**`, `AGENTS.md`, `.claude/**`, `docker/**` khỏi repo code; bản sao
`src/omi/template/**` giữ nguyên; phát triển omi qua `omi install-user`.

Đầu ra dưới đây là stdout thật do Coordinator chạy trên Windows host ngày 2026-10-31.

### Lệnh và kết quả (T1, trên host)

```
$ python -m omi install-user
installed omi user integration
$ grep -n "omi guard" ~/.claude/settings.json
89:            "command": "C:\\Users\\Admin\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe -m omi guard"
```

`omi status` trước khi attach (6 dòng đầu):

```
$ python -m omi status
branch: development
omi 0.5.0 (project 0.5.0)
no `test` command in .omi/config.json; set one, e.g. "test": "python3 -m pytest -q"
PLAN-007 omi 0.6.0 - professional omi board: done 3/16
done plans: PLAN-002, PLAN-003, PLAN-004, PLAN-005, PLAN-006
done: 124/142
```

```
$ python -m omi attach        (4 dòng cuối)
wrote C:\Users\Admin\.omi\state\projects\omi\.omi\plans\CATALOG.md (1 plans)
tools: git ok, gh ok, docker ok, claude ok, codex ok
attached: C:\Users\Admin\.omi\state\projects\omi
WARN: in-repo omi files ignored (detached): .omi/, AGENTS.md, .claude/
```

Chép `.omi/{agents,config.json,decisions.md,hooks,plans,references,rules,skills,tasks,version,workflows}` và `docker/` đè lên seed, rồi sinh lại catalog:

```
wrote C:\Users\Admin\.omi\state\projects\omi\.omi\skills\CATALOG.md (19 skills)
wrote C:\Users\Admin\.omi\state\projects\omi\.omi\agents\CATALOG.md (9 roles)
wrote C:\Users\Admin\.omi\state\projects\omi\.omi\workflows\CATALOG.md (11 workflows)
wrote C:\Users\Admin\.omi\state\projects\omi\.omi\rules\CATALOG.md (6 rules)
wrote C:\Users\Admin\.omi\state\projects\omi\.omi\references\CATALOG.md (2 references)
wrote C:\Users\Admin\.omi\state\projects\omi\.omi\plans\CATALOG.md (8 plans)
$ git -C ~/.omi/state log --oneline -2
2eb37d5 omi: import state from omi-teams/omi@17712ff; history: git log -- .omi AGENTS.md .claude
01db044 omi: attach omi
$ git -C ~/.omi/state show --stat --oneline 2eb37d5 | tail -1
 159 files changed, 16224 insertions(+), 20 deletions(-)
```

So sánh `omi status` trước và sau (chỉ thêm dòng WARN, vì file in-repo vẫn còn cho tới khi PR gỡ merge):

```
$ diff status_before.txt status_after.txt
0a1
> WARN: in-repo omi files ignored (detached): .omi/, AGENTS.md, .claude/
```

Clone mới omi-state vào thư mục tạm và đọc dữ liệu board:

```
$ git clone https://github.com/omi-teams/omi-state.git <tmp>
$ OMI_STATE=<tmp> python -c "from omi.board import data; ..."
['omi', 'omi-pilot-splitbill']
[('PLAN-007', 'active', 3, 16)]
8 plans; {'planned': 17, 'in-progress': 1, 'review': 0, 'blocked': 0, 'done': 124}
$ curl -s http://127.0.0.1:8765/api/projects   (tên dự án)
['omi', 'omi-pilot-splitbill']
```

Lịch sử trước khi import xem bằng `git log -- .omi AGENTS.md .claude` trong repo code
(ghi trong commit message của omi-state).

### PR gỡ file in-repo (T2)

Một PR duy nhất gỡ `.omi/**`, `AGENTS.md`, `.claude/**`, `docker/**` khỏi repo code.
Test đổi theo: `tests/test_cli.py:16`, `tests/test_content.py:137,252` chỉ đọc TEMPLATE;
`tests/test_board.py:297` bỏ kiểm tra text `omi-modules.md`. Trước khi merge, kiểm tra trên worktree đã gỡ file (không in dòng WARN):

```
$ python -c "from pathlib import Path; from omi.setup import attach; attach.warn_in_repo_files(Path('../omi.wt/TASK-135'))"
$
```

### Sau khi merge

```
$ git log --oneline -1
(Coordinator điền sau khi merge)
$ python -m omi status
(Coordinator điền sau khi merge)
```

### Rollback

1. Trong repo code, khôi phục file từ commit ngay trước PR gỡ:
   `git checkout <sha-trước-khi-gỡ> -- .omi AGENTS.md .claude docker`
2. Trong omi-state, gỡ thư mục dự án và push:
   `git rm -r projects/omi`, commit, `git push`.
3. Chạy `omi status`: không còn project `omi` trong state; repo code dùng lại state in-repo.

Đóng băng: từ lúc chép sang omi-state đến khi PR gỡ merge, không sửa `.omi` trong repo code
(mọi sửa sau lúc chép sẽ không có trong state).
