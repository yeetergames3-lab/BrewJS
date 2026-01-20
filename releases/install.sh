#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${BREW_INSTALL_DIR:-${HOME}/.local/bin}"
BINARY_NAME="brew"
SOURCE_BIN="${ROOT_DIR}/releases/${BINARY_NAME}"

mkdir -p "${TARGET_DIR}"

if [[ ! -x "${SOURCE_BIN}" ]]; then
  chmod +x "${SOURCE_BIN}"
fi

INSTALL_PATH="${TARGET_DIR}/${BINARY_NAME}"

if [[ -L "${INSTALL_PATH}" || -f "${INSTALL_PATH}" ]]; then
  rm -f "${INSTALL_PATH}"
fi

ln -s "${SOURCE_BIN}" "${INSTALL_PATH}"

echo "Installed ${BINARY_NAME} to ${INSTALL_PATH}"
if ! command -v "${BINARY_NAME}" >/dev/null 2>&1; then
  echo "Note: ensure ${TARGET_DIR} is on your PATH."
  echo "Example: export PATH=\"${TARGET_DIR}:\$PATH\""
fi
