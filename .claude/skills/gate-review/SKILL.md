---
name: gate-review
level: L2
kind: Verification
scope: Project
description: 実装完了後の品質ゲート。受入条件の照合（acceptance-match）と知識配置の監査（4type-review）を実行する。
argument-hint: "<Issue番号 または 確認対象の説明>"
allowed-tools: Read, Bash, mcp__github__get_issue
---

# gate-review — 実装後の品質ゲート（gate③）

acceptance-match（受入条件 vs 実装の照合）と 4type-review（知識配置の監査）を統合したレビュースキル。
[[Wiki/横断/知識配置パイプライン_IssueからリリースまでのAIスキル設計]] の gate③ に対応する。

## いつ使うか

- 実装が完了し、テストが全 Green になった後
- PR を出す前の最終チェックとして
- 「レビューして」「gate を通して」と言われたとき

## ステップ

### 1. 入力の収集

Issue の受入条件と、実装の diff を取得する。

```bash
# Issue の受入条件
gh issue view <番号> --repo <owner/repo> --json body -q '.body'

# 実装の diff（直近コミットまたはブランチ全体）
git diff main...HEAD --stat
git diff main...HEAD -- '*.py' '*.ts' '*.tsx'

# テスト一覧
grep -rn "def test_\|it(" tests/ --include="*.py" --include="*.ts" | head -30
```

### 2. acceptance-match（受入条件の照合）

Issue の各受入条件（`- [ ] ...`）に対して、対応するテストが存在するかを照合する。

出力形式:

```
| # | 受入条件 | テスト | 状態 |
|---|---------|--------|------|
| 1 | ... | test_... | ✅ カバー |
| 2 | ... | — | ⚠️ 未検証 |
| 3 | ... | — | ⏭️ スコープ外（後続対応と明記） |
```

判定基準:
- **✅ カバー**: 対応するテストが存在し Green
- **⚠️ 未検証**: テストがない。CSS/UIなど自動テスト困難な場合は手動確認済みかを確認
- **⏭️ スコープ外**: Issue に「後続対応」「Phase 2」等の明記がある
- **❌ 未実装**: テストも実装もない

必須条件に ❌ があれば gate 不通過。

### 3. 4type-review（知識配置の監査）

ドメイン知識の4分類が正しい場所にあるかを監査する。

| 種別 | あるべき場所 | チェック方法 |
|------|-------------|------------|
| How | コード（型・命名・実装） | コードの関数名・変数名が意図を表しているか |
| What | テストコード | テストが振る舞いを記述し、実装詳細に依存していないか |
| Why | Issue / ADR | 動機が Issue の「背景と動機」に書かれているか |
| Why not | Issue / ADR | 却下理由・スコープ外が記述されているか |

配置ミスのパターン:
- コード内コメントに Why が書かれている（Issue/ADR に移すべき）
- テストが内部実装に依存している（How がテストに漏れている）
- Issue に How（実装手順）が書かれている（コードに任せるべき）

### 4. 結果報告

```
## gate-review 結果

### acceptance-match
- 必須条件: N/N カバー
- 未検証: M件（理由: ...)
- スコープ外: K件

### 4type-review
| 種別 | 配置 | 判定 |
|------|------|------|
| How | ... | ✅ / ⚠️ |
| What | ... | ✅ / ⚠️ |
| Why | ... | ✅ / ⚠️ |
| Why not | ... | ✅ / ⚠️ |

### 総合判定
- **通過** / **条件付き通過** / **不通過**
- 不通過の場合: 具体的な是正アクション
```

## gate 条件の調整

プロジェクトの成熟度に合わせて gate 条件を調整してよい。

- リリースプロセスが未整備 → changelog 生成は保留可
- ADR を起こすほどの意思決定がない → ADR crystallize はスキップ可
- 個人プロジェクト → 4type-review は軽量チェックでよい
