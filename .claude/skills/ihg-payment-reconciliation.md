---
name: ihg-payment-reconciliation
description: Đối chiếu thanh toán - Đối chiếu khối lượng, công nợ, trùng lắp
---

# Skill: ihg-payment-reconciliation

## Đối chiếu thanh toán

### Mục đích
Đối chiếu khối lượng thực hiện với khối lượng nghiệm thu và thanh toán, phát hiện trùng lắp.

### Điều kiện kích hoạt
- Khi chuẩn bị hồ sơ thanh toán
- Khi cần đối chiếu công nợ
- Khi phát hiện bất thường

### Đầu vào
- Danh sách khối lượng thực hiện theo kỳ
- Danh sách khối lượng nghiệm thu
- Danh sách thanh toán đã thực hiện
- Hợp đồng và điều khoản thanh toán

### Các bước thực hiện

#### Bước 1: Thu thập dữ liệu
- Khối lượng thực hiện kỳ này
- Luỹ kế khối lượng thực hiện
- Khối lượng nghiệm thu đến nay
- Số thanh toán đã thực hiện

#### Bước 2: Đối chiếu khối lượng
- So sánh khối lượng thực hiện với nghiệm thu
- Phát hiện khối lượng chưa nghiệm thu
- Phát hiện khối lượng vượt thiết kế

#### Bước 3: Kiểm tra trùng lắp
- Kiểm tra khối lượng trùng giữa các kỳ
- Kiểm tra khối lượng trùng giữa các hạng mục
- Kiểm tra tính trùng với thanh toán trước

#### Bước 4: Đối chiếu công nợ
- Tính giá trị còn phải thanh toán
- Kiểm tra đối chiếu với hợp đồng
- Kiểm tra tạm ứng và thu hồi

#### Bước 5: Lập báo cáo
- Tổng hợp kết quả đối chiếu
- Ghi nhận bất thường
- Đề xuất xử lý

### Đầu ra

\`\`\`markdown
# BÁO CÁO ĐỐI CHIẾU THANH TOÁN

**Mã dự án**: [mã]
**Kỳ đối chiếu**: [kỳ]
**Ngày**: [ngày]

## 1. TỔNG QUAN

| Trường | Giá trị |
|---------|---------|
| Giá trị hợp đồng | [số] |
| Giá trị đã nghiệm thu | [số] |
| Giá trị đã thanh toán | [số] |
| Còn phải thanh toán | [số] |

## 2. CHI TIẾT ĐỐI CHIẾU

| Hạng mục | Kỳ này | Luỹ kế | Nghiệm thu | Thanh toán | Chênh lệch |
|-----------|---------|--------|-------------|------------|-------------|

## 3. PHÁT HIỆN TRÙNG LẮP

| STT | Hạng mục | Khối lượng | Vị trí trùng | Xử lý |
|-----|-----------|------------|--------------|--------|

## 4. CÔNG NỢ

| Trường | Giá trị |
|---------|---------|
| Tổng giá trị nghiệm thu | [số] |
| Đã thanh toán | [số] |
| Tạm ứng chưa thu hồi | [số] |
| Giữ lại chưa giải toả | [số] |
| **Còn phải thanh toán** | [số] |

## 5. VẤN ĐỀ CẦN XỬ LÝ

| STT | Vấn đề | Mức độ | Đề xuất |
|-----|---------|--------|----------|
\`\`\`

### Giới hạn
- **KHÔNG tự quyết định** thanh toán
- **KHÔNG phát hành chứng từ** - chỉ lập bảng trình duyệt
- Phát hiện trùng lắp phải được xác minh lại
