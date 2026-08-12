# Подробная инструкция по установке Kin / Jarvis

## Требования

| Компонент | Минимум | Рекомендуется |
|-----------|---------|---------------|
| ОС | Windows 10/11 | Windows 11 |
| Python | 3.10+ | 3.11+ |
| RAM | 4 GB | 8 GB |
| Микрофон | Любой | USB-конденсаторный |
| Интернет | Для Gemini API | Стабильное соединение |
| Discord | Установлен | Последняя версия |

## Шаг 1: Установка Python

1. Скачайте Python с [python.org](https://www.python.org/downloads/)
2. При установке **обязательно** отметьте **"Add Python to PATH"**
3. Проверьте: откройте cmd и введите `python --version`

## Шаг 2: Клонирование репозитория

```bash
git clone https://github.com/KinajUF0/Kin-Jarvis-Assistent.git
cd Kin-Jarvis-Assistent
```

## Шаг 3: Автоматическая установка (Windows)

**Способ 1 — BAT-файл:**

```bat
scripts\install_windows.bat
```

**Способ 2 — PowerShell (если BAT выдаёт ошибки вроде `'errorlevel' is not recognized`):**

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_windows.ps1
```

> Если BAT-файл показывает кракозябры или `'errorlevel' is not recognized` — используйте PowerShell-скрипт. Это проблема кодировки Windows cmd.exe с UTF-8.

Скрипт:
- Создаст виртуальное окружение `venv/`
- Установит все зависимости
- Создаст `.env` из шаблона

## Шаг 3 (альтернатива): Ручная установка

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
copy .env.example .env       # Windows
# cp .env.example .env       # Linux/macOS
```

## Шаг 4: Gemini API Key

1. Перейдите на [Google AI Studio](https://aistudio.google.com/apikey)
2. Создайте API Key
3. Откройте `.env` и вставьте ключ:

```env
GEMINI_API_KEY=AIzaSy...ваш_ключ...
```

## Шаг 5: Настройка Discord контактов

Откройте `config/contacts.json` и добавьте своих друзей:

```json
{
  "display_name": "Сэм",
  "username": "[S_E_X_Y] Quinsames",
  "aliases": ["сэм", "sam", "quinsames"],
  "quick_switcher_query": "Quinsames"
}
```

### Как узнать Discord ник?

1. Откройте Discord → профиль друга
2. Скопируйте **Display Name** и **Username**
3. `quick_switcher_query` — то, что вы вводите в Ctrl+K для поиска

## Шаг 6: Запуск

```bash
scripts\run.bat
```

Или вручную:

```bash
venv\Scripts\activate
python -m src.main
```

## Шаг 7: Первое использование

1. Нажмите **«АКТИВИРОВАТЬ»** в интерфейсе
2. Разрешите доступ к микрофону (Windows)
3. Скажите: **«Кин, как дела?»**
4. Ассистент ответит голосом!

## Решение проблем

### Микрофон не работает

- Проверьте настройки Windows → Конфиденциальность → Микрофон
- Убедитесь, что PyAudio установлен: `pip install PyAudio`
- Если PyAudio не ставится: скачайте wheel с [этого сайта](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)

### Gemini API ошибка

- Проверьте ключ в `.env`
- Убедитесь, что ключ активен на [AI Studio](https://aistudio.google.com/apikey)
- Проверьте интернет-соединение

### Discord не открывает чат

- Discord должен быть установен и хотя бы раз запущен
- Убедитесь, что контакт есть в `config/contacts.json`
- Quick Switcher (Ctrl+K) должен находить контакт вручную
- Не двигайте мышь во время автоматизации (pyautogui)

### Программа не запускается

- Проверьте лог: `kin_data/kin.log`
- Запустите тест: `python scripts/test_components.py`

## Linux / macOS

Проект оптимизирован для Windows, но базовые функции работают:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m src.main
```

Discord-автоматизация (Ctrl+K) лучше всего работает на Windows.
