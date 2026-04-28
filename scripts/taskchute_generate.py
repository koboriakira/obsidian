#!/usr/bin/env python3
"""
taskchute_generate.py

指定した日付（デフォルト: 今日）のルーティンタスクを生成する。

使い方:
    python3 taskchute_generate.py [YYYY-MM-DD]
"""

import sys
import os
import uuid
import glob
from datetime import datetime, date, timedelta
from pathlib import Path

import yaml

VAULT = Path("/Users/koboriakira/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault")
ROUTINES_DIR = VAULT / "templates" / "routines"
DAILYNOTE_DIR = VAULT / "dailynote"

WEEKDAY_MAP = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


def parse_frontmatter(filepath: Path) -> tuple[dict, str]:
    """YAMLフロントマターと本文を分離して返す。"""
    text = filepath.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return fm, body


def last_business_day(target: date) -> date:
    """指定月の末営業日（土日を除く最終日）を返す。"""
    # 翌月1日から1日引く = 月末
    if target.month == 12:
        last_day = date(target.year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(target.year, target.month + 1, 1) - timedelta(days=1)
    # 土日なら前の平日へ
    while last_day.weekday() >= 5:
        last_day -= timedelta(days=1)
    return last_day


def nth_weekday_dates(target: date, weeks: list[int], weekday: str) -> list[date]:
    """今月の第N曜日の日付リストを返す。weekday は 'mon'〜'sun'。"""
    wd = WEEKDAY_MAP.get(weekday)
    if wd is None:
        return []
    results = []
    d = date(target.year, target.month, 1)
    count = 0
    while d.month == target.month:
        if d.weekday() == wd:
            count += 1
            if count in weeks:
                results.append(d)
        d += timedelta(days=1)
    return results


def find_last_completion(name: str) -> date | None:
    """dailynote/**/tasks/{name}.md を全検索し、最後の完了日を返す。"""
    pattern = str(DAILYNOTE_DIR / "**" / "tasks" / f"{name}.md")
    candidates = []
    for filepath in glob.glob(pattern, recursive=True):
        fp = Path(filepath)
        try:
            fm, _ = parse_frontmatter(fp)
        except Exception:
            continue
        if fm.get("status") == "done" and fm.get("scheduled_date"):
            try:
                d = date.fromisoformat(str(fm["scheduled_date"]))
                candidates.append(d)
            except ValueError:
                continue
    return max(candidates) if candidates else None


def should_generate(fm: dict, target: date) -> bool:
    """frequency条件を評価して生成すべきか判断する。"""
    frequency = fm.get("frequency", "")

    if frequency == "daily":
        return True

    elif frequency == "weekly":
        weekdays_raw = fm.get("weekdays", [])
        # YAML がリストまたは文字列で来る場合に対応
        if isinstance(weekdays_raw, str):
            weekdays_raw = [weekdays_raw]
        target_wd = target.weekday()
        return any(WEEKDAY_MAP.get(wd) == target_wd for wd in weekdays_raw)

    elif frequency == "monthly_first":
        return target.day == 1

    elif frequency == "monthly_last":
        return target == last_business_day(target)

    elif frequency == "monthly_day":
        return target.day == fm.get("day")

    elif frequency == "nth_weekday":
        weeks = fm.get("weeks", [])
        weekday = fm.get("weekday", "")
        return target in nth_weekday_dates(target, weeks, weekday)

    elif frequency in ("after_days", "after_weeks"):
        name = fm.get("name", "")
        interval = fm.get("interval", 0)
        last = find_last_completion(name)
        if last is None:
            return True
        if frequency == "after_days":
            return (target - last).days >= interval
        else:
            return (target - last).days >= interval * 7

    return False


def generate_task_file(fm: dict, body: str, target: date, task_dir: Path) -> Path:
    """タスクファイルを生成して Path を返す。"""
    name = fm.get("name", "unknown")
    # ファイル名に使えない文字を置換
    safe_name = name.replace("/", "_").replace("\\", "_")
    task_file = task_dir / f"{safe_name}.md"

    if task_file.exists():
        return task_file  # 既存の場合はスキップ

    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M")
    date_str = target.strftime("%Y-%m-%d")

    section = str(fm.get("section", ""))
    estimate = fm.get("estimate", 0)
    mode = fm.get("mode", "ルーティン")

    task_fm = {
        "uid": str(uuid.uuid4()),
        "created": now_str,
        "updated": now_str,
        "tags": [],
        "scheduled_date": date_str,
        "section": section,
        "estimate": estimate,
        "start_time": "",
        "end_time": "",
        "mode": mode,
        "status": "todo",
        "is_routine": True,
    }

    lines = ["---"]
    for k, v in task_fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: []")
        elif isinstance(v, bool):
            lines.append(f"{k}: {str(v).lower()}")
        elif v == "":
            lines.append(f'{k}: ""')
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")

    content = "\n".join(lines)
    if body.strip():
        content += "\n\n" + body.rstrip("\n") + "\n"
    else:
        content += "\n"

    task_file.write_text(content, encoding="utf-8")
    return task_file


def generate_base_file(target: date, day_dir: Path) -> Path | None:
    """taskchute_YYYYMMDD.base を生成して Path を返す（既存の場合はスキップ）。"""
    date_str = target.strftime("%Y%m%d")
    base_file = day_dir / f"taskchute_{date_str}.base"
    if base_file.exists():
        return None  # スキップ

    iso_date = target.strftime("%Y-%m-%d")
    content = f"""filters:
  and:
    - note.scheduled_date == "{iso_date}"
views:
  - type: table
    name: 今日のタスク
    order:
      - section
      - estimate
"""
    base_file.write_text(content, encoding="utf-8")
    return base_file


def main():
    if len(sys.argv) > 1:
        target = date.fromisoformat(sys.argv[1])
    else:
        target = date.today()

    print(f"対象日: {target} ({target.strftime('%A')})")

    # tasks ディレクトリ
    year = target.strftime("%Y")
    month = target.strftime("%m")
    day = target.strftime("%d")
    day_dir = DAILYNOTE_DIR / year / month / day
    task_dir = day_dir / "tasks"
    task_dir.mkdir(parents=True, exist_ok=True)

    # routines を全件読み込み
    generated = []
    skipped = []
    for routine_file in sorted(ROUTINES_DIR.glob("*.md")):
        try:
            fm, body = parse_frontmatter(routine_file)
        except Exception as e:
            print(f"  [WARN] {routine_file.name}: パース失敗 ({e})")
            continue

        name = fm.get("name", routine_file.stem)
        if should_generate(fm, target):
            task_path = generate_task_file(fm, body, target, task_dir)
            generated.append(name)
            print(f"  [生成] {name} -> {task_path.name}")
        else:
            skipped.append(name)
            print(f"  [スキップ] {name} (frequency={fm.get('frequency')})")

    # Basesファイル生成
    base_path = generate_base_file(target, day_dir)
    if base_path:
        print(f"  [生成] {base_path.name}")
    else:
        print(f"  [スキップ] taskchute_{target.strftime('%Y%m%d')}.base (既存)")

    print(f"\n完了: {len(generated)}件生成, {len(skipped)}件スキップ")
    print(f"生成されたルーティン: {', '.join(generated) if generated else 'なし'}")


if __name__ == "__main__":
    main()
