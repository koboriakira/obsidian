---
name: generate-ip
level: L2
kind: Action
scope: Project
description: 素材（raw）からIP（Intermediate Packet）を蒸留する。第1層のIP生成。
argument-hint: "[ソースファイルのパス or ノート名]"
allowed-tools: Read, Write, Bash
---

# generate-ip — 素材からIPを蒸留する

> IPの定義・フォーマット・保存先ルールは `/ip` スキルを参照すること。

既存のノート（議事録・調査メモ・記事要約など）を読み込み、再利用可能な知識（IP）として蒸留する。

## 手順

### Step 1: ソースファイルを読む

引数で受け取ったパスまたはノート名でファイルを読む。

```bash
VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault"
```

ファイルが見つからない場合は、Vault全体をファイル名で検索して候補を提示する。

### Step 2: IPを設計する

ソースを読んで以下を判断する：

1. **このファイルから抽出できるIPは何か？**
   - 1ファイルから複数IPが抽出できることもある
   - IPを生成すべきでないケースは `/ip` スキルを参照

2. **IP候補ごとに以下を決める：**
   - `concept`: 何についての知識か（10〜20字）
   - `title`: 命題型タイトル（「Aは Bである」「CにはDを使う」）
   - `tags`: 検索・分類用タグ（3〜5個）
   - `body`: 結論→理由→判断基準の順で150〜300字
   - 保存先: Wiki/ か Projects/ か Areas/（`/ip` スキルの保存先ルール参照）

### Step 3: 重複チェック

```bash
ls "$VAULT/Wiki/" 2>/dev/null
```

概念が重複する場合は新規生成せず、既存IPの更新または統合を提案する。

### Step 4: IPを生成する

UIDの生成:
```bash
uuidgen | tr '[:upper:]' '[:lower:]'
```

フォーマットは `/ip` スキルの「type: ip」仕様に従う。

### Step 5: ソースファイルの処理

IPを生成した後、元のソースファイルを `Raws/` に移動する。

```bash
mv "$VAULT/<元の場所>/<ファイル名>" "$VAULT/Raws/<ファイル名>"
```

- ソースが既に Raws/ にある場合は移動不要
- ソースを削除するかはユーザーに確認してから行う（デフォルトは Raws/ に保全）

### Step 6: 完了報告

- 生成したIPのタイトルとパスを報告する
- 「このソースから他にIPが抽出できそう」な場合は提案する
- ソースファイルの移動先を報告する
