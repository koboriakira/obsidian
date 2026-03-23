---
name: analyze-screen-ocr
description: Fetch ScreenOCR logs for the past hour and append a behavior analysis section to the Obsidian daily note
context: fork
agent: general-purpose
disable-model-invocation: true
argument-hint: "[YYYY-MM-DD HH:MM]"
allowed-tools: Read, Glob, Edit, Write, Bash
---

# ScreenOCR 行動分析レポート（1時間単位・追記）

## コンテキスト

- ホームディレクトリ: !`echo $HOME`
- Vaultパス: !`echo ${OBSIDIAN_VAULT_PATH:-$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault}`
- 現在日時: !`date '+%Y-%m-%d %H:%M'`
- 1時間前の日時: !`date -v-1H '+%Y-%m-%d %H:%M'`

## 対象期間の決定

$ARGUMENTS が `YYYY-MM-DD HH:MM` 形式で指定されている場合、その日時を `{TO}` として使用し、1時間前を `{FROM}` とする。
指定がない場合は現在日時を `{TO}`、1時間前を `{FROM}` とする。

### 日付の決定ルール（05:00を日付切り替えとする）

`{FROM}` の時刻が 00:00〜04:59 の場合は **前日** を `{DATE}` とする。
`{FROM}` の時刻が 05:00 以降の場合は `{FROM}` の日付をそのまま `{DATE}` とする。

例:
- FROM = `2026-03-11 01:00` → DATE = `2026-03-10`（前日）
- FROM = `2026-03-11 05:00` → DATE = `2026-03-11`（当日）

`{YYYY}`, `{MM}`, `{DD}` は `{DATE}` から導出する（例: 2026-03-10 → 2026/03/10）。

出力先ファイル: `{Vaultパス}/dailynote/{YYYY}/{MM}/{DD}/screenocr.md`

## 処理手順

### 1. データ取得

以下のコマンドで対象ユーザーごとにログを取得する（並列実行）:

```bash
screenocr fetch --user koboriakira --from "{FROM}" --to "{TO}"
screenocr fetch --user a_kobori --from "{FROM}" --to "{TO}"
```

両ユーザーの出力をマージして以降の処理を行う。
両方とも空（レコード0件）の場合は「{FROM}〜{TO} のログが存在しません」と報告して終了する。

### 2. データ読み込み（並列で実行）

- 上記コマンドの出力（JSON/JSONL）を解析する
- 出力先ファイル（`screenocr.md`）が既存であれば Read で読み込む（追記のため）
- 対象日の dailynote を Read で読み込む（背景情報用）

### 3. データ分析

- 全レコードを時系列に整理する
- window_title からアプリケーション使用時間を集計する
- ocr_text から具体的な作業内容を特定する
- 端末（user）別の操作時間を集計する

### 4. レポートセクション生成と追記

#### ファイルが存在しない場合（初回）

以下のフロントマターとヘッダーを含む新規ファイルを作成し、時間帯セクションを追加する:

```markdown
---
tags:
  - dailynote
  - screenocr
created: {DATE}
---

# ScreenOCR Logger - 行動分析レポート

<!-- sections -->
```

#### ファイルが既存の場合（2回目以降）

ファイルの末尾に新しい時間帯セクションを追記する（時間の昇順になるよう末尾追加）。
同じ時間帯のセクション（同じ `## HH:MM〜HH:MM` 見出し）が既にある場合は上書き更新する。

#### 時間帯セクションのフォーマット

```markdown
## {FROM_HH:MM}〜{TO_HH:MM}

| 指標 | 値 |
|------|-----|
| 記録レコード数 | N件 |
| 主要使用アプリ | アプリ1, アプリ2, アプリ3 |
| 使用端末 | 端末1（X件）, 端末2（Y件） |

### 活動サマリー

（この時間帯に何をしていたか2〜4文で簡潔に記述）

### アプリ別詳細

| アプリケーション | 推定使用時間 | 主な内容 |
|----------------|------------|---------|
| ... | 約X分 | ... |
```

## 分析ガイドライン

- 「リピート」タスク（定常業務やルーチン）は簡潔に記述する
- 「単発」「プロジェクト」「差し込み」タスクを優先的に詳述する
- 会議や通話（Zoom, Teams, Google Meet 等）は内容を明記する
- レコードがほとんどない時間帯は「操作なし（{N}件）」と一行で記載する

## プライバシー配慮

- 子どもの名前は記載しない
- 資産額・個人を特定できる情報は抽象化する
