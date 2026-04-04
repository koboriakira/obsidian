---
name: ip
level: L1
kind: Knowledge
scope: Project
description: IP（Intermediate Packet）の定義・フォーマット・type・保存先ルール。IPに関わるすべてのスキルはこれを参照する。
allowed-tools: Read
---

# ip — Intermediate Packet 定義

IPとは「再利用可能な知識の塊」。バラバラな情報を蒸留し、文脈を超えて使える形にしたもの。

> **整理 = ファイルの移動 ではなく 整理 = 新しいIPの作成**

## IPの原則

- **1IP = 1概念・1結論** — 複数の概念を1ファイルに詰め込まない
- **命題型タイトル** — 「〇〇は〇〇である」「〇〇するには〇〇する」
- **ソースへのバックリンク** — 元ファイルを必ず `sources` で参照する
- **自己完結** — このIPだけ読めば理解できる。他のIPを読まないと意味不明、にしない

## IPのtype

| type | 階層 | 内容 | 生成スキル |
|------|------|------|-----------|
| ip | 第1層 | 素材から蒸留された知識 | `/generate-ip` |
| ip | 第2層 | 複数IPを合成した抽象知識 | `/synthesize-ip` |
| express | 第3層 | IP群から特定目的で生成した成果物 | `/express-ip` |

## フロントマター仕様

### type: ip（第1層・第2層共通）

```yaml
---
type: ip
concept: （何についての知識か。10〜20字）
tags:
  - タグ1
  - タグ2
sources:
  - "[[元ノート名]]"           # 第1層: rawへのリンク
  # or
  - "[[元IP名]]"              # 第2層: 他IPへのリンク
created: YYYY-MM-DD
uid: （uuidgen で生成）
---
```

### type: express（第3層）

```yaml
---
type: express
purpose: （何のために作ったか。「チーム勉強会スライド」など）
tags:
  - タグ1
  - タグ2
composed_from:
  - "[[IP名1]]"
  - "[[IP名2]]"
created: YYYY-MM-DD
uid: （uuidgen で生成）
---
```

## 本文の構造

### ip の本文

```markdown
# タイトル（命題型）

（結論を1文で）

（理由・背景を1〜2文で）

**判断ルール:**
- （この知識をいつ使うか・使わないかを箇条書きで）
```

150〜300字に収める。長くなるなら分割して複数IPにする。

### express の本文

成果物の形式に合わせて自由。ただし冒頭に「このドキュメントの目的」を1文で書く。

## 保存先ルール

| 条件 | 保存先 |
|------|--------|
| 汎用知識（文脈を超えて再利用できる） | `Wiki/` |
| 特定プロジェクトに紐づく | `Projects/<PJ名>/` |
| 特定エリアに紐づく | `Areas/<エリア名>/` |
| 迷ったら | `Wiki/` |

express も同じルールに従う。

## 関連するtype（IP以外）

| type | 内容 | 主な置き場 |
|------|------|-----------|
| document | 特定の文脈に属する正式な文書 | Projects/ or Areas/ |
| raw | 未整理の素材 | Raws/ |
| project | プロジェクト概要 | Projects/xxx/_index.md |
| task | タスク一覧 | Projects/xxx/tasks.md |

## Vault ディレクトリ構造

```
Inbox/        ← 未処理
Projects/     ← アクティブなプロジェクト
Areas/        ← 継続的な責任
Wiki/         ← IPのみ（蒸留済み汎用知識の倉庫）
Raws/         ← IPの原材料（放置OK）
```

## IPを生成すべきでないケース

| ケース | 対応 |
|--------|------|
| タスク・TODOのみ | タスク管理に任せる |
| 時事性が高く再利用不可 | そのまま保持か削除を提案 |
| 情報が断片的すぎる | 「情報が不足している」と報告 |
| 既存IPと内容が重複 | 既存IPを更新するか統合を提案 |
