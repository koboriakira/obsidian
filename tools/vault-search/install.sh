#!/bin/bash
# vault-search のインストールスクリプト
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 依存関係インストール
pip install -r "$SCRIPT_DIR/requirements.txt"

# ~/.local/bin に配置（PATHに含まれているため）
mkdir -p ~/.local/bin
cp "$SCRIPT_DIR/vault_search.py" ~/.local/bin/vault-search
chmod +x ~/.local/bin/vault-search
echo "インストール完了: ~/.local/bin/vault-search"
