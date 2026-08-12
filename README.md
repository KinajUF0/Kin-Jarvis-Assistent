<p align="center">
  <img src="assets/logo.png" alt="Kin Jarvis" width="180"/>
</p>

<h1 align="center">Kin / Jarvis — AI Assistant</h1>

<p align="center">
  <strong>Голосовой AI-ассистент для Kinaj</strong><br>
  Gemini AI • Discord • Любые программы • Авто-определение браузера
</p>

<p align="center">
  <a href="https://github.com/KinajUF0/Kin-Jarvis-Assistent/releases"><img src="https://img.shields.io/github/v/release/KinajUF0/Kin-Jarvis-Assistent?style=for-the-badge" alt="Release"/></a>
  <img src="https://img.shields.io/badge/Windows-10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
</p>

---

## Скачать (Releases)

**Не нужно разбираться с Python и папками — просто скачай установщик:**

1. Перейди в **[Releases](https://github.com/KinajUF0/Kin-Jarvis-Assistent/releases)**
2. Скачай **`KinJarvis-Setup-2.0.0.exe`**
3. Установи → запусти → вставь **GEMINI_API_KEY** во вкладке **Settings**
4. Нажми **АКТИВИРОВАТЬ** → скажи **«Кин, как дела?»**

---

## Куда что сохраняется

После установки через `.exe` все понятно и в одном месте:

```
C:\Users\<ты>\AppData\Local\Programs\Kin Jarvis\   ← программа (KinJarvis.exe)
C:\Users\<ты>\AppData\Local\KinJarvis\             ← ВСЕ твои данные:
    .env                  ← GEMINI_API_KEY (вставь ключ сюда)
    config\
        apps.json         ← список программ
        contacts.json     ← Discord друзья
        settings.yaml     ← настройки
    logs\
        kin.log           ← логи ошибок
    cache\                ← скриншоты, временные файлы
```

Открыть папку с настройками: **Settings → Open Config Folder** или скажи **«Кин, открой папку config»**.

---

## Возможности

| Что умеет | Пример |
|-----------|--------|
| Разговор | «Кин, как дела?» |
| Любые программы | «Джарvis, открой Discord / Steam / блокнот» |
| **Браузер (авто!)** | «Кин, открой браузер» → откроет **твой** Edge/Chrome/Firefox |
| Discord чаты | «Кин, открой в Discord чат с Сэмом» |
| Сайты | «Кин, открой youtube.com» |
| Поиск | «Кин, найди рецепт пиццы» |
| Папки/файлы | «Кин, открой папку загрузки» |
| Система | громкость, блокировка, скриншот, выключение |
| Команды | «Кин, выполни ipconfig» |

**Wake words** (только эти имена): **Джарвис, Кин, Jarvis, Астра, Astra**

---

## Браузер — авто-определение

Kin **сам определяет** какой браузер у тебя стоит по умолчанию:
- Microsoft Edge
- Google Chrome
- Firefox, Brave, Opera, Yandex

Команды «открой браузер», «найди в интернете» — всегда через **твой** браузер, не Chrome.

---

## Discord контакты

`config/contacts.json` (или `%LOCALAPPDATA%\KinJarvis\config\contacts.json`):

```json
{
  "display_name": "Сэм",
  "username": "[S_E_X_Y] Quinsames",
  "aliases": ["сэм", "sam", "quinsames"],
  "quick_switcher_query": "Quinsames"
}
```

«Кин, открой в Discord чат с Сэмом» → fuzzy поиск → открывает DM.

---

## Сборка из исходников (для разработчиков)

```bat
git clone https://github.com/KinajUF0/Kin-Jarvis-Assistent.git
cd Kin-Jarvis-Assistent
scripts\install_windows.bat
```

Вставь ключ в `.env` или `kin_data\.env`, запусти `scripts\run.bat`.

### Собрать .exe самому

```bat
scripts\build_release.bat
iscc installer\kin_jarvis.iss
```

Результат: `dist\installer\KinJarvis-Setup-2.0.0.exe`

### GitHub Release (автоматически)

```bat
git tag v2.0.0
git push origin v2.0.0
```

GitHub Actions соберёт `.exe` установщик и зальёт в Releases.

---

## Документация

| Файл | Описание |
|------|----------|
| [docs/INSTALL.md](docs/INSTALL.md) | Установка через .exe, папки, первый запуск |
| [docs/SETUP.md](docs/SETUP.md) | Установка из исходников |
| [docs/DISCORD.md](docs/DISCORD.md) | Discord интеграция |
| [docs/COMMANDS.md](docs/COMMANDS.md) | Все команды |

---

## Автор

**Kinaj** — [@KinajUF0](https://github.com/KinajUF0)

MIT License
