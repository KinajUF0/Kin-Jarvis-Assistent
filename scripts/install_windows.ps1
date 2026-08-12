# Kin/Jarvis - Windows install (PowerShell, UTF-8 safe)
# Run: powershell -ExecutionPolicy Bypass -File scripts/install_windows.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host ""
Write-Host "  ========================================" -ForegroundColor Cyan
Write-Host "    KIN / JARVIS - AI Assistant" -ForegroundColor Cyan
Write-Host "    Установка зависимостей..." -ForegroundColor Cyan
Write-Host "  ========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "  Python: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "[ОШИБКА] Python не найден!" -ForegroundColor Red
    Write-Host "Скачайте Python 3.10+ с https://python.org"
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "[1/4] Создание виртуального окружения..."
python -m venv venv

Write-Host "[2/4] Установка зависимостей..."
& .\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "[3/4] Настройка конфигурации..."
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "  Создан файл .env — вставьте GEMINI_API_KEY!" -ForegroundColor Yellow
    Write-Host "  Получить ключ: https://aistudio.google.com/apikey"
    Write-Host ""
}

Write-Host "[4/4] Создание папки данных..."
New-Item -ItemType Directory -Force -Path "kin_data" | Out-Null

Write-Host ""
Write-Host "  Установка завершена!" -ForegroundColor Green
Write-Host ""
Write-Host "  Следующие шаги:"
Write-Host "    1. Откройте .env и вставьте GEMINI_API_KEY"
Write-Host "    2. Настройте config/contacts.json"
Write-Host "    3. Запустите: scripts\run.bat"
Write-Host ""
Read-Host "Нажмите Enter для выхода"
