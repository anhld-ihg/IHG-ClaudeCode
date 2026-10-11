#!/bin/bash
# Script chuyển đổi hệ quy chiếu
# Trạng thái: TEMPLATE - CHƯA TEST

# === CẤU HÌNH ===
INPUT="$1"
OUTPUT="$2"
SOURCE_EPSG="$3"
TARGET_EPSG="$4"

if [ -z "$INPUT" ] || [ -z "$OUTPUT" ] || [ -z "$SOURCE_EPSG" ] || [ -z "$TARGET_EPSG" ]; then
    echo "Sử dụng: $0 <input.shp> <output.shp> <source_epsg> <target_epsg>"
    echo "Ví dụ: $0 input.shp output.shp EPSG:4326 EPSG:3857"
    exit 1
fi

echo "=== CHUYỂN ĐỔI HỆ QUY CHIẾU ==="
echo "Đầu vào: $INPUT"
echo "Đầu ra: $OUTPUT"
echo "Từ: $SOURCE_EPSG → $TARGET_EPSG"

# Kiểm tra ogr2ogr
if ! command -v ogr2ogr &> /dev/null; then
    echo "Lỗi: ogr2ogr không tìm thấy. Cần cài GDAL."
    exit 1
fi

# Chuyển đổi
ogr2ogr -t_srs "$TARGET_EPSG" -s_srs "$SOURCE_EPSG" "$OUTPUT" "$INPUT"

if [ $? -eq 0 ]; then
    echo "✓ Chuyển đổi thành công"
else
    echo "✗ Chuyển đổi thất bại"
    exit 1
fi
