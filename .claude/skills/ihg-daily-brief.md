---
name: ihg-daily-brief
description: Báo cáo hàng ngày - Tổng hợp tiến độ, vấn đề, công việc cần xử lý
---

# Skill: ihg-daily-brief

## Báo cáo hàng ngày

### Mục đích
Tổng hợp tình hình các dự án, vấn đề cần xử lý và công việc sắp đến hạn.

### Đầu vào
- Danh sách dự án đang thực hiện
- Trạng thái các nhiệm vụ
- Các vấn đề phát sinh

### Đầu ra

\`\`\`markdown
# BÁO CÁO HÀNG NGÀY

**Ngày**: [YYYY-MM-DD]
**Người tổng hợp**: [tên]

## 1. TỔNG QUAN

| Dự án | Tiến độ | Trạng thái |
|-------|---------|------------|

## 2. TIẾN ĐỘ THEO DỰ ÁN

### [Mã dự án]
- **Hôm nay**: [công việc đã làm]
- **Ngày mai**: [công việc dự kiến]
- **Vấn đề**: [nếu có]
- **Hạn**: [ngày]

## 3. VẤN ĐỀ CẦN XỬ LÝ

| STT | Vấn đề | Dự án | Mức độ | Người phụ trách |
|-----|--------|-------|--------|------------------|

## 4. CÔNG VIỆC SẮP ĐẾN HẠN

| STT | Công việc | Dự án | Hạn | Ưu tiên |
|-----|-----------|-------|------|----------|

## 5. QUY ĐỊNH MỚI ẢNH HƯỞNG

| STT | Văn bản | Dự án ảnh hưởng | Việc cần làm |
|-----|---------|-----------------|--------------|
\`\`\`

### Quy trình
1. Thu thập trạng thái từ các dự án
2. Tổng hợp vấn đề và hạn
3. Kiểm tra quy định mới
4. Tạo báo cáo
5. Gửi (nếu được cấp quyền)

### Lưu ý
- Chỉ tổng hợp, không tự đưa ra quyết định
- Đánh dấu "CHƯA XÁC NHẬN" cho thông tin thiếu
- Không gửi ra ngoài nếu chưa được phép
