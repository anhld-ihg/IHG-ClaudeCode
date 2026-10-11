---
name: ihg-project-costing
description: Dự toán dự án - Lập dự toán từ khối lượng, đơn giá, định mức
---

# Skill: ihg-project-costing

## Dự toán dự án

### Mục đích
Lập dự toán chi phí dự án dựa trên khối lượng, đơn giá và định mức đã được xác nhận.

### Điều kiện kích hoạt
- Khi tiếp nhận dự án mới
- Khi có thay đổi khối lượng
- Khi cần cập nhật dự toán

### Đầu vào bắt buộc
- Danh sách hạng mục công việc
- Khối lượng từng hạng mục
- Đơn giá (có căn cứ)
- Định mức (nếu có)

### Đầu vào cần xác nhận
- Giá trị hợp đồng gốc
- Tỷ lệ tạm ứng, giữ lại
- Thuế suất áp dụng
- Chi phí khác (vận chuyển, bảo hiểm...)

### Các bước thực hiện

#### Bước 1: Xác nhận đơn giá và định mức
- Kiểm tra đơn giá có căn cứ
- Kiểm tra định mức được duyệt
- Ghi rõ nguồn đơn giá/định mức

#### Bước 2: Tính chi phí từng hạng mục
- Chi phí = Khối lượng × Đơn giá
- Tách rõ các đơn vị (không trộn)

#### Bước 3: Tổng hợp chi phí
- Chi phí nhân công
- Chi phí thiết bị
- Chi phí vật tư
- Chi phí nhà thầu phụ
- Chi phí khác

#### Bước 4: Tính giá trị dự toán
- Cộng chi phí
- Cộng thuế
- Trừ tạm ứng (nếu có)
- Cộng giữ lại (nếu có)

### Đầu ra

\`\`\`markdown
# BẢNG DỰ TOÁN DỰ ÁN

**Mã dự án**: [mã]
**Ngày lập**: [ngày]

## 1. THÔNG TIN CHUNG

| Trường | Giá trị | Căn cứ |
|---------|---------|--------|

## 2. CHI PHÍ THEO HẠNG MỤC

| STT | Hạng mục | Đơn vị | Khối lượng | Đơn giá | Thành tiền | Căn cứ ĐG |
|-----|-----------|---------|------------|----------|------------|------------|

**Tổng chi phí**: [số]

## 3. TỔNG HỢP CHI PHÍ

| Loại chi phí | Thành tiền |
|---------------|------------|
| Nhân công | [số] |
| Thiết bị | [số] |
| Vật tư | [số] |
| Nhà thầu phụ | [số] |
| Chi phí khác | [số] |
| **Tổng cộng** | [số] |

## 4. GIÁ TRỊ DỰ TOÁN

| Khoản mục | Thành tiền |
|------------|------------|
| Tổng chi phí | [số] |
| Thuế VAT | [số] |
| Tạm ứng đã nhận | [số] |
| Giữ lại | [số] |
| **Giá trị dự toán** | [số] |

## 5. SO SÁNH VỚI HỢP ĐỒNG

| Trường | Hợp đồng | Dự toán | Chênh lệch |
|---------|-----------|---------|------------|
| Giá trị | [số] | [số] | [số] |
| Chênh lệch (%) | | | [%] |
\`\`\`

### Giới hạn nghiêm ngặt
- **KHÔNG tự đặt đơn giá** - phải có căn cứ
- **KHÔNG tự đặt định mức** - phải có căn cứ
- **KHÔNG trộn đơn vị** (trang/tờ/hồ sơ/thửa/mét)
- **KHÔNG ghi sổ chính thức** - chỉ lập bảng trình duyệt
