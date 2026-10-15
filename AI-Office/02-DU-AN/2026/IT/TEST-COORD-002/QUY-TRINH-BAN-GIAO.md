# Quy trình bàn giao & khôi phục — IHG AI OS

## 1. Bàn giao giữa các Agent

Khi 1 Agent xong việc, phải bàn giao cho Agent kế tiếp theo 4 thứ:

1. **Task ID** + state hiện tại
2. **Artifact path** + SHA-256
3. **Reason / next action** (lý do + bước kế)
4. **Output** (text hoặc file)

Quy ước message:
```
[IHG-HANDOFF]
task_id: TASK-XXX
state: SUCCEEDED | QA_PENDING | FAILED | ...
artifact: /path/to/file.md
sha256: abcdef...
reason: "QA can kiem tra X"
next: "qa agent review"
output_head: "first 200 chars of artifact"
[/IHG-HANDOFF]
```

## 2. Khôi phục khi crash

Nếu Coordinator crash giữa chừng:
1. Đọc `state/tasks.json` — tất cả task đã tạo đều có sẵn.
2. Với mỗi task, xem state:
   - `PENDING` → chưa dispatch → gọi `dispatch_task` lại
   - `DISPATCHED` / `RUNNING` → đang chạy → gọi `dispatch_task` lại (idempotent sẽ REUSED hoặc chạy lại)
   - `SUCCEEDED` / `QA_PENDING` → đã chạy xong, chỉ cần gọi `run_qa(task_id)`
   - `FAILED` → xem `last_error` để biết lý do → sửa hoặc `RETRY` thủ công
   - `DRIFT` → artifact đã bị sửa/mất → chạy lại từ `RUNNING`

3. Mọi lần chạy đều qua `verify_artifact_integrity()` để phát hiện artifact cũ còn tốt → REUSED.

## 3. Backup state

State ở 2 nơi:
- `state/tasks.json` — JSON đầy đủ, mỗi lần transition đều ghi đè (atomic write)
- `state/store.log` — append-only audit log

Backup hàng ngày:
```bash
cp state/tasks.json state/backup/tasks-$(date +%Y%m%d).json
```

## 4. Khôi phục từ backup

```bash
# Xem lich su
ls state/backup/

# Khoi phuc
cp state/backup/tasks-20261013.json state/tasks.json
# Tiep tuc dispatch nhu binh thuong
```

## 5. Test bàn giao

Xem test `test_coordinator_idempotent_reused` trong `tests/runtests.py`:
- Chạy 1 task lần 1 → state = SUCCEEDED → artifact ghi
- Chạy lại cùng task → phát hiện artifact còn → REUSED, không gọi Agent lần 2
- Đây là dạng "bàn giao qua state" — Coordinator kế tiếp đọc state và tiếp tục.

## 6. Phân tách trách nhiệm

| Actor | Trách nhiệm | KHÔNG được |
|-------|-------------|-----------|
| Worker (Python) | Ghi artifact, tính SHA, thao tác file | Đánh giá chất lượng |
| AI Agent (Claude CLI) | Sinh nội dung artifact | Tự đánh giá output của mình |
| QA Agent (ihg-qa) | Review artifact (cùng quy trình) | Review artifact do chính nó sinh |
| Coordinator | Điều phối, AuthZ, state | Sinh nội dung |
| GD | Phê duyệt, mở khóa | Chạy lệnh kỹ thuật |
