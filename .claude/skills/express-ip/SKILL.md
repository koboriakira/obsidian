---
name: express-ip
level: L2
kind: Action
scope: Project
description: 複数のIPを組み合わせて特定目的の成果物（express）を生成する。第3層のIP活用。
argument-hint: "[目的の説明] or [成果物の種類]"
allowed-tools: Read, Write, Bash
---

# express-ip — IPから成果物を生成する

> IPの定義・フォーマット・保存先ルールは `/ip` スキルを参照すること。

蓄積されたIPを組み合わせて、特定の目的を持った成果物（type: express）を生成する。Building a Second Brain の「Express」に相当する。

## 成果物の例

- 1on1の共有資料
- チーム勉強会のスライド構成
- ブログ記事の下書き
- 提案書・方針書
- 振り返りレポート

## 手順

### Step 1: 目的を明確にする

引数またはユーザーの指示から以下を確認する：

- **何を作るか** — スライド、記事、資料、レポート等
- **誰に向けたものか** — チームメンバー、上司、自分用等
- **どんな結論・主張を伝えたいか**

### Step 2: 使えるIPを探す

Wiki/ および Projects/ Areas/ から関連IPを収集する。

```bash
VAULT="$HOME/obsidian/my-vault"
# タグで検索
grep -rl "tags:" "$VAULT/Wiki/" | xargs grep -l "<関連タグ>"
# conceptで検索
grep -rl "concept:" "$VAULT/Wiki/" | xargs grep -l "<関連キーワード>"
```

### Step 3: IPを選別・構成する

1. 目的に関連するIPをリストアップする
2. 成果物のアウトラインを組み立てる
3. 各セクションにどのIPを使うか割り当てる
4. IPだけでは足りない部分を特定する（追加調査が必要なら報告）

### Step 4: 成果物を生成する

```yaml
---
type: express
purpose: （何のために作ったか）
tags:
  - タグ1
  - タグ2
composed_from:
  - "[[使ったIP名1]]"
  - "[[使ったIP名2]]"
created: YYYY-MM-DD
uid: （uuidgen で生成）
---
```

本文は成果物の形式に合わせて自由に書く。冒頭に目的を1文で明記する。

保存先は `/ip` スキルの保存先ルールに従う。

### Step 5: 完了報告

- 生成した成果物のタイトルとパスを報告する
- 使用したIPの一覧を示す
- IPが不足していた部分があれば「このテーマのIPがあると次回もっと良い成果物が作れる」と提案する

## express と document の違い

| | express | document |
|---|---------|----------|
| 生成元 | 既存IPの組み合わせ | ゼロから書く or rawから整える |
| composed_from | あり（IPへのリンク） | なし |
| 再利用性 | 高い（他の目的にも転用できる） | 中（特定の文脈向け） |

迷ったら: IPから組み立てたなら express、そうでなければ document。
