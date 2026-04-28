#!/usr/bin/env python3
"""
taskchute_plan.py

指定した日付（デフォルト: 今日）のTaskChute計画フェーズ用データを収集する。

使い方:
    python3 taskchute_plan.py [YYYY-MM-DD]

出力:
    JSON形式で stdout に出力する。
    {
      "date": "2026-04-29",
      "already_scheduled": [...],   # 当日スケジュール済みタスク
      "unscheduled_candidates": [...] # 未スケジュールのプロジェクトタスク候補
    }
"""

import sys
import json
import glob
from datetime import date
from pathlib import Path

import yaml

VAULT = Path("/Users/koboriakira/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault")
PROJECTS_DIR = VAULT / "Projects"
AREAS_DIR = VAULT / "Areas"
DAILYNOTE_DIR = VAULT / "dailynote"


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


def collect_already_scheduled(target: date) -> list[dict]:
    """指定日のdailynote/tasks/から当日スケジュール済みタスクを収集する。"""
    year = target.strftime("%Y")
    month = target.strftime("%m")
    day = target.strftime("%d")
    task_dir = DAILYNOTE_DIR / year / month / day / "tasks"

    results = []
    if not task_dir.exists():
        return results

    for task_file in sorted(task_dir.glob("*.md")):
        try:
            fm, _ = parse_frontmatter(task_file)
        except Exception:
            continue

        status = fm.get("status", "")
        if status in ("done", "cancelled"):
            continue

        results.append({
            "name": task_file.stem,
            "section": str(fm.get("section", "")),
            "estimate": fm.get("estimate", 0),
            "mode": fm.get("mode", ""),
            "status": status,
            "is_routine": bool(fm.get("is_routine", False)),
            "file": str(task_file),
        })

    return results


def collect_unscheduled_candidates(target: date) -> list[dict]:
    """Projects/*/tasks/*.md と Areas/*/tasks/*.md を全件スキャンして未スケジュール or 指定日のタスクを収集する。"""
    target_str = target.isoformat()
    results = []

    patterns = [
        (str(PROJECTS_DIR / "*" / "tasks" / "*.md"), "project"),
        (str(AREAS_DIR / "*" / "tasks" / "*.md"), "area"),
    ]

    for pattern, source_type in patterns:
        for filepath_str in sorted(glob.glob(pattern)):
            task_file = Path(filepath_str)
            try:
                fm, _ = parse_frontmatter(task_file)
            except Exception:
                continue

            status = fm.get("status", "")
            if status in ("done", "cancelled"):
                continue

            scheduled_date = str(fm.get("scheduled_date", "")).strip()
            # scheduled_date が空または指定日のものを対象にする
            if scheduled_date and scheduled_date != target_str:
                continue

            # プロジェクト/エリア名はtasks/の親ディレクトリ
            parent_name = task_file.parent.parent.name

            results.append({
                "name": task_file.stem,
                "project": parent_name,
                "source_type": source_type,
                "scheduled_date": scheduled_date,
                "due": str(fm.get("due", "")).strip(),
                "section": str(fm.get("section", "")),
                "estimate": fm.get("estimate", 0),
                "status": status,
                "file": str(task_file),
            })

    return results


def main():
    if len(sys.argv) > 1:
        target = date.fromisoformat(sys.argv[1])
    else:
        target = date.today()

    already_scheduled = collect_already_scheduled(target)
    unscheduled_candidates = collect_unscheduled_candidates(target)

    output = {
        "date": target.isoformat(),
        "already_scheduled": already_scheduled,
        "unscheduled_candidates": unscheduled_candidates,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
