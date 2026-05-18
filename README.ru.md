# opencode-db

**Управление базой данных OpenCode: просмотр, экспорт, аналитика и очистка сессий.**

`opencode-db` — это CLI-утилита для работы с локальной базой данных OpenCode (SQLite). Она позволяет просматривать историю диалогов с AI-ассистентом, экспортировать диалоги в Markdown, анализировать расход токенов и стоимость, управлять хранилищем — удалять ненужные сессии и оптимизировать БД.

```
opencode-db help        # все команды, примеры, флаги
opencode-db list        # последние сессии
opencode-db stats       # сводка по всей БД
opencode-db export      # сохранить диалог в .md (интерактивно)
opencode-db costs --total  # общие расходы
```

---

## Установка

### Требования

- Python 3.10+
- OpenCode (должен быть хотя бы раз запущен — создаётся БД)
- macOS / Linux

### Быстрая установка

```bash
git clone https://github.com/VasilevNStas/opencode-db.git ~/.local/share/opencode-db
ln -s ~/.local/share/opencode-db/bin/opencode-db ~/.local/bin/opencode-db
```

### Ручная установка

1. Скопируйте содержимое проекта в `~/.local/share/opencode-db/`:

```bash
mkdir -p ~/.local/share/opencode-db
# скопируйте все файлы проекта в эту директорию
```

2. Создайте лаунчер в `~/.local/bin/opencode-db`:

```bash
cat > ~/.local/bin/opencode-db << 'SCRIPT'
#!/usr/bin/env python3
"""Лаунчер opencode-db."""
import sys, os
PKG_DIR = os.path.expanduser("~/.local/share/opencode-db")
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)
import cli
sys.exit(cli.main())
SCRIPT
chmod +x ~/.local/bin/opencode-db
```

3. Убедитесь, что `~/.local/bin` есть в `$PATH`:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

4. Проверьте:

```bash
opencode-db --help
```

---

## Быстрый старт

```bash
# Посмотреть последние сессии
opencode-db list

# Детальная информация о сессии (можно по префиксу ID)
opencode-db info ses_1c9d

# Сохранить диалог в Markdown
opencode-db export ses_1c9d --force

# Общие расходы на токены
opencode-db costs --total

# Статистика по всей БД
opencode-db stats
```

---

## Команды

### `list` — список сессий

Показывает таблицу последних сессий: ID, название, проект, модель, дату последней активности, количество сообщений и стоимость.

```bash
opencode-db list                         # последние 25
opencode-db list --limit 10              # последние 10
opencode-db list --all                   # все сессии
opencode-db list --sort cost             # сортировка по стоимости
opencode-db list --project proj_xxx      # фильтр по проекту
opencode-db list --agent build           # фильтр по агенту
opencode-db list --model deepseek        # фильтр по модели
opencode-db list --json                  # вывод в JSON
```

| Флаг | Описание | По умолчанию |
|---|---|---|
| `--limit N` | Сколько показать | 25 |
| `--offset N` | Смещение | 0 |
| `--project ID` | Фильтр по проекту | — |
| `--agent NAME` | Фильтр по типу агента | — |
| `--model NAME` | Фильтр по модели | — |
| `--sort {date,cost,tokens,messages}` | Сортировка | date |
| `--json` | Вывод в JSON | — |
| `--all` | Показать все (без limit) | — |

---

### `info` — детальная информация о сессии

Показывает метаданные, статистику сообщений и токенов, стоимость, код-изменения, дочерние сессии и todo-задачи.

```bash
opencode-db info ses_1c9d9fa58ffe        # по полному ID
opencode-db info ses_1c9d                # по префиксу ID
opencode-db info ses_1c9d --json         # в JSON
```

Пример вывода:

```
============================================================
  Анализ export-dialog скрипта
============================================================
  ID:        ses_1c9d9fa58ffeiqsrHGVg8MPZes
  Проект:    global (global)
  Модель:    deepseek-reasoner
  Агент:     plan
  Версия:    1.15.1
  Создана:   2026-05-17 13:35:22
  Активна:   2026-05-17 14:13:23
  Длит-сть:  38 мин

  ────────────────────────────────────────────────────────
  Сообщений: 43
  Частей:    224
  ────────────────────────────────────────────────────────
  Токены ввода:     82 026
  Токены вывода:    36 837
  Токены reasoning: 17 211
  Кэш (чтение):     2 077 312
  Всего токенов:    118 863
  Стоимость:        $0.085
```

---

### `export` — экспорт диалога в Markdown

Сохраняет диалог в файл `opencode-YYYY-MM-DD_HH.MM.SS.md` в текущей директории.

**Три режима выбора сессии:**

| Режим | Пример | Описание |
|---|---|---|
| По ID | `export ses_1c9d` | Явный ID (полный или префикс) |
| Последняя | `export --latest` | Самая свежая сессия |
| Интерактивный | `export` (без аргументов) | Выбор из нумерованного списка |

```bash
opencode-db export ses_1c9d                    # по ID
opencode-db export --latest                    # самая свежая
opencode-db export --latest --force            # последняя, перезаписать
opencode-db export --latest -n "рефакторинг"   # последняя, с заметкой
opencode-db export                             # интерактивный выбор
opencode-db export --full                      # полный вывод (без обрезания output'ов)
opencode-db export -o ~/backup                 # сохранить в другую директорию
```

Интерактивный режим показывает 15 последних сессий с датой и стоимостью — выбираешь номер, и диалог сохраняется.

Формат файла — Markdown с заголовком (дата, модель, ID) и сообщениями по порядку с разбивкой на роли (user/assistant), рассуждения модели (reasoning) и вызовы инструментов.

Если в проекте есть директория `.obsidian` — автоматически дополняется `log.md` со snapshot структуры проекта (AGENTS.md, количество файлов и директорий).

| Флаг | Описание | По умолчанию |
|---|---|---|
| `session_id` | ID сессии (опционально) | — |
| `--latest`, `-l` | Экспорт самой свежей сессии | — |
| `--full`, `-F` | Полный вывод (не обрезать длинные output'ы) | — |
| `--force`, `-f` | Перезаписать существующий файл | — |
| `--note`, `-n` | Описание сессии для log.md | — |
| `--output`, `-o` | Директория для сохранения | `os.getcwd()` |

---

### `delete` — удаление сессии

Удаляет сессию и все связанные данные (сообщения, части, todo) благодаря CASCADE в схеме БД.

```bash
opencode-db delete ses_1c9d --dry-run    # показать что будет удалено
opencode-db delete ses_1c9d              # с подтверждением
opencode-db delete ses_1c9d --force      # без подтверждения
```

Всегда показывает информацию о сессии перед удалением.

| Флаг | Описание |
|---|---|
| `--dry-run` | Только показать что будет удалено |
| `--force`, `-f` | Без подтверждения |

---

### `costs` — анализ расходов на токены

Детальная разбивка токенов и стоимости по сессии, проекту или всей БД.

```bash
opencode-db costs ses_1c9d               # расходы по одной сессии
opencode-db costs --total                # всего по БД
opencode-db costs --project proj_xxx     # всего по проекту
opencode-db costs                        # топ сессий по расходам
opencode-db costs --limit 10             # топ-10
opencode-db costs ses_1c9d --json        # в JSON
```

Стоимость берётся напрямую из БД (`session.cost`) — это фактическая стоимость, рассчитанная провайдером модели. Справочник цен больше не используется.

| Флаг | Описание | По умолчанию |
|---|---|---|
| `session_id` | ID сессии (опционально) | — |
| `--project` | Фильтр по проекту | — |
| `--total` | Сумма по всей БД | — |
| `--limit N` | Макс. строк в списке | 30 |
| `--json` | Вывод в JSON | — |

---

### `prune` — массовая очистка старых сессий

Удаляет сессии по возрасту, проекту или с ограничением на количество сохраняемых.

```bash
opencode-db prune --older-than 30d --dry-run   # что можно удалить
opencode-db prune --older-than 90d              # удалить сессии старше 90 дней
opencode-db prune --older-than 6m               # старше 6 месяцев
opencode-db prune --older-than 1y               # старше года
opencode-db prune --keep-last 20                # оставить 20 последних
opencode-db prune --older-than 30d --keep-last 10  # комбинация
opencode-db prune --project proj_xxx            # по проекту
opencode-db prune --older-than 30d --force      # без подтверждения
```

Форматы `--older-than`: `30d` (дни), `6m` (месяцы), `1y` (года).

| Флаг | Описание |
|---|---|
| `--older-than SPEC` | Удалить сессии без активности после указанного срока |
| `--keep-last N` | Оставить N последних сессий |
| `--project ID` | Ограничить проектом |
| `--dry-run` | Только показать что будет удалено |
| `--force`, `-f` | Без подтверждения |

---

### `search` — поиск по сообщениям

Ищет в тексте сообщений и вызовов инструментов (регистронезависимо).

```bash
opencode-db search "баг"                 # поиск по всем сессиям
opencode-db search "export" --limit 5    # первые 5 результатов
opencode-db search "фикс" --session ses_1c9d  # в конкретной сессии
opencode-db search "deploy" --json       # в JSON
```

| Флаг | Описание | По умолчанию |
|---|---|---|
| `query` | Текст для поиска | обязательный |
| `--session ID` | Ограничить сессией | — |
| `--limit N` | Макс. результатов | 30 |
| `--json` | Вывод в JSON | — |

---

### `tree` — дерево ветвления сессий

Показывает иерархию сессий через `parent_id`. Полезно для понимания от какой сессии ответвилась текущая.

```bash
opencode-db tree                          # все корневые сессии с детьми
opencode-db tree ses_1c9d                 # ветка от указанной сессии
opencode-db tree --project proj_xxx       # по проекту
opencode-db tree --depth 3                # глубина 3 уровня
```

Пример вывода:

```
  🌳 Все корневые сессии (ветвление)
  ───────────────────────────────────────────────────────
  ses_1ed78233fffe  2026-05-10  Starting a project
    └─ ses_1ed5d1a05ffe  2026-05-10  Create README and meta files (@general subagent)
    └─ ses_1ed5c6c29ffe  2026-05-10  Create Module 01 Fundamentals (@general subagent)
    └─ ses_1ed5b7adbffe  2026-05-10  Create Module 02 Anatomy (@general subagent)
    └─ ses_1ed5a91efffe  2026-05-10  Create Module 03 Mechanics (@general subagent)
    ...
```

| Флаг | Описание | По умолчанию |
|---|---|---|
| `session_id` | Начать с указанной сессии (опционально) | — |
| `--depth N` | Макс. глубина | 5 |
| `--project ID` | Фильтр по проекту | — |

---

### `projects` — список проектов

Показывает все проекты в БД со статистикой: количество сессий, токены, стоимость.

```bash
opencode-db projects                      # таблица проектов
opencode-db projects --json               # в JSON
```

| Флаг | Описание |
|---|---|
| `--json` | Вывод в JSON |

---

### `stats` — общая статистика БД

Сводка по всей базе данных: количество сессий, сообщений, частей, проектов, задач; общее количество токенов и стоимость; первая и последняя сессия; топ моделей и агентов.

```bash
opencode-db stats                         # сводка
opencode-db stats --json                  # в JSON
```

| Флаг | Описание |
|---|---|
| `--json` | Вывод в JSON |

---

### `todos` — просмотр задач из сессий

Показывает todo-записи, созданные в ходе сессий OpenCode.

```bash
opencode-db todos                         # все задачи
opencode-db todos ses_1c9d                # задачи конкретной сессии
opencode-db todos --status pending        # только ожидающие
opencode-db todos --json                  # в JSON
```

| Флаг | Описание | По умолчанию |
|---|---|---|
| `session_id` | ID сессии (опционально) | — |
| `--status {pending,completed,cancelled}` | Фильтр по статусу | — |
| `--limit N` | Макс. записей | 30 |
| `--json` | Вывод в JSON | — |

---

### `vacuum` — оптимизация базы данных

Выполняет `VACUUM`, `REINDEX` и `ANALYZE` для освобождения дискового пространства и оптимизации производительности. Особенно полезно после массовых удалений (prune, delete).

```bash
opencode-db vacuum                        # с подтверждением
opencode-db vacuum --force                # без подтверждения
```

| Флаг | Описание |
|---|---|
| `--force`, `-f` | Без подтверждения |

---

### `help` — подробная справка

Показывает список всех команд с описанием, флагами и примерами использования. Работает как в CLI, так и через `/bash opencode-db help` из TUI OpenCode.

```bash
opencode-db help                          # полная справка по всем командам
opencode-db help export                   # справка по конкретной команде
opencode-db help --json                   # справка в JSON
```

Пример вывода `opencode-db help`:

```
  ╔══════════════════════════════════════════════════════════╗
  ║                 opencode-db — справка                    ║
  ╚══════════════════════════════════════════════════════════╝

  Использование: opencode-db <команда> [флаги]

  list          Список сессий
                  opencode-db list                               # Сессии за последнее время
                  opencode-db list --sort cost                     # Сортировка по стоимости
                  opencode-db list --json                          # Вывод в JSON

  export        Экспорт диалога в Markdown
                  opencode-db export <session_id>                  # Экспорт по ID
                  opencode-db export --latest                      # Самая свежая сессия
                  opencode-db export                               # Интерактивный выбор
                  opencode-db export --full                        # Полный вывод без обрезания

  costs         Анализ расходов на токены
                  opencode-db costs <session_id>                   # Детально по сессии
                  opencode-db costs --total                        # Сумма по всей БД

  ...
```

---

## Сводная таблица команд

| Команда | Описание | Ключевые флаги |
|---|---|---|
| `list` | Список сессий с фильтрацией | `--limit`, `--sort`, `--project`, `--json`, `--all` |
| `info` | Детальная информация о сессии | `--json` |
| `export` | Экспорт диалога в Markdown | `--latest`, `--full`, `--force`, `--note`, `--output` |
| `delete` | Удаление сессии | `--dry-run`, `--force` |
| `costs` | Анализ расходов на токены | `--total`, `--project`, `--json` |
| `prune` | Массовая очистка старых сессий | `--older-than`, `--keep-last`, `--dry-run` |
| `search` | Поиск по тексту сообщений | `--session`, `--json` |
| `tree` | Дерево ветвления сессий | `--depth`, `--project` |
| `projects` | Сводка по проектам | `--json` |
| `stats` | Общая статистика БД | `--json` |
| `todos` | Просмотр задач из сессий | `--status`, `--json` |
| `vacuum` | Оптимизация базы данных | `--force` |
| `help` | Подробная справка | `<команда>`, `--json` |

---

## Архитектура проекта

```
~/.local/bin/opencode-db                  ← точка входа (в PATH)
│
~/.local/share/opencode-db/               ← весь код
│
├── __init__.py                           ← исполняемая точка входа
├── __main__.py                           ← python -m opencode_db
├── cli.py                                ← argparse + диспетчер команд
│
├── config.py                             ← константы и пути
├── db.py                                 ← запросы к SQLite
├── utils.py                              ← форматирование дат, токенов, валидация
├── formatters.py                         ← таблицы, JSON, Markdown, snapshot
├── i18n.py                               ← локализация (EN/RU, 238 ключей)
│
├── commands/
│   └── __init__.py                       ← реестр команд
│
├── cmd_list.py                           ← opencode-db list
├── cmd_info.py                           ← opencode-db info
├── cmd_export.py                         ← opencode-db export
├── cmd_delete.py                         ← opencode-db delete
├── cmd_costs.py                          ← opencode-db costs
├── cmd_prune.py                          ← opencode-db prune
├── cmd_search.py                         ← opencode-db search
├── cmd_tree.py                           ← opencode-db tree
├── cmd_projects.py                       ← opencode-db projects
├── cmd_stats.py                          ← opencode-db stats
├── cmd_todos.py                          ← opencode-db todos
├── cmd_vacuum.py                         ← opencode-db vacuum
└── cmd_help.py                           ← opencode-db help
```

### Как это работает

1. Лаунчер `~/.local/bin/opencode-db` (шебанг + 10 строк Python) добавляет `~/.local/share/opencode-db/` в `sys.path` и вызывает `cli.main()`.
2. `cli.py` собирает `argparse` с subparser'ами от всех команд и диспетчеризирует вызов.
3. Каждая команда — отдельный модуль `cmd_*.py` с двумя функциями: `register(subparsers)` и `run(args, db)`.
4. `db.py` открывает соединение с SQLite-базой OpenCode (`~/.local/share/opencode/opencode.db`).
5. Для опасных операций (`delete`, `prune`) используется подтверждение через `input()`.

### Схема базы данных (ключевые таблицы)

```
session        — сессии: id, title, model (JSON), agent, cost, tokens_*, parent_id, summary_*
message        — сообщения: id, session_id, time_created, data (JSON: role, agent)
part           — части сообщений: id, message_id, session_id, data (JSON: type, text, state)
todo           — задачи: session_id, content, status, priority
project        — проекты: id, worktree, name
```

---

## Использование из TUI OpenCode

`opencode-db` можно вызывать прямо из интерфейса OpenCode двумя способами.

### Напрямую (без AI, без токенов)

Встроенная команда `/bash` в чате OpenCode:

```
/bash opencode-db list
/bash opencode-db info ses_1c9d
/bash opencode-db costs --total
/bash opencode-db export --latest --force
```

Вывод показывается **напрямую**, AI не участвует — **токены не тратятся**.

### Кастомная команда `/db` (через AI, тратит токены)

Добавь команды из `opencode-db-commands.json` в `opencode.json` проекта:

```json
{
  "command": {
    "db": {
      "template": "!`opencode-db {{input}} --json`\n\nПокажи результат понятно и структурированно.",
      "description": "Управление БД: list, info, stats, costs, search...",
      "agent": "explore",
      "model": "deepseek/deepseek-chat"
    }
  }
}
```

В TUI:

```
/db list --limit 5        → список сессий
/db info ses_1c9d         → детали сессии
/db costs --total         → общие расходы
/db export --latest       → сохранить последний диалог
```

> ⚠️ **Предупреждение:** команда `/db` отправляет данные через AI-модель, что расходует токены (обычно 500–5000 токенов на вход). Если нужно просто посмотреть данные без обработки AI — используй `/bash opencode-db ...`.

Готовый конфиг лежит в:
```
~/.local/share/opencode-db/opencode-db-commands.json
```

---

## Безопасность

| Принцип | Реализация |
|---|---|
| Подтверждение удаления | `delete` и `prune` запрашивают `y/N` |
| Сухой запуск | `--dry-run` показывает результат без изменений |
| Только чтение | `list`, `info`, `costs`, `search`, `tree`, `projects`, `stats`, `todos` — read-only |
| Префиксный ID | При вводе неполного ID проверяется уникальность; если найдено несколько — ошибка |
| Нет внешних зависимостей | Весь код на стандартной библиотеке Python |

---

## Язык вывода (i18n)

CLI поддерживает русский и английский язык вывода.

- **По умолчанию**: русский
- **Английский**: флаг `--lang en`, например `opencode-db --lang en list`

```bash
opencode-db list                  # русский (по умолчанию)
opencode-db --lang en list        # английский
opencode-db --lang en help        # справка на английском
opencode-db --lang en stats       # статистика на английском
```

Флаг `--lang` работает с любой командой. Переведены все 238 строк интерфейса. Содержимое данных (названия сессий, проектов и т.д.) остаётся на языке оригинала.

Язык также можно задать через переменную окружения `OPENCODE_DB_LANG=en`.

---

## Зависимости

- **Python 3.10+** — вся функциональность на стандартной библиотеке
- **SQLite** — встроенный модуль `sqlite3`
- **OpenCode** — нужна установленная и хотя бы раз запущенная программа (создаёт БД)

Никаких `pip install`, `npm`, `brew` или других пакетных менеджеров не требуется.

---

## Troubleshooting

### «База OpenCode не найдена»

```
❌ База OpenCode не найдена: ~/.local/share/opencode/opencode.db
```

OpenCode ещё не запускался или БД находится в нестандартном месте. Убедитесь что:
- OpenCode установлен и хотя бы один раз запущен
- Файл `~/.local/share/opencode/opencode.db` существует

### «Найдено несколько сессий с префиксом»

```
❌ Найдено несколько сессий с префиксом ses_1c9d:
    ses_1c9d9fa58ffeiqsrHGVg8MPZes
    ses_1c9d8fa58ffeabc123def456xyz
```

Уточните ID — используйте более длинный префикс или полный ID (можно узнать через `list --json`).

### Ошибка VACUUM

Если БД используется другим процессом (например, открыта в OpenCode), VACUUM может не выполниться. Закройте OpenCode и повторите.

---

## Разработка

### Добавление новой команды

1. Создайте `cmd_xxx.py`:

```python
def register(subparsers):
    p = subparsers.add_parser("xxx", help="Описание")
    p.add_argument("--flag", type=str)

def run(args, db):
    # ваша логика
    return 0
```

2. Зарегистрируйте в `commands/__init__.py`:

```python
import cmd_xxx
COMMANDS["xxx"] = cmd_xxx
```

Готово. Команда появится в `--help` автоматически.

### Локальный запуск без установки

```bash
python3 ~/.local/share/opencode-db list
```

Или через модуль:

```bash
python3 -m opencode_db list
```

---

## Лицензия

MIT. Используйте свободно.
