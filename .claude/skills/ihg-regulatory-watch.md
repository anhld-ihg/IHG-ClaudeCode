---
name: ihg-regulatory-watch
description: Theo dõi quy định - Giám sát thay đổi văn bản pháp luật
---

# Skill: ihg-regulatory-watch

## Theo dõi quy định

### Mục đích
Giám sát thay đổi văn bản pháp luật liên quan đến hoạt động của IHG.

### Điều kiện kích hoạt
- Kiểm tra định kỳ (hàng ngày/tuần)
- Khi có thông báo từ cơ quan
- Khi phát hiện văn bản mới từ nguồn

### Nguồn theo dõi

| Nguồn | URL | Tần suất |
|-------|-----|----------|
| CSDL quốc gia | https://vbpl.vn/ | Hàng ngày |
| Văn bản Chính phủ | https://vanban.chinhphu.vn/ | Hàng ngày |
| Công báo | https://congbao.chinhphu.vn/ | Hàng ngày |
| Bộ TN&MT | https://mt.gov.vn/ | Tuần |

### Các bước thực hiện

#### Bước 1: Kiểm tra nguồn
- Truy cập nguồn theo lịch
- Kiểm tra văn bản mới ban hành
- Kiểm tra văn bản sửa đổi/thay thế

#### Bước 2: Lọc liên quan
- Xác định văn bản liên quan đến:
  - Đất đai, đo đạc, bản đồ
  - Hồ sơ, lưu trữ
  - Kế toán, tài chính
  - Hợp đồng, nghiệm thu

#### Bước 3: Ghi nhận thay đổi
- Số hiệu, tên văn bản
- Ngày ban hành, ngày hiệu lực
- Loại thay đổi (ban hành mới/sửa đổi/thay thế/bãi bỏ)

#### Bước 4: Cập nhật sổ theo dõi
- Cập nhật danh sách văn bản
- Ghi lại lịch sử thay đổi
- Đánh dấu cần đánh giá tác động

### Đầu ra

\`\`\`markdown
# BÁO CÁO THEO DÕI QUY ĐỊNH

**Ngày kiểm tra**: [YYYY-MM-DD]

## 1. TỔNG QUAN

| Loại | Số lượng |
|------|----------|
| Văn bản mới | [số] |
| Văn bản sửa đổi | [số] |

## 2. VĂN BẢN MỚI LIÊN QUAN

| STT | Số hiệu | Tên văn bản | Ngày BH | Nguồn |
|-----|---------|-------------|---------|-------|

## 3. CẦN ĐÁNH GIÁ TÁC ĐỘNG

| STT | Văn bản | Mức độ ảnh hưởng |
|-----|---------|-------------------|
\`\`\`

### Lịch theo dõi (đề xuất)

| Thời gian | Hoạt động |
|-----------|-----------|
| 07:00 hàng ngày | Quét nguồn chính |
| Thứ 2 hàng tuần | Đối soát danh mục |
| Trước mốc quan trọng | Kiểm tra tập trung |

### Giới hạn
- **KHÔNG tự đưa ra kết luận** về ảnh hưởng pháp lý
- **KHÔNG gửi thông báo** ra ngoài khi chưa được phép
