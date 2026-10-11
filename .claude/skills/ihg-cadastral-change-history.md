---
name: ihg-cadastral-change-history
description: Lịch sử biến động - Quản lý và truy nguyên thay đổi dữ liệu
---

# Skill: ihg-cadastral-change-history

## Lịch sử biến động CSDL địa chính

### Mục đích
Quản lý và truy nguyên các thay đổi trong CSDL địa chính, đảm bảo tính toàn vẹn lịch sử.

### Điều kiện kích hoạt
- Khi cần ghi nhận thay đổi
- Khi cần truy nguyên nguồn gốc
- Khi cần kiểm tra lịch sử biến động

### Đầu vào
- Loại thay đổi
- Dữ liệu trước/sau thay đổi
- Người thực hiện
- Căn cứ thay đổi

### Các bước thực hiện

#### Bước 1: Ghi nhận thay đổi
- Mô tả loại thay đổi
- Lưu dữ liệu trước thay đổi
- Lưu dữ liệu sau thay đổi
- Ghi người và thời gian

#### Bước 2: Kiểm tra tính hợp lệ
- Kiểm tra căn cứ thay đổi
- Kiểm tra quyền thực hiện
- Kiểm tra tính đầy đủ

#### Bước 3: Truy nguyên
- Tra cứu theo đối tượng
- Tra cứu theo thời gian
- Tra cứu theo người thực hiện

#### Bước 4: Báo cáo
- Tổng hợp biến động
- Báo cáo truy nguyên

### Đầu ra

\`\`\`markdown
# BÁO CÁO LỊCH SỬ BIẾN ĐỘNG

**Ngày**: [ngày]
**Đối tượng**: [mã thửa/chủ thể]

## 1. THÔNG TIN ĐỐI TƯỢNG

| Trường | Giá trị |
|---------|---------|

## 2. LỊCH SỬ THAY ĐỔI

| Ngày | Loại thay đổi | Người thực hiện | Căn cứ | Chi tiết |
|------|---------------|------------------|--------|----------|

## 3. TRUY NGUYÊN

### Dữ liệu tại thời điểm [ngày]
[Chi tiết dữ liệu]

### Thay đổi từ [ngày A] đến [ngày B]
[Chi tiết thay đổi]
\`\`\`

### Giới hạn
- **KHÔNG ghi đè lịch sử** - luôn lưu cả trước và sau
- **KHÔNG xoá** bản ghi lịch sử
- **KHÔNG tự quyết định** thay đổi dữ liệu đang vận hành
