---
name: ihg-archive-inventory
description: Kiểm kê hồ sơ - Khảo sát, kiểm kê, mô tả hồ sơ
---

# Skill: ihg-archive-inventory

## Kiểm kê hồ sơ

### Mục đích
Khảo sát, kiểm kê và mô tả hồ sơ để xác định nội dung, tình trạng và quản lý.

### Điều kiện kích hoạt
- Khi tiếp nhận hồ sơ mới
- Khi cần kiểm kê kho lưu trữ
- Khi chuẩn bị bàn giao hồ sơ

### Đầu vào
- Danh sách hồ sơ cần kiểm kê
- Thông tin nguồn hình thành (nếu có)
- Quy tắc phân loại của dự án

### Các bước thực hiện

#### Bước 1: Khảo sát ban đầu
- Xác định phạm vi hồ sơ
- Xác định nguồn hình thành
- Xác định thời gian
- Xác định số lượng ước tính

#### Bước 2: Kiểm kê chi tiết
- Đếm số lượng (hộp/tập/trang)
- Kiểm tra mã hồ sơ
- Kiểm tra tiêu đề
- Kiểm tra thời gian
- Kiểm tra tình trạng vật lý

#### Bước 3: Mô tả hồ sơ
- Mô tả nội dung
- Mô tả hình thức
- Mô tả mối liên hệ
- Ghi nhận đặc điểm

#### Bước 4: Lập biên bản
- Biên bản kiểm kê
- Danh mục chi tiết
- Nhận xét và đề xuất

### Đầu ra

\`\`\`markdown
# BIÊN BẢN KIỂM KÊ HỒ SƠ

**Ngày kiểm kê**: [ngày]
**Người kiểm kê**: [tên]
**Phạm vi**: [mô tả]

## 1. THÔNG TIN CHUNG

| Trường | Giá trị |
|---------|---------|
| Số lượng hộp | [số] |
| Số lượng tập | [số] |
| Số lượng trang | [số] |
| Thời gian | [từ - đến] |

## 2. DANH MỤC HỒ SƠ

| Mã HS | Tiêu đề | Số tập | Số trang | Thời gian | Tình trạng | Ghi chú |
|--------|---------|---------|----------|-----------|------------|---------|

## 3. TÌNH TRẠNG VẬT LÝ

| Tình trạng | Số lượng | Tỷ lệ |
|------------|----------|-------|
| Tốt | [số] | [%] |
| Hư hỏng nhẹ | [số] | [%] |
| Hư hỏng nặng | [số] | [%] |

## 4. PHÁT HIỆN

| STT | Vấn đề | Vị trí | Đề xuất |
|-----|---------|--------|----------|
\`\`\`

### Giới hạn
- **KHÔNG tự quyết định loại bỏ** hồ sơ
- **KHÔNG thay đổi** trật tự hồ sơ - chỉ ghi nhận
- Thiếu căn cứ thì ghi "chờ xác minh"
