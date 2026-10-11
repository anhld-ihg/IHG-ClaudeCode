# GitHub Actions cho IHG Workspace

## Giới thiệu

Workspace IHG sử dụng GitHub Actions để tự động hóa các quy trình CI/CD.

## Workflows

### 1. CI - Continuous Integration
- **File**: `.github/workflows/ci.yml`
- **Chạy**: Khi push lên main/develop hoặc tạo PR
- **Chức năng**:
  - Markdown lint
  - YAML lint
  - Chạy test fixtures
  - Backup tự động

### 2. Deploy Agents & Skills
- **File**: `.github/workflows/deploy-agents.yml`
- **Chạy**: Khi có thay đổi trong `.claude/agents/` hoặc `.claude/skills/`
- **Chức năng**:
  - Validate agents và skills
  - Sync lên production

### 3. Regulatory Watch
- **File**: `.github/workflows/regulatory-watch.yml`
- **Chạy**: Hàng ngày lúc 00:00 UTC (07:00 VN)
- **Chức năng**:
  - Kiểm tra nguồn pháp luật
  - Tạo issue khi có thay đổi

### 4. Project Workflow Automation
- **File**: `.github/workflows/project-automation.yml`
- **Chạy**: Khi có PR mới với thay đổi trong `projects/`
- **Chức năng**:
  - Validate cấu trúc dự án
  - Chạy QA checks

## Cài đặt

### 1. Tạo GitHub repository
```bash
git init
git add .
git commit -m "Initial commit"
gh repo create IHG-ClaudeCode --public --push
```

### 2. Enable GitHub Actions
Repository settings → Actions → Enable

### 3. (Tùy chọn) Thêm Secrets
- `PROD_SYNC_KEY`: API key để sync lên production
- `WEBHOOK_URL`: URL để thông báo

## Lịch chạy

| Workflow | Thời gian | Mục đích |
|----------|-----------|-----------|
| CI | Mỗi push/PR | Kiểm tra chất lượng code |
| Regulatory Watch | 00:00 UTC hàng ngày | Theo dõi quy định |
| Deploy | Khi có thay đổi agents/skills | Deploy tự động |
| Project | Khi có PR trong projects/ | Validate dự án |

## Tùy chỉnh

### Thay đổi thời gian regulatory watch
```yaml
schedule:
  - cron: '0 0 * * *'  # 00:00 UTC = 07:00 VN
```

### Thêm nguồn pháp luật
```yaml
- name: Check custom source
  run: |
    curl -s "https://custom-source.vn/api/updates"
```

## Troubleshooting

### Workflow không chạy
- Kiểm tra Actions permissions trong Settings
- Kiểm tra workflow syntax

### Lỗi validation
- Xem logs trong Actions tab
- Chạy local: `markdownlint .claude/**/*.md`
