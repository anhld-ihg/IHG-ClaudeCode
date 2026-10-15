@echo off
REM IHG Test Runner — chay 25 test case, luu log + exit code
REM Su dung: run-tests.bat  (click chuot phai -> Run as Administrator neu can)
REM Hoac:   cmd /c run-tests.bat
REM Log ghi vao: state\test-results-YYYYMMDD-HHMMSS.log
REM Exit code 0 = PASS tat ca, 1 = co FAIL, 2 = runtime loi

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Tao thu muc tam cho test (khong anh huong state that)
set IHG_ROOT_TMP=%TEMP%\ihg-test-%RANDOM%
set IHG_STATE_DIR=%IHG_ROOT_TMP%\state
set IHG_OUTPUT_DIR=%IHG_ROOT_TMP%\output
set IHG_LOG_DIR=%IHG_ROOT_TMP%\logs

REM Tao timestamp
for /f "tokens=2 delims==" %%a in ('wmic os get localdatetime /value') do set TS=%%a
set TS=%TS:~0,8%-%TS:~8,6%

set LOG_FILE=state\test-results-%TS%.log
set SUMMARY=state\test-summary-%TS%.json
set IHG_TEST_SUMMARY=%SUMMARY%

echo ===============================================================
echo IHG AI OS Test Runner
echo Started: %date% %time%
echo Working dir: %cd%
echo Log file: %LOG_FILE%
echo Summary: %SUMMARY%
echo =============================================================== > %LOG_FILE%
echo Started: %date% %time% >> %LOG_FILE%
echo Working dir: %cd% >> %LOG_FILE%

REM Kiem tra python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python khong co trong PATH
    echo [ERROR] Python khong co trong PATH >> %LOG_FILE%
    exit /b 2
)

REM Lay version python
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo Python: %PYVER% >> %LOG_FILE%
echo Python: %PYVER%

REM Chay test
echo.
echo [RUNNING] python tests\runtests.py ...
python tests\runtests.py >> %LOG_FILE% 2>&1
set RC=%ERRORLEVEL%

echo.
echo ===============================================================
echo [RESULT] Exit code: %RC%
echo ===============================================================
echo [RESULT] Exit code: %RC% >> %LOG_FILE%

if %RC% equ 0 (
    echo [OK] All tests PASS
    echo [OK] All tests PASS >> %LOG_FILE%
) else (
    echo [FAIL] Co test FAIL. Xem log: %LOG_FILE%
    echo [FAIL] Co test FAIL. Xem log: %LOG_FILE%
)

echo Finished: %date% %time% >> %LOG_FILE%
exit /b %RC%
