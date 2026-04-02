# obsidian

Obsidian Vault 管理用のスクリプト・Claude Code スキル集。

## Claude Code プラグインのインストール

このリポジトリは Claude Code のプラグインマーケットプレイスとして機能する。
`obsidian-skills` プラグインをインストールすると、以下のスキルが使えるようになる。

- `obsidian-cli` — Vault をローカル CLI で操作する
- `obsidian-bases` — Bases ファイルの作成・編集
- `obsidian-classify` — PARA メソッドに基づく格納先判断
- `obsidian-project` — プロジェクトノートの作成・更新
- `para` — PARAメソッドに基づくノート管理ルール

### 手順

**1. リポジトリをクローンする**

```bash
git clone https://github.com/koboriakira/obsidian
```

**2. ローカルパスをマーケットプレイスとして登録する**

```bash
claude plugin marketplace add ./obsidian
```

**3. プラグインをインストールする**

```bash
claude plugin install obsidian-skills
```

**4. 確認**

```bash
claude plugin list
```

### アップデート

```bash
git -C ./obsidian pull
claude plugin update obsidian-skills
```

### アンインストール

```bash
claude plugin uninstall obsidian-skills
claude plugin marketplace remove obsidian-local
```

## scripts/

Vault 管理用の Python スクリプト群。

| ファイル | 内容 |
|----------|------|
| `generate_tag_index.py` | タグ一覧を生成する |
| `apply_tag_changes.py` | タグの一括変更を適用する |
| `archive_old_tasks.py` | 古いタスクをアーカイブする |
