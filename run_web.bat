@echo off
cd /d "%~dp0"
for /f "delims=" %%i in ('poetry --directory nlip\nlip_web env info --path') do set VENV=%%i
"%VENV%\Scripts\python.exe" nlip\nlip_web\nlip_web\stress_test_chat.py
pause