@echo off
echo ========================================
echo ShellIA - Mode Local
echo ========================================
echo.

set SHELLIA_ENV=local
cd src
py -m uvicorn main:app --reload
