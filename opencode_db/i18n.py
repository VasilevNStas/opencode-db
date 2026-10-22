"""Интернационализация: поддержка русского и английского языка.

Использование:
  from opencode_db.i18n import _, set_lang

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
    "list.header.directory": {"ru": "Директория", "en": "Directory"},
    "list.header.model": {"ru": "Модель", "en": "Model"},
    "list.header.activity": {"ru": "Активность", "en": "Activity"},
    "list.header.messages": {"ru": "Сообщ.", "en": "Msgs"},
    "list.header.cost": {"ru": "Стоимость", "en": "Cost"},
    "list.scope_conflict": {
        "ru": "❌ --parent нельзя сочетать с --root/--sub",
        "en": "❌ --parent cannot be combined with --root/--sub",
    },
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
    "export.selection_conflict": {
        "ru": "❌ Выберите один режим: session_id, --latest, --last, --since, --project или --all",
        "en": "❌ Choose one selection mode: session_id, --latest, --last, --since, --project, or --all",
    },
    "export.invalid_last": {"ru": "❌ --last должен быть >= 1", "en": "❌ --last must be at least 1"},
    "export.invalid_since": {
        "ru": "❌ --since ожидает дату ГГГГ-ММ-ДД",
        "en": "❌ --since expects YYYY-MM-DD",
    },
    "export.selection_required": {
        "ru": "❌ --with-subagents/--no-subagents требует явного выбора сессии",
        "en": "❌ --with-subagents/--no-subagents requires an explicit session selection",
    },
    "export.no_matches": {
        "ru": "❌ Под выбранное правило не попала ни одна сессия.",
        "en": "❌ No sessions matched the selection rule.",
    },
    "export.bundle_title": {"ru": "Экспорт OpenCode", "en": "OpenCode export"},
    "export.bundle_rule": {"ru": "Правило", "en": "Selection"},
    "export.bundle_value": {"ru": "Значение", "en": "Value"},
    "export.bundle_format": {"ru": "Формат", "en": "Format"},
    "export.bundle_total": {"ru": "Всего сессий", "en": "Total sessions"},
    "export.bundle_sessions": {"ru": "Сессии", "en": "Sessions"},
    "export.bundle_msgs": {"ru": "сообщений", "en": "messages"},
    "export.bundle_saved": {"ru": "✅ Bundle сохранён: {path}", "en": "✅ Bundle saved: {path}"},
    "export.bundle_counts": {
        "ru": "   Roots: {roots}, subagents: {subagents}, всего: {total}",
        "en": "   Roots: {roots}, subagents: {subagents}, total: {total}",
    },
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
    "delete.children": {"ru": "Дочерних сессий", "en": "Child sessions"},
    "delete.children_more": {"ru": "ещё {n}", "en": "{n} more"},
    "delete.done_children": {
        "ru": "   Дочерних: {n}, всего строк удалено: {rows}",
        "en": "   Children: {n}, rows deleted: {rows}",
    },
    "delete.error": {"ru": "❌ Ошибка удаления: {error}", "en": "❌ Delete failed: {error}"},
    "delete.with_children_scope": {
        "ru": "❌ --with-children работает только с session_id или --missing-directories",
        "en": "❌ --with-children works only with session_id or --missing-directories",
    },
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
    "delete.none": {"ru": "  ✅ Нет сессий для удаления.", "en": "  ✅ No sessions to delete."},
    "delete.filter_required": {
        "ru": "❌ Укажи ID сессии, фильтр, или --interactive",
        "en": "❌ Specify session ID, a filter, or --interactive",
    },
    "delete.usage": {
        "ru": "  Использование: opencode-db delete <session_id>",
        "en": "  Usage: opencode-db delete <session_id>",
    },
    "delete.bad_spec": {
        "ru": "❌ Не могу разобрать: --older-than {spec}",
        "en": "❌ Cannot parse: --older-than {spec}",
    },
    "delete.bad_date": {
        "ru": "❌ Неверный формат даты: {date}. Используй ГГГГ-ММ-ДД",
        "en": "❌ Invalid date format: {date}. Use YYYY-MM-DD",
    },
    "delete.mass_header": {
        "ru": "Будет удалено сессий: {n}",
        "en": "Sessions to delete: {n}",
    },
    "delete.cost_total": {
        "ru": "Стоимость удаляемых: {cost}",
        "en": "Cost of deleted sessions: {cost}",
    },
    "delete.tokens_total": {"ru": "Освободится токенов: ~{n}", "en": "Tokens freed: ~{n}"},
    "delete.mass_confirm": {"ru": "Удалить {n} сессий?", "en": "Delete {n} sessions?"},
    "delete.done_mass": {"ru": "  ✅ Удалено {n} сессий.", "en": "  ✅ Deleted {n} sessions."},
    "delete.interactive_header": {"ru": "Последние сессии:", "en": "Recent sessions:"},
    "delete.missing_header": {
        "ru": "ОЧИСТКА СЕССИЙ ИЗ ОТСУТСТВУЮЩИХ ДИРЕКТОРИЙ",
        "en": "DELETE SESSIONS FROM MISSING DIRECTORIES",
    },
    "delete.missing_none": {
        "ru": "  ✅ Сессий из отсутствующих директорий не найдено.",
        "en": "  ✅ No sessions from missing directories found.",
    },
    "delete.missing_children": {
        "ru": "  Дочерних сессий: {n} (из существующих директорий: {existing})",
        "en": "  Child sessions: {n} (from existing directories: {existing})",
    },
    "delete.missing_existing_child": {
        "ru": "    + {id}  {title}  (существующая директория: {path})",
        "en": "    + {id}  {title}  (existing directory: {path})",
    },
    "delete.missing_summary": {
        "ru": "  Сессий: {sessions}, директорий: {dirs}, стоимость: {cost}",
        "en": "  Sessions: {sessions}, directories: {dirs}, cost: {cost}",
    },
    "delete.missing_dir_line": {"ru": "    {path} — {n} сессий", "en": "    {path} — {n} sessions"},
    "delete.missing_preview": {
        "ru": "Это preview. Для удаления добавь --execute.",
        "en": "This is a preview. Add --execute to delete.",
    },
    "delete.missing_incompatible": {
        "ru": "--missing-directories нельзя сочетать с --older-than/--before/--after/--keep-last/--interactive/session_id.",
        "en": "--missing-directories cannot be combined with --older-than/--before/--after/--keep-last/--interactive/session_id.",
    },
    "delete.missing_execute_requires": {
        "ru": "--execute используется только вместе с --missing-directories.",
        "en": "--execute can only be used with --missing-directories.",
    },
    "delete.missing_no_backup_warning": {
        "ru": "  ⚠️ Backup отключён (--no-backup). Удаление необратимо.",
        "en": "  ⚠️ Backup disabled (--no-backup). Deletion is irreversible.",
    },
    "delete.missing_backup_choice": {
        "ru": "Для --execute укажи --backup или --no-backup (осознанный выбор).",
        "en": "For --execute, choose --backup or --no-backup explicitly.",
    },
    "delete.missing_both_backup": {
        "ru": "Нельзя одновременно --backup и --no-backup.",
        "en": "Cannot use --backup and --no-backup together.",
    },
    "delete.missing_phrase_prompt": {
        "ru": "Введи точно «{phrase}» для продолжения: ",
        "en": 'Type exactly "{phrase}" to continue: ',
    },
    "delete.missing_phrase_mismatch": {
        "ru": "Фраза не совпала. Удаление отменено.",
        "en": "Phrase did not match. Deletion canceled.",
    },
    "delete.missing_final_confirm": {
        "ru": "Последнее подтверждение: удалить {n} сессий? Это необратимо.",
        "en": "Final confirmation: delete {n} sessions? This is irreversible.",
    },
    "delete.missing_changed": {
        "ru": "Список кандидатов изменился. Удаление отменено; повтори preview.",
        "en": "Candidate list changed. Deletion canceled; rerun the preview.",
    },
    "delete.missing_backup_done": {"ru": "  Backup: {path}", "en": "  Backup: {path}"},
    "delete.missing_backup_failed": {
        "ru": "Не удалось создать backup: {error}. Удаление отменено.",
        "en": "Failed to create backup: {error}. Deletion canceled.",
    },
    "delete.missing_done": {
        "ru": "  ✅ Удалено сессий: {n}; строк: {rows}.",
        "en": "  ✅ Sessions deleted: {n}; rows: {rows}.",
    },
    "delete.missing_error": {
        "ru": "Ошибка удаления: {error}. Транзакция отменена.",
        "en": "Deletion error: {error}. Transaction rolled back.",
    },
    "delete.missing_db": {"ru": "  База: {path}", "en": "  Database: {path}"},
    "delete.missing_dry_run": {
        "ru": "Это preview; база не изменена.",
        "en": "This is a preview; the database was not changed.",
    },
    "delete.interactive_prompt": {
        "ru": "  Введи номера (1,3-5) или Enter для отмены: ",
        "en": "  Enter numbers (1,3-5) or Enter to cancel: ",
    },
    "delete.no_sessions": {"ru": "❌ Нет сессий для удаления.", "en": "❌ No sessions to delete."},
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
    "projects.header.path": {"ru": "Путь", "en": "Path"},
    "projects.header.activity": {"ru": "Активность", "en": "Activity"},
    "projects.header.sessions": {"ru": "Сессии", "en": "Sessions"},
    "projects.header.tokens": {"ru": "Токены", "en": "Tokens"},
    "projects.header.cost": {"ru": "Стоимость", "en": "Cost"},
    "projects.global": {"ru": "Global (без корня)", "en": "Global (no project root)"},
    "projects.missing": {"ru": "не найдена", "en": "not found"},
    "projects.none": {"ru": "Проекты не найдены.", "en": "No projects found."},
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
    # HEALTH
    # ==================================================================
    "health.title": {"ru": "🩺 Здоровье базы данных", "en": "🩺 Database health"},
    "health.path": {"ru": "База", "en": "Database"},
    "health.file": {"ru": "Файл", "en": "File"},
    "health.wal": {"ru": "WAL", "en": "WAL"},
    "health.shm": {"ru": "SHM", "en": "SHM"},
    "health.pages": {"ru": "Страницы", "en": "Pages"},
    "health.live": {"ru": "Живые данные", "en": "Live data"},
    "health.freelist": {"ru": "Freelist", "en": "Freelist"},
    "health.reclaimable": {"ru": "Можно вернуть", "en": "Reclaimable"},
    "health.auto_vacuum": {"ru": "auto_vacuum", "en": "auto_vacuum"},
    "health.journal": {"ru": "journal_mode", "en": "journal_mode"},
    "health.schema": {"ru": "Схема", "en": "Schema"},
    "health.read_only": {"ru": "Только чтение", "en": "Read-only"},
    "health.yes": {"ru": "да", "en": "yes"},
    "health.no": {"ru": "нет", "en": "no"},
    "health.lock": {"ru": "Процессы", "en": "Processes"},
    "health.lock_unknown": {
        "ru": "не удалось проверить (нет lsof/fuser)",
        "en": "unknown (lsof/fuser not available)",
    },
    "health.lock_in_use": {
        "ru": "БД открыта (PID {pids})",
        "en": "database is open (PID {pids})",
    },
    "health.lock_free": {"ru": "не запущен", "en": "not running"},
    "health.source": {"ru": "Источник", "en": "Source"},
    "health.source_backup": {"ru": "backup: {path}", "en": "backup: {path}"},
    "health.backup": {"ru": "Backup", "en": "Backup"},
    "health.backup_none": {"ru": "нет (opencode-db backup)", "en": "none (opencode-db backup)"},
    "health.backup_error": {"ru": "ошибка manifest: {error}", "en": "manifest error: {error}"},
    "health.backup_aligned": {
        "ru": "{file} ({date}) — совпадает",
        "en": "{file} ({date}) — aligned",
    },
    "health.backup_out_of_sync": {
        "ru": "{file} ({date}) — устарел",
        "en": "{file} ({date}) — out of sync",
    },
    "health.backup_unknown": {
        "ru": "{file} — проверить не удалось ({error})",
        "en": "{file} — alignment unknown ({error})",
    },
    # ==================================================================
    # BACKUP
    # ==================================================================
    "backup.header": {"ru": "💾 Создание backup", "en": "💾 Create backup"},
    "backup.source": {"ru": "Источник", "en": "Source"},
    "backup.output": {"ru": "Каталог", "en": "Output"},
    "backup.format": {"ru": "Формат", "en": "Format"},
    "backup.format_gzip": {"ru": "gzip (.db.gz)", "en": "gzip (.db.gz)"},
    "backup.format_plain": {"ru": "без сжатия (.db)", "en": "uncompressed (.db)"},
    "backup.dry_run": {"ru": "Dry run", "en": "Dry run"},
    "backup.dry_run_hint": {"ru": "ничего не записано", "en": "nothing written"},
    "backup.error": {"ru": "❌ Ошибка backup: {error}", "en": "❌ Backup error: {error}"},
    "backup.saved": {"ru": "✅ Backup создан: {path}", "en": "✅ Backup created: {path}"},
    "backup.size": {
        "ru": "   Размер: {size} (raw: {raw})",
        "en": "   Size: {size} (raw: {raw})",
    },
    "backup.counts": {
        "ru": "   Сессий: {sessions}, сообщений: {messages}, частей: {parts}",
        "en": "   Sessions: {sessions}, messages: {messages}, parts: {parts}",
    },
    "backup.sha": {"ru": "   sha256: {sha}", "en": "   sha256: {sha}"},
    "backup.source_error": {"ru": "❌ Backup не найден: {error}", "en": "❌ Backup not found: {error}"},
    "backup.read_only_command": {
        "ru": "❌ Команда {command} не может писать в backup. Открой живую БД.",
        "en": "❌ Command {command} cannot write to a backup. Use the live database.",
    },
    # ==================================================================
    # BACKUPS
    # ==================================================================
    "backups.empty": {"ru": "  Управляемых backup-снимков нет.", "en": "  No managed backups."},
    "backups.error": {"ru": "❌ Ошибка backup: {error}", "en": "❌ Backup error: {error}"},
    "backups.not_found": {"ru": "❌ Backup не найден: {file}", "en": "❌ Backup not found: {file}"},
    "backups.header.date": {"ru": "Дата", "en": "Date"},
    "backups.header.file": {"ru": "Файл", "en": "File"},
    "backups.header.size": {"ru": "Размер", "en": "Size"},
    "backups.header.schema": {"ru": "Схема", "en": "Schema"},
    "backups.header.sessions": {"ru": "Сессий", "en": "Sessions"},
    "backups.header.messages": {"ru": "Сообщений", "en": "Messages"},
    "backups.header.parts": {"ru": "Частей", "en": "Parts"},
    "backups.view_title": {"ru": "🔎 Backup", "en": "🔎 Backup"},
    "backups.view.path": {"ru": "Путь", "en": "Path"},
    "backups.view.raw_size": {"ru": "Исходный размер", "en": "Raw size"},
    "backups.view.compression": {"ru": "Сжатие", "en": "Compression"},
    "backups.view.gzip": {"ru": "gzip", "en": "gzip"},
    "backups.view.plain": {"ru": "нет", "en": "none"},
    "backups.view.max_updated": {"ru": "Последняя сессия", "en": "Max updated"},
    "backups.view.source": {"ru": "Источник", "en": "Source"},
    "backups.view.sha256": {"ru": "sha256", "en": "sha256"},
    "backups.view.ok": {"ru": "OK", "en": "OK"},
    "backups.view.bad": {"ru": "НЕ СОВПАДАЕТ", "en": "MISMATCH"},
    "backups.view.alignment": {"ru": "С живой БД", "en": "Vs live DB"},
    "backups.view.aligned": {"ru": "совпадает", "en": "aligned"},
    "backups.view.out_of_sync": {"ru": "устарел", "en": "out of sync"},
    "backups.view.alignment_unknown": {"ru": "неизвестно", "en": "unknown"},
    "backups.verify_ok": {"ru": "✅ Backup OK: {file} ({message})", "en": "✅ Backup OK: {file} ({message})"},
    "backups.verify_failed": {
        "ru": "❌ Backup повреждён: {file} ({error})",
        "en": "❌ Backup verification failed: {file} ({error})",
    },
    "backups.remove_confirm": {"ru": "Удалить backup {file}?", "en": "Remove backup {file}?"},
    "backups.removed": {"ru": "  ✅ Backup удалён: {file}", "en": "  ✅ Backup removed: {file}"},
    "backups.removed_path": {"ru": "     {path}", "en": "     {path}"},
    "backups.prune_invalid": {
        "ru": "❌ keep должен быть >= 1",
        "en": "❌ keep must be at least 1",
    },
    "backups.prune_nothing": {
        "ru": "  Нечего удалять (keep={keep}).",
        "en": "  Nothing to prune (keep={keep}).",
    },
    "backups.prune_confirm": {
        "ru": "Удалить {count} старых backup, оставить {keep}?",
        "en": "Remove {count} old backups and keep {keep}?",
    },
    "backups.prune_done": {
        "ru": "  ✅ Удалено: {count}, оставлено: {keep}",
        "en": "  ✅ Removed: {count}, kept: {keep}",
    },
    # ==================================================================
    # VACUUM
    # ==================================================================
    "vacuum.header": {"ru": "🗄️  Оптимизация базы данных", "en": "🗄️  Database optimization"},
    "vacuum.size_before": {"ru": "Размер до", "en": "Size before"},
    "vacuum.size_after": {"ru": "Размер после", "en": "Size after"},
    "vacuum.path": {"ru": "Путь", "en": "Path"},
    "vacuum.freed": {"ru": "Освобождено", "en": "Freed"},
    "vacuum.wal": {"ru": "WAL", "en": "WAL"},
    "vacuum.freelist": {"ru": "Freelist", "en": "Freelist"},
    "vacuum.journal": {"ru": "journal_mode", "en": "journal_mode"},
    "vacuum.backup": {"ru": "Backup", "en": "Backup"},
    "vacuum.backup_enabled": {"ru": "включён", "en": "enabled"},
    "vacuum.backup_disabled": {"ru": "отключён", "en": "disabled"},
    "vacuum.backup_creating": {"ru": "Создаётся backup...", "en": "Creating backup..."},
    "vacuum.backup_path": {"ru": "Backup", "en": "Backup"},
    "vacuum.backup_skipped": {"ru": "  Backup пропущен.", "en": "  Backup skipped."},
    "vacuum.free_space": {"ru": "Свободно", "en": "Free space"},
    "vacuum.required": {"ru": "нужно", "en": "required"},
    "vacuum.lock": {"ru": "Процессы", "en": "Processes"},
    "vacuum.lock_free": {"ru": "не запущен", "en": "not running"},
    "vacuum.lock_in_use": {
        "ru": "❌ База открыта процессом: {pids}",
        "en": "❌ Database is open by PID(s): {pids}",
    },
    "vacuum.close_opencode": {
        "ru": "Закройте OpenCode и повторите.",
        "en": "Close OpenCode and try again.",
    },
    "vacuum.lock_unknown": {
        "ru": "❌ Не удалось проверить, кто держит базу: нет lsof/fuser.",
        "en": "❌ Cannot check database users: lsof/fuser not available.",
    },
    "vacuum.lock_unknown_hint": {
        "ru": "Установите lsof/fuser или запустите с --skip-lock-check, если уверены, что OpenCode закрыт.",
        "en": "Install lsof/fuser, or rerun with --skip-lock-check if you are sure OpenCode is closed.",
    },
    "vacuum.lock_unknown_short": {"ru": "не удалось проверить", "en": "unknown"},
    "vacuum.lock_skipped": {
        "ru": "проверка пропущена (PID {pids})",
        "en": "check skipped (PID {pids})",
    },
    "vacuum.integrity_failed": {
        "ru": "❌ Проверка целостности не прошла: {message}",
        "en": "❌ Integrity check failed: {message}",
    },
    "vacuum.checkpoint": {"ru": "WAL checkpoint", "en": "WAL checkpoint"},
    "vacuum.checkpoint_failed": {
        "ru": "❌ WAL checkpoint не выполнен: {message}",
        "en": "❌ WAL checkpoint failed: {message}",
    },
    "vacuum.final_checkpoint_failed": {
        "ru": "⚠️  Финальный WAL checkpoint не выполнен: {message}",
        "en": "⚠️  Final WAL checkpoint failed: {message}",
    },
    "vacuum.no_space": {
        "ru": "❌ Недостаточно места: нужно ~{required}, доступно {free}.",
        "en": "❌ Not enough free space: need ~{required}, available {free}.",
    },
    "vacuum.no_space_hint": {
        "ru": "Освободите место или запустите с --no-backup (не рекомендуется).",
        "en": "Free some space, or rerun with --no-backup (not recommended).",
    },
    "vacuum.no_backup_warning": {
        "ru": "⚠️  Backup отключён. Убедитесь, что у вас есть внешняя копия.",
        "en": "⚠️  Backup disabled. Make sure you have an external copy.",
    },
    "vacuum.backup_conflict": {
        "ru": "Нельзя одновременно использовать --backup и --no-backup.",
        "en": "Cannot use --backup and --no-backup together.",
    },
    "vacuum.auto_vacuum": {"ru": "auto_vacuum", "en": "auto_vacuum"},
    "vacuum.journal_restored": {
        "ru": "journal_mode восстановлен: wal",
        "en": "journal_mode restored: wal",
    },
    "vacuum.journal_restore_failed": {
        "ru": "❌ Не удалось восстановить journal_mode: {error}",
        "en": "❌ Failed to restore journal_mode: {error}",
    },
    "vacuum.post_check_failed": {
        "ru": "❌ Проверка после VACUUM не прошла: {message}",
        "en": "❌ Post-VACUUM integrity check failed: {message}",
    },
    "vacuum.restore_hint": {
        "ru": "Для восстановления: остановите OpenCode, скопируйте {backup} поверх {path} и удалите {path}-wal / {path}-shm.",
        "en": "To restore: stop OpenCode, copy {backup} over {path}, and remove {path}-wal / {path}-shm.",
    },
    "vacuum.vacuum": {"ru": "Выполняется VACUUM...", "en": "Running VACUUM..."},
    "vacuum.reindex": {"ru": "Выполняется REINDEX...", "en": "Running REINDEX..."},
    "vacuum.analyze": {"ru": "Выполняется ANALYZE...", "en": "Running ANALYZE..."},
    "vacuum.confirm": {"ru": "Запустить VACUUM?", "en": "Run VACUUM?"},
    "vacuum.error": {"ru": "❌ Ошибка: {error}", "en": "❌ Error: {error}"},
    "vacuum.done": {"ru": "✅", "en": "✅"},
    "vacuum.canceled": {"ru": "  Отменено.", "en": "  Canceled."},
    # ==================================================================
    # VIEW
    # ==================================================================
    "view.header": {
        "ru": "Просмотр сессии",
        "en": "Session View",
    },
    "view.role_user": {
        "ru": "Вы",
        "en": "You",
    },
    "view.role_assistant": {
        "ru": "Ассистент",
        "en": "Assistant",
    },
    "view.no_messages": {
        "ru": "⏳ Нет сообщений в этой сессии.",
        "en": "⏳ No messages in this session.",
    },
    "view.no_sessions": {
        "ru": "❌ Нет сессий для просмотра.",
        "en": "❌ No sessions to view.",
    },
    "view.interactive_header": {
        "ru": "Последние сессии:",
        "en": "Recent sessions:",
    },
    "view.interactive_prompt": {
        "ru": "Выбери номер (или Enter для отмены): ",
        "en": "Pick a number (or Enter to cancel): ",
    },
    "view.interactive_error": {
        "ru": "Введи число от 1 до {n}",
        "en": "Enter a number from 1 to {n}",
    },
    "view.interactive_viewing": {
        "ru": "  Просмотр: {title}",
        "en": "  Viewing: {title}",
    },
    "view.interactive_abort": {
        "ru": "  Отменено.",
        "en": "  Canceled.",
    },
    "view.footer": {
        "ru": "конец сессии",
        "en": "end of session",
    },
    "view.flag.latest": {
        "ru": "Просмотр самой свежей сессии",
        "en": "View the most recent session",
    },
    "view.flag.no_pager": {
        "ru": "Вывод без пейджера (просто печатать)",
        "en": "Print without pager",
    },
    "view.flag.raw": {
        "ru": "Без ANSI-цветов (обычный текст)",
        "en": "Plain text, no ANSI colors",
    },
    # ==================================================================
    # DIGEST
    # ==================================================================
    "digest.header": {"ru": "🗜️ Compaction-сводки: {title}", "en": "🗜️ Compaction digests: {title}"},
    "digest.empty": {"ru": "Compaction-сводок нет.", "en": "No compaction digests."},
    "digest.no_text": {"ru": "текст сводки отсутствует", "en": "no digest text"},
    "digest.invalid_last": {
        "ru": "❌ --last должен быть >= 1",
        "en": "❌ --last must be at least 1",
    },
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
    "help.cmd.delete": {"ru": "Удаление сессий", "en": "Delete sessions"},
    "help.cmd.costs": {"ru": "Анализ расходов на токены", "en": "Token cost analysis"},
    "help.cmd.prune": {"ru": "Массовая очистка сессий", "en": "Bulk session cleanup"},
    "help.cmd.search": {"ru": "Поиск по сообщениям", "en": "Search messages"},
    "help.cmd.tree": {"ru": "Дерево ветвления сессий", "en": "Session branching tree"},
    "help.cmd.projects": {"ru": "Список проектов", "en": "Project list"},
    "help.cmd.directories": {"ru": "Директории запусков", "en": "Launch directories"},
    "help.directories.e0": {
        "ru": "Все директории с сессиями",
        "en": "All directories with sessions",
    },
    "help.directories.e1": {
        "ru": "Только отсутствующие директории",
        "en": "Only missing directories",
    },
    "help.directories.e2": {"ru": "Вывод в JSON", "en": "JSON output"},
    "help.directories.e3": {"ru": "Не проверять файловую систему", "en": "Skip filesystem check"},
    "directories.title": {
        "ru": "Директории запусков OpenCode",
        "en": "OpenCode launch directories",
    },
    "directories.header.path": {"ru": "Путь", "en": "Path"},
    "directories.header.status": {"ru": "Статус", "en": "Status"},
    "directories.header.project": {"ru": "Проект", "en": "Project"},
    "directories.header.sessions": {"ru": "Сессии", "en": "Sessions"},
    "directories.header.last": {"ru": "Последняя", "en": "Last"},
    "directories.header.cost": {"ru": "Стоимость", "en": "Cost"},
    "directories.exists": {"ru": "да", "en": "yes"},
    "directories.missing": {"ru": "не найдена", "en": "not found"},
    "directories.unknown": {"ru": "?", "en": "?"},
    "directories.global": {"ru": "Global (без корня)", "en": "Global (no project root)"},
    "directories.none": {"ru": "Директории не найдены.", "en": "No directories found."},
    "directories.total": {"ru": "Всего директорий: {n}", "en": "Directories: {n}"},
    "directories.summary": {
        "ru": "Директорий: {total}, сессий: {sessions}, отсутствует: {missing}",
        "en": "Directories: {total}, sessions: {sessions}, missing: {missing}",
    },
    "directories.conflict": {
        "ru": "Нельзя одновременно использовать --missing и --existing.",
        "en": "Cannot use --missing and --existing together.",
    },
    "help.cmd.stats": {"ru": "Статистика БД", "en": "Database statistics"},
    "help.cmd.todos": {"ru": "Задачи из сессий", "en": "Tasks from sessions"},
    "help.cmd.vacuum": {"ru": "Оптимизация БД", "en": "Database optimization"},
    "help.cmd.view": {"ru": "Просмотр сессии с прокруткой", "en": "View session with scrolling"},
    "help.cmd.help": {"ru": "Подробная справка", "en": "Detailed help"},
    "help.cmd.schema": {
        "ru": "Схема БД и совместимость",
        "en": "Database schema and compatibility",
    },
    "help.cmd.health": {"ru": "Здоровье хранилища SQLite", "en": "SQLite storage health"},
    "help.health.e0": {
        "ru": "Размер, freelist, WAL и режим БД",
        "en": "Size, freelist, WAL and DB mode",
    },
    "help.health.e1": {"ru": "То же в JSON", "en": "Same as JSON"},
    "help.cmd.backup": {"ru": "Создать backup БД", "en": "Create a database backup"},
    "help.cmd.backups": {"ru": "Управление backup-снимками", "en": "Manage backups"},
    "help.backup.e0": {"ru": "Создать gzip-backup", "en": "Create a gzip backup"},
    "help.backup.e1": {"ru": "Показать план без записи", "en": "Show the plan without writing"},
    "help.backup.e2": {"ru": "Свой каталог", "en": "Custom directory"},
    "help.backup.e3": {"ru": "Без сжатия", "en": "No compression"},
    "help.backups.e0": {"ru": "Список снимков", "en": "List backups"},
    "help.backups.e1": {"ru": "Детали снимка", "en": "Backup details"},
    "help.backups.e2": {"ru": "Проверить sha256 и целостность", "en": "Verify sha256 and integrity"},
    "help.backups.e3": {"ru": "Удалить снимок", "en": "Remove a backup"},
    "help.backups.e4": {"ru": "Оставить 5 новейших", "en": "Keep the 5 newest"},
    "help.backups.list": {"ru": "Список backup", "en": "List backups"},
    "help.backups.view": {"ru": "Детали backup", "en": "Backup details"},
    "help.backups.verify": {"ru": "Проверить backup", "en": "Verify a backup"},
    "help.backups.remove": {"ru": "Удалить backup", "en": "Remove a backup"},
    "help.backups.prune": {"ru": "Очистить старые backup", "en": "Prune old backups"},
    "help.schema.e0": {
        "ru": "Определить семейство схемы и миграции",
        "en": "Detect schema family and migrations",
    },
    "help.schema.e1": {"ru": "То же в JSON", "en": "Same as JSON"},
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
    "help.list.e5": {"ru": "Показать директории сессий", "en": "Show session directories"},
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
    "help.export.e6": {"ru": "Lossless JSON-экспорт", "en": "Lossless JSON export"},
    "help.export.e7": {"ru": "Последние 5 root-сессий + subagents", "en": "Last 5 roots + subagents"},
    "help.export.e8": {"ru": "Сессии, созданные с даты", "en": "Sessions created since a date"},
    "help.export.e9": {"ru": "Все сессии проекта", "en": "All sessions in a project"},
    "help.export.e10": {"ru": "Все сессии", "en": "All sessions"},
    "help.export.e11": {"ru": "Включить дочерние сессии", "en": "Include child sessions"},
    "help.export.e12": {"ru": "Без дочерних сессий", "en": "Exclude child sessions"},
    "help.export.e13": {
        "ru": "Best-effort redaction секретов",
        "en": "Best-effort secret redaction",
    },
    "help.cmd.digest": {"ru": "Compaction-сводки сессии", "en": "Session compaction digests"},
    "help.digest.e0": {"ru": "Все compaction-сводки", "en": "All compaction digests"},
    "help.digest.e1": {"ru": "Последние 3 сводки", "en": "Last 3 digests"},
    "help.digest.e2": {"ru": "То же в JSON", "en": "Same as JSON"},
    "help.delete.e0": {"ru": "Удалить с подтверждением", "en": "Delete with confirmation"},
    "help.delete.e1": {"ru": "Показать что будет удалено", "en": "Preview what will be deleted"},
    "help.delete.e2": {"ru": "Без подтверждения", "en": "Skip confirmation"},
    "help.delete.e3": {
        "ru": "Удалить сессии старше 90 дней",
        "en": "Delete sessions older than 90 days",
    },
    "help.delete.e4": {
        "ru": "Оставить 30 последних, остальное удалить",
        "en": "Keep 30 most recent, delete the rest",
    },
    "help.delete.e5": {
        "ru": "Удалить сессии до указанной даты",
        "en": "Delete sessions before a date",
    },
    "help.delete.e7": {
        "ru": "Очистить сессии из отсутствующих директорий (preview)",
        "en": "Preview sessions from missing directories",
    },
    "help.delete.e8": {
        "ru": "Выполнить очистку после подтверждений",
        "en": "Execute cleanup after confirmations",
    },
    "help.delete.e9": {
        "ru": "Удалить сессию и всех потомков",
        "en": "Delete a session and all descendants",
    },
    "help.delete.e10": {
        "ru": "Очистка отсутствующих директорий вместе с потомками",
        "en": "Missing-directory cleanup including descendants",
    },
    "help.prune.e4": {
        "ru": "Preview очистки отсутствующих директорий",
        "en": "Preview missing-directory cleanup",
    },
    "help.prune.e5": {
        "ru": "Выполнить очистку отсутствующих директорий",
        "en": "Execute missing-directory cleanup",
    },
    "help.prune.e6": {
        "ru": "Очистка отсутствующих директорий с потомками",
        "en": "Missing-directory cleanup with descendants",
    },
    "help.delete.e6": {
        "ru": "Интерактивный выбор из списка",
        "en": "Choose sessions from a list",
    },
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
    "help.projects.e2": {"ru": "Скрыть Global-проект", "en": "Hide the Global project"},
    "help.projects.e3": {
        "ru": "Только проекты с отсутствующим путём",
        "en": "Only projects with a missing path",
    },
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
        "ru": "VACUUM + REINDEX + ANALYZE с backup и проверками",
        "en": "VACUUM + REINDEX + ANALYZE with backup and checks",
    },
    "help.vacuum.e1": {"ru": "Без подтверждения", "en": "Skip confirmation"},
    "help.vacuum.e2": {
        "ru": "Без backup (не рекомендуется)",
        "en": "Without backup (not recommended)",
    },
    "help.vacuum.e3": {
        "ru": "Включить incremental auto-vacuum",
        "en": "Enable incremental auto-vacuum",
    },
    "help.vacuum.notes": {
        "ru": "\nВажно:\n  - VACUUM требует свободного места примерно равного размеру БД.\n  - Backup включён по умолчанию и требует ещё столько же места.\n  - --no-backup отключает backup; используйте только при наличии внешней копии.\n  - Закройте OpenCode. Проверка блокировки — best-effort.\n  - WAL checkpoint выполняется, режим WAL сохраняется.\n  - VACUUM не удаляет сессии и историю чатов.\n",
        "en": "\nImportant:\n  - VACUUM needs free space roughly equal to the database size.\n  - A verified backup is enabled by default and needs about the same space again.\n  - --no-backup disables the backup; use it only if you have an external copy.\n  - Close OpenCode. The lock check is best-effort.\n  - WAL is checkpointed and preserved.\n  - VACUUM does not delete sessions or chat history.\n",
    },
    "help.view.e0": {
        "ru": "Просмотр по ID",
        "en": "View by ID",
    },
    "help.view.e1": {
        "ru": "Самая свежая сессия",
        "en": "Most recent session",
    },
    "help.view.e2": {
        "ru": "Интерактивный выбор из списка",
        "en": "Interactive picker",
    },
    "help.view.e3": {
        "ru": "Без пейджера (простой вывод)",
        "en": "Without pager (plain output)",
    },
    "help.view.e4": {
        "ru": "Без ANSI-цветов",
        "en": "Without ANSI colors",
    },
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
    "md.patch": {"ru": "Патч", "en": "Patch"},
    "md.patch_hash": {"ru": "hash: `{hash}`", "en": "hash: `{hash}`"},
    "md.file": {"ru": "Файл", "en": "File"},
    "md.file_mime": {"ru": "MIME: {mime}", "en": "MIME: {mime}"},
    "md.file_url": {"ru": "URL: {url}", "en": "URL: {url}"},
    "md.compaction": {"ru": "Compaction", "en": "Compaction"},
    "md.unknown_part": {
        "ru": "Неизвестная часть: {type}",
        "en": "Unknown part: {type}",
    },
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
    "schema.title": {
        "ru": "Схема БД OpenCode",
        "en": "OpenCode database schema",
    },
    "schema.db_path": {"ru": "База", "en": "Database"},
    "schema.family": {"ru": "Схема", "en": "Schema"},
    "schema.tables": {"ru": "Таблиц", "en": "Tables"},
    "schema.migrations": {"ru": "Миграций", "en": "Migrations"},
    "schema.max_migration": {"ru": "Макс. миграция", "en": "Max migration"},
    "schema.capabilities": {"ru": "Возможности", "en": "Capabilities"},
    "schema.manifest": {"ru": "Манифест", "en": "Manifest"},
    "schema.read_only": {"ru": "только чтение", "en": "read-only"},
    "schema.unknown": {
        "ru": "  ⚠️  Семейство схемы не распознано. Ожидается `session` или `session_v2`.",
        "en": "  ⚠️  Unknown schema family. Expected `session` or `session_v2`.",
    },
    "schema.warning": {"ru": "  ⚠️  {message}", "en": "  ⚠️  {message}"},
    "schema.unsupported_write": {
        "ru": "❌ Запись в v2-схему пока не поддерживается. Доступны только read-only команды.",
        "en": "❌ Writing to the v2 schema is not supported yet. Only read-only commands are available.",
    },
    "db.next_fallback": {
        "ru": "ℹ️  opencode.db не найден, используется preview-база: {path}",
        "en": "ℹ️  opencode.db not found, using preview database: {path}",
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
