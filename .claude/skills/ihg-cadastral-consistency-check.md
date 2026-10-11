---
name: ihg-cadastral-consistency-check
description: Kiểm tra nhất quán CSDL - Kiểm tra khoá, quan hệ, miền giá trị
---

# Skill: ihg-cadastral-consistency-check

## Kiểm tra nhất quán CSDL địa chính

### Mục đích
Kiểm tra tính nhất quán của CSDL địa chính, phát hiện lỗi khoá, quan hệ và dữ liệu.

### Điều kiện kích hoạt
- Khi cần kiểm tra trước nhập dữ liệu
- Khi cần đánh giá chất lượng CSDL
- Khi phát hiện bất thường

### Đầu vào
- Cấu trúc CSDL (schema)
- Dữ liệu cần kiểm tra
- Quy tắc nhất quán

### Các bước thực hiện

#### Bước 1: Kiểm tra khoá
- Kiểm tra khoá trùng
- Kiểm tra khoá null
- Kiểm tra khoá ngoại

#### Bước 2: Kiểm tra quan hệ
- Kiểm tra bản ghi thiếu liên kết
- Kiểm tra quan hệ nhiều đối tượng
- Kiểm tra tính khớp nối

#### Bước 3: Kiểm tra miền giá trị
- Kiểm tra giá trị nằm ngoài danh mục
- Kiểm tra kiểu dữ liệu
- Kiểm tra trường bắt buộc

#### Bước 4: Kiểm tra không gian-thuộc tính
- Kiểm tra thửa không có ranh giới
- Kiểm tra ranh giới không có thửa
- Kiểm tra thuộc tính không khớp không gian

### Đầu ra

\`\`\`markdown
# BÁO CÁO KIỂM TRA NHẤT QUÁN

**Ngày**: [ngày]
**CSDL**: [tên]

## 1. TỔNG QUAN

| Trường | Giá trị |
|---------|---------|
| Số bảng | [số] |
| Số bản ghi | [số] |
| Lỗi phát hiện | [số] |

## 2. LỖI KHOÁ

| Bảng | Trường | Số lỗi | Mẫu |
|-------|---------|---------|-----|

## 3. LỖI QUAN HỆ

| Bảng cha | Bảng con | Số mất liên kết |
|----------|----------|------------------|

## 4. LỖI MIỀN GIÁ TRỊ

| Bảng | Trường | Giá trị lỗi | Số lỗi |
|-------|---------|--------------|---------|

## 5. LỖI KHÔNG GIAN-THUỘC TÍNH

| Loại | Số lỗi | Chi tiết |
|-------|---------|----------|
\`\`\`

### Giới hạn
- **KHÔNG tự sửa** dữ liệu
- **KHÔNG gộp chủ thể** chỉ vì trùng tên
- **KHÔNG coi số thửa là khoá duy nhất** toàn hệ thống
