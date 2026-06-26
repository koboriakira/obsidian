# obsidian

Obsidian Vault 管理用のスクリプト・Copilot CLI スキル集。

## Copilot CLI プラグインのインストール

このリポジトリは Copilot CLI のプラグインとして1コマンドで導入できる。
インストールすると、以下のスキルが使えるようになる。

- `obsidian-cli` — Vault をローカル CLI で操作する
- `obsidian-bases` — Bases ファイルの作成・編集
- `obsidian-classify` — PARA メソッドに基づく格納先判断
- `obsidian-project` — プロジェクトノートの作成・更新
- `para` — PARAメソッドに基づくノート管理ルール
- `ai-captured` — 一日の行動記録を作成する
- `daily-note-summary` — デイリーノートにサマリーを追記する
- `task-board` — タスクボードでタスク管理する
- `tag-cleanup` — タグを整理・統合する

### インストール（推奨）

```bash
copilot plugin install koboriakira/obsidian
```

### 確認・更新・アンインストール

```bash
# インストール済みプラグイン一覧
copilot plugin list

# 更新（リポジトリの最新を取得）
copilot plugin update obsidian

# アンインストール
copilot plugin uninstall obsidian
```

## vault-search のセットアップ

Vault 内のノートをハイブリッド検索（FTS5 + ベクトル検索）するツール。

### HF_TOKEN の設定

モデルのダウンロードに Hugging Face Hub を使用する。認証トークンを設定するとレート制限の緩和・高速ダウンロードが有効になる（未設定でも動作するが警告が出る）。

トークンは無料アカウントで作成できる。

```bash
# 1. https://huggingface.co/settings/tokens でトークンを作成（Read 権限）
# 2. CLI でログイン
hf auth login
```

詳細: https://huggingface.co/docs/huggingface_hub/guides/cli

## scripts/

Vault 管理用の Python スクリプト群。

| ファイル | 内容 |
|----------|------|
| `generate_tag_index.py` | タグ一覧を生成する |
| `apply_tag_changes.py` | タグの一括変更を適用する |
| `archive_old_tasks.py` | 古いタスクをアーカイブする |
