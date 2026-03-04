---
name: daily-summary
description: Collect and summarize Obsidian session notes for a given date. Use when gathering daily development records from Obsidian vault.
argument-hint: "[YYYY-MM-DD] (省略時は今日の日付)"
allowed-tools: Read, Grep, Glob, Bash
---

# 日次記録サマリー

Obsidian Vault から指定日に更新されたセッション記録を収集し、プロジェクト別に構造化した要約を返す。

## Vault パス

```
$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault
```

## 実行手順

1. 引数として対象日（YYYY-MM-DD）を受け取る。省略時は今日の日付（`date +%Y-%m-%d`）を使う
2. `Claude/` ディレクトリ配下全体から、ファイル名が対象日で始まる `.md` ファイルを検索する

```bash
find "$VAULT_PATH/Claude" -type f -name "YYYY-MM-DD*.md"
```

3. さらに `dailynote/` 配下の対象日ファイルも含める（例: `dailynote/YYYY-MM-DD.md`）

```bash
find "$VAULT_PATH/dailynote" -type f -name "YYYY-MM-DD.md"
```

4. 検出したファイルをすべて読み取る
5. プロジェクト別にグルーピングする。グループのキーは:
   - `Claude/Code/{org}/{repo}/` → `{repo}`
   - `Claude/Projects/{project}/` → `{project}`
   - `Claude/Chat/` → `Chat`
   - `dailynote/` → `DailyNote`
   - その他 → ファイルパスからの推定

6. 各ファイルから以下を抽出する:
   - タイトル（`#` 見出し）
   - 概要セクションの内容
   - やりとりの詳細の各マイルストーン名
   - 具体的な成果（テスト数、ビルド番号、スコアなど数値情報）
   - 重要な設計判断

## 出力フォーマット

以下の形式で返す:

```
# 日次記録サマリー（YYYY-MM-DD）

## {プロジェクト名1}
セッション数: N

### {セッションタイトル1}
- 概要: ...
- 主な成果: ...
- 設計判断: ...（あれば）

### {セッションタイトル2}
...

## {プロジェクト名2}
...
```

## 制約

- ファイルの内容を改変・解釈しない。記録されている事実をそのまま要約する
- 感情や意図の推測はしない
- 数値データ（テスト数、ビルド番号、スコアなど）は正確に転記する

## 機密情報に関する注記

収集結果が公開用途で使われる場合に備え、以下の情報源を含む場合、サマリーの該当プロジェクト名に `[業務]` タグを付与すること。利用側で適切にぼかす判断材料になる。

- `a-kobori` ユーザーに紐づくリポジトリの記録
- `spine-lab` 組織配下のリポジトリの記録
- 上記に関連する Slack の要約・業務連絡
