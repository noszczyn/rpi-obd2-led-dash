#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

PYTHON_BIN="${PROJECT_DIR}/.venv/bin/python"
if [ ! -x "${PYTHON_BIN}" ]; then
  PYTHON_BIN="python3"
fi

# main_perf.py imports modules from ../src
sudo env PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" "${SCRIPT_DIR}/main_perf.py"