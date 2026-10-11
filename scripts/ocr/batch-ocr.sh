#!/bin/bash
# Script xử lý OCR hàng loạt
# Trạng thái: TEMPLATE - CHƯA TEST

# === CẤU HÌNH ===
INPUT_DIR="${1:-./input}"
OUTPUT_DIR="${2:-./output}"
LANG="${3:-vie}"
LOG_FILE="ocr-batch-$(date +%Y%m%d-%H%M%S).log"

# === KIỂM TRA ===
if [ ! -d "$INPUT_DIR" ]; then
    echo "Lỗi: Thư mục đầu vào không tồn tại"
    exit 1
fi

# Tạo thư mục đầu ra
mkdir -p "$OUTPUT_DIR"

echo "=== BẮT ĐẦU XỬ LÝ OCR ===" | tee "$LOG_FILE"
echo "Thư mục đầu vào: $INPUT_DIR" | tee -a "$LOG_FILE"
echo "Thư mục đầu ra: $OUTPUT_DIR" | tee -a "$LOG_FILE"
echo "Ngôn ngữ: $LANG" | tee -a "$LOG_FILE"
echo "Thời gian bắt đầu: $(date)" | tee -a "$LOG_FILE"

# === ĐẾM FILE ===
IMAGE_COUNT=$(find "$INPUT_DIR" -type f \( -iname "*.jpg" -o -iname "*.png" -o -iname "*.tif" \) | wc -l)
echo "Số file ảnh cần xử lý: $IMAGE_COUNT" | tee -a "$LOG_FILE"

# === XỬ LÝ ===
PROCESSED=0
SUCCESS=0
FAILED=0

find "$INPUT_DIR" -type f \( -iname "*.jpg" -o -iname "*.png" -o -iname "*.tif" \) | while read -r FILE; do
    ((PROCESSED++))
    FILENAME=$(basename "$FILE")
    BASENAME="${FILENAME%.*}"
    
    echo "[$PROCESSED/$IMAGE_COUNT] Đang xử lý: $FILENAME"
    
    # Chạy OCR (cần cài tesseract)
    # tesseract "$FILE" "$OUTPUT_DIR/$BASENAME" -l "$LANG" --oem 1 --psm 1 2>/dev/null
    
    if [ $? -eq 0 ]; then
        ((SUCCESS++))
        echo "  ✓ Thành công" | tee -a "$LOG_FILE"
    else
        ((FAILED++))
        echo "  ✗ Thất bại" | tee -a "$LOG_FILE"
    fi
done

# === BÁO CÁO ===
echo "" | tee -a "$LOG_FILE"
echo "=== KẾT QUẢ ===" | tee -a "$LOG_FILE"
echo "Tổng file: $IMAGE_COUNT" | tee -a "$LOG_FILE"
echo "Thành công: $SUCCESS" | tee -a "$LOG_FILE"
echo "Thất bại: $FAILED" | tee -a "$LOG_FILE"
echo "Thời gian kết thúc: $(date)" | tee -a "$LOG_FILE"

echo "Nhật ký: $LOG_FILE"
