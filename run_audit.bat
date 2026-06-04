@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [Audit] Running logging guard...
python tools/audit_logging_guard.py --root core
set AUDIT_EXIT=%ERRORLEVEL%

if %AUDIT_EXIT% EQU 0 (
  echo [Audit] PASS
) else (
  echo [Audit] FAIL (exit code: %AUDIT_EXIT%)
)

pause
exit /b %AUDIT_EXIT%

