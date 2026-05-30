# MCPツール仕様

MCP の [Streamable HTTP Transport](https://modelcontextprotocol.io/docs/concepts/transports) を使用する。
Python SDK: `mcp[cli]` (FastMCP または低レベル SDK)

## ツール一覧

### 1. `create_note`

Vault に新規ノートを作成する。すでにファイルが存在する場合はエラー。

**引数**

| 名前 | 型 | 必須 | 説明 |
|------|----|------|------|
| `path` | `string` | ✓ | Vault ルートからの相対パス（例: `Inbox/アイデア.md`） |
| `content` | `string` | ✓ | ノート本文（Markdown） |
| `frontmatter` | `object` | | YAML フロントマターとして設定するキーバリュー |

**返却**

```json
{
  "path": "Inbox/アイデア.md",
  "sha": "abc123...",
  "commit_url": "https://github.com/.../commit/..."
}
```

**エラー**

- `FileExistsError`: 同パスのファイルがすでに存在する

---

### 2. `append_to_note`

既存ノートの末尾に内容を追記する。ファイルが存在しない場合は新規作成する。

**引数**

| 名前 | 型 | 必須 | 説明 |
|------|----|------|------|
| `path` | `string` | ✓ | Vault ルートからの相対パス |
| `content` | `string` | ✓ | 追記する内容（先頭の改行は自動補完） |

**返却**

```json
{
  "path": "Projects/MyProject/メモ.md",
  "action": "created" | "appended",
  "sha": "abc123..."
}
```

---

### 3. `append_to_daily_note`

今日（または指定日）のデイリーノートに追記する。

デイリーノートのパス規則: `dailynote/{YYYY}-{MM}-{DD}.md`

**引数**

| 名前 | 型 | 必須 | 説明 |
|------|----|------|------|
| `content` | `string` | ✓ | 追記する内容 |
| `date` | `string` | | 対象日付（`YYYY-MM-DD` 形式）。省略時は今日 |
| `section` | `string` | | 追記先のセクション名（例: `## メモ`）。省略時は末尾 |

**返却**

```json
{
  "path": "dailynote/2026-05-30.md",
  "action": "created" | "appended",
  "sha": "abc123..."
}
```

**備考**

- セクションが指定された場合、そのセクションの末尾に挿入する
- セクションが存在しない場合はファイル末尾に `## {section}\n{content}` を追記する

---

### 4. `read_note`

指定パスのノートを読み取る。

**引数**

| 名前 | 型 | 必須 | 説明 |
|------|----|------|------|
| `path` | `string` | ✓ | Vault ルートからの相対パス |

**返却**

```json
{
  "path": "Projects/MyProject/context.md",
  "content": "# プロジェクト概要\n...",
  "frontmatter": { "status": "active", "tags": ["python"] },
  "sha": "abc123..."
}
```

**エラー**

- `FileNotFoundError`: ファイルが存在しない

---

### 5. `list_notes`

指定ディレクトリ配下のノート一覧を返す。

**引数**

| 名前 | 型 | 必須 | 説明 |
|------|----|------|------|
| `directory` | `string` | | 対象ディレクトリ（例: `Projects/MyProject`）。省略時は Vault ルート直下 |
| `recursive` | `boolean` | | サブディレクトリも含めるか（デフォルト: `false`） |

**返却**

```json
{
  "directory": "Projects/MyProject",
  "notes": [
    { "path": "Projects/MyProject/context.md", "name": "context" },
    { "path": "Projects/MyProject/tasks/作業A.md", "name": "作業A" }
  ]
}
```

---

## 認証

すべてのリクエストに Bearer トークンが必要。

```
Authorization: Bearer <OBSIDIAN_MCP_TOKEN>
```

トークンは Render の環境変数 `OBSIDIAN_MCP_TOKEN` で設定する。
Claude の MCP 設定にも同じトークンを記載する。

## エラーレスポンス形式

MCP のエラーは `isError: true` を設定してツール結果として返す（例外をそのままスローしない）。

```json
{
  "isError": true,
  "content": [{ "type": "text", "text": "FileNotFoundError: Projects/foo.md が見つかりません" }]
}
```
