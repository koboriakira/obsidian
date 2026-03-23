#!/usr/bin/env python3
"""
Obsidian Vault のタグ一覧を生成するスクリプト。
全ノートのフロントマターから tags を収集し、
件数付きの一覧を Vault 直下に _tag_index.md として出力する。
"""

import os
import re
from collections import Counter
from pathlib import Path

VAULT = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault"
OUTPUT = VAULT / "_tag_index.md"

# 除外ディレクトリ（Obsidian の内部フォルダ）
EXCLUDE_DIRS = {".obsidian", ".trash"}


def parse_frontmatter_tags(content: str) -> list[str]:
    """マークダウンファイルのフロントマターから tags を抽出する。"""
    # フロントマターを抽出
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return []

    fm = match.group(1)

    # tags: [a, b, c] 形式
    inline = re.search(r"^tags:\s*\[([^\]]+)\]", fm, re.MULTILINE)
    if inline:
        return [t.strip().strip('"').strip("'") for t in inline.group(1).split(",")]

    # tags:\n  - a\n  - b 形式
    block = re.search(r"^tags:\s*\n((?:\s+- .+\n?)+)", fm, re.MULTILINE)
    if block:
        return [re.sub(r"^\s*-\s*", "", line).strip() for line in block.group(1).splitlines() if line.strip()]

    # tags: single_value 形式
    single = re.search(r"^tags:\s+(\S+)", fm, re.MULTILINE)
    if single:
        return [single.group(1).strip()]

    return []


def collect_tags() -> Counter:
    counter = Counter()
    for path in VAULT.rglob("*.md"):
        # 除外ディレクトリをスキップ
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        # 出力ファイル自体をスキップ
        if path == OUTPUT:
            continue
        try:
            content = path.read_text(encoding="utf-8")
            tags = parse_frontmatter_tags(content)
            counter.update(tags)
        except Exception:
            pass
    return counter


def generate_markdown(counter: Counter) -> str:
    lines = [
        "---",
        "type: tag_index",
        "---",
        "",
        "# タグ一覧",
        "",
        f"全 {sum(counter.values())} タグ使用 / {len(counter)} 種類",
        "",
        "| タグ | 件数 |",
        "|-----|------|",
    ]

    for tag, count in sorted(counter.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| #{tag} | {count} |")

    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print("タグを収集中...")
    counter = collect_tags()
    print(f"{len(counter)} 種類のタグを発見")

    md = generate_markdown(counter)
    OUTPUT.write_text(md, encoding="utf-8")
    print(f"出力: {OUTPUT}")
