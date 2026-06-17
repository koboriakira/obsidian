#!/usr/bin/env python3
"""
Obsidian Vault のフロントマタータグを一括変更するスクリプト。

使用例:
  # タグを統合（old_tag → new_tag）
  python3 apply_tag_changes.py --merge "ai-session:ai" --merge "ai-agent:ai"

  # タグを削除
  python3 apply_tag_changes.py --delete "3WAYマッチ" --delete "tmp"

  # 複合
  python3 apply_tag_changes.py --merge "memo:note" --delete "old-tag"

  # ドライラン（変更せず影響ファイルを確認）
  python3 apply_tag_changes.py --merge "memo:note" --dry-run
"""

import argparse
import re
from pathlib import Path

VAULT = Path.home() / "obsidian/my-vault"
EXCLUDE_DIRS = {".obsidian", ".trash"}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--merge", action="append", default=[], metavar="OLD:NEW",
                        help="タグを統合する (例: --merge old_tag:new_tag)")
    parser.add_argument("--delete", action="append", default=[], metavar="TAG",
                        help="タグを削除する (例: --delete old_tag)")
    parser.add_argument("--dry-run", action="store_true",
                        help="変更せずに影響ファイルを確認する")
    return parser.parse_args()


def build_rules(merge_args, delete_args):
    """変換ルール辞書を作成: {old_tag: new_tag_or_None}"""
    rules = {}
    for m in merge_args:
        old, new = m.split(":", 1)
        rules[old.strip()] = new.strip()
    for d in delete_args:
        rules[d.strip()] = None
    return rules


def apply_rules_to_tags(tags: list[str], rules: dict) -> tuple[list[str], bool]:
    """タグリストにルールを適用。変更があれば True を返す。"""
    new_tags = []
    changed = False
    for tag in tags:
        if tag in rules:
            new_val = rules[tag]
            changed = True
            if new_val is not None and new_val not in new_tags:
                new_tags.append(new_val)
        else:
            if tag not in new_tags:
                new_tags.append(tag)
    return new_tags, changed


def replace_frontmatter_tags(content: str, rules: dict) -> tuple[str, bool]:
    """フロントマター内の tags を書き換える。変更があれば True を返す。"""
    match = re.match(r"^(---\s*\n)(.*?)(\n---)", content, re.DOTALL)
    if not match:
        return content, False

    prefix, fm, suffix = match.group(1), match.group(2), match.group(3)
    rest = content[match.end():]

    # tags: [a, b, c] 形式
    inline = re.search(r"^(tags:\s*\[)([^\]]+)(\])", fm, re.MULTILINE)
    if inline:
        raw_tags = [t.strip().strip('"').strip("'") for t in inline.group(2).split(",")]
        new_tags, changed = apply_rules_to_tags(raw_tags, rules)
        if not changed:
            return content, False
        new_inline = inline.group(1) + ", ".join(new_tags) + inline.group(3)
        new_fm = fm[:inline.start()] + new_inline + fm[inline.end():]
        return prefix + new_fm + suffix + rest, True

    # tags:\n  - a\n  - b 形式
    block = re.search(r"^(tags:\s*\n)((?:\s+- .+\n?)+)", fm, re.MULTILINE)
    if block:
        raw_tags = [re.sub(r"^\s*-\s*", "", line).strip()
                    for line in block.group(2).splitlines() if line.strip()]
        new_tags, changed = apply_rules_to_tags(raw_tags, rules)
        if not changed:
            return content, False
        new_block_body = "".join(f"  - {t}\n" for t in new_tags)
        new_fm = fm[:block.start(2)] + new_block_body + fm[block.end(2):]
        return prefix + new_fm + suffix + rest, True

    return content, False


def main():
    args = parse_args()
    rules = build_rules(args.merge, args.delete)

    if not rules:
        print("変更ルールが指定されていません。--merge または --delete を指定してください。")
        return

    print("適用ルール:")
    for old, new in rules.items():
        action = f"→ #{new}" if new else "削除"
        print(f"  #{old} {action}")
    print()

    changed_files = []
    for path in VAULT.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
            new_content, changed = replace_frontmatter_tags(content, rules)
            if changed:
                changed_files.append(path)
                if not args.dry_run:
                    path.write_text(new_content, encoding="utf-8")
        except Exception as e:
            print(f"エラー: {path}: {e}")

    mode = "[ドライラン]" if args.dry_run else "[適用済み]"
    print(f"{mode} 変更ファイル数: {len(changed_files)}")
    for f in changed_files:
        print(f"  {f.relative_to(VAULT)}")


if __name__ == "__main__":
    main()
