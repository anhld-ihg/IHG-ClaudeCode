# ihg_core — IHG AI OS Core

Module lõi cho hệ thống IHG AI OS. Phân biệt rõ:

- **Worker (Python)**: chương trình có logic xác định (vd: `worker_checksum.py`).
- **AI Agent**: tiến trình AI thật, gọi qua `AgentRuntime` (Claude CLI / HTTP API / ...).
- **Coordinator**: Worker điều phối, gọi AI Agent + Worker theo capability.
- **StateStore**: state machine (PENDING → ... → DELIVERED), phát hiện DRIFT.
- **AuthZ**: phân quyền ở tầng code, default-deny.
- **QA**: 4 check kỹ thuật + AI QA qua `ihg-qa` (ghi rõ lý do khi runtime không khả dụng).

## Cài đặt

Không cần cài thêm — chỉ dùng thư viện chuẩn Python (3.8+).

## Cấu hình

Qua env vars:

```bash
export IHG_ROOT=/path/to/ihg
export IHG_STATE_DIR=$IHG_ROOT/state
export IHG_OUTPUT_DIR=$IHG_ROOT/output
export IHG_PRINCIPAL=gd-ihg
export IHG_AGENT_RUNTIME_BIN=claude   # hoặc python, hoặc mock
```

## Chạy thử

### Cách 1: Batch file (Windows, khuyến nghị)
```cmd
cd D:\IHG-ClaudeCode\.claude\worktrees\blissful-pascal-805ac0\AI-Office\02-DU-AN\2026\IT\TEST-COORD-002
run-tests.bat
```
Kết quả: `state\test-results-*.log` + `state\test-summary-*.json`

### Cách 2: Shell script (Linux/VPS)
```bash
cd /path/to/TEST-COORD-002
chmod +x run-tests.sh
./run-tests.sh
```

### Cách 3: Chạy trực tiếp từng lệnh
```bash
# Smoke test nhanh (5 giay)
python tests/smoke.py

# Self-test AuthZ
python src/ihg_core/authz.py

# Xem runtime mặc định
python src/ihg_core/agent_runtime.py

# Dispatch 1 task
python -m ihg_core.coordinator TEST-001 file-write "Viết 5 dòng"

# QA
python -m ihg_core.qa_check TEST-001

# Tất cả 25 test
python tests/runtests.py
```

## State machine

```
PENDING → DISPATCHED → RUNNING → SUCCEEDED → QA_PENDING → QA_PASS → DELIVERED
   │          │           │            │
   │          │           │            └─→ DRIFT
   │          │           └─→ FAILED
   │          └─→ FAILED
   └─→ BLOCKED

FAILED → RETRY → DISPATCHED
REUSED (artifact cũ còn tốt) → QA_PENDING
```

## Phân quyền

Xem `src/ihg_core/authz.py`. Mặc định DENY. Mỗi principal có policy riêng.

## Giới hạn hiện tại

- AI Agent runtime phụ thuộc `claude` CLI trong PATH. Khi CLI chưa login, runtime trả về lý do rõ (`cli_requires_login`).
- Khi không gọi được AI Agent thật, kết quả là `QA_UNVERIFIED` (không phải `PASS`).
- Không có HTTP API runtime — sẽ thêm khi deploy VPS.
