---
name: ihg-gis-intake
description: Tiếp nhận dữ liệu GIS - Kiểm kê lớp dữ liệu, hệ quy chiếu, chất lượng
---

# Skill: ihg-gis-intake

## Tiếp nhận dữ liệu GIS

### Mục đích
Kiểm kê và đánh giá chất lượng dữ liệu GIS đầu vào trước khi xử lý.

### Điều kiện kích hoạt
- Khi nhận dữ liệu GIS mới
- Khi cần đánh giá chất lượng đầu vào
- Khi chuẩn bị xây dựng CSDL

### Đầu vào
- Danh sách lớp dữ liệu
- Thông tin hệ thống nguồn
- Yêu cầu về chất lượng

### Các bước thực hiện

#### Bước 1: Kiểm kê lớp dữ liệu
- Liệt kê các lớp dữ liệu
- Xác định loại dữ liệu (vector/raster)
- Xác định định dạng file
- Ghi nhận số lượng đối tượng

#### Bước 2: Kiểm tra hệ quy chiếu
- Xác định hệ quy chiếu hiện tại
- Kiểm tra phép chiếu
- Kiểm tra đơn vị
- Kiểm tra thông tin độ cao (nếu có)

#### Bước 3: Kiểm tra chất lượng
- Kiểm tra hình học cơ bản
- Kiểm tra thuộc tính
- Kiểm tra mã
- Kiểm tra dữ liệu trùng

#### Bước 4: Lập báo cáo
- Tổng hợp kết quả kiểm tra
- Ghi nhận vấn đề
- Đề xuất xử lý

### Đầu ra

\`\`\`markdown
# BÁO CÁO TIẾP NHẬN DỮ LIỆU GIS

**Ngày**: [ngày]
**Nguồn**: [tên]

## 1. TỔNG QUAN

| Trường | Giá trị |
|---------|---------|
| Số lớp dữ liệu | [số] |
| Loại dữ liệu | Vector/Raster |
| Định dạng | [định dạng] |

## 2. DANH MỤC LỚP DỮ LIỆU

| STT | Tên lớp | Loại | Số đối tượng | Hệ quy chiếu |
|-----|---------|------|--------------|--------------|

## 3. KIỂM TRA HỆ QUY CHIẾU

| Lớp | Hệ hiện tại | Phép chiếu | Đơn vị | Kết quả |
|-----|-------------|-----------|--------|----------|

## 4. VẤN ĐỀ PHÁT HIỆN

| STT | Lớp | Vấn đề | Mức độ | Xử lý |
|-----|-----|---------|--------|--------|
\`\`\`

### Giới hạn
- **KHÔNG tự gán mã EPSG** - phải xác minh đủ tham số
- **KHÔNG sửa dữ liệu gốc** - chỉ báo cáo
- **KHÔNG xác nhận độ chính xác** - chỉ kiểm tra tính hợp lệ
