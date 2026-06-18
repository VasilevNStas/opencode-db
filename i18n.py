"""Интернационализация: поддержка русского и английского языка.

Использование:
  from i18n import _, set_lang

  set_lang("en")
  print(_("list.header.id"))          # → "ID"
  print(_("export.saved", path="f"))  # → "✅ Диалог сохранён: f"

Структура словаря:
  L[ключ] = {"ru": "...", "en": "..."}

Если ключа нет — возвращается сам ключ.
Если язык не указан — русский (по умолчанию).
"""

import os

current_lang = os.environ.get("OPENCODE_DB_LANG", "ru")


L: dict[str, dict[str, str]] = {
    # ==================================================================
    # ГЛОБАЛЬНЫЕ
    # ==================================================================
    "db.not_found": {
        "ru": "❌ База OpenCode не найдена: {path}",
        "en": "❌ OpenCode database not found: {path}",
    },
    "db.not_found_hint": {
        "ru": "   Убедись, что opencode установлен и хотя бы раз запускался.",
        "en": "   Make sure OpenCode is installed and has been run at least once.",
    },
    "session.not_found": {
        "ru": "❌ Сессия {session_id} не найдена",
        "en": "❌ Session {session_id} not found",
    },
    "session.no_sessions": {
        "ru": "❌ Нет сессий в базе",
        "en": "❌ No sessions in the database",
    },
    "session.multiple_match": {
        "ru": "❌ Найдено несколько сессий с префиксом {session_id}:",
        "en": "❌ Multiple sessions match prefix {session_id}:",
    },
    "session.specify_id": {
        "ru": "   Уточни ID",
        "en": "   Use a longer prefix or the full ID",
    },
    "session.latest": {
        "ru": "  🕐 Последняя сессия: {title}",
        "en": "  🕐 Latest session: {title}",
    },
    "cmd.unknown": {
        "ru": "❌ Неизвестная команда: {cmd}",
        "en": "❌ Unknown command: {cmd}",
    },
    "empty": {
        "ru": "  (пусто)",
        "en": "  (empty)",
    },
    "total_count": {
        "ru": "  Всего: {n}",
        "en": "  Total: {n}",
    },
    "canceled": {
        "ru": "  Отменено.",
        "en": "  Canceled.",
    },
    "yes_no_prompt": {
        "ru": "Подтвердить операцию?",
        "en": "Proceed with the operation?",
    },
    "yes_no_true": {
        "ru": " [Y/n]: ",
        "en": " [Y/n]: ",
    },
    "yes_no_false": {
        "ru": " [y/N]: ",
        "en": " [y/N]: ",
    },
    "not_obsidian": {
        "ru": "ℹ️ log.md пропущен (не Obsidian-проект)",
        "en": "ℹ️ log.md skipped (not an Obsidian project)",
    },
    "log_updated": {
        "ru": "✅ log.md обновлён: {path}",
        "en": "✅ log.md updated: {path}",
    },
    # ==================================================================
    # LIST
    # ==================================================================
    "list.header.id": {"ru": "ID", "en": "ID"},
    "list.header.title": {"ru": "Название", "en": "Title"},
    "list.header.project": {"ru": "Проект", "en": "Project"},
    "list.header.model": {"ru": "Модель", "en": "Model"},
    "list.header.activity": {"ru": "Активность", "en": "Activity"},
    "list.header.messages": {"ru": "Сообщ.", "en": "Msgs"},
    "list.header.cost": {"ru": "Стоимость", "en": "Cost"},
    # ==================================================================
    # INFO
    # ==================================================================
    "info.id": {"ru": "ID", "en": "ID"},
    "info.project": {"ru": "Проект", "en": "Project"},
    "info.model": {"ru": "Модель", "en": "Model"},
    "info.agent": {"ru": "Агент", "en": "Agent"},
    "info.version": {"ru": "Версия", "en": "Version"},
    "info.created": {"ru": "Создана", "en": "Created"},
    "info.updated": {"ru": "Активна", "en": "Last active"},
    "info.duration": {"ru": "Длит-сть", "en": "Duration"},
    "info.parent": {"ru": "Родитель", "en": "Parent"},
    "info.branches": {"ru": "Веток", "en": "Children"},
    "info.messages": {"ru": "Сообщений", "en": "Messages"},
    "info.parts": {"ru": "Частей", "en": "Parts"},
    "info.tokens_input": {"ru": "Токены ввода", "en": "Input tokens"},
    "info.tokens_output": {"ru": "Токены вывода", "en": "Output tokens"},
    "info.tokens_reasoning": {"ru": "Токены reasoning", "en": "Reasoning tokens"},
    "info.cache_read": {"ru": "Кэш (чтение)", "en": "Cache (read)"},
    "info.cache_write": {"ru": "Кэш (запись)", "en": "Cache (write)"},
    "info.tokens_total": {"ru": "Всего токенов", "en": "Total tokens"},
    "info.cost": {"ru": "Стоимость", "en": "Cost"},
    "info.code_changes": {"ru": "Изменения кода", "en": "Code changes"},
    "info.files_changed": {"ru": "Файлов", "en": "Files"},
    "info.lines_added": {"ru": "Добавлено", "en": "Added"},
    "info.lines_deleted": {"ru": "Удалено", "en": "Deleted"},
    "info.todos": {"ru": "Задачи (todo)", "en": "Tasks (todo)"},
    "info.todos_status": {
        "ru": "Статус: {status}, создано: {created}",
        "en": "Status: {status}, created: {created}",
    },
    "info.unnamed": {"ru": "Безымянная сессия", "en": "Unnamed session"},
    "info.children_prefix": {"ru": "    └─ {id} — {title}", "en": "    └─ {id} — {title}"},
    "info.parent_fmt": {"ru": "  {id} — {title}", "en": "  {id} — {title}"},
    "info.not_found": {
        "ru": "❌ Сессия {session_id} не найдена",
        "en": "❌ Session {session_id} not found",
    },
    # ==================================================================
    # EXPORT
    # ==================================================================
    "export.saved": {"ru": "✅ Диалог сохранён: {path}", "en": "✅ Dialog saved: {path}"},
    "export.messages": {"ru": "   Сообщений: {n}", "en": "   Messages: {n}"},
    "export.exists": {
        "ru": "❌ Файл уже существует: {path}",
        "en": "❌ File already exists: {path}",
    },
    "export.exists_hint": {
        "ru": "   Используй --force для перезаписи",
        "en": "   Use --force to overwrite",
    },
    "export.interactive_header": {"ru": "Последние сессии:", "en": "Recent sessions:"},
    "export.interactive_prompt": {
        "ru": "Выбери номер (или Enter для отмены): ",
        "en": "Pick a number (or Enter to cancel): ",
    },
    "export.interactive_error": {
        "ru": "Введи число от 1 до {n}",
        "en": "Enter a number from 1 to {n}",
    },
    "export.interactive_exporting": {"ru": "  Экспорт: {title}", "en": "  Exporting: {title}"},
    "export.no_sessions": {"ru": "❌ Нет сессий для экспорта.", "en": "❌ No sessions to export."},
    "export.interactive_abort": {"ru": "  Отменено.", "en": "  Canceled."},
    # ==================================================================
    # DELETE
    # ==================================================================
    "delete.header": {"ru": "УДАЛЕНИЕ СЕССИИ", "en": "DELETE SESSION"},
    "delete.id": {"ru": "ID", "en": "ID"},
    "delete.title": {"ru": "Название", "en": "Title"},
    "delete.model": {"ru": "Модель", "en": "Model"},
    "delete.created": {"ru": "Создана", "en": "Created"},
    "delete.messages": {"ru": "Сообщений", "en": "Messages"},
    "delete.parts": {"ru": "Частей", "en": "Parts"},
    "delete.cost": {"ru": "Стоимость", "en": "Cost"},
    "delete.dry_run": {
        "ru": "  🔍 Сухой запуск — ничего не удалено.",
        "en": "  🔍 Dry run — nothing deleted.",
    },
    "delete.dry_run_hint": {
        "ru": "  Для удаления запусти без --dry-run",
        "en": "  Run without --dry-run to actually delete",
    },
    "delete.confirm": {"ru": "Удалить сессию {id}?", "en": "Delete session {id}?"},
    "delete.done": {"ru": "  ✅ Сессия удалена: {id}…", "en": "  ✅ Session deleted: {id}…"},
    "delete.done_detail": {
        "ru": "     Сообщений: {msg}, частей: {parts}",
        "en": "     Messages: {msg}, parts: {parts}",
    },
    # ==================================================================
    # COSTS
    # ==================================================================
    "costs.session": {"ru": "Сессия", "en": "Session"},
    "costs.model": {"ru": "Модель", "en": "Model"},
    "costs.input": {"ru": "Ввод", "en": "Input"},
    "costs.output": {"ru": "Вывод", "en": "Output"},
    "costs.reasoning": {"ru": "Reasoning", "en": "Reasoning"},
    "costs.total": {"ru": "Всего", "en": "Total"},
    "costs.cost": {"ru": "Стоимость", "en": "Cost"},
    "costs.total_header": {"ru": "ИТОГО ПО {scope}", "en": "TOTAL BY {scope}"},
    "costs.scope_all": {"ru": "ВСЕЙ БД", "en": "DATABASE"},
    "costs.scope_project": {"ru": "ПРОЕКТУ", "en": "PROJECT"},
    "costs.sessions": {"ru": "Сессий", "en": "Sessions"},
    "costs.tokens_input": {"ru": "Токенов ввода", "en": "Input tokens"},
    "costs.tokens_output": {"ru": "Токенов вывода", "en": "Output tokens"},
    "costs.tokens_reasoning": {"ru": "Токенов reasoning", "en": "Reasoning tokens"},
    "costs.tokens_total": {"ru": "Всего токенов", "en": "Total tokens"},
    "costs.cache_read": {"ru": "Кэш (чтение)", "en": "Cache (read)"},
    "costs.cache_write": {"ru": "Кэш (запись)", "en": "Cache (write)"},
    # ==================================================================
    # PRUNE
    # ==================================================================
    "prune.header": {"ru": "Будет удалено сессий: {n}", "en": "Sessions to delete: {n}"},
    "prune.none": {"ru": "  ✅ Нет сессий для удаления.", "en": "  ✅ No sessions to delete."},
    "prune.filter_required": {
        "ru": "❌ Укажи хотя бы один фильтр: --older-than, --keep-last или --project",
        "en": "❌ Specify at least one filter: --older-than, --keep-last, or --project",
    },
    "prune.filter_example": {
        "ru": "   Пример: opencode-db prune --older-than 90d --dry-run",
        "en": "   Example: opencode-db prune --older-than 90d --dry-run",
    },
    "prune.bad_spec": {
        "ru": "❌ Не могу разобрать: --older-than {spec}",
        "en": "❌ Cannot parse: --older-than {spec}",
    },
    "prune.bad_spec_hint": {
        "ru": "   Используй формат: 30d, 90d, 6m, 1y",
        "en": "   Use format: 30d, 90d, 6m, 1y",
    },
    "prune.dry_run": {
        "ru": "  🔍 Сухой запуск — ничего не удалено.",
        "en": "  🔍 Dry run — nothing deleted.",
    },
    "prune.confirm": {"ru": "Удалить {n} сессий?", "en": "Delete {n} sessions?"},
    "prune.done": {"ru": "  ✅ Удалено {n} сессий.", "en": "  ✅ Deleted {n} sessions."},
    "prune.cost_total": {
        "ru": "Стоимость удаляемых: {cost}",
        "en": "Cost of deleted sessions: {cost}",
    },
    "prune.tokens_total": {"ru": "Освободится токенов: ~{n}", "en": "Tokens freed: ~{n}"},
    # ==================================================================
    # SEARCH
    # ==================================================================
    "search.header": {
        "ru": "🔍 Результаты поиска: «{query}»",
        "en": "🔍 Search results: «{query}»",
    },
    "search.none": {
        "ru": "\n  🔍 Ничего не найдено по запросу: {query}",
        "en": "\n  🔍 Nothing found for: {query}",
    },
    "search.found": {"ru": "Найдено: {n}", "en": "Found: {n}"},
    # ==================================================================
    # TREE
    # ==================================================================
    "tree.header": {
        "ru": "🌳 Дерево сессий (от: {title})",
        "en": "🌳 Session tree (from: {title})",
    },
    "tree.header_all": {
        "ru": "🌳 Все корневые сессии (ветвление)",
        "en": "🌳 All root sessions (branching)",
    },
    "tree.header_project": {
        "ru": "🌳 Дерево сессий проекта {project}",
        "en": "🌳 Session tree for project {project}",
    },
    # ==================================================================
    # PROJECTS
    # ==================================================================
    "projects.header.id": {"ru": "ID", "en": "ID"},
    "projects.header.name": {"ru": "Название", "en": "Name"},
    "projects.header.activity": {"ru": "Активность", "en": "Activity"},
    "projects.header.sessions": {"ru": "Сессии", "en": "Sessions"},
    "projects.header.tokens": {"ru": "Токены", "en": "Tokens"},
    "projects.header.cost": {"ru": "Стоимость", "en": "Cost"},
    # ==================================================================
    # STATS
    # ==================================================================
    "stats.header": {"ru": "📊 СТАТИСТИКА БАЗЫ OPENCODE", "en": "📊 OPENCODE DATABASE STATISTICS"},
    "stats.projects": {"ru": "Проектов", "en": "Projects"},
    "stats.sessions": {"ru": "Сессий", "en": "Sessions"},
    "stats.messages": {"ru": "Сообщений", "en": "Messages"},
    "stats.parts": {"ru": "Частей", "en": "Parts"},
    "stats.todos": {"ru": "Задач (todo)", "en": "Tasks (todo)"},
    "stats.first_session": {"ru": "Первая сессия", "en": "First session"},
    "stats.last_session": {"ru": "Последняя", "en": "Last session"},
    "stats.tokens_input": {"ru": "Токенов ввода", "en": "Input tokens"},
    "stats.tokens_output": {"ru": "Токенов вывода", "en": "Output tokens"},
    "stats.tokens_reasoning": {"ru": "Токенов reasoning", "en": "Reasoning tokens"},
    "stats.tokens_total": {"ru": "Всего токенов", "en": "Total tokens"},
    "stats.cost": {"ru": "Стоимость", "en": "Cost"},
    "stats.top_models": {"ru": "Топ моделей", "en": "Top models"},
    "stats.agents": {"ru": "Агенты", "en": "Agents"},
    # ==================================================================
    # TODOS
    # ==================================================================
    "todos.header": {"ru": "📝 Задачи ({n})", "en": "📝 Tasks ({n})"},
    "todos.none": {"ru": "\n  📝 Нет задач.", "en": "\n  📝 No tasks."},
    "todos.session": {"ru": "Сессия", "en": "Session"},
    "todos.status": {"ru": "Статус", "en": "Status"},
    "todos.created": {"ru": "создано", "en": "created"},
    # ==================================================================
    # VACUUM
    # ==================================================================
    "vacuum.header": {"ru": "🗄️  Оптимизация базы данных", "en": "🗄️  Database optimization"},
    "vacuum.size_before": {"ru": "Размер до", "en": "Size before"},
    "vacuum.size_after": {"ru": "Размер после", "en": "Size after"},
    "vacuum.path": {"ru": "Путь", "en": "Path"},
    "vacuum.freed": {"ru": "Освобождено", "en": "Freed"},
    "vacuum.vacuum": {"ru": "Выполняется VACUUM...", "en": "Running VACUUM..."},
    "vacuum.reindex": {"ru": "Выполняется REINDEX...", "en": "Running REINDEX..."},
    "vacuum.analyze": {"ru": "Выполняется ANALYZE...", "en": "Running ANALYZE..."},
    "vacuum.confirm": {"ru": "Запустить VACUUM?", "en": "Run VACUUM?"},
    "vacuum.error": {"ru": "❌ Ошибка: {error}", "en": "❌ Error: {error}"},
    "vacuum.done": {"ru": "✅", "en": "✅"},
    "vacuum.canceled": {"ru": "  Отменено.", "en": "  Canceled."},
    # ==================================================================
    # HELP
    # ==================================================================
    "help.header_box_top": {
        "ru": "╔══════════════════════════════════════════════════════════╗",
        "en": "╔══════════════════════════════════════════════════════════╗",
    },
    "help.header_title": {
        "ru": "║                 opencode-db — справка                    ║",
        "en": "║                 opencode-db — help                       ║",
    },
    "help.header_box_bottom": {
        "ru": "╚══════════════════════════════════════════════════════════╝",
        "en": "╚══════════════════════════════════════════════════════════╝",
    },
    "help.intro": {
        "ru": "opencode-db — управление базой данных OpenCode:",
        "en": "opencode-db — OpenCode database manager:",
    },
    "help.intro2": {
        "ru": "просмотр, экспорт, аналитика, очистка сессий.",
        "en": "browse, export, analyze, clean up sessions.",
    },
    "help.usage": {
        "ru": "Использование: opencode-db <команда> [флаги]",
        "en": "Usage: opencode-db <command> [flags]",
    },
    "help.footer": {
        "ru": "opencode-db help <команда>  — справка по конкретной команде",
        "en": "opencode-db help <command>  — help for a specific command",
    },
    "help.footer2": {
        "ru": "opencode-db <команда> --help  — флаги команды",
        "en": "opencode-db <command> --help  — command flags",
    },
    "help.footer3": {
        "ru": "opencode-db --help          — краткий список команд",
        "en": "opencode-db --help          — brief command list",
    },
    "help.unknown": {"ru": "❌ Неизвестная команда: {cmd}", "en": "❌ Unknown command: {cmd}"},
    "help.available": {"ru": "   Доступные: {cmds}", "en": "   Available: {cmds}"},
    "help.usage_header": {
        "ru": "Примеры использования команды {cmd}:",
        "en": "Usage examples for {cmd}:",
    },
    "help.flags_header": {
        "ru": "Все доступные флаги для {cmd}:",
        "en": "Available flags for {cmd}:",
    },
    # ==================================================================
    # HELP — команды (краткие описания в справке)
    # ==================================================================
    "help.cmd.list": {"ru": "Список сессий", "en": "List sessions"},
    "help.cmd.info": {"ru": "Детальная информация о сессии", "en": "Session details"},
    "help.cmd.export": {"ru": "Экспорт диалога в Markdown", "en": "Export dialog to Markdown"},
    "help.cmd.delete": {"ru": "Удаление сессии", "en": "Delete a session"},
    "help.cmd.costs": {"ru": "Анализ расходов на токены", "en": "Token cost analysis"},
    "help.cmd.prune": {"ru": "Массовая очистка сессий", "en": "Bulk session cleanup"},
    "help.cmd.search": {"ru": "Поиск по сообщениям", "en": "Search messages"},
    "help.cmd.tree": {"ru": "Дерево ветвления сессий", "en": "Session branching tree"},
    "help.cmd.projects": {"ru": "Список проектов", "en": "Project list"},
    "help.cmd.stats": {"ru": "Статистика БД", "en": "Database statistics"},
    "help.cmd.todos": {"ru": "Задачи из сессий", "en": "Tasks from sessions"},
    "help.cmd.vacuum": {"ru": "Оптимизация БД", "en": "Database optimization"},
    "help.cmd.help": {"ru": "Подробная справка", "en": "Detailed help"},
    # ==================================================================
    # HELP — примеры (epilog для argparse --help)
    # ==================================================================
    "help.cmd.list.examples": {
        "ru": "\nПримеры:\n  opencode-db list                              # Сессии за последнее время\n  opencode-db list --limit 10                # Показать 10 последних\n  opencode-db list --sort cost               # Сортировка по стоимости\n  opencode-db list --project proj_xxx        # Фильтр по проекту\n  opencode-db list --json                    # Вывод в JSON\n",
        "en": "\nExamples:\n  opencode-db list                              # Recent sessions\n  opencode-db list --limit 10                # Show last 10\n  opencode-db list --sort cost               # Sort by cost\n  opencode-db list --project proj_xxx        # Filter by project\n  opencode-db list --json                    # JSON output\n",
    },
    "help.list.e0": {"ru": "Сессии за последнее время", "en": "Recent sessions"},
    "help.list.e1": {"ru": "Показать 10 последних", "en": "Show last 10"},
    "help.list.e2": {"ru": "Сортировка по стоимости", "en": "Sort by cost"},
    "help.list.e3": {"ru": "Фильтр по проекту", "en": "Filter by project"},
    "help.list.e4": {"ru": "Вывод в JSON", "en": "JSON output"},
    "help.info.e0": {
        "ru": "Все метаданные, токены, todo, ветвление",
        "en": "Metadata, tokens, todos, branching",
    },
    "help.info.e1": {"ru": "То же в JSON", "en": "Same in JSON"},
    "help.export.e0": {"ru": "Экспорт по ID", "en": "Export by ID"},
    "help.export.e1": {"ru": "Самая свежая сессия", "en": "Most recent session"},
    "help.export.e2": {"ru": "Интерактивный выбор из списка", "en": "Interactive picker"},
    "help.export.e3": {
        "ru": "Полный вывод без обрезания output'ов",
        "en": "Full output, no truncation",
    },
    "help.export.e4": {"ru": "Перезаписать существующий файл", "en": "Overwrite existing file"},
    "help.export.e5": {"ru": "Добавить заметку в log.md", "en": "Add a note to log.md"},
    "help.delete.e0": {"ru": "Удалить с подтверждением", "en": "Delete with confirmation"},
    "help.delete.e1": {"ru": "Показать что будет удалено", "en": "Preview what will be deleted"},
    "help.delete.e2": {"ru": "Без подтверждения", "en": "Skip confirmation"},
    "help.costs.e0": {"ru": "Топ сессий по расходам", "en": "Top sessions by cost"},
    "help.costs.e1": {"ru": "Детально по сессии", "en": "Single session breakdown"},
    "help.costs.e2": {"ru": "Сумма по всей БД", "en": "Total across all sessions"},
    "help.costs.e3": {"ru": "Сумма по проекту", "en": "Total by project"},
    "help.costs.e4": {"ru": "Вывод в JSON", "en": "JSON output"},
    "help.prune.e0": {"ru": "Удалить старше 90 дней", "en": "Delete older than 90 days"},
    "help.prune.e1": {"ru": "Оставить 20 последних", "en": "Keep 20 most recent"},
    "help.prune.e2": {"ru": "Показать что будет удалено", "en": "Preview deletions"},
    "help.prune.e3": {"ru": "Без подтверждения", "en": "Skip confirmation"},
    "help.search.e0": {"ru": "Поиск по всем сессиям", "en": "Search all sessions"},
    "help.search.e1": {"ru": "В конкретной сессии", "en": "Within a specific session"},
    "help.search.e2": {"ru": "Вывод в JSON", "en": "JSON output"},
    "help.tree.e0": {"ru": "Корневые сессии с детьми", "en": "Root sessions with children"},
    "help.tree.e1": {"ru": "Ветка от указанной сессии", "en": "Branch from a session"},
    "help.tree.e2": {"ru": "Глубина 3 уровня", "en": "Max depth of 3"},
    "help.projects.e0": {"ru": "Проекты со статистикой", "en": "Projects with statistics"},
    "help.projects.e1": {"ru": "Вывод в JSON", "en": "JSON output"},
    "help.stats.e0": {
        "ru": "Сессии, сообщения, токены, стоимость, топ моделей",
        "en": "Sessions, messages, tokens, costs, top models",
    },
    "help.stats.e1": {"ru": "Вывод в JSON", "en": "JSON output"},
    "help.todos.e0": {"ru": "Все задачи", "en": "All tasks"},
    "help.todos.e1": {"ru": "Задачи конкретной сессии", "en": "Tasks for a session"},
    "help.todos.e2": {"ru": "Только ожидающие", "en": "Pending only"},
    "help.todos.e3": {"ru": "Вывод в JSON", "en": "JSON output"},
    "help.vacuum.e0": {
        "ru": "VACUUM + REINDEX + ANALYZE с подтверждением",
        "en": "VACUUM + REINDEX + ANALYZE with confirmation",
    },
    "help.vacuum.e1": {"ru": "Без подтверждения", "en": "Skip confirmation"},
    "help.help.e0": {
        "ru": "Общая справка по всем командам",
        "en": "General help for all commands",
    },
    "help.help.e1": {
        "ru": "Справка по конкретной команде",
        "en": "Help for a specific command",
    },
    # ==================================================================
    # MARKDOWN EXPORT (formatters.py, config.py)
    # ==================================================================
    "md.reasoning": {"ru": "Рассуждение", "en": "Reasoning"},
    "md.sound": {"ru": "Аудиосообщение", "en": "Voice message"},
    "md.result": {"ru": "Результат", "en": "Result"},
    "md.header.title": {"ru": "Диалог", "en": "Conversation"},
    "md.header.date": {"ru": "Дата", "en": "Date"},
    "md.header.model": {"ru": "Модель", "en": "Model"},
    "md.header.session_id": {"ru": "ID сессии", "en": "Session ID"},
    "md.header.messages": {"ru": "Сообщений", "en": "Messages"},
    "md.log_agents": {"ru": "AGENTS.md: {v}", "en": "AGENTS.md: {v}"},
    "md.log_files": {
        "ru": "Файлов: {files}, директорий: {dirs}",
        "en": "Files: {files}, directories: {dirs}",
    },
    "md.log_not_found": {"ru": "не найден", "en": "not found"},
    "md.log_lines": {
        "ru": "{lines} строк, {sections} секций",
        "en": "{lines} lines, {sections} sections",
    },
    # ==================================================================
    # SCHEMA GUARD
    # ==================================================================
    "schema.table_missing": {
        "ru": "  ⚠️  Таблица '{table}' не найдена в БД. Возможно, OpenCode обновился.",
        "en": "  ⚠️  Table '{table}' not found in the database. OpenCode may have been updated.",
    },
    "schema.column_missing": {
        "ru": "  ⚠️  В таблице '{table}' отсутствуют колонки: {columns}",
        "en": "  ⚠️  Table '{table}' is missing columns: {columns}",
    },
    "schema.check_upgrade": {
        "ru": "   Проверь совместимость версий opencode-db и OpenCode.",
        "en": "   Check opencode-db and OpenCode version compatibility.",
    },
    # ==================================================================
    # ФОРМАТТЕРЫ
    # ==================================================================
    "fmt.rows_count": {"ru": "\n  Всего: {n}", "en": "\n  Total: {n}"},
    # ==================================================================
    # HELP — лейблы для _print_command_help
    # ==================================================================
    "help.cmd_header": {"ru": "  ── {cmd} ── {desc}", "en": "  ── {cmd} ── {desc}"},
    # ==================================================================
    # INFO — duration helpers
    # ==================================================================
    "info.dur_sec": {"ru": "{n} сек", "en": "{n} sec"},
    "info.dur_min": {"ru": "{n} мин", "en": "{n} min"},
    "info.dur_hours": {"ru": "{h}ч {m}мин", "en": "{h}h {m}m"},
    # ==================================================================
    # CLI — da
    # ==================================================================
    "cli.yn_yes": {"ru": "да", "en": "yes"},
    # ==================================================================
    # MARKDOWN ROLES (export headers)
    # ==================================================================
    "export.role_user": {"ru": "👤 Вы ({ts})", "en": "👤 You ({ts})"},
    "export.role_assistant": {
        "ru": "🤖 Ассистент{agent} ({ts})",
        "en": "🤖 Assistant{agent} ({ts})",
    },
    "export.agent_tag": {"ru": " ({agent})", "en": " ({agent})"},
    # ==================================================================
    # COSTS — scope labels
    # ==================================================================
    "costs.by_project": {"ru": "ПРОЕКТУ", "en": "PROJECT"},
    "costs.by_all": {"ru": "ВСЕЙ БД", "en": "DATABASE"},
    # ==================================================================
    # TABLE — header separators
    # ==================================================================
    # (эмодзи и символы не переводим)
}


def set_lang(lang: str):
    """Устанавливает язык вывода.

    Args:
      lang: "ru" или "en"
    """
    global current_lang
    if lang in ("ru", "en"):
        current_lang = lang


def _(key: str, **kwargs) -> str:
    """Возвращает локализованную строку по ключу.

    Args:
      key: ключ в словаре L (например "list.header.id")
      **kwargs: значения для str.format()

    Returns:
      str на текущем языке, или сам key если ключ не найден
    """
    entry = L.get(key)
    if entry is None:
        return key
    text = entry.get(current_lang, entry.get("ru", key))
    if kwargs:
        return text.format(**kwargs)
    return text
