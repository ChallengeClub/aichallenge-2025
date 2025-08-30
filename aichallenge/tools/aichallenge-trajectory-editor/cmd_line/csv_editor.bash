#!/bin/bash

# 仮想環境をアクティベート
source "$(
  cd "$(dirname "${BASH_SOURCE[0]}")/../"
  pwd
)/.venv/bin/activate"

# このスクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 一つ前のディレクトリを取得
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
# editor.pyを実行
python3 "$PROJECT_ROOT/editor/editor.py"