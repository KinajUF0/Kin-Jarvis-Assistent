@echo off
chcp 65001 >nul
title Kin/Jarvis — Установка

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   KIN / JARVIS — AI Assistant        ║
echo  ║   Установка зависимостей             ║
echo  ╚══════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo Скачайте Python 3.10+ с https://python.org
    echo При установке отметьте "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/4] Создание виртуального окружения...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/4] Установка зависимостей...
pip install --upgrade pip
pip install -r requirements.txt

echo [3/4] Настройка конфигурации...
if not exist .env (
    copy .env.example .env
    echo.
    echo  ⚠  Создан файл .env — вставьте ваш GEMINI_API_KEY!
    echo     Получить ключ: https://aistudio.google.com/apikey
    echo.
)

echo [4/4] Создание папки данных...
if not exist kin_data mkdir kin_data

echo.
echo  ✅ Установка завершена!
echo.
echo  Следующие шаги:
echo    1. Откройте .env и вставьте GEMINI_API_KEY
echo    2. Настройте config/contacts.json (ваши Discord друзья)
echo    3. Запустите: scripts\run.bat
echo.
pause
