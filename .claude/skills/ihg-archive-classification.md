---
name: ihg-archive-classification
description: Phân loại hồ sơ - Đề xuất phân loại, lập mục lục
---

# Skill: ihg-archive-classification

## Phân loại hồ sơ

### Mục đích
Đề xuất phân loại hồ sơ và lập mục lục theo quy tắc của dự án.

### Điều kiện kích hoạt
- Sau khi kiểm kê hồ sơ
- Khi cần sắp xếp hồ sơ
- Khi chuẩn bị bàn giao

### Đầu vào
- Kết quả kiểm kê từ ihg-archive-inventory
- Quy tắc phân loại của dự án
- Yêu cầu về mục lục

### Các bước thực hiện

#### Bước 1: Xác định tiêu chí phân loại
- Theo nguồn hình thành
- Theo nội dung
- Theo thời gian
- Theo hình thức

#### Bước 2: Phân loại hồ sơ
- Áp dụng tiêu chí đã xác định
- Gán mã phân loại
- Kiểm tra tính nhất quán

#### Bước 3: Lập mục lục
- Sắp xếp theo thứ tự
- Đánh số thứ tự
- Lập bảng tra cứu

#### Bước 4: Đề xuất sắp xếp
- Đề xuất vị trí lưu trữ
- Đề xuất điều kiện bảo quản
- Đề xuất thời hạn bảo quản

### Đầu ra

\`\`\`markdown
# BÁO CÁO PHÂN LOẠI HỒ SƠ

**Ngày**: [ngày]
**Người phân loại**: [tên]

## 1. TIÊU CHÍ PHÂN LOẠI

| STT | Tiêu chí | Mô tả | Áp dụng |
|-----|----------|--------|---------|

## 2. PHÂN LOẠI CHI TIẾT

| Mã HS | Tiêu đề | Nhóm | Loại | Vị trí | Thời hạn |
|--------|---------|------|------|--------|-----------|

## 3. MỤC LỤC

| STT | Mã | Tiêu đề | Trang |
|-----|-----|---------|-------|

## 4. ĐỀ XUẤT

### Vị trí lưu trữ
| Nhóm | Vị trí | Điều kiện |
|------|--------|-----------|

### Thời hạn bảo quản
| Loại | Thời hạn | Căn cứ |
|------|----------|--------|
\`\`\`

### Giới hạn
- **KHÔNG tự quyết định loại bỏ** hồ sơ
- **KHÔNG thay đổi** hồ sơ gốc
- Đề xuất cần được duyệt trước khi thực hiện
