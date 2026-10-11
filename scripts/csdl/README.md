# Thư mục Scripts CSDL

## Mục đích
Chứa các script xử lý và kiểm tra CSDL địa chính.

## Scripts có sẵn

| Script | Mô tả | Trạng thái |
|--------|--------|------------|
| check-duplicate.py | Kiểm tra bản ghi trùng | Template |
| export-csv.py | Xuất dữ liệu ra CSV | Template |
| import-csv.py | Nhập dữ liệu từ CSV | Template |
| check-reference.py | Kiểm tra tham chiếu | Template |

## Yêu cầu
- Python 3.8+
- Thư viện: psycopg2 (PostgreSQL), pymssql (SQL Server)

## Hướng dẫn sử dụng
\`\`\`bash
# Kiểm tra bản ghi trùng
python check-duplicate.py --db connection.json --table thua_dat

# Xuất CSV
python export-csv.py --db connection.json --query "SELECT * FROM thua_dat"

# Nhập CSV
python import-csv.py --db connection.json --table thua_dat --file data.csv

# Kiểm tra tham chiếu
python check-reference.py --db connection.json --table thua_dat
\`\`\`

## Lưu ý
- **CHƯA TEST** - Cần kiểm tra trên máy thực tế
- Cần tạo file cấu hình kết nối trước khi sử dụng
- Không lưu mật khẩu trong script
