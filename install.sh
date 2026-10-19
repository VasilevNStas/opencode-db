#!/bin/sh
#
# install.sh — opencode-db installer
# Usage: curl -fsSL https://raw.githubusercontent.com/VasilevNStas/opencode-db/master/install.sh | sh
#
# Installs to ~/.local/share/opencode-db/ and creates ~/.local/bin/opencode-db

set -eu

REPO="VasilevNStas/opencode-db"
BRANCH="master"
INSTALL_DIR="${HOME}/.local/share/opencode-db"
BIN_DIR="${HOME}/.local/bin"
LAUNCHER="${BIN_DIR}/opencode-db"

# Colors
GREEN='\033[0;32m'
BOLD='\033[1m'
NC='\033[0m'

echo "==> opencode-db installer"
echo ""

# --- 1. Find a supported Python ---
find_python() {
    for candidate in python3.13 python3.12 python3; do
        if command -v "${candidate}" >/dev/null 2>&1 \
            && "${candidate}" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 12) else 1)' >/dev/null 2>&1; then
            command -v "${candidate}"
            return 0
        fi
    done

    # uv can manage Python versions for us.
    if command -v uv >/dev/null 2>&1; then
        for spec in '>=3.12' '3.13' '3.12'; do
            candidate=$(uv python find "${spec}" 2>/dev/null || true)
            case "${candidate}" in
                */.venv/*) continue ;;
            esac
            if [ -n "${candidate}" ] && [ -x "${candidate}" ]; then
                printf '%s\n' "${candidate}"
                return 0
            fi
        done
    fi

    return 1
}

if ! PYTHON_BIN=$(find_python); then
    echo "ERROR: opencode-db requires Python 3.12+."
    echo "  Recommended (uv):"
    echo "    uv python install 3.13"
    echo "    uv tool install --editable ."
    echo "  Or install Python 3.12+ and rerun this installer."
    exit 1
fi

PY_VERSION=$("${PYTHON_BIN}" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')
echo "  Python: ${PY_VERSION} (${PYTHON_BIN})"

# --- 2. Create directories ---
mkdir -p "${BIN_DIR}"

# --- 3. Download code ---
echo "  Downloading opencode-db from ${REPO}..."
DOWNLOAD_URL="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz"

TMP_ARCHIVE=$(mktemp /tmp/opencode-db-XXXXXXXX.tar.gz)
trap 'rm -f "${TMP_ARCHIVE}"' EXIT

if command -v curl >/dev/null 2>&1; then
    curl -fsSL -o "${TMP_ARCHIVE}" "${DOWNLOAD_URL}"
elif command -v wget >/dev/null 2>&1; then
    wget -qO "${TMP_ARCHIVE}" "${DOWNLOAD_URL}"
else
    echo "ERROR: Neither curl nor wget found."
    exit 1
fi

if [ ! -s "${TMP_ARCHIVE}" ]; then
    echo "ERROR: Failed to download opencode-db from ${DOWNLOAD_URL}"
    exit 1
fi

# Replace the previous installation so files removed by a refactor do not linger.
rm -rf "${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"
tar xz -C "${INSTALL_DIR}" --strip-components=1 -f "${TMP_ARCHIVE}"

if [ ! -f "${INSTALL_DIR}/opencode_db/cli.py" ]; then
    echo "ERROR: Download failed — opencode_db/cli.py not found in ${INSTALL_DIR}"
    exit 1
fi

# --- 4. Create launcher ---
cat > "${LAUNCHER}" << SCRIPT
#!${PYTHON_BIN}
"""opencode-db launcher"""
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
chmod +x "${LAUNCHER}"

# --- 5. Verify ---
if ! "${LAUNCHER}" --help >/dev/null 2>&1; then
    echo "ERROR: Installation corrupted — opencode-db --help failed"
    exit 1
fi

# --- 6. Done ---
echo ""
printf "${GREEN}==> opencode-db installed successfully!${NC}\n"
echo ""
printf "  Run:  ${BOLD}opencode-db help${NC}\n"
echo ""
echo "  If the command is not found, add ~/.local/bin to your PATH:"
echo "    echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
echo "    source ~/.zshrc"
echo ""
echo "  Uninstall: rm -rf ${INSTALL_DIR} ${LAUNCHER}"
