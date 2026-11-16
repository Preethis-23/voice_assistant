@echo off
echo Configuring KIRA to start automatically on laptop boot...
"%~dp0.venv\Scripts\python.exe" "%~dp0scripts\setup_startup.py"
pause
