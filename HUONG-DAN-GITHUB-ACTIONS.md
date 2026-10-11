# HƯỚNG DẪN CHI TIẾT: TÍCH HỢP GITHUB ACTIONS

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Cài đặt ban đầu](#2-cài-đặt-ban-đầu)
3. [Các workflows](#3-các-workflows)
4. [Sử dụng thực tế](#4-sử-dụng-thực-tế)
5. [Tùy chỉnh](#5-tùy-chỉnh)
6. [Xem kết quả](#6-xem-kết-quả)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Tổng quan

### 1.1. GitHub Actions là gì?

GitHub Actions là tính năng CI/CD miễn phí của GitHub, cho phép:
- Tự động chạy tests, lint, build khi có thay đổi code
- Deploy tự động khi code thay đổi
- Chạy các tác vụ theo lịch (như kiểm tra quy định hàng ngày)
- Backup tự động

### 1.2. Các workflows đã cài đặt

| Workflow | File | Chạy khi nào | Làm gì |
|----------|------|---------------|---------|
| **CI** | `ci.yml` | Push/PR | Lint, test, backup |
| **Deploy Agents** | `deploy-agents.yml` | Thay đổi agents/skills | Validate & sync |
| **Regulatory Watch** | `regulatory-watch.yml` | 07:00 VN hàng ngày | Kiểm tra quy định |
| **Project Automation** | `project-automation.yml` | PR vào projects/ | Validate dự án |

---

## 2. Cài đặt ban đầu

### Bước 1: Tạo GitHub Repository

**Cách 1: Qua Command Line (GitHub CLI)**

```bash
# Cài đặt GitHub CLI (nếu chưa có)
# Windows: winget install GitHub.cli
# Mac: brew install gh

# Đăng nhập
gh auth login

# Di chuyển vào thư mục workspace
cd D:\IHG-ClaudeCode

# Khởi tạo Git repo
git init

# Thêm tất cả files
git add .

# Tạo commit đầu tiên
git commit -m "Initial commit - IHG Claude Code Workspace v2.0"

# Tạo GitHub repo và push
gh repo create IHG-ClaudeCode --public --source=. --push
```

**Cách 2: Qua GitHub Web**

1. Truy cập: https://github.com/new
2. Điền thông tin:
   - Repository name: `IHG-ClaudeCode`
   - Description: `Workspace Claude Code cho IHG`
   - Public/Private: Tùy chọn
3. Click "Create repository"
4. Làm theo hướng dẫn:
   ```bash
   cd D:\IHG-ClaudeCode
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR-USERNAME/IHG-ClaudeCode.git
   git branch -M main
   git push -u origin main
   ```

### Bước 2: Enable GitHub Actions

1. Truy cập repository vừa tạo
2. Vào tab **Actions**
3. Click **"I understand my workflows, go ahead and enable them"**

### Bước 3: Kiểm tra

Sau khi push code, vào **Actions** tab để xem workflows chạy.

---

## 3. Các workflows

### 3.1. CI Pipeline (`ci.yml`)

**Chạy tự động khi:**
- Push lên branch `main` hoặc `develop`
- Tạo Pull Request

**Các bước thực hiện:**

```
1. Checkout code
2. Markdown lint - Kiểm tra syntax markdown
3. YAML lint - Kiểm tra syntax YAML  
4. Run tests - Chạy test fixtures
5. Backup (chỉ trên main)
```

**Ví dụ output:**
```
✓ Markdown lint passed
✓ YAML lint passed
✓ Tests completed
✓ Backup created: backup-20260106-120000.tar.gz
```

### 3.2. Deploy Agents (`deploy-agents.yml`)

**Chạy tự động khi:**
- Có file thay đổi trong `.claude/agents/`
- Có file thay đổi trong `.claude/skills/`
- Click "Run workflow" thủ công

**Các bước thực hiện:**

```
1. Validate Agents - Kiểm tra mỗi agent có đủ:
   - name field
   - description
   - các trường bắt buộc

2. Validate Skills - Kiểm tra mỗi skill có đủ:
   - name field
   - description
   - đầu vào/đầu ra

3. Sync to Production - Sync lên production
```

### 3.3. Regulatory Watch (`regulatory-watch.yml`)

**Chạy tự động khi:**
- 07:00 giờ Việt Nam hàng ngày (00:00 UTC)
- Click "Run workflow" thủ công

**Các bước thực hiện:**

```
1. Checkout code
2. Kiểm tra vbpl.vn - CSDL quốc gia văn bản pháp luật
3. Kiểm tra vanban.chinhphu.vn - Văn bản Chính phủ
4. Kiểm tra congbao.chinhphu.vn - Công báo
5. So sánh với sổ đăng ký hiện tại
6. Nếu có thay đổi → Tạo GitHub Issue
```

**Tự động tạo Issue như thế này:**

```markdown
## Quy định mới cần xem xét

**Ngày phát hiện:** 2026-01-06
**Nguồn:** vanban.chinhphu.vn

### Thay đổi:
- [Mô tả thay đổi]

### Dự án ảnh hưởng:
- [Danh sách dự án]

### Việc cần làm:
- [ ] Xác minh hiệu lực
- [ ] Đánh giá tác động
- [ ] Cập nhật sổ đăng ký
```

### 3.4. Project Automation (`project-automation.yml`)

**Chạy tự động khi:**
- Tạo PR với thay đổi trong `projects/`
- Push lên `projects/` trên main
- Click "Run workflow" thủ công

**Các bước thực hiện:**

```
1. Validate Project Structure
   - Kiểm tra thư mục project tồn tại
   - Kiểm tra các file bắt buộc:
     * phiếu-tiếp-nhận.md
     * bang-can-cu-ap-dung.md
     * danh-muc-ho-so.md

2. Run QA Checks
   - Kiểm tra YAML/JSON syntax
   - Kiểm tra encoding

3. Notify
   - Tạo summary report
```

---

## 4. Sử dụng thực tế

### 4.1. Thêm agent mới

```bash
# 1. Tạo file agent mới
# File: .claude/agents/ihg-new-agent.md

# 2. Git add & commit
git add .claude/agents/ihg-new-agent.md
git commit -m "feat: Add new agent ihg-new-agent"

# 3. Push lên GitHub
git push

# 4. GitHub Actions sẽ tự:
#    - Validate agent file
#    - Chạy CI tests
#    - Sync lên production
```

### 4.2. Thêm skill mới

```bash
# 1. Tạo file skill
# File: .claude/skills/ihg-new-skill.md

# 2. Commit & push
git add .claude/skills/ihg-new-skill.md
git commit -m "feat: Add new skill ihg-new-skill"
git push

# 3. Kết quả trên GitHub:
#    ✓ Validate skill structure
#    ✓ Sync completed
```

### 4.3. Tạo dự án mới

```bash
# 1. Tạo thư mục dự án
mkdir projects/DU-AN-001

# 2. Tạo các file cần thiết
echo "# Phiếu tiếp nhận" > projects/DU-AN-001/phiếu-tiếp-nhận.md
echo "# Căn cứ áp dụng" > projects/DU-AN-001/bang-can-cu-ap-dung.md
echo "# Danh mục hồ sơ" > projects/DU-AN-001/danh-muc-ho-so.md

# 3. Commit & push
git add projects/DU-AN-001/
git commit -m "feat: Add new project DU-AN-001"
git push

# 4. GitHub Actions sẽ:
#    - Validate project structure
#    - Run QA checks
```

### 4.4. Xem báo cáo Regulatory Watch

```bash
# Kết quả hàng ngày sẽ tự động xuất hiện
# GitHub sẽ tạo Issue nếu có quy định mới
```

---

## 5. Tùy chỉnh

### 5.1. Thay đổi giờ Regulatory Watch

Mở file `.github/workflows/regulatory-watch.yml`:

```yaml
on:
  schedule:
    # Thay đổi cron expression
    # Ví dụ: 08:00 VN = 01:00 UTC
    - cron: '0 1 * * *'  # 01:00 UTC = 08:00 VN
    
    # Hoặc 12:00 VN = 05:00 UTC  
    - cron: '0 5 * * *'    # 05:00 UTC = 12:00 VN
```

**Bảng chuyển đổi:**

| Giờ VN | Cron (UTC) |
|--------|------------|
| 07:00 | `0 0 * * *` |
| 08:00 | `0 1 * * *` |
| 12:00 | `0 5 * * *` |
| 18:00 | `0 11 * * *` |

### 5.2. Thêm nguồn pháp luật

Mở file `.github/workflows/regulatory-watch.yml`, thêm trong phần `steps`:

```yaml
- name: Check Custom Source
  run: |
    echo "=== Checking Custom Source ==="
    # Thêm logic kiểm tra nguồn của bạn
    curl -s "https://custom-source.vn/api/updates" || true
```

### 5.3. Thêm Secrets (cho production sync)

1. Vào GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Thêm:

| Name | Value | Mô tả |
|------|-------|--------|
| `PROD_SYNC_KEY` | `your-api-key` | Key để sync lên production |
| `WEBHOOK_URL` | `https://example.com/webhook` | URL để thông báo |

### 5.4. Thêm branch protection

1. Vào **Settings** → **Branches** → **Add rule**
2. Rule name: `main`
3. Bật:
   - ✓ Require pull request before merging
   - ✓ Require status checks to pass before merging
   - ✓ Require branches to be up to date before merge

---

## 6. Xem kết quả

### 6.1. Tab Actions

Truy cập: `https://github.com/YOUR-USERNAME/IHG-ClaudeCode/actions`

**Xem chi tiết workflow run:**
1. Click vào workflow name
2. Click vào run cụ thể
3. Expand từng job để xem logs

### 6.2. Notifications

**Cài đặt thông báo:**

1. Vào **Settings** → **Notifications** → **Actions**
2. Chọn:
   - Email notifications: Bật cho failures
   - GitHub notifications: Tùy chọn

### 6.3. Badge Status

Thêm badge vào README:

```markdown
[![CI](https://github.com/YOUR-USERNAME/IHG-ClaudeCode/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR-USERNAME/IHG-ClaudeCode/actions/workflows/ci.yml)
```

---

## 7. Troubleshooting

### Lỗi: "Workflow not found"

**Nguyên nhân:** Chưa enable Actions

**Khắc phục:**
1. Vào repo → **Actions** tab
2. Click **"I understand my workflows, go ahead and enable them"**

---

### Lỗi: "Permission denied"

**Nguyên nhân:** Không đủ quyền

**Khắc phục:**
1. Vào **Settings** → **Actions** → **General**
2. Kiểm tra **Workflow permissions**
3. Chọn: "Read and write permissions"

---

### Lỗi: Markdown lint fail

**Nguyên nhân:** Syntax markdown không đúng

**Khắc phục:**
```bash
# Cài đặt markdownlint locally
npm install -g markdownlint-cli

# Chạy kiểm tra
markdownlint .claude/**/*.md

# Sửa lỗi theo hướng dẫn trong output
```

---

### Lỗi: Workflow không chạy tự động

**Nguyên nhân thường gặp:**
1. File nằm sai vị trí
2. Syntax YAML không đúng
3. Branch không match trigger

**Kiểm tra:**
```bash
# Verify file location
ls -la .github/workflows/

# Verify YAML syntax
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
```

---

## Quick Reference

### Các lệnh Git thường dùng

```bash
# Xem trạng thái
git status

# Xem thay đổi
git diff

# Thêm & commit
git add .
git commit -m "message"

# Push
git push

# Xem branches
git branch -a

# Chuyển branch
git checkout develop
```

### Kiểm tra Workflow

```bash
# Xem workflow runs
gh run list

# Xem run cụ thể
gh run view RUN_ID

# Chạy workflow thủ công
gh workflow run ci.yml
```

---

## Liên hệ hỗ trợ

Nếu có vấn đề:
1. Kiểm tra logs trong Actions tab
2. Xem troubleshooting ở trên
3. Tạo Issue trên GitHub repo

---

*Cập nhật: 2026-01-06*
