---
name: ihg-acceptance-check
description: Kiểm tra nghiệm thu - Đánh giá mức sẵn sàng bàn giao
---

# Skill: ihg-acceptance-check

## Kiểm tra nghiệm thu

### Mục đích
Đánh giá mức độ sẵn sàng của sản phẩm/sản phẩm trước khi trình nghiệm thu.

### Điều kiện kích hoạt
- Khi cần đánh giá trước nghiệm thu
- Khi cần kiểm tra đầy đủ hồ sơ
- Khi cần xác nhận chất lượng

### Đầu vào
- Sản phẩm cần kiểm tra
- Tiêu chí nghiệm thu
- Danh sách hồ sơ cần có

### Các bước thực hiện

#### Bước 1: Kiểm tra sản phẩm
- Kiểm tra theo tiêu chí đã duyệt
- Kiểm tra chất lượng
- Kiểm tra đầy đủ

#### Bước 2: Kiểm tra hồ sơ
- Kiểm tra đầy đủ hồ sơ
- Kiểm tra trạng thái hồ sơ
- Kiểm tra chữ ký và phê duyệt

#### Bước 3: Đánh giá
- Tổng hợp kết quả kiểm tra
- Đánh giá mức sẵn sàng
- Đề xuất xử lý

### Đầu ra

\`\`\`markdown
# BÁO CÁO KIỂM TRA NGHIỆM THU

**Ngày**: [ngày]
**Sản phẩm**: [tên]

## 1. TỔNG QUAN

| Trường | Giá trị |
|---------|---------|
| Số tiêu chí | [số] |
| Đạt | [số] |
| Không đạt | [số] |
| **Mức sẵn sàng** | [%] |

## 2. KIỂM TRA SẢN PHẨM

| STT | Tiêu chí | Kết quả | Ghi chú |
|-----|----------|---------|---------|

## 3. KIỂM TRA HỒ SƠ

| STT | Hồ sơ | Trạng thái | Ghi chú |
|-----|-------|------------|---------|

## 4. KẾT LUẬN

| Mức độ | Đánh giá |
|--------|----------|
| Sẵn sàng trình nghiệm thu | [Có/Không] |
| Cần sửa chữa trước | [Danh sách] |
\`\`\`

### Giới hạn
- **KHÔNG ghi "đã nghiệm thu"** - chỉ ghi "sẵn sàng trình nghiệm thu"
- **KHÔNG thay thế** kiểm tra của bên có thẩm quyền
- Kết luận chỉ mang tính đề xuất
