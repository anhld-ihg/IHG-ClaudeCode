# TEST-COORD-002 — SPEC

## 1. Mục tiêu

Khắc phục các thiếu sót GĐ chỉ ra ở CHẶNG 2:
1. Phân biệt rõ Worker (Python có logic xác định) vs AI Agent (tiến trình AI thật).
2. Phân quyền thật ở tầng code (default-deny), có test tự động.
3. Sửa state machine: FAILED không tự thành DONE; phát hiện DRIFT (artifact mất/thay đổi).
4. Cấu hình qua env vars, không hard-code path worktree.
5. Gọi AI Agent thật qua interface (ClaudeCliRuntime), có lý do rõ khi không gọi được.
6. QA chạy qua AI Agent ihg-qa thật, có lý do rõ khi runtime không khả dụng.

## 2. Kiến trúc

```
┌─────────────────────────────────────────────────────┐
│ Coordinator (Worker)                                │
│   - dispatch_task(task_id, capability, prompt)      │
│   - AuthZ.check() trước mỗi thao tác               │
│   - State machine (PENDING -> ... -> DELIVERED)     │
└─────┬────────────────────────────┬──────────────────┘
      │ (Worker)                   │ (AI Agent)
      ▼                            ▼
┌──────────────────┐      ┌──────────────────┐
│ Worker (Python)  │      │ Agent Runtime    │
│ - checksum       │      │ - ClaudeCli      │
│ - ...            │      │ - Mock (test)    │
└──────────────────┘      └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │ AI Agent (thật)  │
                          │ - ihg-it         │
                          │ - ihg-qa         │
                          │ - ihg-admin-legal│
                          └──────────────────┘

┌──────────────────────────────────────────────────────┐
│ StateStore (độc lập với Coordinator)                 │
│   - state/tasks.json + state/store.log               │
│   - transition() enforce VALID_TRANSITIONS            │
│   - verify_artifact_integrity() detect DRIFT          │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ AuthZ (mặc định DENY)                                │
│   - principal × action × resource pattern            │
│   - raise PermissionError nếu không có quyền         │
│   - không dựa vào prompt làm lớp bảo vệ duy nhất    │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ QA Check                                             │
│   - 4 check kỹ thuật (Q1-Q4) — luôn chạy            │
│   - AI QA qua Agent ihg-qa — chạy khi runtime OK    │
│   - QA_UNVERIFIED khi runtime không khả dụng         │
└──────────────────────────────────────────────────────┘
```

## 3. Phân biệt Worker vs AI Agent

| Tiêu chí | Worker (Python) | AI Agent |
|----------|----------------|----------|
| Logic | Xác định, code Python | Mô hình AI + tools |
| Runtime | Module Python | Claude CLI / API / ... |
| Khi không gọi được | Không có khái niệm | RuntimeResult.reason ghi rõ |
| Registry tag | `kind=worker` | `kind=agent` |
| Gọi trong coordinator | `importlib.import_module` | `runtime.invoke()` |
| Bằng chứng chạy thật | Kết quả xác định (SHA) | Lời gọi runtime + stdout |

## 4. Agent Runtime Interface

```python
class AgentRuntime:
    name: str
    def invoke(self, agent: AgentManifest, prompt: str, **kwargs) -> RuntimeResult: ...
    def available(self) -> bool: ...
```

Hiện có:
- `ClaudeCliRuntime` — gọi `claude -p --bare --add-dir <root> <prompt>`. Lỗi ghi rõ: `cli_requires_login`, `cli_unavailable`, `cli_error`, `timeout`, `binary_not_found`.
- `MockRuntime` — chỉ để test interface. KHÔNG tính là AI Agent thật.

Khi deploy VPS: thêm `HttpApiRuntime` (gọi API Anthropic trực tiếp) mà không cần sửa coordinator.

## 5. State Machine

```
PENDING → DISPATCHED → RUNNING → SUCCEEDED → QA_PENDING → QA_PASS → DELIVERED
   │          │           │            │
   │          │           │            └─→ DRIFT (artifact mất/đổi)
   │          │           └─→ FAILED
   │          └─→ FAILED
   └─→ BLOCKED (no agent / no permission)

FAILED → RETRY → DISPATCHED
DRIFT → RUNNING (chạy lại) | FAILED
QA_FAIL → FAILED
REUSED (artifact cũ còn tốt) → QA_PENDING
```

**Quy tắc cứng**:
- Không có transition nào từ FAILED trực tiếp sang DONE/DELIVERED.
- Mỗi `transition()` raise `StateMachineError` nếu không hợp lệ.
- `verify_artifact_integrity()` SHA-256 file còn sống so với `expected_sha256` → DRIFT nếu khác/mất.

## 6. Phân quyền

Nguyên tắc:
- **Default DENY**: principal không có trong policy = từ chối.
- **Pattern-based**: `principal × action × [regex]` — khớp 1 trong n list = OK.
- **Path resolution**: chuyển path tuyệt đối về relative với `IHG_ROOT` để match pattern. Path ngoài IHG_ROOT = từ chối.
- **Có test tự động**: 12 case trong `authz._self_tests()`.

Các principal:
- `gd-ihg` — GĐ: mọi quyền.
- `dept-it` — Trưởng phòng IT: đọc AI-Office, ghi IT project, dispatch + run `ihg-(it|qa|admin-legal)`.
- `agent-it`, `agent-qa`, `agent-admin-legal` — các AI Agent: giới hạn theo `allowed_paths`.
- `nhan-vien` — Chatbot nhân viên: chỉ đọc `01-PHONG-BAN/*/public/` và `03-TRI-THUC/EMPLOYEE/`. **KHÔNG** bao giờ vào PRIVATE_CORE.

## 7. Cấu hình

Qua env vars (xem `src/ihg_core/config.py`):

| Env var | Mặc định | Mô tả |
|---------|----------|-------|
| `IHG_ROOT` | heuristic | Thư mục gốc |
| `IHG_STATE_DIR` | `<root>/state` | Nơi lưu tasks.json + log |
| `IHG_OUTPUT_DIR` | `<root>/output` | Nơi ghi artifact |
| `IHG_KNOWLEDGE_DIR` | `<root>/knowledge` | Second Brain (chặng 3) |
| `IHG_PRIVATE_CORE_DIR` | `<root>/private_core` | Private Core (chặng 4) |
| `IHG_LOG_DIR` | `<root>/logs` | Log Coordinator/QA/State |
| `IHG_AGENT_RUNTIME_BIN` | `claude` | Binary runtime Agent |
| `IHG_AGENT_RUNTIME_TIMEOUT` | `120` | Timeout gọi Agent (giây) |
| `IHG_PRINCIPAL` | `gd-ihg` | Principal mặc định |
| `IHG_MAX_RETRY` | `2` | Số lần retry tối đa |

## 8. Cấu trúc file

```
TEST-COORD-002/
├── SPEC.md
├── BAO-CAO-HOAN-THANH.md
├── src/ihg_core/
│   ├── __init__.py
│   ├── config.py          # cấu hình qua env
│   ├── authz.py           # phân quyền thật
│   ├── state_store.py     # state machine + DRIFT
│   ├── registry.py        # Worker vs AI Agent
│   ├── agent_runtime.py   # interface gọi AI Agent
│   ├── worker_checksum.py # Worker SHA-256
│   ├── coordinator.py     # Worker điều phối
│   └── qa_check.py        # QA qua ihg-qa
├── tests/
│   ├── __init__.py
│   └── test_all.py        # 18 test tự động
├── fixtures/              # dữ liệu mẫu
├── output/                # artifact
├── state/                 # tasks.json + log
├── logs/                  # coordinator.log
├── qa/                    # QA reports
└── runtime/               # runtime configs (sau)
```

## 9. Kết quả mong đợi

Sau khi chạy `python tests/test_all.py`:
- 18/18 test PASS (AuthZ, State Machine, Drift, Coordinator, QA)
- AI Agent ihg-it và ihg-qa được gọi qua ClaudeCliRuntime (hoặc ghi lý do không gọi được)
- Artifact có SHA-256 verify được
- Phát hiện DRIFT khi artifact mất/thay đổi
- QA: PASS nếu AI QA OK, QA_UNVERIFIED nếu runtime không khả dụng, FAIL nếu kỹ thuật fail
