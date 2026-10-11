---
name: ihg-digitization-pipeline
description: Quy trình số hoá - Xử lý hàng loạt tài liệu quét
---

# Skill: ihg-digitization-pipeline

## Quy trình số hoá

### Mục đích
Xử lý hàng loạt tài liệu quét, bao gồm kiểm tra chất lượng, OCR và trích xuất dữ liệu.

### Điều kiện kích hoạt
- Khi nhận lô tài liệu cần số hoá
- Khi cần xử lý tài liệu quét
- Khi cần trích xuất dữ liệu từ OCR

### Đầu vào
- Danh sách file cần xử lý
- Yêu cầu về định dạng đầu ra
- Schema trích xuất dữ liệu

### Các bước thực hiện

#### Bước 1: Kiểm kê đầu vào
- Liệt kê file cần xử lý
- Kiểm tra định dạng
- Kiểm tra kích thước
- Kiểm tra khả năng mở

#### Bước 2: Kiểm tra chất lượng ảnh
- Phát hiện ảnh mờ
- Phát hiện ảnh lệch
- Phát hiện ảnh cắt mất nội dung
- Phát hiện trang trùng

#### Bước 3: OCR
- Chọn công cụ OCR phù hợp
- Chạy OCR hàng loạt
- Lưu kết quả

#### Bước 4: Trích xuất dữ liệu
- Áp dụng schema
- Kiểm tra trường bắt buộc
- Ghi nhận độ tin cậy

#### Bước 5: Kiểm tra sau xử lý
- Kiểm tra số lượng file
- Kiểm tra chất lượng OCR
- Lập báo cáo lỗi

### Đầu ra

\`\`\`markdown
# BÁO CÁO QUY TRÌNH SỐ HOÁ

**Ngày**: [ngày]
**Lô**: [mã lô]

## 1. TỔNG QUAN

| Trường | Giá trị |
|---------|---------|
| Tổng số file | [số] |
| Đã xử lý | [số] |
| Thành công | [số] |
| Lỗi | [số] |

## 2. CHẤT LƯỢNG ẢNH

| Loại lỗi | Số file | Tỷ lệ |
|-----------|---------|-------|
| Ảnh mờ | [số] | [%] |
| Ảnh lệch | [số] | [%] |
| Thiếu nội dung | [số] | [%] |
| Trùng trang | [số] | [%] |

## 3. KẾT QUẢ OCR

| Trường | Giá trị |
|---------|---------|
| Tổng trang OCR | [số] |
| Độ tin cậy trung bình | [%] |
| Cần kiểm tra thủ công | [số] |

## 4. FILE LỖI

| STT | File | Lỗi | Xử lý |
|-----|------|------|--------|
\`\`\`

### Giới hạn
- **KHÔNG tự quyết định** định dạng lưu trữ
- **KHÔNG tự đặt DPI** - phải theo yêu cầu
- Lỗi cần kiểm tra thủ công trước khi kết luận
