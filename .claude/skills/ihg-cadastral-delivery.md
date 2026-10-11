---
name: ihg-cadastral-delivery
description: Bàn giao CSDL - Bộ bàn giao, từ điển dữ liệu, nhật ký
---

# Skill: ihg-cadastral-delivery

## Bàn giao CSDL địa chính

### Mục đích
Chuẩn bị bộ bàn giao CSDL địa chính bao gồm dữ liệu, từ điển và hướng dẫn.

### Điều kiện kích hoạt
- Khi kết thúc giai đoạn xây dựng CSDL
- Khi cần bàn giao cho đơn vị vận hành
- Khi cần xuất dữ liệu cho hệ thống khác

### Đầu vào
- Dữ liệu đã xây dựng
- Schema CSDL
- Báo cáo kiểm tra
- Danh mục mã

### Các bước thực hiện

#### Bước 1: Chuẩn bị dữ liệu
- Xuất theo định dạng đích
- Kiểm tra tính đầy đủ
- Nén và đóng gói

#### Bước 2: Chuẩn bị tài liệu
- Từ điển dữ liệu
- Bảng ánh xạ
- Danh mục mã
- Hướng dẫn nhập

#### Bước 3: Chuẩn bị nhật ký
- Nhật ký chuyển đổi
- Báo cáo kiểm tra
- Báo cáo lỗi

#### Bước 4: Kiểm tra cuối
- Kiểm tra đầy đủ bộ bàn giao
- Kiểm tra chất lượng
- Lập biên bản bàn giao

### Đầu ra

\`\`\`markdown
# BỘ BÀN GIAO CƠ SỞ DỮ LIỆU

**Ngày**: [ngày]
**Dự án**: [mã]

## 1. THÔNG TIN CHUNG

| Trường | Giá trị |
|---------|---------|
| Số bảng | [số] |
| Số bản ghi | [số] |
| Dung lượng | [GB/MB] |

## 2. DANH MỤC BÀN GIAO

| STT | Tên file | Mô tả | Dung lượng |
|-----|----------|--------|------------|

## 3. TỪ ĐIỂN DỮ LIỆU

| Bảng | Trường | Kiểu | Mô tả |
|------|---------|------|--------|

## 4. NHẬT KÝ CHUYỂN ĐỔI

| Lần chạy | Ngày | Số đọc | Số nhập | Thành công | Lỗi |
|-----------|------|--------|---------|------------|-----|
\`\`\`

### Giới hạn
- **KHÔNG ghi vào CSDL đang vận hành** - chỉ bàn giao
- **KHÔNG tự chọn nền tảng** - phải theo yêu cầu
- **KHÔNG xác nhận tương thích** - chỉ kiểm tra theo yêu cầu
