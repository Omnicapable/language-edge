#!/bin/bash
set -e
cd "$(dirname "$0")"
command -v python3.11 >/dev/null || { echo 'Install Python 3.11 from python.org first.'; exit 1; }
test -d .venv || python3.11 -m venv .venv
.venv/bin/python -m pip install -c constraints-tested.txt -e '.[generate]'
.venv/bin/python scripts/install_demo.py
echo 'Setup complete. Launch Start Mac.command next.'
