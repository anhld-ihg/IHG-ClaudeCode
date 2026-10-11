---
name: ihg-metadata-validation
description: Kiểm tra metadata - Xác minh thông tin trích xuất từ OCR
---

# Skill: ihg-metadata-validation

## Kiểm tra metadata

### Mục đích
Xác minh thông tin trích xuất từ OCR đảm bảo đầy đủ và chính xác theo yêu cầu.

### Điều kiện kích hoạt
- Sau khi chạy OCR từ ihg-digitization-pipeline
- Khi cần kiểm tra dữ liệu trích xuất
- Khi cần xác nhận trước khi lưu

### Đầu vào
- Kết quả OCR từ ihg-digitization-pipeline
- Schema metadata yêu cầu
- Danh sách trường bắt buộc

### Các bước thực hiện

#### Bước 1: Kiểm tra trường bắt buộc
- Kiểm tra từng trường bắt buộc
- Ghi nhận trường thiếu
- Đánh giá mức độ thiếu

#### Bước 2: Kiểm tra định dạng
- Kiểm tra định dạng ngày tháng
- Kiểm tra định dạng số
- Kiểm tra định dạng mã

#### Bước 3: Kiểm tra logic
- Kiểm tra mối liên hệ giữa các trường
- Phát hiện dữ liệu bất thường
- Kiểm tra tính nhất quán

#### Bước 4: Kiểm tra độ tin cậy
- Đánh giá điểm tin cậy OCR
- Xác định phần cần kiểm tra thủ công
- Phân loại theo mức độ tin cậy

### Đầu ra

\`\`\`markdown
# BÁO CÁO KIỂM TRA METADATA

**Ngày**: [ngày]
**Lô**: [mã lô]

## 1. TỔNG QUAN

| Trường | Giá trị |
|---------|---------|
| Tổng bản ghi | [số] |
| Đạt yêu cầu | [số] |
| Cần sửa | [số] |
| Cần kiểm tra thủ công | [số] |

## 2. KIỂM TRA TRƯỜNG BẮT BUỘC

| Trường | Số thiếu | Tỷ lệ | Mức độ |
|--------|----------|-------|--------|
| [Tên trường] | [số] | [%] | Cao/Trung bình/Thấp |

## 3. LỖI ĐỊNH DẠNG

| STT | Bản ghi | Trường | Giá trị | Lỗi |
|-----|---------|--------|---------|------|

## 4. LỖI LOGIC

| STT | Bản ghi | Mô tả lỗi |
|-----|---------|------------|

## 5. ĐỘ TIN CẬY OCR

| Mức độ | Số bản ghi | Tỷ lệ |
|---------|------------|-------|
| Cao (>90%) | [số] | [%] |
| Trung bình (70-90%) | [số] | [%] |
| Thấp (<70%) | [số] | [%] |

## 6. CẦN KIỂM TRA THỦ CÔNG

| STT | Bản ghi | Trường | Lý do |
|-----|---------|--------|-------|
\`\`\`

### Giới hạn
- **KHÔNG tự sửa** dữ liệu OCR
- **KHÔNG tự đặt ngưỡng** độ tin cậy
- Chỉ ghi nhận và đề xuất kiểm tra thủ công
