---
name: obsidian-bases
level: L2
kind: Knowledge
scope: Project
description: Obsidian Bases (.base ファイル) の作成・編集・管理を行う
allowed-tools: Read, Write, Edit, Bash
---

# obsidian-bases — Obsidian Bases 操作スキル

Obsidian Bases（v1.9〜）を使ってノートをデータベースビューとして管理する。
`.base` ファイルは YAML 形式で記述し、Vault 内のフロントマターを参照する。

## 基本原則

- **Vault 全体が1つのDB**: `.base` ファイルはビュー定義（クエリ）であり、データはフロントマターに格納される
- **フロントマターのみ**: ノート本文のインラインデータ（Dataview の `key::value`）は認識しない
- **直接編集可能**: テーブルのセルを編集するとフロントマターが自動更新される

## .base ファイルの基本構文

```yaml
filters:         # グローバルフィルター（全ビューに適用）
formulas:        # 計算プロパティ定義
properties:      # 列の表示名などを定義
summaries:       # カスタム集計関数
views:           # ビュー定義（複数可）
```

## フィルターの書き方

### 重要: フィルター条件はシングルクォートで囲む

Obsidian の YAML パーサーは、フィルター条件内の `"` を含む文字列をオブジェクトとして誤解析することがある。
**フィルター条件は必ずシングルクォート `'...'` で囲むこと。**

```yaml
# NG（"が入ると誤解析される）
filters:
  and:
    - file.inFolder("DB_Projects")

# OK（シングルクォートで囲む）
filters:
  and:
    - 'file.inFolder("DB_Projects")'
```

また `filters` 直下のキーは `and` / `or` / `not` の**いずれか1つのみ**使用可能（複数キーは不可）。

### フォルダで絞り込む（最重要）

```yaml
filters:
  and:
    - 'file.inFolder("DB_Projects")'
```

### タグで絞り込む

```yaml
filters:
  and:
    - 'file.hasTag("project")'
```

### 複合条件

```yaml
filters:
  or:
    - 'file.hasTag("book")'
    - and:
        - 'file.inFolder("DB_Projects")'
        - 'file.hasTag("active")'
    - not:
        - 'file.hasTag("archived")'
```

### よく使うフィルター式（すべてシングルクォートで囲む）

| 目的 | 式 |
|------|-----|
| フォルダで絞り込む | `'file.inFolder("FolderName")'` |
| タグで絞り込む | `'file.hasTag("tag")'` |
| 複数タグ（OR） | `'file.hasTag("cat", "dog")'` |
| プロパティが存在する | `'file.hasProperty("status")'` |
| 今日作成 | `'file.ctime.date() == today()'` |
| 直近7日更新 | `'file.mtime >= today() - "7d"'` |
| リンク先で絞り込む | `'file.hasLink("NoteName")'` |
| 現在のファイルへのリンク | `'file.hasLink(this)'` |
| 同じフォルダ | `'file.inFolder(this.file.folder)'` |

## ビューの書き方

### Table ビュー

```yaml
views:
  - type: table
    name: All Projects
    order:
      - note.status
      - note.start_date
      - file.name
    groupBy:
      property: note.status
      direction: ASC
    filters:
      and:
        - 'note.status != "Done"'
    limit: 50
```

### Cards ビュー

```yaml
views:
  - type: cards
    name: Gallery
    # image_property: cover  # カバー画像プロパティ名
```

### List ビュー

```yaml
views:
  - type: list
    name: Simple List
```

## フォーミュラの書き方

オブジェクト指向構文でチェーン可能（v1.9.2〜）。

```yaml
formulas:
  days_left: "due_date - today()"
  is_overdue: "if(due_date < today(), true, false)"
  label: 'status.upper() + " - " + file.name'
  price_formatted: 'if(price, price.toFixed(2) + " 円")'
```

フォーミュラの参照は `formula.days_left` のように `formula.` プレフィックスをつける。

## プロパティの表示設定

```yaml
properties:
  note.status:
    displayName: Status
  note.start_date:
    displayName: 開始日
  formula.days_left:
    displayName: 残日数
  file.name:
    displayName: ノート名
```

## サマリー（集計）

```yaml
summaries:
  customAverage: 'values.mean().round(3)'

views:
  - type: table
    summaries:
      note.price: Average   # 組み込みサマリー
      formula.score: Sum
```

組み込みサマリー: `Average`, `Sum`, `Min`, `Max`, `Range`, `Median`, `Stddev`, `Earliest`, `Latest`, `Checked`, `Unchecked`, `Empty`, `Filled`, `Unique`

## 完全な DB_Projects テンプレート

```yaml
filters:
  and:
    - file.inFolder("DB_Projects")

views:
  - type: table
    name: Active
    groupBy:
      property: note.status
      direction: ASC
    order:
      - note.start_date
      - file.name
    filters:
      and:
        - 'note.status != "Done"'
        - 'note.status != "Trash"'

  - type: table
    name: All
    order:
      - note.start_date
      - file.name
```

## フロントマターの型対応

| Obsidian 型 | YAML 例 | Bases での扱い |
|-------------|---------|--------------|
| Text | `status: "ToDo"` | 文字列比較 |
| Number | `priority: 3` | 数値比較・演算 |
| Date | `due_date: 2026-03-21` | 日付比較・演算 |
| Checkbox | `done: true` | Boolean |
| List | `tags: [a, b]` | リスト操作 |
| Link | `assignee: "[[田中太郎]]"` | リンク参照 |

## DB 作成手順

### 1. フォルダを作成

```
DB_ProjectName/        ← ノートを置くフォルダ
  _template.md         ← テンプレート（status等のフロントマターを含む）
```

### 2. .base ファイルを作成

場所: フォルダの外（`DB_ProjectName.base`）または中（`DB_ProjectName/DB_ProjectName.base`）

```yaml
filters:
  and:
    - file.inFolder("DB_ProjectName")

views:
  - type: table
    name: Active
    ...
```

### 3. ノートのフロントマターに必要なプロパティを定義

```yaml
---
status: ToDo
start_date: 2026-03-21
end_date:
tags: []
---
```

## Vault パス

```
$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault
```

## 注意事項

- `.base` ファイルは純粋な YAML（コードブロックで囲まない）
- `filters: []` は無効。空のフィルターは `filters: and: []` または省略
- `file.inFolder()` はサブフォルダも含む（再帰的）
- Obsidian アプリが起動していないと変更が即時反映されないことがある
- `_template.md` や `README.md` もフォルダ内にあると Bases に表示される（フロントマターに `status` がなければ判別可能）
