# 実装ガイド

## リポジトリ名

`obsidian-mcp`

テンプレート: `koboriakira/python-project-2026`

## ディレクトリ構成

```
obsidian-mcp/
├── src/
│   └── obsidian_mcp/
│       ├── __init__.py
│       ├── server.py          # MCP サーバーエントリポイント (FastMCP)
│       ├── api.py             # FastAPI アプリ（ヘルスチェック・認証ミドルウェア）
│       ├── github_client.py   # GitHub Contents API ラッパー
│       ├── vault.py           # Vault 操作ロジック（パス解決・frontmatter 組み立て等）
│       └── auth.py            # Bearer トークン検証
├── tests/
│   ├── test_vault.py
│   ├── test_github_client.py
│   └── test_server.py
├── pyproject.toml
├── Procfile                   # Render 用
├── render.yaml                # Render Blueprint（任意）
├── .env.example
├── CLAUDE.md
└── README.md
```

## 依存関係（pyproject.toml）

```toml
[project]
name = "obsidian-mcp"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.128.0",
    "uvicorn[standard]>=0.40.0",
    "mcp[cli]>=1.0.0",          # MCP Python SDK
    "httpx>=0.25.0",            # GitHub API 呼び出し
    "python-frontmatter>=1.1.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.0.0", # 環境変数管理
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.6.0",
    "mypy>=1.8.0",
]
```

## 環境変数

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `GITHUB_TOKEN` | GitHub Personal Access Token（repo スコープ） | `ghp_xxxx` |
| `GITHUB_OWNER` | Vault リポジトリのオーナー | `koboriakira` |
| `GITHUB_REPO` | Vault リポジトリ名 | `my-vault` |
| `GITHUB_BRANCH` | 書き込み先ブランチ | `main` |
| `OBSIDIAN_MCP_TOKEN` | MCP サーバーへのアクセストークン | 任意の文字列 |
| `ENVIRONMENT` | `development` / `production` | `production` |

`.env.example` に全項目を列挙する（値は空）。

## MCP サーバーの実装方針

[FastMCP](https://github.com/jlowin/fastmcp) または `mcp` SDK の `Server` クラスを使用する。

### server.py の骨格

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("obsidian-mcp")

@mcp.tool()
async def create_note(path: str, content: str, frontmatter: dict | None = None) -> dict:
    ...

@mcp.tool()
async def append_to_note(path: str, content: str) -> dict:
    ...

@mcp.tool()
async def append_to_daily_note(content: str, date: str | None = None, section: str | None = None) -> dict:
    ...

@mcp.tool()
async def read_note(path: str) -> dict:
    ...

@mcp.tool()
async def list_notes(directory: str = "", recursive: bool = False) -> dict:
    ...
```

### Streamable HTTP Transport

FastMCP は `mcp.run(transport="streamable-http")` で Streamable HTTP を有効化できる。
Render はポート `10000` を使うため、起動コマンドで指定する。

```python
# server.py の末尾
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=10000)
```

### 認証ミドルウェア

FastAPI の `Middleware` として実装し、`/mcp` エンドポイントのリクエストヘッダーを検証する。

```python
# auth.py
async def verify_token(request: Request) -> None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or auth[7:] != settings.obsidian_mcp_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
```

## GitHub Contents API の利用方針

### ファイル作成・更新

`PUT /repos/{owner}/{repo}/contents/{path}` を使用する。

- 新規作成: `sha` なしで PUT
- 更新（append）: 先に GET でファイルの `sha` を取得してから PUT

### Base64 エンコード

GitHub API はファイル内容を Base64 で送受信する。

```python
import base64

def encode_content(text: str) -> str:
    return base64.b64encode(text.encode()).decode()

def decode_content(encoded: str) -> str:
    return base64.b64decode(encoded.encode()).decode()
```

### コミットメッセージ規則

```
chore: create/update {path} via obsidian-mcp
```

## Render デプロイ設定

### Procfile

```
web: uvicorn obsidian_mcp.server:app --host 0.0.0.0 --port $PORT
```

FastMCP が FastAPI インスタンスを返す場合は `mcp.get_asgi_app()` 等で取得する。
詳細は実装時に SDK のドキュメントを参照すること。

### render.yaml（Blueprint）

```yaml
services:
  - type: web
    name: obsidian-mcp
    runtime: python
    buildCommand: pip install -e .
    startCommand: uvicorn obsidian_mcp.server:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: GITHUB_TOKEN
        sync: false   # Render ダッシュボードで手動設定
      - key: GITHUB_OWNER
        sync: false
      - key: GITHUB_REPO
        sync: false
      - key: GITHUB_BRANCH
        value: main
      - key: OBSIDIAN_MCP_TOKEN
        generateValue: true  # Render が自動生成
```

### ヘルスチェックエンドポイント

Render の Health Check Path に設定する: `GET /health`

```json
{ "status": "healthy", "version": "0.1.0" }
```

## Claude への接続設定

Claude Code の `.mcp.json` または Claude.ai の MCP 設定に以下を追加する。

```json
{
  "mcpServers": {
    "obsidian": {
      "transport": "http",
      "url": "https://obsidian-mcp.onrender.com/mcp",
      "headers": {
        "Authorization": "Bearer <OBSIDIAN_MCP_TOKEN>"
      }
    }
  }
}
```

## テスト方針

- `github_client.py`: GitHub API 呼び出しを `pytest-mock` でモック
- `vault.py`: パス解決・frontmatter 組み立てを純粋関数テスト
- `server.py`: FastMCP のテストクライアント（または httpx）でツール呼び出しを検証

GitHub API への実 HTTP リクエストは Integration テスト扱いとし、CI では `@pytest.mark.integration` でスキップ。

## 実装順序（推奨）

1. リポジトリ作成（python-project-2026 をテンプレートに）
2. `github_client.py` の実装とテスト
3. `vault.py` の実装とテスト（パス解決・frontmatter・section append）
4. `server.py` の MCP ツール実装
5. 認証ミドルウェア追加
6. Render デプロイ・疎通確認
7. Claude Code の `.mcp.json` に追加して動作確認

## 未解決事項（実装時に決定）

- FastMCP と低レベル `mcp.Server` のどちらを使うか（FastMCP が安定していれば推奨）
- `mcp.run(transport="streamable-http")` と FastAPI の統合方法（SDK バージョンによって異なる）
- Vault リポジトリを専用リポジトリにするか、既存の Vault リポジトリを使うか
