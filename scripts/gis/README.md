# Thư mục Scripts GIS

## Mục đích
Chứa các script xử lý dữ liệu GIS hàng loạt.

## Scripts có sẵn

| Script | Mô tả | Trạng thái |
|--------|--------|------------|
| check-geometry.py | Kiểm tra lỗi hình học | Template |
| reproject.sh | Chuyển đổi hệ quy chiếu | Template |
| export-csv.py | Xuất dữ liệu GIS ra CSV | Template |

## Yêu cầu
- Python 3.8+
- GDAL/OGR đã cài đặt
- Hoặc QGIS Python đã cài đặt

## Hướng dẫn sử dụng
\`\`\`bash
# Kiểm tra hình học
python check-geometry.py input.shp

# Chuyển đổi hệ quy chiếu
./reproject.sh input.shp output.shp EPSG:4326 EPSG:3857

# Xuất CSV
python export-csv.py input.shp output.csv
\`\`\`

## Lưu ý
- **CHƯA TEST** - Cần kiểm tra trên máy thực tế
- Cần cài GDAL/OGR trước khi sử dụng
