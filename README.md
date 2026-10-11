# Hệ thống trợ lý AI cho IHG

## Giới thiệu

Đây là workspace Claude Code được thiết lập để hỗ trợ điều hành doanh nghiệp IHG trong bốn mảng chính:

1. **Chỉnh lý hồ sơ, tài liệu lưu trữ**
2. **Số hoá tài liệu và xây dựng dữ liệu**
3. **Đo đạc, bản đồ và GIS**
4. **Xây dựng và cập nhật CSDL địa chính**

## Cách bắt đầu

### 1. Tiếp nhận dự án mới

Khi có dự án mới, gõ lệnh:
```
/ihg-project-intake
```

Hoặc cung cấp thông tin cơ bản:
- Tên dự án
- Loại hợp đồng
- Địa phương

### 2. Sử dụng skills

Skills giúp thực hiện các công việc cụ thể. Một số skills quan trọng:

| Skill | Lệnh | Chức năng |
|-------|-------|-----------|
| Kiểm tra quy định | `/ihg-regulatory-check` | Kiểm tra văn bản pháp luật trước khi thực hiện |
| Tiếp nhận dự án | `/ihg-project-intake` | Thu thập thông tin dự án mới |
| Lập kế hoạch | `/ihg-project-planning` | Lập kế hoạch chi tiết |
| Hồ sơ nghiệm thu | `/ihg-acceptance-dossier` | Lập hồ sơ nghiệm thu |
| Hồ sơ thanh toán | `/ihg-payment-dossier` | Lập hồ sơ thanh toán |
| Kiểm tra chất lượng | `/ihg-quality-audit` | Kiểm tra chất lượng đầu ra |
| Bàn giao dự án | `/ihg-handover-package` | Chuẩn bị bộ bàn giao |

### 3. Sử dụng agents

Agents là các chuyên gia được phân công xử lý từng phần công việc:

| Agent | Chức năng |
|-------|-----------|
| **ihg-finance** | Kế toán, dự toán, đối chiếu thanh toán |
| **ihg-admin-legal** | Hành chính, pháp lý, hồ sơ dự án |
| **ihg-archives** | Chỉnh lý hồ sơ lưu trữ |
| **ihg-digitization** | Số hoá tài liệu, OCR |
| **ihg-gis** | Đo đạc, bản đồ, kiểm tra không gian |
| **ihg-cadastral-db** | CSDL địa chính, ánh xạ, ETL |
| **ihg-it** | IT, tự động hoá, script |
| **ihg-qa** | Kiểm tra chất lượng |

## Workflow chuẩn

```
Tiếp nhận dự án
    ↓
Xác minh căn cứ pháp lý
    ↓
Xử lý nghiệp vụ / Xây dựng CSDL
    ↓
Kiểm tra chất lượng
    ↓
Dự thảo nghiệm thu
    ↓
Đối chiếu tài chính
    ↓
Dự thảo thanh toán
    ↓
Trình người có thẩm quyền phê duyệt
```

## Cấu trúc thư mục

```
IHG-ClaudeCode/
├── CLAUDE.md              # Hướng dẫn chi tiết cho AI
├── README.md              # File này - hướng dẫn sử dụng
│
├── .claude/
│   ├── agents/            # Định nghĩa 8 agent
│   └── skills/            # 28 skills cho các công việc cụ thể
│
├── knowledge/
│   ├── company/           # Thông tin IHG
│   └── regulations/       # Sổ đăng ký văn bản pháp luật
│
├── templates/             # 10 biểu mẫu chuẩn
│
├── projects/              # Dữ liệu từng dự án
│   └── [ma-du-an]/
│
├── scripts/               # Công cụ tự động hoá
│
├── tests/                 # Dữ liệu kiểm thử
│
└── reports/               # Báo cáo tổng hợp
```

## Quy tắc quan trọng

### 1. Không suy đoán
- Ghi **"CHƯA XÁC NHẬN"** cho thông tin chưa rõ
- Không tự đặt tỷ lệ thuế, đơn giá, mã EPSG

### 2. Bằng chứng trước kết luận
- Mỗi kết luận phải có căn cứ
- Không tạo chữ ký, con dấu giả
- Không tạo biên bản sự kiện chưa diễn ra

### 3. Kiểm tra quy định
- Sử dụng `/ihg-regulatory-check` trước khi:
  - Lập hồ sơ chính thức
  - Nghiệm thu, thanh toán
  - Chuyển dữ liệu vào hệ thống

### 4. Phân tách trách nhiệm
- Hành chính: hoàn thiện hồ sơ
- Kế toán: kiểm tra số tiền
- QA: xác minh chất lượng
- Người có thẩm quyền: phê duyệt và ký

## Dữ liệu kiểm thử

Thư mục `tests/fixtures/` chứa dữ liệu giả lập để kiểm thử workflow:

- **sample-archive.yml**: Kịch bản kiểm thử hồ sơ
- **sample-digitization.yml**: Kịch bản số hoá
- **sample-cadastral-db.yml**: Kịch bản CSDL địa chính
- **sample-finance.yml**: Kịch bản tài chính
- **sample-regulations.yml**: Kịch bản quy định pháp luật

## Cập nhật quy định

Hệ thống có cơ chế theo dõi văn bản pháp luật mới:

- **Quét hàng ngày** (07:00): Kiểm tra nguồn chính thức
- **Đối soát tuần**: Cập nhật danh mục
- **Kiểm tra trước mốc**: Trước các thời hạn quan trọng

Nguồn ưu tiên:
1. vbpl.vn - CSDL quốc gia văn bản pháp luật
2. vanban.chinhphu.vn - Hệ thống văn bản Chính phủ
3. congbao.chinhphu.vn - Công báo
4. thuvienphapluat.vn - Thư viện pháp luật

## Thông tin liên hệ

- **Người điều hành**: [Cần xác nhận]
- **Ngôn ngữ**: Tiếng Việt
- **Múi giờ**: Asia/Ho_Chi_Minh

## Lịch sử cập nhật

| Phiên bản | Ngày | Thay đổi |
|-----------|------|-----------|
| 2.0 | 2026-01-06 | Bổ sung 20 skills mới với tên tiếng Việt |
| 1.0 | 2026-10-11 | Thiết lập ban đầu |

---

*Hệ thống này hỗ trợ điều hành doanh nghiệp. Mọi quyết định cuối cùng thuộc về người điều hành.*
