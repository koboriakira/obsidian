---
name: tag-cleanup
description: Obsidian Vault のタグを整理する。重複・類似タグの統合と不要タグの削除を行う。
allowed-tools: Read, Write, Edit, Bash
---

# tag-cleanup — Obsidian タグ整理スキル

## 概要

`_tag_index.md` を分析してタグの問題を洗い出し、ユーザーの確認を得てから実際に修正する。
**必ずユーザーの承認を得てから変更を適用すること。**

## 実行手順

### 1. タグ一覧を取得

```bash
python3 ~/git/obsidian/scripts/generate_tag_index.py
```

生成された `_tag_index.md` を読み込む。

### 2. 問題のあるタグを分析

以下の観点で分類する:

**統合候補（重複・類似）**
- 表記揺れ: `#ai-session` / `#ai-agent` / `#agent` など
- 階層関係: `#プロレス` / `#プロレス/NJPW` など上位と下位が混在
- 同義: `#memo` / `#note` / `#メモ` など

**削除候補（今後増えなさそう）**
- 件数が 1〜2 件でテーマが特定すぎる
- 使われなくなったカテゴリ
- 一時的な用途で付けられたもの（例: `#tmp`）

**命名改善候補**
- 日英混在していて統一したいもの
- 意味が曖昧なもの

### 3. 提案をユーザーに提示

以下の形式で提案する:

```
【統合提案】
- #ai-session + #ai-agent → #ai  (15件 + 3件 → 18件)
  理由: どちらも AIセッション記録を指しており区別が不明確

【削除提案】
- #3WAYマッチ (2件)
  理由: 件数が少なく今後も増えにくいプロレス形式タグ。#プロレス タグで十分

【保留】変更しない候補
```

**ユーザーの承認を得てから次のステップへ進む。**

### 4. 変更を実行

承認が得られた変更を Python スクリプトで一括適用する。

```bash
python3 ~/git/obsidian/scripts/apply_tag_changes.py \
  --merge "old_tag1:new_tag" \
  --merge "old_tag2:new_tag" \
  --delete "delete_tag1" \
  --delete "delete_tag2"
```

`apply_tag_changes.py` が存在しない場合は以下の処理を実装してから実行:
- 全 `.md` ファイルのフロントマターを読み込む
- 指定されたタグ名を置換・削除する
- ファイルを上書き保存する

### 5. タグ一覧を再生成

```bash
python3 ~/git/obsidian/scripts/generate_tag_index.py
```

変更後の `_tag_index.md` を確認する。

## Vault パス

```
$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault
```

## 注意事項

- **変更前にユーザーの明示的な承認を得ること**
- タグ名の変更はフロントマターのみ対象（本文の `#tag` 記述は対象外）
- 階層タグ（`#parent/child`）を削除する場合は子タグのみ削除・親は残す
- バックアップの代わりに、変更ファイル数を事前に報告してから実行する
