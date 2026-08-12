@echo off
setlocal DisableDelayedExpansion
title Kin Jarvis - Build Release

cd /d "%~dp0.."

echo.
echo  Building Kin/Jarvis for Release...
echo.

python --version >nul 2>&1
if not %ERRORLEVEL%==0 (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

if not exist venv (
    echo Creating venv...
    python -m venv venv
)
call venv\Scripts\activate.bat

echo Installing build dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo Building EXE...
pyinstaller build/kin_jarvis.spec --noconfirm
if not %ERRORLEVEL%==0 (
    echo [ERROR] PyInstaller failed.
    pause
    exit /b 1
)

echo.
echo EXE built: dist\KinJarvis\KinJarvis.exe
echo.
echo To create installer, install Inno Setup and run:
echo   iscc installer\kin_jarvis.iss
echo.
echo Output: dist\installer\KinJarvis-Setup-2.0.0.exe
echo.
pause
endlocal
