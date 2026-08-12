# Kin / Jarvis — Ollama setup for Windows
# Downloads Ollama and pulls AI model for Kin

@echo off
setlocal DisableDelayedExpansion
title Kin Jarvis — Ollama Setup
chcp 65001 >nul 2>&1

echo.
echo  ========================================
echo    KIN JARVIS — Ollama Setup
echo  ========================================
echo.

:: Check if ollama already installed
where ollama >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [OK] Ollama already installed.
    goto :pull_model
)

echo Step 1: Installing Ollama...
echo.

:: Try winget first
where winget >nul 2>&1
if %ERRORLEVEL%==0 (
    echo Installing via winget...
    winget install Ollama.Ollama --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL%==0 goto :wait_start
)

echo.
echo Download Ollama manually:
echo   https://ollama.com/download/windows
echo.
echo After install, run this script again.
start https://ollama.com/download/windows
pause
exit /b 0

:wait_start
echo.
echo Waiting for Ollama to start...
timeout /t 5 /nobreak >nul

:pull_model
echo.
echo Step 2: Downloading AI model (llama3.2, ~2 GB)...
echo This may take 5-15 minutes depending on internet speed.
echo.

ollama pull llama3.2
if not %ERRORLEVEL%==0 (
    echo.
    echo [ERROR] Failed to pull model.
    echo Make sure Ollama is running (check system tray).
    pause
    exit /b 1
)

echo.
echo  ========================================
echo    Ollama ready for Kin Jarvis!
echo  ========================================
echo.
echo  Model: llama3.2
echo  Now launch Kin Jarvis and click Activate.
echo.
pause
endlocal
