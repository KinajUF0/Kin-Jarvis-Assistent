# Discord интеграция — подробное руководство

## Как это работает

Когда вы говорите **«Кин, открой в Discord чат с Сэмом»**, ассистент:

1. **Запускает Discord** (если не запущен) или переключается на окно
2. **Ищет контакт** в `config/contacts.json` через fuzzy matching (rapidfuzz)
3. **Открывает Quick Switcher** (Ctrl+K) в Discord
4. **Вводит** `quick_switcher_query` контакта
5. **Нажимает Enter** для открытия чата

## Fuzzy Matching — нечёткий поиск

Ассистент понимает множество вариантов имени:

| Вы говорите | Найдёт |
|-------------|--------|
| «Сэм» | [S_E_X_Y] Quinsames |
| «sam» | [S_E_X_Y] Quinsames |
| «quinsames» | [S_E_X_Y] Quinsames |
| «quins» | [S_E_X_Y] Quinsames |
| «sex y» | [S_E_X_Y] Quinsames |

### Настройка порога совпадения

В `config/settings.yaml`:

```yaml
discord:
  fuzzy_match_threshold: 60  # 0-100
```

- **60** (по умолчанию) — баланс точности и гибкости
- **80+** — строгий поиск, меньше ложных срабатываний
- **40-** — очень мягкий, может путать похожие имена

## Добавление контактов

### Шаблон записи

```json
{
  "display_name": "Имя для отображения",
  "username": "Полный Discord ник",
  "aliases": ["вариант1", "вариант2", "nickname"],
  "search_terms": ["дополнительные", "строки", "поиска"],
  "quick_switcher_query": "Что вводить в Ctrl+K",
  "notes": "Заметки (необязательно)"
}
```

### Поля

| Поле | Описание | Пример |
|------|----------|--------|
| `display_name` | Как ассистент называет контакт | `"Сэм"` |
| `username` | Полный Discord ник | `"[S_E_X_Y] Quinsames"` |
| `aliases` | Как вы можете обращаться | `["сэм", "sam", "quins"]` |
| `search_terms` | Доп. строки для fuzzy match | `["S_E_X_Y", "Quinsames"]` |
| `quick_switcher_query` | Запрос в Quick Switcher | `"Quinsames"` |

### Советы

1. **`aliases`** — добавьте все варианты, как вы обычно называете человека
2. **`quick_switcher_query`** — проверьте вручную: откройте Discord, Ctrl+K, введите строку
3. Используйте **уникальную часть** ника для `quick_switcher_query`
4. Для кириллических имён добавьте и латинские варианты

## Примеры команд

```
Кин, открой в Discord чат с Сэмом
Джарvis, найди в Discord Sam
Jarvis, open Discord chat with Quinsames
Астра, напиши Сэму в Discord
```

## Ограничения

- Работает только с **DM и серверными каналами**, доступными через Quick Switcher
- Discord должен быть **установлен локально** (не в браузере)
- Во время автоматизации **не двигайте мышь** (pyautogui)
- Discord **должен быть на английской раскладке** для Quick Switcher query (латиница)

## Тестирование

```bash
python scripts/test_components.py
```

Проверит fuzzy matching для всеall configured contacts.
