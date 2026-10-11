---
name: ihg-gis-quality-check
description: Kiểm tra chất lượng GIS - Kiểm tra hình học, topology, thuộc tính
---

# Skill: ihg-gis-quality-check

## Kiểm tra chất lượng GIS

### Mục đích
Kiểm tra chất lượng dữ liệu GIS theo quy tắc của dự án, phát hiện lỗi hình học và topology.

### Điều kiện kích hoạt
- Sau khi tiếp nhận từ ihg-gis-intake
- Khi cần kiểm tra trước xuất bản
- Khi cần đánh giá chất lượng

### Đầu vào
- Lớp dữ liệu cần kiểm tra
- Quy tắc kiểm tra của dự án
- Tiêu chuẩn chất lượng

### Các bước thực hiện

#### Bước 1: Kiểm tra hình học
- Kiểm tra null geometry
- Kiểm tra geometry hợp lệ
- Kiểm tra self-intersection
- Kiểm tra duplicate vertices

#### Bước 2: Kiểm tra topology
- Kiểm tra vùng hở
- Kiểm tra chồng lấn
- Kiểm tra gap (nếu yêu cầu)
- Kiểm tra overshoot/undershoot

#### Bước 3: Kiểm tra thuộc tính
- Kiểm tra giá trị null
- Kiểm tra miền giá trị
- Kiểm tra kiểu dữ liệu
- Kiểm tra mã

#### Bước 4: Lập báo cáo
- Tổng hợp lỗi
- Phân loại theo mức độ
- Đề xuất sửa

### Đầu ra

\`\`\`markdown
# BÁO CÁO KIỂM TRA CHẤT LƯỢNG GIS

**Ngày**: [ngày]
**Lớp**: [tên lớp]

## 1. TỔNG QUAN

| Trường | Giá trị |
|---------|---------|
| Tổng đối tượng | [số] |
| Lỗi phát hiện | [số] |
| Tỷ lệ lỗi | [%] |

## 2. LỖI HÌNH HỌC

| Loại lỗi | Số lỗi | Vị trí |
|-----------|---------|--------|

## 3. LỖI TOPOLOGY

| Loại lỗi | Số lỗi | Mức độ |
|-----------|---------|--------|

## 4. LỖI THUỘC TÍNH

| Trường | Loại lỗi | Số lỗi |
|---------|-----------|---------|

## 5. ĐỀ XUẤT SỬA

| STT | Đối tượng | Lỗi | Cách sửa |
|-----|-----------|------|----------|
\`\`\`

### Giới hạn
- **KHÔNG tự sửa** dữ liệu gốc
- **KHÔNG mặc định** vùng hở/chồng lấn đều là lỗi
- **KHÔNG kết luận độ chính xác** - chỉ kiểm tra tính hợp lệ
