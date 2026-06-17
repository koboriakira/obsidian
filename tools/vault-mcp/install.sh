#!/bin/bash
# vault-mcp のインストールスクリプト
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 依存関係インストール
pip install -r "$SCRIPT_DIR/requirements.txt"

# ~/.local/bin に配置（PATHに含まれているため）
mkdir -p ~/.local/bin
cp "$SCRIPT_DIR/vault_mcp.py" ~/.local/bin/vault-mcp
chmod +x ~/.local/bin/vault-mcp
echo "インストール完了: ~/.local/bin/vault-mcp"
echo ""
echo "Claude Desktop 設定例 (~/Library/Application Support/Claude/claude_desktop_config.json):"
echo ""
cat <<'JSON'
{
  "mcpServers": {
    "obsidian-vault": {
      "command": "vault-mcp",
      "env": {
        "OBSIDIAN_VAULT_PATH": "/path/to/your/vault"
      }
    }
  }
}
JSON
