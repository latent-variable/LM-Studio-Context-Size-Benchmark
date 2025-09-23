#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_ROOT"

if [[ "${INSTALL_DEPS:-0}" == "1" ]];
then
    echo "📦 Installing requirements..."
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
fi

python smart_benchmark.py "$@"
