---
name: ihg-project-documents
description: Quản lý hồ sơ dự án - Quản lý phiên bản, thời hạn, người phụ trách
---

# Skill: ihg-project-documents

## Quản lý hồ sơ dự án

### Mục đích
Theo dõi và quản lý hồ sơ của dự án, bao gồm phiên bản, thời hạn và người phụ trách.

### Điều kiện kích hoạt
- Khi tiếp nhận dự án mới
- Khi cần cập nhật trạng thái hồ sơ
- Khi cần kiểm tra tiến độ hồ sơ
- Khi cần bàn giao hồ sơ

### Đầu vào
- Mã dự án
- Danh sách hồ sơ cần quản lý

### Các bước thực hiện

#### Bước 1: Khởi tạo danh mục
- Liệt kê tất cả hồ sơ của dự án
- Phân loại theo loại (kỹ thuật, pháp lý, tài chính, khác)
- Gán mã và phiên bản ban đầu

#### Bước 2: Theo dõi trạng thái
- Cập nhật trạng thái hồ sơ
- Ghi nhận người phụ trách
- Ghi nhận thời hạn

#### Bước 3: Quản lý phiên bản
- Theo dõi lịch sử thay đổi
- Lưu bằng chứng thay đổi
- Kiểm soát phát hành

#### Bước 4: Báo cáo
- Tổng hợp trạng thái
- Cảnh báo hồ sơ quá hạn
- Đề xuất xử lý

### Đầu ra

\`\`\`markdown
# BÁO CÁO QUẢN LÝ HỒ SƠ DỰ ÁN

**Mã dự án**: [mã]
**Ngày báo cáo**: [YYYY-MM-DD]

## 1. TỔNG QUAN

| Tổng số hồ sơ | Đã hoàn thành | Đang thực hiện | Chưa bắt đầu |
|----------------|---------------|----------------|---------------|
| [số] | [số] | [số] | [số] |

## 2. DANH MỤC HỒ SƠ

| Mã | Tên | Loại | Trạng thái | Người phụ trách | Hạn |
|----|-----|------|------------|-----------------|-----|
\`\`\`

### Trạng thái hồ sơ

| Mã | Trạng thái | Mô tả |
|----|------------|--------|
| CS | Chưa bắt đầu | Chưa có hoạt động |
| DX | Đang xử lý | Đang triển khai |
| CL | Chờ duyệt | Đã xong, chờ phê duyệt |
| HT | Hoàn thành | Đã duyệt, lưu trữ |
| QH | Quá hạn | Vượt thời hạn |

### Giới hạn
- **KHÔNG tự xoá** hồ sơ đã lưu trữ
- **KHÔNG phát hành** hồ sơ chưa được duyệt
- **KHÔNG thay đổi** nội dung hồ sơ đã phát hành - tạo phiên bản mới
