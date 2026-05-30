# obsidian-mcp PRD

Claude から Obsidian Vault を操作するリモート MCP サーバーの仕様書。

## ドキュメント一覧

| ファイル | 内容 |
|----------|------|
| [overview.md](overview.md) | 目的・背景・アーキテクチャ決定（方式選定含む） |
| [mcp-tools.md](mcp-tools.md) | MCP ツール仕様（引数・返却値・エラー） |
| [implementation-guide.md](implementation-guide.md) | ディレクトリ構成・依存関係・Render デプロイ設定 |

## 実装リポジトリ

作成予定: `koboriakira/obsidian-mcp`
テンプレート: `koboriakira/python-project-2026`

## 前提条件（実装開始前に準備するもの）

- [ ] Vault を GitHub リポジトリとして公開（または専用リポジトリを作成）
- [ ] GitHub Personal Access Token 発行（`repo` スコープ）
- [ ] Obsidian の obsidian-git プラグインをインストール・設定
- [ ] Render アカウントでプロジェクト作成
