---
name: test-seed
level: L2
kind: Design
scope: Project
description: Issue の受入条件をテストスケルトン（it("...") の一覧）に変換する。設計フェーズの起点。
argument-hint: "<Issue番号 または 受入条件のテキスト>"
allowed-tools: Read, Write, Bash, mcp__github__get_issue
---

# test-seed — 受入条件からテストスケルトンを生成

Issue（または口頭）の受入条件を `it("...")` / `def test_...` のテストスケルトンに変換する。
TDD の起点となるファイルを生成し、Red 状態で渡す。

## いつ使うか

- Issue の受入条件が確定した後、実装に入る前
- kickstart 完了後の次ステップとして
- 「テストから書いて」と言われたとき

## ステップ

### 1. 受入条件の取得

引数が Issue 番号なら GitHub から取得する。テキストならそのまま使う。

```bash
gh issue view <番号> --repo <owner/repo> --json body -q '.body'
```

受入条件（`- [ ] ...` のリスト）を抽出する。

### 2. テスト言語・フレームワークの検出

プロジェクトのテスト構成を自動検出する。

```bash
# Python
ls pytest.ini pyproject.toml setup.cfg 2>/dev/null | head -1
ls tests/test_*.py tests/conftest.py 2>/dev/null | head -3

# TypeScript/JavaScript
ls jest.config.* vitest.config.* 2>/dev/null | head -1
find . -maxdepth 3 -name "*.test.ts" -o -name "*.spec.ts" 2>/dev/null | head -3
```

既存テストのスタイル（クラスベース / 関数ベース、命名規則）を1ファイル読んで合わせる。

### 3. 受入条件 → テスト名の変換

各受入条件を1つ以上のテスト名に変換する。

変換ルール:
- 1つの受入条件が複数のテストケースに分かれてよい（正常系 + 異常系）
- テスト名は振る舞いを記述する（実装詳細を含めない）
- テストクラスの docstring に元の受入条件を引用する

```python
class TestFileList:
    """受入条件: output/ 配下のファイル一覧が表示される（md, PDF, HTML 対応）"""

    def test_lists_all_files_in_output_directory(self, client):
        ...

    def test_returns_file_metadata_from_frontmatter(self, client):
        ...
```

### 4. スケルトンファイルの生成

テストファイルを生成する。本体は `...` または `pass` のみ。

- fixture は最小限の型ヒント付きで用意する
- import は検出したフレームワークに合わせる
- 既存テストファイルがある場合は末尾に追記するか、別ファイルにするか判断する

### 5. Red 確認

```bash
pytest <テストファイル> -v 2>&1 | tail -20
```

全テストが FAILED または ERROR であること（Red 状態）を確認する。
テストが収集すらされない場合は構文エラーがあるので修正する。

### 6. 完了報告

```
## test-seed 完了

### 受入条件 → テスト対応表
| 受入条件 | テスト |
|---------|--------|
| ... | test_... |

### 生成ファイル
- tests/test_xxx.py（N件のテストスケルトン）

### 次のステップ
- tdd-cycle で Red → Green → Refactor を進める
```
