@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul 2>&1
title Kin/Jarvis - Install

cd /d "%~dp0.."

echo.
echo  ========================================
echo    KIN / JARVIS - AI Assistant
echo    Installing dependencies...
echo  ========================================
echo.

python --version >nul 2>&1
if not %ERRORLEVEL%==0 (
    echo [ERROR] Python not found.
    echo Download Python 3.10+ from https://python.org
    echo During install, check "Add Python to PATH".
    pause
    exit /b 1
)

echo Step 1/4: Creating virtual environment...
python -m venv venv
if not %ERRORLEVEL%==0 (
    echo [ERROR] Failed to create venv.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
if not %ERRORLEVEL%==0 (
    echo [ERROR] Failed to activate venv.
    pause
    exit /b 1
)

echo Step 2/4: Installing Python packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if not %ERRORLEVEL%==0 (
    echo [ERROR] pip install failed.
    echo If PyAudio fails, see docs/SETUP.md
    pause
    exit /b 1
)

echo Step 3/4: Creating config file...
if not exist .env (
    copy /Y .env.example .env >nul
    echo.
    echo  Created .env file.
    echo  Add your GEMINI_API_KEY from https://aistudio.google.com/apikey
    echo.
)

echo Step 4/4: Creating data folder...
if not exist kin_data mkdir kin_data

echo.
echo  ========================================
echo    Installation complete!
echo  ========================================
echo.
echo  Next steps:
echo    1. Edit .env and set GEMINI_API_KEY
echo    2. Edit config/contacts.json for Discord friends
echo    3. Run: scripts\run.bat
echo.
pause
endlocal
