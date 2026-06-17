---
name: task-board
level: L2
kind: Knowledge
scope: Project
description: Task management with Obsidian task board. Use for every task — record all work on the task board regardless of size. Optionally link to GitHub Issues when criteria are met.
argument-hint: "[タスク名（省略可）]"
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion, mcp__github__create_issue, mcp__github__get_issue, mcp__github__list_issues, mcp__github__search_issues
---

# タスクボード管理

Obsidian ベースのタスクボードを管理し、GitHub Issues との連携を行う。
Obsidian Tasks プラグインの記法に準拠する。

## ファイルパス

```
$HOME/obsidian/my-vault/Claude/task-board.md
```

## タスクの確認（任意のタイミングで実行）

`obsidian` CLI を優先して使用する（失敗時は Read でファイル直接読み込み）。

```bash
# 進行中タスクを自端末で絞り込む
obsidian tasks file="task-board" in-progress | grep "🖥 $(whoami)"

# 未着手タスクを絞り込む
obsidian tasks file="task-board" todo | grep "🖥 $(whoami)"

# キーワードで絞り込む場合
obsidian tasks file="task-board" in-progress | grep "キーワード"
```

自端末のタスクを優先的に表示する。他端末のタスクはユーザーから明示的に求められた場合のみ表示する。

## 作業開始フロー

### ステップ1：タスクボードへの追加

すべての作業をタスクボードに記録する。Issue の有無にかかわらず、作業を開始したら `## 🚧 In Progress` セクションに `[/]` ステータスで追加する。作成日を ➕ で、開始時刻を 🕐 で、端末ユーザー名を 🖥 で記録する。端末ユーザー名は `whoami` コマンドで、日付・時刻は `date` コマンドで取得する。

```markdown
- [/] タスク名 🖥 ユーザー名 ➕ YYYY-MM-DD 🕐 HH:MM
```

### ステップ2：Issue化の検討（該当する場合のみ）

以下の3基準のいずれかに該当する場合、Issue化するかユーザーに確認する。該当しない場合はこのステップをスキップする。

| 基準 | 内容 |
|---|---|
| 外部共有・レビュー | チームメンバーへの共有やコードレビューが必要か |
| システム変更 | コードやインフラ等の変更を伴うか |
| トラッキング | 進捗をチームで追跡する必要があるか |

Issue化する場合:

1. GitHub Issue を作成する（mcp__github__create_issue を使用）
2. タスクボードのタスクにリンクを追加する

```markdown
- [/] [#番号](https://github.com/org/repo/issues/番号) タスク名
```

### ステップ3：作業完了時

タスクが完了したら:

1. `[/]` → `[x]` に変更し、完了日を ✅ で記録する
2. Claude Code で作業した場合、Issue化しなかったタスクにはセッションURLを付与する（`[session](https://claude.ai/chat/${CLAUDE_SESSION_ID})`）。他ツール（GitHub Copilot Agent 等）で作業した場合はセッションURLなしでよい
3. タスクを `## 🚧 In Progress` から `## ✅ Done` セクション内のアーカイブ領域（クエリブロックの下）に移動する
4. `updated` フロントマターを更新する

```markdown
- [x] タスク名 [session](https://claude.ai/chat/xxxx) 🖥 ユーザー名 ➕ 2026-02-27 🕐 09:00 ✅ 2026-02-27 ⏰ 09:30
```

## タスクの記法

### ステータス記号（Tasks プラグイン準拠）

| 記号 | ステータス | 用途 |
|---|---|---|
| `[ ]` | TODO | 未着手（📋 Todo セクション） |
| `[/]` | IN_PROGRESS | 作業中（🚧 In Progress セクション） |
| `[x]` | DONE | 完了（✅ Done セクション） |
| `[-]` | CANCELLED/ON_HOLD | ブロック中（🚫 Blocked セクション） |

### 絵文字フィールド（Tasks プラグイン対応）

| 絵文字 | 意味 | 備考 |
|---|---|---|
| ➕ | 作成日（➕ YYYY-MM-DD） | Tasks 標準 |
| ✅ | 完了日（✅ YYYY-MM-DD） | Tasks 標準・自動付与 |
| 📅 | 期日（📅 YYYY-MM-DD） | Tasks 標準 |
| 🛫 | 開始可能日（🛫 YYYY-MM-DD） | Tasks 標準・任意 |
| ⏳ | 作業予定日（⏳ YYYY-MM-DD） | Tasks 標準・任意 |
| 🔺 | 優先度：最高 | Tasks 標準 |
| ⏫ | 優先度：高 | Tasks 標準 |
| 🔼 | 優先度：中 | Tasks 標準 |
| 🔽 | 優先度：低 | Tasks 標準 |
| ⏬️ | 優先度：最低 | Tasks 標準 |

### カスタムフィールド（Tasks 非対応・独自拡張）

Tasks プラグインには認識されないが、タスク行に自由テキストとして記載可能。クエリによる絞り込みはできないが、表示・記録目的で使用する。

| 絵文字 | 意味 |
|---|---|
| 🖥 | 端末ユーザー名（🖥 koboriakira など。`whoami` で取得） |
| 🔗 | 外部チケットURL（🔗 [PROJ-123](URL)） |
| 🕐 | 開始時刻（🕐 HH:MM。`date +%H:%M` で取得） |
| ⏰ | 完了時刻（⏰ HH:MM。`date +%H:%M` で取得） |

### 外部チケットリンク

GitHub Issue 以外のチケット管理サービス（Jira、Linear、Asana、Backlog 等）のURLがある場合、🔗 でタスクに記録する。リンクテキストはチケットIDや短い識別名にする。

```markdown
- [/] タスク名 🔗 [PROJ-123](https://example.atlassian.net/browse/PROJ-123)
```

GitHub Issue リンクと併用も可能:

```markdown
- [/] [#番号](https://github.com/org/repo/issues/番号) タスク名 🔗 [PROJ-123](https://example.atlassian.net/browse/PROJ-123)
```

### セクションの使い分け

| セクション | ステータス記号 | 用途 |
|---|---|---|
| 🚧 In Progress | `[/]` | 現在作業中のタスク |
| 📋 Todo | `[ ]` | 未着手のタスク |
| 🚫 Blocked | `[-]` | ブロックされているタスク |
| ✅ Done | `[x]` | 完了タスクのアーカイブ。クエリブロック＋その下にアーカイブ行 |

## 注意事項

- タスクボードファイルが存在しない場合はエラーを報告し、ユーザーに確認する
- 既存のタスクを上書き・削除しない。追記のみ行う
- フロントマターの `updated` は操作のたびに更新する
- Tasks プラグインのクエリ（`status.type is IN_PROGRESS` など）で検索可能にするため、セクション内のステータス記号を必ず対応させる
