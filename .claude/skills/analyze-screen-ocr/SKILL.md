---
name: analyze-screen-ocr
description: Analyze ScreenOCR JSONL logs for a given date and generate a behavior analysis report appended to the Obsidian daily note
context: fork
agent: general-purpose
disable-model-invocation: true
argument-hint: "[YYYY-MM-DD]"
allowed-tools: Read, Glob, Edit, Write, Bash
---

# ScreenOCR 行動分析レポート作成

## コンテキスト

- ホームディレクトリ: !`echo $HOME`
- Vaultパス: !`echo ${OBSIDIAN_VAULT_PATH:-$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault}`
- 現在の日付: !`date +%Y-%m-%d`
- デフォルト対象日（昨日）: !`date -v-1d +%Y-%m-%d`

## 対象日付の決定

$ARGUMENTS が YYYY-MM-DD 形式で指定されている場合はその日付を使用する。
指定がない場合は昨日の日付（上記デフォルト対象日）を使用する。
以降、決定した日付を `{DATE}` と表記する。

## データソース

### 1. ScreenOCRログ

- ディレクトリ: `{Vaultパス}/screenocr_logs/`
- 対象ファイル: `*/{DATE}*.jsonl` にマッチする全ファイル（アカウント別サブディレクトリ配下）
- 各レコードはJSON形式で timestamp, window_title, ocr_text 等を含む
- 1分間隔の画面キャプチャOCRデータ

### 2. Dailynote

- ディレクトリ: `{ホームディレクトリ}/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault/dailynote/`
- 対象ファイル: `{DATE}.md`
- 背景情報として過去1週間分の dailynotes も参照する

## 処理手順

### 1. 対象ファイルの確認

Glob で `{Vaultパス}/screenocr_logs/*/{DATE}*.jsonl` を検索する。
ファイルが見つからない場合は「対象日のログが存在しません」と報告して終了する。

### 2. データ読み込み（並列で実行）

- 全JSONLファイルを Read で読み込む
- 対象日の dailynote を Read で読み込む
- 過去1週間分の dailynotes を Read で読み込む（背景情報用）

JSONLファイルが大きい場合は、Bash で `wc -l` でレコード数を確認し、必要に応じて分割して読み込む。

### 3. データ分析

- 全レコードを時系列に整理する
- 各レコードのファイルパスからアカウント名（端末名）を判別する（`screenocr_logs/{アカウント名}/` 部分）
- window_title からアプリケーション使用時間を集計する
- 時間帯別に活動を分類する
- ocr_text から具体的な作業内容を特定する
- 過去の dailynotes から関連プロジェクトの背景を補完する
- 端末別に以下を集計する:
  - 端末ごとの操作時間とアクティブ時間帯
  - 同一時間帯に複数端末のログがある場合、端末間の切り替えパターンを分析する

### 4. レポート生成と追記

- 以下の出力フォーマットに従ってレポートを生成する
- dailynote ファイル `{DATE}.md` の末尾に追記する
- ファイルが存在しない場合は新規作成する

### 5. 処理済みJSONLファイルの削除

レポート生成完了後、処理に使用したJSONLファイルを削除してiCloudストレージを節約する。

1. **削除対象の特定**: ステップ1で検索した全JSONLファイルを対象とする。ただし `.current_jsonl` ファイルは現在書き込み中のため除外する
2. **ユーザーへの確認**: 削除前に以下の形式でファイル一覧を提示し、承認を待つ
   ```
   | ファイル | サイズ |
   |---------|--------|
   | path/to/file1.jsonl | XX KB |
   | path/to/file2.jsonl | XX KB |
   | **合計** | **XX KB** |
   ```
   `1. 削除する` / `2. 削除しない` の選択肢を提示する
3. **ファイル削除の実行**: 承認後に `rm` で各ファイルを削除し、完了メッセージを表示する

## 出力フォーマット

dailynote に以下のMarkdown構造で追記する:

```markdown
## ScreenOCR Logger - 行動分析レポート

### Executive Summary

- 1日の概要（2-3文）

| 指標 | 値 |
|------|-----|
| PC操作時間 | HH:MM |
| 会議時間 | HH:MM |
| 主要使用アプリ | アプリ1, アプリ2, アプリ3 |
| 使用端末 | 端末1, 端末2 |
| 記録レコード数 | N件（端末1: X件, 端末2: Y件） |

### 活動内容の詳細

#### 深夜〜早朝（0:00-6:00）
...

#### 朝（6:00-9:00）
...

#### 午前（9:00-12:00）
...

#### 昼〜午後（12:00-15:00）
...

#### 夕方（15:00-18:00）
...

#### 夜〜深夜（18:00-24:00）
...

### 端末別分析

（複数端末のログがある場合のみ表示）

| 端末 | 操作時間 | アクティブ時間帯 | レコード数 |
|------|---------|----------------|-----------|
| 端末1 | HH:MM | HH:MM〜HH:MM | N件 |
| 端末2 | HH:MM | HH:MM〜HH:MM | N件 |

- 端末間の切り替えパターン（同一時間帯に両端末のログがある場合に記載）

### ウインドウ別分析

| アプリケーション | 使用割合 | 主な用途 |
|----------------|---------|---------|
| ... | ...% | ... |

### 今日の振り返り

（ブログ掲載用の要約）
```

## 分析ガイドライン

- 「リピート」タスク（定常業務やルーチン）は簡潔に記述する
- 「単発」「プロジェクト」「差し込み」タスクを優先的に詳述する
- 過去の dailynotes から関連プロジェクトの経緯や背景を補完する
- 会議や通話（Zoom, Teams, Google Meet 等）は時間帯と内容を明記する
- レコードが存在しない時間帯は「記録なし」と記載する

## プライバシー配慮

「今日の振り返り」セクション（ブログ掲載用）では以下を省略する:

- 子どもの名前
- 資産額
- 個人を特定できる情報は抽象化する
