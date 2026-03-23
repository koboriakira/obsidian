#!/usr/bin/env python3
"""
タスクボードの古い完了タスクを月別アーカイブファイルへ移動するスクリプト。

完了から THRESHOLD_DAYS 日以上経過した [x] タスクを
Claude/task-board-archive/YYYY-MM.md へ移動する。

使用例:
  # 1週間以上前の完了タスクをアーカイブ（デフォルト）
  python3 archive_old_tasks.py

  # 30日以上前をアーカイブ
  python3 archive_old_tasks.py --days 30

  # 確認のみ（変更なし）
  python3 archive_old_tasks.py --dry-run
"""

import argparse
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

VAULT = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault"
TASK_BOARD = VAULT / "Claude/task-board.md"
ARCHIVE_DIR = VAULT / "Claude/task-board-archive"
THRESHOLD_DAYS = 7

DONE_DATE_RE = re.compile(r"✅\s*(\d{4}-\d{2}-\d{2})")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=THRESHOLD_DAYS,
                        help=f"アーカイブ対象の日数（デフォルト: {THRESHOLD_DAYS}日）")
    parser.add_argument("--dry-run", action="store_true",
                        help="変更せずに対象タスクを確認する")
    return parser.parse_args()


def get_done_date(line: str) -> date | None:
    """タスク行から ✅ YYYY-MM-DD を抽出する。"""
    m = DONE_DATE_RE.search(line)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            return None
    return None


def load_task_board() -> list[str]:
    return TASK_BOARD.read_text(encoding="utf-8").splitlines()


def split_sections(lines: list[str]) -> dict[str, list[str]]:
    """ファイルをセクションごとに分割する。順序を保持するため OrderedDict 相当のリストも返す。"""
    order = []
    sections: dict[str, list[str]] = {}
    current = "__header__"
    order.append(current)
    sections[current] = []

    for line in lines:
        if line.startswith("## "):
            current = line
            if current not in sections:
                order.append(current)
                sections[current] = []
        else:
            sections[current].append(line)

    return order, sections


def rebuild_lines(order: list[str], sections: dict[str, list[str]]) -> list[str]:
    out = []
    for key in order:
        if key == "__header__":
            out.extend(sections[key])
        else:
            out.append(key)
            out.extend(sections[key])
    return out


def archive_path(done_date: date) -> Path:
    return ARCHIVE_DIR / f"{done_date.strftime('%Y-%m')}.md"


def append_to_archive(path: Path, tasks: list[tuple[date, str]]):
    """月別アーカイブファイルにタスクを追記する。"""
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        header = f"---\ntype: task-archive\nmonth: {path.stem}\n---\n\n# タスクアーカイブ {path.stem}\n\n"
        path.write_text(header, encoding="utf-8")

    existing = path.read_text(encoding="utf-8")
    new_lines = [t for _, t in sorted(tasks, key=lambda x: x[0])]
    path.write_text(existing + "\n".join(new_lines) + "\n", encoding="utf-8")


def main():
    args = parse_args()
    threshold = date.today() - timedelta(days=args.days)

    lines = load_task_board()
    order, sections = split_sections(lines)

    done_section = "## ✅ Done"
    if done_section not in sections:
        print("✅ Done セクションが見つかりません。")
        return

    done_lines = sections[done_section]

    # アーカイブ対象と残留を分離
    # tasks クエリブロックは触らない
    to_archive: list[tuple[date, str]] = []   # (done_date, line)
    remaining: list[str] = []
    in_query = False

    for line in done_lines:
        stripped = line.strip()

        # クエリブロック内はそのまま残す
        if stripped.startswith("```tasks"):
            in_query = True
            remaining.append(line)
            continue
        if in_query:
            remaining.append(line)
            if stripped == "```":
                in_query = False
            continue

        # [x] タスクでアーカイブ条件を判定
        if re.match(r"^- \[x\]", line):
            done_date = get_done_date(line)
            if done_date and done_date < threshold:
                to_archive.append((done_date, line))
                continue

        remaining.append(line)

    # 末尾の連続空行を整理
    while remaining and remaining[-1].strip() == "":
        remaining.pop()

    if not to_archive:
        print(f"アーカイブ対象タスクはありません（閾値: {threshold} より前に完了）。")
        return

    # 月別に分類
    by_month: dict[str, list[tuple[date, str]]] = defaultdict(list)
    for d, line in to_archive:
        by_month[d.strftime("%Y-%m")].append((d, line))

    mode = "[ドライラン]" if args.dry_run else "[実行]"
    print(f"{mode} アーカイブ対象: {len(to_archive)} 件（閾値: {threshold} より前）\n")
    for month, tasks in sorted(by_month.items()):
        print(f"  → {ARCHIVE_DIR.relative_to(VAULT)}/{month}.md : {len(tasks)} 件")
        for _, line in tasks:
            print(f"    {line[:90]}")

    if args.dry_run:
        return

    # アーカイブファイルへ書き込み
    for month, tasks in by_month.items():
        path = ARCHIVE_DIR / f"{month}.md"
        append_to_archive(path, tasks)
        print(f"\n書き込み: {path.relative_to(VAULT)}")

    # task-board.md を更新
    sections[done_section] = remaining
    new_lines = rebuild_lines(order, sections)
    TASK_BOARD.write_text("\n".join(new_lines), encoding="utf-8")

    print(f"\ntask-board.md から {len(to_archive)} 件を削除しました。")


if __name__ == "__main__":
    main()
