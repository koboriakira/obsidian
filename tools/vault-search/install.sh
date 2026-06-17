#!/bin/bash
# vault-search のインストールスクリプト
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$HOME/.local/share/vault-search-venv"

# venvを作成（uvが使えればuv、なければpython3 -m venv）
if command -v uv &>/dev/null; then
    uv venv "$VENV_DIR"
    uv pip install --python "$VENV_DIR/bin/python" -r "$SCRIPT_DIR/requirements.txt"
else
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# ~/.local/bin に配置
mkdir -p ~/.local/bin
cp "$SCRIPT_DIR/vault_search.py" ~/.local/bin/vault-search
# shebangをvenvのPythonに書き換え
sed -i '' "1s|.*|#!${VENV_DIR}/bin/python|" ~/.local/bin/vault-search
chmod +x ~/.local/bin/vault-search
echo "インストール完了: ~/.local/bin/vault-search"
echo "Python: ${VENV_DIR}/bin/python"
