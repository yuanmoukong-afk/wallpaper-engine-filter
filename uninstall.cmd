@echo off
cd /d "%~dp0"
python tools\install.py uninstall %*
pause
