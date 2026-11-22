@echo off
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
python -m cruscotto
if errorlevel 1 pause
