#!/bin/sh
#
# install.sh — opencode-db installer
# Usage: curl -fsSL https://raw.githubusercontent.com/VasilevNStas/opencode-db/main/install.sh | sh
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

# --- 1. Check Python ---
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: Python 3 not found. Install Python 3.12+ first."
    echo "  https://www.python.org/downloads/"
    exit 1
fi

PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "${PY_MAJOR}" -lt 3 ] || [ "${PY_MAJOR}" -eq 3 -a "${PY_MINOR}" -lt 12 ]; then
    echo "ERROR: Python 3.12+ required (found ${PY_MAJOR}.${PY_MINOR})"
    echo "  Upgrade Python: https://www.python.org/downloads/"
    exit 1
fi

# --- 2. Create directories ---
mkdir -p "${INSTALL_DIR}" "${BIN_DIR}"

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

tar xz -C "${INSTALL_DIR}" --strip-components=1 -f "${TMP_ARCHIVE}"

if [ ! -f "${INSTALL_DIR}/cli.py" ]; then
    echo "ERROR: Download failed — cli.py not found in ${INSTALL_DIR}"
    exit 1
fi

# --- 4. Create launcher ---
cat > "${LAUNCHER}" << 'SCRIPT'
#!/usr/bin/env python3
"""opencode-db launcher"""
import sys, os
PKG_DIR = os.path.expanduser("~/.local/share/opencode-db")
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)
import cli
sys.exit(cli.main())
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
