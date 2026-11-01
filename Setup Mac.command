#!/bin/bash
set -e
cd "$(dirname "$0")"
setup_python="${LANGUAGE_EDGE_PYTHON:-}"
if [ -z "$setup_python" ]; then
  for candidate in python3.11 python3.12; do
    if command -v "$candidate" >/dev/null; then setup_python="$candidate"; break; fi
  done
fi
test -n "$setup_python" || { echo 'Install native Python 3.11 or 3.12 from python.org first.'; exit 1; }
mode="${1:-auto}"
install_mode="$("$setup_python" -m language_edge.platform_support --install-mode "$mode" --print-install)"
if [ -d .venv ] && [ ! -x .venv/bin/python ]; then
  echo 'This .venv is not a Mac environment. Rename it and run setup again; do not copy a Windows virtual environment.'
  exit 1
fi
test -d .venv || "$setup_python" -m venv .venv
.venv/bin/python -m language_edge.platform_support --install-mode "$install_mode" >/dev/null
.venv/bin/python -m pip install --upgrade pip setuptools wheel
if [ "$install_mode" = full ]; then
  .venv/bin/python -m pip install -c constraints-tested.txt -e '.[generate]'
else
  .venv/bin/python -m pip install -c constraints-tested.txt -e .
fi
.venv/bin/python scripts/install_demo.py
if [ "$install_mode" = full ]; then
  .venv/bin/python -m language_edge.platform_support --check-runtime --require-models
else
  .venv/bin/python -m language_edge.platform_support --check-runtime
fi
echo 'Setup complete. Launch Start Mac.command next.'
