# obsidian-mcp — 概要・アーキテクチャ

## 目的

Claude（Claude.ai / Claude Code）から Obsidian Vault に対してノート作成・追記・検索を行えるようにする。
ローカルマシンに依存しない **リモート MCP サーバー** として Render 上で動作させる。

## 背景・課題

`my-local-mcp`（TypeScript製）はすでに存在するが、ローカルで起動している必要がある。
Claude.ai の Web 版など「ローカルプロセスに接続できない環境」からも Vault を操作したい。

## アーキテクチャ決定

### 根本的な制約

Render 上のサーバーは Obsidian Vault（iCloud Drive 上のローカルファイル）に直接アクセスできない。
この制約を回避するための方式を以下に比較する。

| 方式 | 概要 | メリット | デメリット |
|------|------|----------|------------|
| **A: GitHub 経由（推奨）** | Vault の対象ディレクトリを GitHub に公開し、Render サーバーが GitHub API 経由でファイルをコミット。ローカルは obsidian-git プラグインで pull | Render 側が完結・リアルタイム性不要な用途に最適 | obsidian-git の pull 間隔だけ遅延する |
| B: Obsidian Local REST API + トンネル | Local REST API プラグイン + Cloudflare Tunnel で Vault を外部公開 | ほぼリアルタイム | プラグイン導入・トンネル常時起動が必要 |
| C: taskchute-web 経由 | 既存 taskchute-web の内部 API を使う | 再利用可能 | ローカル起動が前提・ポートを外部公開しなければならない |

**方式 A を採用する。**
- Render 側に外部依存（ローカルトンネル等）が不要
- Vault の git 管理は他の用途でも有用
- 書き込みのレイテンシが許容できる（ノート作成・日記追記など即時性は不要）

### 構成図

```
Claude (claude.ai / Claude Code)
    │
    │ MCP over HTTP (Streamable HTTP Transport)
    ▼
Render Web Service
  obsidian-mcp (FastAPI + mcp[cli])
    │
    │ GitHub Contents API (PUT /repos/.../contents/...)
    ▼
GitHub リポジトリ (koboriakira/my-vault または専用リポジトリ)
    │
    │ obsidian-git プラグイン（ローカルで定期 pull）
    ▼
Obsidian Vault (iCloud Drive)
```

### Vault の git 化方針

- Vault 全体を git 管理する必要はない
- 当面の対象: `dailynote/` `Projects/` `Areas/` `Inbox/`
- `obsidian-git` プラグインの自動 pull 間隔: 5〜10 分（設定可能）

## スコープ（v1）

### 対象

- ノート作成（新規ファイル作成）
- 既存ノートへの追記（append）
- デイリーノートへの追記
- ノート読み取り
- ノート検索（ファイル名・パス）

### 対象外（v1 では実装しない）

- フロントマターの更新
- ファイル移動・リネーム
- タスク管理（taskchute-web が担当）
- 全文検索（GitHub Contents API では困難）
- バイナリファイル（画像等）

## 非機能要件

| 項目 | 目標値 |
|------|--------|
| MCP ツール応答時間 | 5 秒以内（GitHub API 呼び出し含む） |
| 認証 | Bearer トークン（環境変数で管理） |
| デプロイ環境 | Render Free Tier（スリープあり） |
| Python バージョン | 3.12 以上 |
