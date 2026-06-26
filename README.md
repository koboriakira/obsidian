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

## vault-search

Vault 内のノートをハイブリッド検索（FTS5 + ベクトル検索 + リランク）するツール。

### インストール

```bash
bash tools/vault-search/install.sh
```

### HF_TOKEN の設定

モデルのダウンロードに Hugging Face Hub を使用する。認証トークンを設定するとレート制限の緩和・高速ダウンロードが有効になる（未設定でも動作するが警告が出る）。

トークンは無料アカウントで作成できる。

```bash
# 1. https://huggingface.co/settings/tokens でトークンを作成（Read 権限）
# 2. CLI でログイン
hf auth login
```

詳細: https://huggingface.co/docs/huggingface_hub/guides/cli

### 基本的な使い方

```bash
# インデックスの構築・更新
vault-search index

# 検索
vault-search search "キーワード"

# インデックスの状態確認
vault-search status
```

### 複数 Vault の管理

`~/.config/vault-search/config.yaml` で複数の Vault を登録できる。

```yaml
default: my-vault
vaults:
  my-vault:
    path: ~/obsidian/my-vault
    target_dirs: [Wiki, Areas, Projects, Inbox, Raws]
  work:
    path: ~/obsidian/work-vault
    target_dirs: [Notes, Projects]
```

`--vault` オプションで対象を切り替える。省略時は `default` に指定した Vault が使われる。

```bash
# 特定の Vault を指定してインデックス構築
vault-search index --vault work

# 特定の Vault を検索
vault-search search --vault work "キーワード"

# 登録済み Vault の一覧
vault-search vaults
```

設定ファイルがない場合は `~/obsidian/my-vault` をデフォルトとして動作する。

## scripts/

Vault 管理用の Python スクリプト群。

| ファイル | 内容 |
|----------|------|
| `generate_tag_index.py` | タグ一覧を生成する |
| `apply_tag_changes.py` | タグの一括変更を適用する |
| `archive_old_tasks.py` | 古いタスクをアーカイブする |
