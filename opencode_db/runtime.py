"""Проверка минимальной версии Python.

Модуль намеренно написан без синтаксиса новее Python 3.8, чтобы его можно
было импортировать до проверки версии и показать понятную ошибку вместо
ImportError/SyntaxError.
"""

import sys

MIN_PYTHON = (3, 12)
REQUIRED_VERSION = "3.12"


def format_version_error(version_info=None, executable=None) -> str:
    """Возвращает текст ошибки для неподдерживаемой версии Python."""
    info = version_info or sys.version_info
    exe = executable or sys.executable
    current = f"{info[0]}.{info[1]}.{info[2]}"

    return (
        f"opencode-db requires Python {REQUIRED_VERSION}+.\n"
        f"opencode-db требует Python {REQUIRED_VERSION}+.\n"
        "\n"
        f"Current interpreter: Python {current} ({exe})\n"
        f"Текущий интерпретатор: Python {current} ({exe})\n"
        "\n"
        "How to fix / Как исправить:\n"
        "  uv python install 3.13\n"
        "  uv venv --python 3.13\n"
        "  source .venv/bin/activate\n"
        "  pip install -e .\n"
        "\n"
        "Or run with uv / Или запуск через uv:\n"
        "  uv run --python 3.13 opencode-db --help\n"
        "  uv tool install --editable . && opencode-db --help\n"
        "\n"
        "After changing the interpreter, rerun install.sh to regenerate\n"
        "the ~/.local/bin/opencode-db launcher."
    )


def check_python_version(version_info=None):
    """Возвращает None, если версия подходит, иначе текст ошибки."""
    info = version_info or sys.version_info
    if tuple(info[:2]) >= MIN_PYTHON:
        return None
    return format_version_error(info)


def require_python() -> None:
    """Завершает процесс с понятной ошибкой, если Python слишком старый."""
    message = check_python_version()
    if message:
        print(message, file=sys.stderr)
        raise SystemExit(1)
