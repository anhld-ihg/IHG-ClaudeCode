---
name: ihg-backup-restore
description: Sao lưu và phục hồi - Kiểm tra sao lưu, phương án khôi phục
---

# Skill: ihg-backup-restore

## Sao lưu và phục hồi

### Mục đích
Kiểm tra và đảm bảo có phương án sao lưu, phục hồi cho dữ liệu và hệ thống.

### Điều kiện kích hoạt
- Khi cần kiểm tra sao lưu định kỳ
- Khi cần lập phương án khôi phục
- Khi phát hiện mất dữ liệu

### Đầu vào
- Danh sách dữ liệu/hệ thống cần sao lưu
- Yêu cầu về tần suất sao lưu
- Yêu cầu về thời gian khôi phục

### Các bước thực hiện

#### Bước 1: Kiểm tra sao lưu
- Kiểm tra tồn tại bản sao lưu
- Kiểm tra tính đầy đủ
- Kiểm tra tính toàn vẹn

#### Bước 2: Kiểm tra khả năng khôi phục
- Thử khôi phục với dữ liệu mẫu
- Đo thời gian khôi phục
- Kiểm tra dữ liệu sau khôi phục

#### Bước 3: Lập phương án
- Xác định RPO (Recovery Point Objective)
- Xác định RTO (Recovery Time Objective)
- Lập quy trình khôi phục

#### Bước 4: Báo cáo
- Tổng hợp kết quả kiểm tra
- Đề xuất cải thiện

### Đầu ra

\`\`\`markdown
# BÁO CÁO SAO LƯU VÀ PHỤC HỒI

**Ngày**: [ngày]

## 1. TỔNG QUAN

| Trường | Giá trị |
|---------|---------|
| Số hệ thống | [số] |
| Hệ thống đạt yêu cầu | [số] |
| Cần cải thiện | [số] |

## 2. KIỂM TRA SAO LƯU

| Hệ thống | Lần sao lưu cuối | Dung lượng | Trạng thái |
|-----------|-------------------|------------|------------|

## 3. KIỂM TRA KHÔI PHỤC

| Hệ thống | Thời gian khôi phục | RTO đạt được | Kết quả |
|-----------|----------------------|---------------|----------|

## 4. ĐỀ XUẤT

| STT | Hệ thống | Vấn đề | Đề xuất |
|-----|----------|---------|----------|
\`\`\`

### Giới hạn
- **KHÔNG tự thực hiện** sao lưu/phục hồi trên hệ thống thật
- **KHÔNG xoá** dữ liệu gốc
- Chỉ kiểm tra và đề xuất
