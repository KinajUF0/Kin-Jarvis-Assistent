@echo off
chcp 65001 >nul
title Kin/Jarvis — AI Assistant

cd /d "%~dp0.."

if not exist venv (
    echo Виртуальное окружение не найдено. Запустите scripts\install_windows.bat
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

if not exist .env (
    echo [ОШИБКА] Файл .env не найден!
    echo Скопируйте .env.example в .env и вставьте GEMINI_API_KEY
    pause
    exit /b 1
)

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   KIN / JARVIS — AI Assistant        ║
echo  ║   Запуск...                          ║
echo  ╚══════════════════════════════════════╝
echo.

python -m src.main

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Приложение завершилось с ошибкой.
    echo Проверьте kin_data\kin.log для деталей.
    pause
)
