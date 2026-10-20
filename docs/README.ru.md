# opencode-db

**Управление базой данных OpenCode: просмотр, экспорт, аналитика и очистка сессий.**

`opencode-db` — это CLI-утилита для работы с локальной базой данных OpenCode (SQLite). Она позволяет просматривать историю диалогов с AI-ассистентом, экспортировать диалоги в Markdown, анализировать расход токенов и стоимость, управлять хранилищем — удалять ненужные сессии и оптимизировать БД.

[English version](../README.md)

> **Опубликовано на PyPI:** [opencode-db](https://pypi.org/project/opencode-db/) — готовый пакет можно установить через `uv tool install opencode-db` или `pip install opencode-db`.

```
opencode-db --version     # версия установленной программы
opencode-db help        # все команды, примеры, флаги
opencode-db list        # последние сессии
opencode-db stats       # сводка по всей БД
opencode-db schema      # определить схему v1/v2
opencode-db export      # сохранить диалог в .md (интерактивно)
opencode-db costs --total  # общие расходы
```

---

## Установка

### Требования

- Python 3.12+ — при более старом интерпретаторе `opencode-db` завершается с понятным сообщением вместо `ImportError`
- OpenCode (должен быть хотя бы раз запущен — создаётся БД)
- macOS / Linux
- [`uv`](https://docs.astral.sh/uv/) — опционально, но рекомендуется, если системный `python3` старее 3.12

### Расположение базы данных

По умолчанию `opencode-db` ищет БД OpenCode в стандартном пути:

```
~/.local/share/opencode/opencode.db
```

Если твой OpenCode хранит БД в другом месте — есть два способа указать путь:

**1. Переменная окружения** — задаётся один раз в профиле (`.zshrc`, `.bashrc`):

```bash
export OPENCODE_DB=/путь/к/opencode.db
```

**2. Глобальный флаг `--db-path`** — для разовых задач или просмотра другой БД:

```bash
opencode-db --db-path /путь/к/opencode.db list
opencode-db --db-path /путь/к/opencode.db stats
```

Флаг `--db-path` имеет приоритет над переменной окружения.

### Рекомендуется: uv

Если системный `python3` старее 3.12 (например, на macOS это Python 3.9), используйте `uv` — он установит утилиту в изолированное окружение с подходящим интерпретатором:

```bash
uv tool install opencode-db
# с улучшенным Markdown-рендерингом:
uv tool install "opencode-db[rich]"

# разовый запуск без установки:
uvx opencode-db stats
```

### Установка одной командой

```bash
curl -fsSL https://raw.githubusercontent.com/VasilevNStas/opencode-db/master/install.sh | sh
```

Скрипт скачивает код в `~/.local/share/opencode-db/` и создаёт `~/.local/bin/opencode-db`. Installer ищет Python 3.12+ (включая интерпретаторы, установленные через `uv` или `pyenv`) и записывает найденный путь в shebang launcher'а.

### pip / pipx

```bash
pipx install opencode-db
# или
pip install opencode-db
```

Внешних зависимостей нет — только стандартная библиотека Python (`rich` опционален).

### Ручная установка

1. Скачайте релиз или склонируйте репозиторий:

```bash
git clone https://github.com/VasilevNStas/opencode-db.git ~/.local/share/opencode-db
```

2. Создайте лаунчер в `~/.local/bin/opencode-db`:

```bash
cat > ~/.local/bin/opencode-db << 'SCRIPT'
#!/usr/bin/env python3
"""Лаунчер opencode-db."""
import os
import sys

if sys.version_info < (3, 12):
    print(
        "opencode-db requires Python 3.12+; current: %s (%s)"
        % (".".join(map(str, sys.version_info[:3])), sys.executable),
        file=sys.stderr,
    )
    raise SystemExit(1)

PKG_DIR = os.path.expanduser("~/.local/share/opencode-db")
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)
from opencode_db.cli import main
sys.exit(main())
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
opencode-db list --all --directory       # показать директории
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
| `--directory` | Добавить колонку директории | — |

---

### `directories` — директории запусков

Показывает все директории, где запускался OpenCode, включая уже отсутствующие. Объединяет `session.directory`, корни проектов и `project_directory`.

```bash
opencode-db directories                  # группировка по путям
opencode-db directories --missing        # только отсутствующие/недоступные
opencode-db directories --existing       # только существующие
opencode-db directories --project global # сессии Global по реальным путям
opencode-db directories --json           # полные пути, счётчики, токены, стоимость
```

`global` — синтетический проект для директорий вне Git. Команда не показывает
`/` как реальную директорию: видны настоящие `session.directory`, а проект
помечен как `Global (без корня)`.

| Флаг | Описание | По умолчанию |
|---|---|---|
| `--missing` | Только пути, не найденные на диске | — |
| `--existing` | Только существующие пути | — |
| `--project ID` | Фильтр по проекту | — |
| `--sort {date,sessions,cost,path}` | Сортировка | date |
| `--limit N` | Макс. записей | 50 |
| `--no-check` | Не проверять файловую систему (`exists: null`) | — |
| `--json` | Вывод в JSON | — |

> `os.path.isdir()` — проверка на момент выполнения. Отключённый диск или ошибка прав может выглядеть как отсутствующая директория.

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

### `delete` — удаление сессий

Удаляет сессии и все связанные данные (сообщения, части, todo). Поддерживает удаление по ID или массовое с фильтрами.

```bash
opencode-db delete ses_1c9d                              # одна сессия с подтверждением
opencode-db delete ses_1c9d --force                      # одна сессия без подтверждения
opencode-db delete ses_1c9d --dry-run                    # показать что будет удалено
opencode-db delete --older-than 90d                      # сессии старше 90 дней
opencode-db delete --older-than 6m --dry-run             # предпросмотр старше 6 месяцев
opencode-db delete --keep-last 30                        # оставить 30 последних
opencode-db delete --before 2026-05-20                   # сессии до даты
opencode-db delete --after 2026-01-01                    # сессии после даты
opencode-db delete --project proj_xxx                    # по проекту
opencode-db delete --older-than 90d --keep-last 20       # комбинация фильтров
opencode-db delete --interactive                         # выбор из списка
opencode-db prune --missing-directories                  # preview сессий из отсутствующих путей
```

| Флаг | Описание |
|---|---|
| `session_id` | ID сессии (опционально с `--interactive`) |
| `--older-than` | Удалить старше (например `30d`, `6m`, `1y`) |
| `--before` | Удалить до даты (`ГГГГ-ММ-ДД`) |
| `--after` | Удалить после даты (`ГГГГ-ММ-ДД`) |
| `--keep-last` | Оставить N последних |
| `--project` | Фильтр по проекту |
| `--dry-run` | Только показать что будет удалено |
| `--force`, `-f` | Без подтверждения |
| `--interactive` | Выбор из списка |
| `--missing-directories` | Сессии, чья директория больше не существует (по умолчанию preview) |
| `--execute` | Выполнить очистку отсутствующих директорий |
| `--backup` | Создать backup БД перед удалением |
| `--no-backup` | Явно пропустить backup |

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

### `prune` — alias для `delete`

Псевдоним команды `delete` с теми же флагами: `--older-than`, `--keep-last`, `--project`, `--dry-run`, `--force`.

```bash
opencode-db prune --older-than 90d   # то же что opencode-db delete --older-than 90d
opencode-db prune --keep-last 20     # то же что opencode-db delete --keep-last 20
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

### Очистка отсутствующих директорий

OpenCode хранит директорию запуска каждой сессии в `session.directory`. TUI
показывает сессии только для текущего проекта, поэтому сессии из удалённой,
переименованной или отключённой директории легко потерять. Этот режим находит
такие сессии и удаляет их только после нескольких независимых подтверждений.

#### 1. Сначала посмотри кандидатов (безопасно)

```bash
opencode-db directories --missing
opencode-db directories --missing --json
opencode-db prune --missing-directories
opencode-db prune --missing-directories --project global
```

`directories --missing` — самый безопасный первый шаг: база не изменяется,
показываются те же пути, количество сессий и стоимость.

Пример preview:

```text
============================================================
  ОЧИСТКА СЕССИЙ ИЗ ОТСУТСТВУЮЩИХ ДИРЕКТОРИЙ
============================================================
  База: ~/.local/share/opencode/opencode.db
  Сессий: 51, директорий: 10, стоимость: $3.85
  2026-05-06 08:19:14 — 2026-09-12 16:45:41
    /Users/me/old-project — 15 сессий
    /Users/me/Documents/old-notes — 7 сессий
...
Это preview. Для удаления добавь --execute.
```

Как определяется «отсутствует»:

- читается `session.directory` (или `session_v2.directory`);
- для каждого пути выполняется `os.path.isdir()` в момент запуска команды;
- `False` означает **не найдена или недоступна** — директория может быть
  удалена, переименована, лежать на отключённом диске или сетевой шаре, либо
  быть недоступной из-за прав;
- симлинки разыменовываются; результат актуален только на момент проверки;
- `--no-check` у `directories` отключает проверку и возвращает `exists: null`.

Внимательно смотри список. Внешний диск, который сейчас не подключён, выглядит
точно так же, как удалённая директория.

#### 2. Выполнение с защитами

```bash
# рекомендуемый вариант: сначала консистентный backup SQLite
opencode-db prune --missing-directories --execute --backup

# только если у тебя уже есть внешний backup
opencode-db prune --missing-directories --execute --no-backup
```

`delete --missing-directories ...` работает так же, как `prune`.

Перед удалением должны пройти все проверки:

1. `--missing-directories` выбирает только сессии с не найденным путём.
2. Нужен `--execute`; без него команда всегда останавливается на preview.
3. Нужно явно выбрать `--backup` или `--no-backup`.
4. Показываются все пути, число сессий, стоимость и диапазон дат.
5. Нужно ввести точную фразу `DELETE <N> SESSIONS`.
6. Нужно ответить на финальный вопрос `y/N`.
7. Список кандидатов пересчитывается; если он изменился — удаление отменяется.
8. Все удаления идут в одной транзакции; при ошибке выполняется rollback.

`--force` **не** обходит эти проверки. В этом режиме он игнорируется.

#### Что именно удаляется

Для каждой выбранной сессии:

- строка `session`;
- `message`, `part`, `todo`;
- `session_message`, `session_input`, `session_context_epoch`, `session_share`;
- строки `event` и `event_sequence` этой сессии.

Проекты и синтетический проект `global` **никогда** не удаляются. Директории
на диске команда не трогает — удаляются только строки в БД.

После успешной очистки можно освободить место:

```bash
opencode-db vacuum
```

`VACUUM` может занять время и временно требует свободного места примерно
размером с базу.

#### Backup и восстановление

С `--backup` создаётся консистентная копия SQLite рядом с базой:

```text
opencode.db.bak.20261020-111530
```

Точный путь печатается перед удалением. Если удалил лишнее:

1. останови OpenCode;
2. восстанови backup поверх `opencode.db`;
3. удали устаревшие `opencode.db-wal` / `opencode.db-shm`, если они есть;
4. запусти OpenCode снова.

Без backup удалённые сессии и их события восстановить нельзя.

#### Рекомендуемый порядок

```bash
# 1. Закрой OpenCode, чтобы не было конкурентных записей.
opencode-db directories --missing

# 2. Посмотри точный preview удаления.
opencode-db prune --missing-directories

# 3. Опционально: только один проект.
opencode-db prune --missing-directories --project global

# 4. Выполни с backup.
opencode-db prune --missing-directories --execute --backup

# 5. Освободи место.
opencode-db vacuum
```

#### Ограничения

- Режим доступен для v1-схемы; на v2 он отклоняется до реализации записи.
- Нельзя отличить удалённую директорию от отключённого диска или ошибки прав.
- Строки `project` и директории на диске не удаляются.
- Нельзя сочетать с `--older-than`, `--before`, `--after`, `--keep-last`,
  `--interactive` или ID сессии.
- Автоматической или фоновой очистки нет.

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
opencode-db projects                      # проекты с путями
opencode-db projects --json               # в JSON
opencode-db projects --missing            # проекты с отсутствующим путём
opencode-db projects --no-global          # скрыть синтетический Global
```

| Флаг | Описание |
|---|---|
| `--json` | Вывод в JSON |
| `--missing` | Только проекты с отсутствующим путём |
| `--no-global` | Скрыть синтетический Global |

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

### `schema` — определение схемы БД

Показывает семейство схемы OpenCode, применённую миграцию и доступные операции.

```bash
opencode-db schema                        # краткая сводка
opencode-db schema --json                 # в JSON
```

Поддерживаемые семейства:

| OpenCode | Схема | Поддержка |
|---|---|---|
| 1.19.x | v1 | чтение + запись |
| 2.x preview | v2 | только чтение |

На v2-базе `delete`, `prune` и `vacuum` отклоняются до реализации записи. Определение идёт по таблицам и журналу миграций, а не по строке версии OpenCode.

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
opencode-db/
├── opencode_db/                          ← Python-пакет (устанавливается как opencode_db)
│   ├── __init__.py                       ← init пакета + проверка Python
│   ├── __main__.py                       ← python3 -m opencode_db
│   ├── cli.py                            ← argparse + диспетчер команд
│   ├── config.py                         ← константы и пути
│   ├── db.py                             ← запросы к SQLite
│   ├── formatters.py                     ← таблицы, JSON, Markdown, snapshot
│   ├── i18n.py                           ← локализация (EN/RU, 348 ключей)
│   ├── markdown_to_ansi.py               ← Markdown → ANSI для `view`
│   ├── runtime.py                        ← проверка Python 3.12+
│   ├── utils.py                          ← форматирование дат, токенов, валидация
│   └── commands/
│       ├── __init__.py                   ← реестр команд
│       ├── cmd_list.py                   ← opencode-db list
│       ├── cmd_info.py                   ← opencode-db info
│       ├── cmd_export.py                 ← opencode-db export
│       ├── cmd_delete.py                 ← opencode-db delete
│       ├── cmd_costs.py                  ← opencode-db costs
│       ├── cmd_prune.py                  ← opencode-db prune
│       ├── cmd_search.py                 ← opencode-db search
│       ├── cmd_tree.py                   ← opencode-db tree
│       ├── cmd_projects.py               ← opencode-db projects
│       ├── cmd_stats.py                  ← opencode-db stats
│       ├── cmd_todos.py                  ← opencode-db todos
│       ├── cmd_vacuum.py                 ← opencode-db vacuum
│       ├── cmd_view.py                   ← opencode-db view
│       └── cmd_help.py                   ← opencode-db help
│
├── docs/
│   ├── README.ru.md                      ← эта документация
│   └── README_PYPI.md                    ← страница PyPI
├── contrib/
│   └── opencode-db-commands.json         ← команды для OpenCode TUI
├── tests/
├── README.md                             ← английская документация
├── LICENSE
├── Makefile
├── pyproject.toml
└── install.sh
```

### Как это работает

1. Console script `opencode-db` (или `python3 -m opencode_db`) импортирует `opencode_db.cli` и вызывает `main()`.
2. `runtime.require_python()` проверяет интерпретатор до импорта `cli`/`db`: на Python < 3.12 выводится понятное сообщение с командами исправления вместо `ImportError`.
3. `cli.py` собирает `argparse` с subparser'ами от всех команд и диспетчеризирует вызов.
4. Каждая команда — отдельный модуль `opencode_db/commands/cmd_*.py` с двумя функциями: `register(subparsers)` и `run(args, db)`.
5. `db.py` открывает соединение с SQLite-базой OpenCode (`~/.local/share/opencode/opencode.db`, с fallback на `opencode-next.db`) и определяет семейство схемы.
6. `store/` выбирает `V1Store` или `V2Store`; команды читают через единый интерфейс независимо от схемы.
7. Для опасных операций (`delete`, `prune`) используется подтверждение через `input()`; на v2 они отклоняются до реализации записи.

### Схема базы данных (ключевые таблицы)

Стабильный OpenCode 1.19.x (v1):

```
session        — сессии: id, title, model (JSON), agent, cost, tokens_*, parent_id, summary_*
message        — сообщения: id, session_id, time_created, data (JSON: role, agent)
part           — части сообщений: id, message_id, session_id, data (JSON: type, text, state)
todo           — задачи: session_id, content, status, priority
project        — проекты: id, worktree, name
```

Preview OpenCode 2.x (v2):

```
session_v2      — переименованная таблица сессий с теми же полями расхода
session_message — типизированные JSON-сообщения: user, assistant, synthetic, system, shell, compaction, ...
project         — проекты: id, worktree, name, time_active, ...
```

В v2 нет таблиц `message`, `part` и `todo`. Контент assistant вложен в
`session_message.data.content`, а задачи вычисляются из последнего завершённого
вызова инструмента `todowrite`. Перед записывающими командами проверяйте
семейство через `opencode-db schema`.

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

Добавь команды из `contrib/opencode-db-commands.json` в `opencode.json` проекта:

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
~/.local/share/opencode-db/contrib/opencode-db-commands.json
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

Флаг `--lang` работает с любой командой. Переведены все 348 строк интерфейса. Содержимое данных (названия сессий, проектов и т.д.) остаётся на языке оригинала.

Язык также можно задать через переменную окружения `OPENCODE_DB_LANG=en`.

---

## Зависимости

- **Python 3.12+** — вся функциональность на стандартной библиотеке
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

### `ImportError: cannot import name 'UTC' from 'datetime'`

`opencode-db` запущен на Python старше 3.12 (например, на системном Python 3.9). Проверьте:

```bash
python3 --version
```

Исправление через `uv` (рекомендуется):

```bash
uv python install 3.13
uv tool install opencode-db
opencode-db stats
```

Или запуск из репозитория с явным интерпретатором:

```bash
uv run --python 3.13 opencode-db stats
```

После смены интерпретатора перезапустите `install.sh`, чтобы пересоздать launcher `~/.local/bin/opencode-db`.

---

## Разработка

### Локальная разработка

Нужны Python 3.12+ и `pytest`/`ruff`:

```bash
git clone https://github.com/VasilevNStas/opencode-db.git
cd opencode-db

uv venv --python 3.13
source .venv/bin/activate
uv pip install -e ".[rich]"
uv pip install pytest ruff==0.17.1

make check          # check-python + ruff + 224 тестов
```

`make check` сразу завершается с понятной ошибкой, если активный интерпретатор старее 3.12.

### Добавление новой команды

1. Создайте `opencode_db/commands/cmd_xxx.py`:

```python
def register(subparsers):
    p = subparsers.add_parser("xxx", help="Описание")
    p.add_argument("--flag", type=str)

def run(args, db):
    # ваша логика
    return 0
```

2. Зарегистрируйте в `opencode_db/commands/__init__.py`:

```python
import cmd_xxx
COMMANDS["xxx"] = cmd_xxx
```

Готово. Команда появится в `--help` автоматически.

### Локальный запуск без установки

```bash
python3 ~/.local/share/opencode-db list
```

Или из корня репозитория (Python 3.12+):

```bash
python3 -m opencode_db list
uvx --from . opencode-db list
```

---

## Лицензия

MIT. Используйте свободно.
