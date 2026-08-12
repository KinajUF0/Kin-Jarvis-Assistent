# Установка Kin / Jarvis через .exe

## Быстрая установка (3 минуты)

### Шаг 1 — Скачать

1. Открой **[Releases](https://github.com/KinajUF0/Kin-Jarvis-Assistent/releases)**
2. Скачай **`KinJarvis-Setup-2.0.0.exe`**

### Шаг 2 — Установить

1. Запусти установщик
2. Программа установится в:
   ```
   C:\Users\<имя>\AppData\Local\Programs\Kin Jarvis\
   ```
3. На рабочем столе появится ярлык **Kin Jarvis**

### Шаг 3 — API ключ Gemini

1. Получи бесплатный ключ: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Запусти **Kin Jarvis**
3. Перейди во вкладку **Settings**
4. Вставь ключ в поле **GEMINI API KEY** → **Save API Key**

   Или вручную отредактируй файл:
   ```
   C:\Users\<имя>\AppData\Local\KinJarvis\.env
   ```

### Шаг 4 — Discord контакты (опционально)

Открой файл:
```
C:\Users\<имя>\AppData\Local\KinJarvis\config\contacts.json
```

Добавь друзей:
```json
{
  "display_name": "Сэм",
  "username": "[S_E_X_Y] Quinsames",
  "aliases": ["сэм", "sam"],
  "quick_switcher_query": "Quinsames"
}
```

### Шаг 5 — Запуск

1. Нажми **АКТИВИРОВАТЬ**
2. Разреши доступ к микрофону
3. Скажи: **«Кин, как дела?»**

---

## Где что лежит

| Что | Путь |
|-----|------|
| Программа | `%LOCALAPPDATA%\Programs\Kin Jarvis\KinJarvis.exe` |
| API ключ | `%LOCALAPPDATA%\KinJarvis\.env` |
| Настройки | `%LOCALAPPDATA%\KinJarvis\config\` |
| Логи | `%LOCALAPPDATA%\KinJarvis\logs\kin.log` |
| Скриншоты | `%LOCALAPPDATA%\KinJarvis\cache\` |

Быстрый путь: Win+R → `%LOCALAPPDATA%\KinJarvis` → Enter

---

## Portable версия

В Releases также есть **`KinJarvis-Portable.zip`**:
1. Распакуй куда угодно
2. Запусти `KinJarvis.exe`
3. Данные всё равно сохраняются в `%LOCALAPPDATA%\KinJarvis\`

---

## Обновление

1. Скачай новый `KinJarvis-Setup-X.X.X.exe` из Releases
2. Установи поверх — **настройки и .env сохранятся** в `%LOCALAPPDATA%\KinJarvis\`

---

## Проблемы

| Проблема | Решение |
|----------|---------|
| Не реагирует на голос | Settings → проверь API key; разреши микрофон в Windows |
| Discord не открывает чат | Проверь contacts.json; Ctrl+K в Discord должен находить контакт |
| Ошибка при запуске | Открой `%LOCALAPPDATA%\KinJarvis\logs\kin.log` |
| Браузер не тот | Kin авто-определяет браузер; скажи «открой Edge» явно |

---

## Удаление

1. Параметры Windows → Приложения → Kin Jarvis → Удалить
2. (Опционально) удали `%LOCALAPPDATA%\KinJarvis\` для полной очистки данных
