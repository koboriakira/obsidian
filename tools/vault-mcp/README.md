# vault-mcp

Claude Desktop 用の Obsidian Vault MCP サーバ。指定した Vault 配下のファイルの
読み取りと新規作成ができる。

## 提供ツール

| ツール | 内容 |
|--------|------|
| `get_vault_info` | Vault のルートパスを返す |
| `read_note` | Vault 内のファイルを読み取る（相対パス指定） |
| `create_note` | Vault 内に新規ファイルを作成する（親ディレクトリは自動作成） |

すべて Vault ルート外のパスは拒否される（パストラバーサル防止）。

## インストール

```bash
./install.sh
```

`pip install -r requirements.txt` で `mcp` パッケージを入れ、`vault-mcp` を
`~/.local/bin/` に配置する。

## Claude Desktop 設定

`~/Library/Application Support/Claude/claude_desktop_config.json` に追記:

```json
{
  "mcpServers": {
    "obsidian-vault": {
      "command": "vault-mcp",
      "env": {
        "OBSIDIAN_VAULT_PATH": "/Users/yourname/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault"
      }
    }
  }
}
```

`OBSIDIAN_VAULT_PATH` を省略した場合、デフォルトの iCloud パス
(`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault`) が使われる。

設定後、Claude Desktop を再起動すると `obsidian-vault` サーバが利用可能になる。

## 動作確認（手動）

```bash
# MCP サーバを起動（stdio 経由のため通常は Claude Desktop から呼ぶ）
OBSIDIAN_VAULT_PATH=/path/to/vault vault-mcp
```

JSON-RPC で `tools/list` を送ると登録ツールが確認できる。
