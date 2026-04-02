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

**1. マーケットプレイスを追加する**

```bash
claude plugin marketplace add koboriakira/obsidian
```

**2. プラグインをインストールする**

```bash
claude plugin install obsidian-skills
```

**3. 確認**

```bash
claude plugin list
```

### アップデート

```bash
claude plugin marketplace update obsidian-local
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
