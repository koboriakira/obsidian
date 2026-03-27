---
name: obsidian-cli
level: L1
kind: Ops
scope: Project
description: >
  Obsidian Vault をローカル CLI (`obsidian` コマンド) で操作するときに使う。
  「Obsidianにノートを作って」「デイリーノートに追記して」「Vaultを検索して」
  「タスクを確認して」「ノートのプロパティを変更して」など、Obsidian に対して
  何らかの操作を行う場合は必ずこのスキルを参照すること。
  Write/Edit ツールでの直接ファイル操作より obsidian コマンドを優先すること。
---

# obsidian-cli — Obsidian CLI 操作スキル

`obsidian` コマンドを使って Vault を操作する。Obsidian アプリが起動している必要がある（未起動の場合は最初のコマンドで自動起動）。

## 前提条件

- Obsidian 1.12.x（早期アクセス版）以上
- Settings → General → Command line interface を有効化済み
- Vault パス: `$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault`

## 基本構文

```bash
obsidian [vault=<name>] <command> [options]
```

- `vault=<name>` — 最初のパラメータに指定して Vault を切り替え（省略時はデフォルト Vault）
- スペースを含む値はクォートで囲む: `name="My Note"`
- `\n` で改行、`\t` でタブ
- `file=` は名前（wikilink 形式）、`path=` は正確なパス（`folder/note.md`）

## よく使うコマンド

### ノートの作成・読み書き

```bash
# ノートを作成
obsidian create name="ノート名" content="内容"
obsidian create name="ノート名" template=テンプレート名 open

# ファイルを読む
obsidian read file="ノート名"
obsidian read path="folder/note.md"

# 末尾に追記
obsidian append file="ノート名" content="追記内容"

# 先頭に挿入
obsidian prepend file="ノート名" content="挿入内容"

# ファイルを削除
obsidian delete file="ノート名"
```

### デイリーノート操作

デイリーノートは `dailynote/YYYY-MM-DD.md` にある。

```bash
# 今日のデイリーノートを読む
obsidian read path="dailynote/$(date +%Y-%m-%d).md"

# 今日のデイリーノートに追記
obsidian append path="dailynote/$(date +%Y-%m-%d).md" content="追記内容"

# 今日のデイリーノートのタスク一覧
obsidian tasks path="dailynote/$(date +%Y-%m-%d).md"
```

### 検索

```bash
# テキスト検索
obsidian search query="キーワード"

# フォルダを絞って検索
obsidian search query="キーワード" path="folder"

# コンテキスト付きで検索（マッチした行の前後も表示）
obsidian search:context query="キーワード"

# JSON 形式で検索結果を取得
obsidian search query="キーワード" format=json
```

### タスク管理

```bash
# Vault 全体のタスク一覧（未完了）
obsidian tasks todo

# 特定ファイルのタスク一覧
obsidian tasks file="ノート名" todo

# タスクを完了にする（path:line 形式で指定）
obsidian task ref="dailynote/2026-03-13.md:10" done

# タスクのステータスをトグル
obsidian task ref="dailynote/2026-03-13.md:10" toggle
```

### プロパティ（フロントマター）

```bash
# プロパティを設定
obsidian property:set name="status" value="done" file="ノート名"
obsidian property:set name="tags" value="tag1,tag2" type=list file="ノート名"

# プロパティを読む
obsidian property:read name="date" file="ノート名"

# プロパティを削除
obsidian property:remove name="status" file="ノート名"

# ファイルの全プロパティを表示
obsidian properties file="ノート名"
```

### ファイル・フォルダ一覧

```bash
# ファイル一覧
obsidian files
obsidian files folder="00_inbox"

# フォルダ一覧
obsidian folders

# 最近開いたファイル
obsidian recents

# タグ一覧（使用回数付き）
obsidian tags counts
```

### テンプレート

```bash
# テンプレート一覧
obsidian templates

# テンプレートの内容を確認
obsidian template:read name="テンプレート名"

# アクティブファイルにテンプレートを挿入
obsidian template:insert name="テンプレート名"
```

### ファイル操作

```bash
# ファイル情報を表示
obsidian file file="ノート名"

# ファイルを移動
obsidian move file="ノート名" to="新しいフォルダ"

# ファイルをリネーム
obsidian rename file="ノート名" name="新しい名前"

# ファイルを開く（GUI）
obsidian open file="ノート名"
```

## フォールバック

`obsidian` コマンドが使えない場合（Obsidian が起動していない、CLI 未設定など）は、
Vault ディレクトリへの直接ファイル操作にフォールバックする。

```bash
VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault"
# 例: デイリーノートに追記
echo "追記内容" >> "$VAULT/dailynote/$(date +%Y-%m-%d).md"
```

## 注意事項

- コマンドは Obsidian アプリとの IPC 通信で動作するため、Obsidian が起動していないと動作しない
- `file=` は Wikilink 名（拡張子不要）、`path=` は Vault 内の相対パス（拡張子あり）
- `obsidian --help` で全コマンド一覧を確認できる
- Installer が古い場合の警告が出るが操作自体は実行される
