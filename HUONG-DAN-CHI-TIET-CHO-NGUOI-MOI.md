# HƯỚNG DẪN TỪNG BƯỚC CHO NGƯỜI MỚI BẮT ĐẦU

## Trước khi bắt đầu

Bạn cần chuẩn bị:
- ✅ Máy tính Windows đã cài Git (nếu chưa có, xem **Bước 0**)
- ✅ Tài khoản GitHub (nếu chưa có, xem **Bước 0.5**)

---

# BƯỚC 0: CÀI ĐẶT GITHUB CLI (NẾU CHƯA CÓ)

## 0.1. Tải GitHub CLI

1. Mở trình duyệt, truy cập: **https://cli.github.com/**
2. Click nút **"Download for Windows"**
3. File sẽ tải về, thường nằm ở folder **Downloads**

## 0.2. Cài đặt

1. Click vào file vừa tải (có tên như `gh_installer.exe`)
2. Nếu có cảnh báo bảo mật, click **"Run anyway"**
3. Cửa sổ cài đặt hiện ra:
   - Click **Next**
   - Click **Install**
   - Đợi安装 xong
   - Click **Finish**

## 0.3. Kiểm tra đã cài đặt thành công

1. Mở **Command Prompt** (nhấn phím `Windows + R`, gõ `cmd`, Enter)
2. Gõ lệnh:
```
gh --version
```
3. Nếu hiện số phiên bản (ví dụ: `gh version 2.50.0`) = Thành công!

---

# BƯỚC 0.5: TẠO TÀI KHOẢN GITHUB (NẾU CHƯA CÓ)

## 0.5.1. Đăng ký

1. Mở trình duyệt, truy cập: **https://github.com/**
2. Click **"Sign up"** (Đăng ký)
3. Điền thông tin:
   - **Email**: Nhập email của bạn
   - **Password**: Nhập mật khẩu (ít nhất 8 ký tự)
   - **Username**: Tên tài khoản (viết liền, không dấu, ví dụ: `anhld123`)
4. Click **"Create account"**
5. Mở email, tìm mã xác minh từ GitHub, nhập vào
6. Hoàn tất các bước còn lại

---

# BƯỚC 1: MỞ THƯ MỤC IHG-CLAUDECODE

## 1.1. Tìm thư mục

1. Mở **File Explorer** (nhấn phím `Windows + E`)
2. Tìm đến ổ **D:** hoặc nơi bạn lưu thư mục **IHG-ClaudeCode**
3. Click đúp vào thư mục **IHG-ClaudeCode**
4. Xem bên trong có các thư mục như: `.claude`, `knowledge`, `templates`, v.v.

## 1.2. Mở Command Prompt trong thư mục đó

**Cách 1: Qua địa chỉ thanh**
1. Click vào thanh địa chỉ trong File Explorer
2. Gõ `cmd` rồi Enter
3. Cửa sổ Command Prompt sẽ mở ra đúng thư mục đó

**Cách 2: Qua menu chuột phải**
1. Trong thư mục IHG-ClaudeCode, giữ phím `Shift` + click chuột phải
2. Chọn **"Open PowerShell window here"** hoặc **"Open command window here"**

---

# BƯỚC 2: KHỞI TẠO GIT REPOSITORY

## 2.1. Gõ lệnh khởi tạo

Trong Command Prompt (đang ở thư mục IHG-ClaudeCode), gõ:

```
git init
```

**Kết quả mong đợi:**
```
Initialized empty Git repository in D:/IHG-ClaudeCode/.git/
```

## 2.2. Cấu hình tên và email (chỉ cần làm 1 lần)

```
git config --global user.name "Tên của bạn"
git config --global user.email "email@example.com"
```

**Thay** `Tên của bạn` = tên bạn (không dấu)
**Thay** `email@example.com` = email bạn đã đăng ký GitHub

---

# BƯỚC 3: THÊM TẤT CẢ FILES VÀO GIT

## 3.1. Thêm files

Gõ lệnh:

```
git add .
```

Lệnh này thêm TẤT CẢ files trong thư mục vào Git.

## 3.2. Kiểm tra trạng thái

```
git status
```

**Kết quả mong đợi:**
```
Changes to be committed:
  (list of files...)
```

Nếu thấy danh sách files = Thành công!

---

# BƯỚC 4: TẠO COMMIT ĐẦU TIÊN

## 4.1. Tạo commit

```
git commit -m "Initial commit - IHG Claude Code Workspace v2.0"
```

**Giải thích:**
- `git commit` = Lưu lại trạng thái hiện tại
- `-m` = Thêm ghi chú (message)
- Trong ngoặc kép = Lời nhắn mô tả commit đó

**Kết quả mong đợi:**
```
[master (root-commit) abc1234] Initial commit - IHG Claude Code Workspace v2.0
 43 files changed, 1234 insertions(+)
```

---

# BƯỚC 5: ĐĂNG NHẬP GITHUB

## 5.1. Gõ lệnh đăng nhập

```
gh auth login
```

## 5.2. Trả lời các câu hỏi

```
What account do you want to log into?
→ GitHub.com

What is your preferred protocol for Git operations?
→ HTTPS

Authenticate Git credentials for GitHub operations?
→ Login with a web browser

First copy your one-time code: XXXX-XXXX
(Press Enter to open github.com in your browser...)
```

## 5.3. Xác nhận trên trình duyệt

1. **Nhấn Enter** - Trình duyệt sẽ mở ra trang GitHub
2. Đăng nhập GitHub nếu chưa đăng
3. Nhập mã **XXXX-XXXX** (mã từ Command Prompt) vào ô trên web
4. Click **Authorize github**
5. Quay lại Command Prompt, nhấn **Enter**

**Kết quả mong đợi:**
```
✓ Authentication complete. gh config -h to see available commands
```

---

# BƯỚC 6: TẠO GITHUB REPOSITORY VÀ PUSH

## 6.1. Tạo repository trên GitHub

```
gh repo create IHG-ClaudeCode --public --source=. --push
```

**Giải thích:**
- `gh repo create` = Tạo repository mới
- `IHG-ClaudeCode` = Tên repository (viết liền, không dấu)
- `--public` = Repository công khai (ai cũng xem được)
- `--source=.` = Lấy code từ thư mục hiện tại
- `--push` = Đẩy code lên GitHub luôn

## 6.2. Nhập thông tin (nếu hỏi)

```
Repository name: IHG-ClaudeCode
Description: Workspace Claude Code cho IHG
Visibility: public
```

Nhấn **Enter** để xác nhận.

**Kết quả mong đợi:**
```
✓ Created repository your-username/IHG-ClaudeCode on GitHub
✓ Pushed to github.com/your-username/IHG-ClaudeCode
```

---

# BƯỚC 7: XEM KẾT QUẢ TRÊN GITHUB

## 7.1. Mở repository

Trong Command Prompt, gõ:

```
gh repo view --web
```

Trình duyệt sẽ mở ra trang GitHub của bạn.

## 7.2. Các thành phần trên trang

```
┌─────────────────────────────────────────────────────────┐
│  IHG-ClaudeCode                                    ⚙️ │
│  your-username / IHG-ClaudeCode                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📁 .claude/           (thư mục agents, skills)     │
│  📁 .github/           (thư mục workflows)           │
│  📁 knowledge/                                         │
│  📁 projects/                                          │
│  📁 scripts/                                           │
│  📁 templates/                                         │
│  📄 CLAUDE.md                                          │
│  📄 README.md                                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  🔵 main ✓                                            │
└─────────────────────────────────────────────────────────┘
```

---

# BƯỚC 8: BẬT GITHUB ACTIONS

## 8.1. Vào Actions tab

1. Trên trang GitHub, click tab **"Actions"** (màu xanh dương)

## 8.2. Enable Actions

1. Click **"I understand my workflows, go ahead and enable them"**
2. Done! Actions đã được bật

---

# BƯỚC 9: XEM WORKFLOWS CHẠY

## 9.1. Vào Actions tab

1. Click tab **"Actions"** ở menu trên cùng

## 9.2. Xem workflow

Bạn sẽ thấy danh sách các workflow runs, ví dụ:

```
┌─────────────────────────────────────────────────────────┐
│  CI / ci.yml                        ✓  Passed     2m  │
│  2 minutes ago                                               │
├─────────────────────────────────────────────────────────┤
│  Deploy Agents / deploy-agents...    ✓  Passed     1m  │
│  1 minute ago                                               │
├─────────────────────────────────────────────────────────┤
│  Regulatory Watch / regulatory...     ⏳  In Progress  │
│  Running...                                                 │
└─────────────────────────────────────────────────────────┘
```

---

# CÁC LỆNH THƯỜNG DÙNG (CHEAT SHEET)

## Khi thay đổi code

```bash
# Xem thay đổi
git status

# Thêm thay đổi vào Git
git add .

# Tạo commit với lời nhắn
git commit -m "Mô tả thay đổi"

# Đẩy lên GitHub
git push
```

## Khi cần cập nhật từ GitHub

```bash
# Cập nhật code mới nhất từ GitHub
git pull
```

---

# XỬ LÝ LỖI THƯỜNG GẶP

## Lỗi: "command not found: git"

**Nguyên nhân:** Chưa cài Git

**Khắc phục:**
1. Tải Git tại: https://git-scm.com/download/win
2. Cài đặt (Next, Next, Finish)
3. Mở lại Command Prompt

---

## Lỗi: "gh: command not found"

**Nguyên nhân:** Chưa cài GitHub CLI

**Khắc phục:**
1. Tải tại: https://cli.github.com/
2. Cài đặt
3. Mở lại Command Prompt

---

## Lỗi: "Authentication failed"

**Nguyên nhân:** Chưa đăng nhập GitHub

**Khắc phục:**
```bash
gh auth logout
gh auth login
```

---

## Lỗi: "repository already exists"

**Nguyên nhân:** Đã tạo repository trước đó

**Khắc phục:**
```bash
# Thử push thay vì tạo mới
git push --set-upstream origin main
```

---

# LỜI NHẮN NHỚ

| Việc cần làm | Lệnh |
|--------------|------|
| Thêm code mới | `git add .` → `git commit -m "..."` → `git push` |
| Xem thay đổi | `git status` |
| Cập nhật code mới | `git pull` |
| Xem repository | `gh repo view --web` |

---

# BẠN ĐÃ HOÀN THÀNH! 🎉

Giờ bạn có thể:
- ✅ Xem code trên GitHub
- ✅ Workflows tự động chạy
- ✅ Backup tự động
- ✅ Regulatory Watch chạy hàng ngày

**Bước tiếp theo:** Khi thay đổi code, chỉ cần:
```
git add .
git commit -m "Mô tả thay đổi"
git push
```

GitHub Actions sẽ tự động chạy!

---

*Cập nhật: 2026-01-06*
