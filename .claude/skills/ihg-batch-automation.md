---
name: ihg-batch-automation
description: Tự động hoá xử lý lô - Công cụ xử lý hàng loạt OCR, GIS, CSDL
---

# Skill: ihg-batch-automation

## Tự động hoá xử lý lô

### Mục đích
Xây dựng và vận hành công cụ xử lý hàng loạt cho OCR, GIS và CSDL.

### Điều kiện kích hoạt
- Khi cần xử lý lượng lớn dữ liệu
- Khi cần chạy định kỳ
- Khi cần tiếp tục sau lỗi

### Đầu vào
- Loại xử lý (OCR/GIS/CSDL)
- Thư mục/file đầu vào
- Tham số xử lý
- Lịch chạy (nếu định kỳ)

### Các bước thực hiện

#### Bước 1: Xây dựng công cụ
- Chọn công cụ phù hợp
- Thiết lập tham số
- Kiểm tra với dữ liệu mẫu

#### Bước 2: Chạy xử lý
- Theo dõi tiến trình
- Ghi nhật ký
- Xử lý lỗi

#### Bước 3: Kiểm tra kết quả
- Kiểm tra số lượng
- Kiểm tra chất lượng
- Lưu kết quả

#### Bước 4: Tiếp tục sau lỗi
- Xác định điểm dừng
- Tiếp tục xử lý
- Ghi nhật ký lỗi

### Đầu ra

\`\`\`markdown
# BÁO CÁO XỬ LÝ LÔ

**Ngày**: [ngày]
**Loại**: [OCR/GIS/CSDL]

## 1. TỔNG QUAN

| Trường | Giá trị |
|---------|---------|
| Tổng cần xử lý | [số] |
| Đã xử lý | [số] |
| Thành công | [số] |
| Lỗi | [số] |

## 2. TIẾN TRÌNH

| Thời gian | File | Trạng thái | Ghi chú |
|------------|------|------------|---------|

## 3. LỖI

| STT | File | Lỗi | Xử lý |
|-----|------|------|--------|
\`\`\`

### Giới hạn
- **KHÔNG tự tạo URL API** - phải có căn cứ
- **KHÔNG lưu bí mật** trong mã nguồn
- **KHÔNG chạy không giám sát** - cần kiểm tra kết quả
