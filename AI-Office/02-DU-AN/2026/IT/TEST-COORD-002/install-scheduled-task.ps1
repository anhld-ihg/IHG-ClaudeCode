# IHG Test Scheduled Task Installer
#
# Muc dich: dang ky 1 Windows Scheduled Task chay run-tests.bat moi ngay 06:00.
# Ket qua: state\test-results-YYYYMMDD.log duoc ghi tu dong, khong can phien Claude Code.
#
# SU DUNG (mot lan):
#   1. Click chuot phai vao file nay -> "Run with PowerShell"
#   2. Hoac mo PowerShell as Admin, chay: .\install-scheduled-task.ps1
#
# LUU Y:
#   - Can quyen admin de dang ky Scheduled Task.
#   - Python phai co trong PATH (hoac sua $pythonPath ben duoi).
#   - Nen chay thu cong run-tests.bat 1 lan truoc de chac chan moi thu OK.

# --- Cau hinh (sua neu can) ---
$taskName = "IHG-PILOT-002-Daily-Test"
$scriptDir = $PSScriptRoot
$batchFile = Join-Path $scriptDir "run-tests.bat"
$runTime = "06:00"  # chay moi ngay luc 06:00

# --- Kiem tra batch file co ton tai ---
if (-not (Test-Path $batchFile)) {
    Write-Error "Khong tim thay: $batchFile"
    exit 1
}

# --- Kiem tra python ---
$python = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $python) {
    Write-Warning "Khong tim thay 'python' trong PATH. Scheduled task co the FAIL."
    Write-Warning "Hay sua run-tests.bat de dung duong dan day du, vd: C:\Python312\python.exe"
}

# --- Tao action ---
$action = New-ScheduledTaskAction `
    -Execute $batchFile `
    -WorkingDirectory $scriptDir

# --- Tao trigger (moi ngay 06:00) ---
$trigger = New-ScheduledTaskTrigger -Daily -At $runTime

# --- Tao settings ---
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

# --- Dang ky task ---
try {
    # Xoa task cu neu co
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Chay 25 test case cho IHG AI OS PILOT-002 moi ngay 06:00. Log ghi vao state\test-results-*.log" `
        -RunLevel Highest `
        -ErrorAction Stop

    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Green
    Write-Host "DA DANG KY TASK THANH CONG" -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Green
    Write-Host "Ten task: $taskName"
    Write-Host "Gio chay: moi ngay $runTime"
    Write-Host "Script:   $batchFile"
    Write-Host ""
    Write-Host "Kiem tra: Get-ScheduledTask -TaskName $taskName"
    Write-Host "Chay ngay: Start-ScheduledTask -TaskName $taskName"
    Write-Host "Xoa:      Unregister-ScheduledTask -TaskName $taskName -Confirm:`$false"
} catch {
    Write-Error "Loi khi dang ky task: $_"
    exit 1
}
