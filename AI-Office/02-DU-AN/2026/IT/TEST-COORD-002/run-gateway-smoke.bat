@echo off
REM run-gateway-smoke.bat — smoke test GatewayRuntime voi du lieu gia lap
REM Chi chay neu runtime cho phep (python full path)
setlocal
set "ROOT=%~dp0"
set "PYEXE=C:\Users\anhld\AppData\Local\Python\bin\python.exe"
if not exist "%PYEXE%" (
  echo [ERROR] Khong tim thay python: %PYEXE%
  exit /b 2
)
cd /d "%ROOT%"
"%PYEXE%" tests\gateway_smoke.py
endlocal
