# Thư mục Scripts OCR

## Mục đích
Chứa các script xử lý hàng loạt cho công việc số hóa tài liệu.

## Scripts có sẵn

| Script | Mô tả | Trạng thái |
|--------|--------|------------|
| batch-ocr.sh | Xử lý OCR hàng loạt | Template |
| validate-metadata.py | Kiểm tra metadata sau OCR | Template |

## Hướng dẫn sử dụng

### Yêu cầu
- Python 3.8+
- Thư viện: pytesseract, pillow (cho Python)
- Hoặc: Tesseract OCR đã cài đặt (cho bash)

### Cấu hình
1. Kiểm tra đường dẫn đến Tesseract
2. Cấu hình thư mục đầu vào/đầu ra
3. Thiết lập ngôn ngữ OCR (vie/eng)

### Ví dụ sử dụng
\`\`\`bash
# Chạy OCR trên thư mục
./batch-ocr.sh /path/to/input /path/to/output

# Kiểm tra metadata
python validate-metadata.py --input /path/to/metadata.csv
\`\`\`

## Lưu ý
- **CHƯA TEST** - Cần kiểm tra trên máy thực tế
- **Cần cấu hình** đường dẫn và tham số trước khi sử dụng
- **Sao lưu** dữ liệu gốc trước khi xử lý
