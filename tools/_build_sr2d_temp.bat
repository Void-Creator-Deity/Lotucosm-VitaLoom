@echo off
set "VSROOT=D:\app\Microsoft Visual Studio\18\Community"
call "D:\app\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
set "PATH=%~dp0..\.venv\Scripts;%PATH%"
"%~dp0..\.venv\python.exe" -m pip install --no-build-isolation --force-reinstall "%~dp0..\native\sr2d_cpp"
