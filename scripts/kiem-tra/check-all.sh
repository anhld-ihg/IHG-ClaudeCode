#!/bin/bash
# Script chạy tất cả kiểm tra
# Trạng thái: TEMPLATE - CHƯA TEST

PROJECT_DIR="${1:-.}"

echo "=== CHẠY KIỂM TRA CHẤT LƯỢNG ==="
echo "Thư mục dự án: $PROJECT_DIR"
echo "Thời gian: $(date)"
echo ""

REPORT_FILE="quality-check-$(date +%Y%m%d-%H%M%S).txt"

# === KIỂM TRA HỒ SƠ ===
echo "1. Kiểm tra hồ sơ..."
if [ -f "$PROJECT_DIR/danh-muc-ho-so.md" ]; then
    echo "   ✓ Có danh mục hồ sơ"
else
    echo "   ✗ Thiếu danh mục hồ sơ"
fi

# === KIỂM TRA CĂN CỨ ===
echo "2. Kiểm tra căn cứ pháp lý..."
if [ -f "$PROJECT_DIR/bang-can-cu-ap-dung.md" ]; then
    LINES=$(wc -l < "$PROJECT_DIR/bang-can-cu-ap-dung.md")
    echo "   ✓ Có bảng căn cứ ($LINES dòng)"
else
    echo "   ✗ Thiếu bảng căn cứ"
fi

# === KIỂM TRA DỮ LIỆU ===
echo "3. Kiểm tra dữ liệu..."
if [ -d "$PROJECT_DIR/du-lieu-goc" ]; then
    FILE_COUNT=$(find "$PROJECT_DIR/du-lieu-goc" -type f | wc -l)
    echo "   ✓ Có dữ liệu gốc ($FILE_COUNT files)"
else
    echo "   ⚠ Chưa có thư mục dữ liệu gốc"
fi

# === TỔNG HỢP ===
echo ""
echo "=== KẾT QUẢ ==="
echo "Nhật ký: $REPORT_FILE"
