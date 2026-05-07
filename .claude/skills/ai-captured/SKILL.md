---
name: ai-captured
level: L3
kind: Ops
scope: Project
description: |
  当日の dailynote ファイル群を読み込み、第三者目線で一日の行動記録マークダウン（ai-captured.md）を作成する。
  「一日の行動記録を作って」「ai-captured を作って」「dailynote から今日の記録を作って」「今日何してたか記録して」など、
  日次行動記録の作成・更新を依頼されたときは必ずこのスキルを参照すること。
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# ai-captured — 一日の行動記録作成スキル

dailynote の各種ファイルを読み込み、時系列でまとめた行動記録 `ai-captured.md` を生成する。

## Vault パス

```
$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault
```

## 出力ファイル

```
dailynote/YYYY/MM/DD/ai-captured.md
```

---

## ステップ1：ファイルとカレンダーを読み込む

対象ディレクトリのファイルを確認する（`summary.md` は除外）。

```bash
ls "$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault/dailynote/YYYY/MM/DD/"
```

読み込み優先度：

| ファイル | 内容 |
|---------|------|
| `screenocr.md` | 時間帯ごとのアプリ・操作記録（最も詳細な時系列情報） |
| `AIセッション.md` | Claude Code セッションの概要と成果 |
| `tasks/` (横断) | 当日（scheduled_date = 対象日）のタスク。dailynote/YYYY/MM/DD/tasks/・Projects/*/tasks/・Areas/*/tasks/・Inbox/ を横断して status: done / in_progress のものを取得 |
| `arika-session.md` | Arikaとのセッション作業記録。意思決定・実装内容・ルーティン変更などArika経由の作業が記録されている。screenocrで拾えない作業の補完に使う |
| `Slackサマリー.md` | Slack での発言・アウトプットのサマリー（**存在する場合のみ**） |
| `task-board.md` | 当日着手・完了タスクの一覧（Vault 直下） |

`tasks/` 横断取得コマンド例：

```bash
VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault"
TARGET_DATE="YYYY-MM-DD"
# scheduled_date が対象日 かつ status が done/in_progress のタスクを横断取得
grep -rl "scheduled_date: ${TARGET_DATE}" \
  "${VAULT}/dailynote/${YYYY}/${MM}/${DD}/tasks/" \
  "${VAULT}/Projects" \
  "${VAULT}/Areas" \
  "${VAULT}/Inbox" 2>/dev/null \
| xargs grep -l "status: done\|status: in_progress" 2>/dev/null
```

これらを**並行して**読み込む。

タスクボードは以下のパスにある：
```
$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault/Claude/task-board.md
```
当日付け（`➕ YYYY-MM-DD`）のタスクを抽出する。

### Googleカレンダーから当日の予定を取得する

`gws` コマンドで仕事カレンダーのイベントを取得し、screenocr や donelist に漏れているMTGを補完する。
MTGの正式名称はカレンダーを正とする。

```bash
gws calendar events list --params '{
  "calendarId": "a69970646019f1fff526aa52231392fe8ebe8861eee70666f834fd7e550092cf@group.calendar.google.com",
  "timeMin": "YYYY-MM-DDT00:00:00+09:00",
  "timeMax": "YYYY-MM-DDT23:59:59+09:00",
  "singleEvents": true,
  "orderBy": "startTime"
}' | python3 -c "
import json, sys
data = json.load(sys.stdin)
for e in data.get('items', []):
    start = e.get('start', {}).get('dateTime', e.get('start', {}).get('date', ''))
    end = e.get('end', {}).get('dateTime', e.get('end', {}).get('date', ''))
    print(f\"{start} - {end}: {e.get('summary', '(タイトルなし)')}\" )
"
```

認証エラーが出た場合は `gws auth login` を実行してから再試行する。

---

## ステップ2：ギャップを特定してインタビューする

screenocr の記録と**カレンダーイベント**を照合し、漏れや不明点を洗い出す。
特に以下のケースは積極的に質問する：

- screenocr の記録開始より前の時間（起床前・午前中など）
- 30分以上の記録空白（休憩・外出・食事・育児など）
- カレンダーに存在するが screenocr で Meet 参加が確認できないMTG
- カレンダーにない Google Meet 参加記録（非公式MTGや突発的な通話）
- 予定（donelist）はあるが実施確認できないもの（MTGのキャンセル等）

**インタビュー例：**
```
以下の時間帯について教えてください。

1. 〜13:00：screenocr の記録がありません。何をしていましたか？
2. 18:23〜18:53：記録が途切れています。離席・休憩でしょうか？
3. 14:00 のイテレーションデモ：実施されましたか？内容は？
4. カレンダーに「仕事予定」とありますが、内容を教えてください。
```

ユーザーの回答を得てから、次のステップへ進む。
「後で補足」と言われた項目は `※内容は後で補足予定` とプレースホルダーを入れる。

---

## ステップ3：タイムラインを組み立てる

収集した情報を時系列に整理する。タスクボードに完了時刻はないため、
screenocr のブランチ名・アプリ記録・Slack 内容と照合して時間帯を推定する。

### タイムラインの組み立て方針

- screenocr の時間帯ブロックを骨格にする
- タスクボードのタスクは、ブランチ名やチケット番号が一致する時間帯に配置する
- 配置できないタスクは最も文脈が近い時間帯に入れる
- 深夜帯（23:00以降）は Claude Code 自動化作業として簡潔にまとめる

---

## ステップ4：ai-captured.md を書く

**必ずハイブリッド型（スタイルD）で書くこと。**

### ハイブリッド型のルール

各時間帯ブロックは以下の構造にする：

```markdown
### HH:MM〜HH:MM セクションタイトル

1〜2文の文章で、その時間帯の文脈・流れ・雰囲気を書く。
何に集中していたか、どんな状況だったかを自然な言葉で表現する。

- 具体的な作業1（**重要タスクは太字**）
- 具体的な作業2（チケット番号は [SU-XXXX](URL) 形式でリンク）
- Slack・ツール操作など
```

**太字にするもの：** タスクボード記録のタスク、PR 作成・Merge、重要な設計・実装作業

**文章（冒頭1〜2文）のポイント：**
- 箇条書きの羅列にならないよう、流れや文脈を補う
- 「何に集中していたか」「どんな気分・状況だったか」を第三者目線で書く
- 長くなりすぎない（2文以内）

### ファイル構成

```markdown
---
（フロントマターは Obsidian が自動付与するため不要）
---
# YYYY-MM-DD 行動記録

## 概要
（2〜3文で一日全体を要約）

---

## タイムライン

### 〜HH:MM ...
### HH:MM〜HH:MM ...
...

---

## 仕事・開発の記録

週次レビューでの集計を目的に、チケット・カテゴリ・成果物・概算時間を記録する。

### 手動開発

| チケット | カテゴリ | 成果物・アウトプット | 状態 | 概算時間 |
|----------|----------|----------------------|------|----------|
| [SU-XXXX](URL) タスク名 | 開発 | PR #XXXX 作成・実装内容 | ✅ 完了 / 継続中 / ブロック中 | 〜Xh |

### Claude Code セッション（AI 補助作業）

| タスク | チケット | カテゴリ | 成果物・アウトプット | 状態 | 概算時間 |
|--------|----------|----------|----------------------|------|----------|
| タスク名 | [SU-XXXX](URL) | 開発ツール整備 | 成果物の説明 | ✅ 完了 | 〜Xh |

### マネジメント・調整

| 内容 | カテゴリ | 成果物・アウトプット | 概算時間 |
|------|----------|----------------------|----------|
| MTG名・1on1相手など（HH:MM〜HH:MM） | MTG / マネジメント / 運用 | 決定事項・成果 | Xh |

**カテゴリ一覧：** 開発 / 環境構築 / 設計・ドキュメント / 調査 / 運用 / マネジメント / MTG / 引き継ぎ

---

## Slack でのアウトプット
（Slackサマリー.md のアウトプット部分を箇条書きで）

---

## メモ・思考（Slackタイムズより）
（タイムズ発言・思考の記録）

---

## 翌日以降に継続
（未完了タスク）
```

---

## ステップ5：ファイルを保存する

```
dailynote/YYYY/MM/DD/ai-captured.md
```

に Write で保存する。既存ファイルがある場合は上書きではなく内容を確認してから更新する。

---

## 注意事項

- 記録はあくまで「推定」を含む。確信が持てない時間帯は「〜と考えられる」などの表現を使う
- screenocr のテキストなし（Claude Code 操作中）の記録は「Claude Code 等の自動化作業が継続」と書く
- ユーザーから「後で補足する」と言われた項目には `※内容は後で補足予定` を入れておく
- 深夜〜早朝の作業は端末名（koboriakira / a_kobori）を明記する
