# CHECKPOINT — TEST-COORD-002

> Cập nhật: 2026-10-15
> Trạng thái: **MỨC A VERIFIED — sẵn sàng chuyển sang Second Brain**

## 1. Kết quả Mức A (phiên Claude Code hiện tại)

| Hạng mục | Kết quả | Bằng chứng |
|---------|---------|-----------|
| Agent ihg-it (thật) gọi thành công | PASS | sub-agent chạy độc lập, tạo artifact 4218 chars / 926 từ / 3 heading ## |
| Agent ihg-qa (thật) gọi thành công | PASS | sub-agent riêng, prompt độc lập, trả `{"qa_result":"PASS","qa_detail":"..."}` |
| 2 lần gọi độc lập (context riêng) | PASS | sub-agent #1 + sub-agent #2 = 2 transcript JSONL riêng trong `C:\Users\anhld\AppData\Local\Temp\claude\...\tasks\` |
| 4 hard check cứng | PASS | len≥50 ✓ / no TODO ✓ / has heading ✓ / meaningful≥80 ✓ |
| State machine đầy đủ | PASS | PENDING→DISPATCHED→RUNNING→SUCCEEDED→QA_PENDING→QA_PASS→DELIVERED |
| Artifact + SHA-256 lưu | PASS | `5ccd6a11476276e8edcf6820d72ac652603fb158187e677f99243400ccdbed20` |
| Không dùng token | PASS | sub-agent dùng chính cơ chế Claude Code session, không cần ANTHROPIC_AUTH_TOKEN |
| Không dùng data khách hàng | PASS | chỉ `fixtures/contract-sample.md` (mẫu giả) |
| Không ghi đè file | PASS | artifact tên duy nhất `art-MUC-A-...md` |
| Không OAuth / marketplace | PASS | sub-agent qua session, không qua Anthropic OAuth |

Evidence file: `output/in-session-evidence/MUC-A-EV-summary.json`

## 2. Bộ test 104/104 PASS (giữ nguyên)

| File test | PASS |
|-----------|------|
| test_token_vault | 23 |
| test_worker_runner | 13 |
| test_gateway_runtime | 28 |
| test_e2e_flow | 15 |
| runtests (legacy) | 25 |
| **Tổng** | **104** |

## 3. Phân biệt 2 mức vận hành

### Mức A — PHIÊN CLAUDE CODE HIỆN TẠI ✅
- **Trạng thái**: VERIFIED
- **Cơ chế**: sub-agent (Agent tool) = 2 lần gọi model độc lập, cùng API trung gian bên thứ ba đã cấu hình
- **Tốn chi phí**: 2 lượt model (IT + QA), dữ liệu giả lập
- **Bằng chứng**: `output/in-session-evidence/MUC-A-EV-summary.json` + 2 transcript sub-agent

### Mức B — WORKER RUNNER QUA GATEWAY ⏸️
- **Trạng thái**: CHƯA THỬ (chờ GĐ cấp ANTHROPIC_AUTH_TOKEN khi cần)
- **Cơ chế**: Python `Worker Runner` → `GatewayRuntime` → agentshop247
- **Mục đích**: chạy 24/7 trên VPS / môi trường độc lập, KHÔNG phụ thuộc phiên Desktop
- **KHÔNG trích xuất credential từ Desktop** — phải có cơ chế cấp riêng
- **Đã có sẵn code** (`src/ihg_core/worker_runner.py`, `gateway_runtime.py`) + 28 test
- **Test khô**: GatewayRuntime với token giả → HTTP 401 thật từ server (đã chứng minh network OK, schema OK, retry OK)

## 4. Cấu trúc thư mục evidence

```
output/in-session-evidence/
├── MUC-A-EV-summary.json          # Báo cáo tổng
├── it-artifacts/
│   └── art-MUC-A-1792062469-203981.md  # 4218 chars, SHA-256 đã lưu
└── (sẽ bổ sung khi test Mức B)
```

## 5. Bước tiếp theo (tự triển khai, không chờ GĐ)

1. **IHG Second Brain bản nền tảng** (theo chỉ đạo GĐ mục 6):
   - Nạp tài liệu giả lập
   - Phân loại: PRIVATE CORE / DEPARTMENT / PROJECT / EMPLOYEE KNOWLEDGE
   - Lập chỉ mục tìm kiếm
   - Trả lời có dẫn chứng
   - Lưu kiến thức đã xác minh
   - Kiểm thử phân quyền thực tế

2. **Giữ nguyên**: 104 test, state store, registry, AuthZ, Token Vault, Worker Runner, Gateway Runtime.

3. **KHÔNG làm**:
   - Đọc token từ cookie / file backup Desktop
   - Gọi Mức B (Worker Runner qua gateway) khi chưa có token từ GĐ
   - Sửa `setup_vault.py` / `token_vault.py` thêm bất kỳ logic tự trích xuất credential nào

## 6. Tệp WAITING_APPROVAL (nếu có)

| Tác vụ | Trạng thái |
|--------|-----------|
| Mức B (Worker Runner qua gateway thật) | **WAITING_APPROVAL** — chờ GĐ cấp `ANTHROPIC_AUTH_TOKEN` qua `setup-token-vault.ps1` |
| Kết nối data khách hàng thật | **WAITING_APPROVAL** — chờ GĐ duyệt riêng |
| Triển khai production | **WAITING_APPROVAL** — chờ GĐ |
