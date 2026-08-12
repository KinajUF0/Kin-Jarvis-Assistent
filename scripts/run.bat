@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul 2>&1
title Kin/Jarvis - AI Assistant

cd /d "%~dp0.."

if not exist venv (
    echo [ERROR] Virtual environment not found.
    echo Run scripts\install_windows.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
if not %ERRORLEVEL%==0 (
    echo [ERROR] Failed to activate venv.
    pause
    exit /b 1
)

if not exist .env (
    echo [ERROR] .env file not found.
    echo Copy .env.example to .env and set GEMINI_API_KEY.
    pause
    exit /b 1
)

echo.
echo  ========================================
echo    KIN / JARVIS - AI Assistant
echo    Starting...
echo  ========================================
echo.

python -m src.main

if not %ERRORLEVEL%==0 (
    echo.
    echo [ERROR] Application exited with an error.
    echo Check kin_data\kin.log for details.
    pause
)

endlocal
