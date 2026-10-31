#!/bin/bash
set -e
cd "$(dirname "$0")"
test -x .venv/bin/python || { echo 'Run Setup Mac.command first.'; exit 1; }
.venv/bin/python -m language_edge.cli serve
