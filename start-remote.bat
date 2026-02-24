@echo off
echo ========================================
echo ShellIA - Mode Remote SSH
echo ========================================
echo.

set SHELLIA_ENV=remote
cd src
py -m uvicorn main:app --reload
