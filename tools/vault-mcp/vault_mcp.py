#!/usr/bin/env python3
"""vault-mcp: Claude Desktop 用の Obsidian Vault MCP サーバ

指定した Vault 配下のファイルを読み取り・新規作成する最小機能を提供する。

環境変数:
  OBSIDIAN_VAULT_PATH  Vault のルートディレクトリ（未指定時は iCloud パスを使用）
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP


DEFAULT_VAULT_PATH = (
    Path.home()
    / "Library"
    / "Mobile Documents"
    / "iCloud~md~obsidian"
    / "Documents"
    / "my-vault"
)


def _vault_root() -> Path:
    raw = os.environ.get("OBSIDIAN_VAULT_PATH")
    root = Path(raw).expanduser() if raw else DEFAULT_VAULT_PATH
    return root.resolve()


def _resolve_in_vault(rel_path: str) -> Path:
    """Vault ルートからの相対パスを解決し、Vault 配下にあることを保証する。"""
    if not rel_path or rel_path.strip() == "":
        raise ValueError("path が空です")

    root = _vault_root()
    candidate = (root / rel_path).resolve()

    try:
        candidate.relative_to(root)
    except ValueError as e:
        raise ValueError(
            f"path が Vault の外を指しています: {rel_path} (vault={root})"
        ) from e

    return candidate


mcp = FastMCP("obsidian-vault")


@mcp.tool()
def get_vault_info() -> dict:
    """Vault のルートパスを返す。"""
    root = _vault_root()
    return {
        "vault_path": str(root),
        "exists": root.exists(),
    }


@mcp.tool()
def read_note(path: str) -> str:
    """Vault 内のファイルを読み取って中身を返す。

    Args:
        path: Vault ルートからの相対パス（例: "Inbox/memo.md"）
    """
    target = _resolve_in_vault(path)
    if not target.exists():
        raise FileNotFoundError(f"ファイルが存在しません: {path}")
    if not target.is_file():
        raise IsADirectoryError(f"ファイルではありません: {path}")
    return target.read_text(encoding="utf-8")


@mcp.tool()
def create_note(path: str, content: str, overwrite: bool = False) -> str:
    """Vault 内に新規ファイルを作成する。親ディレクトリは自動作成する。

    Args:
        path: Vault ルートからの相対パス（例: "Inbox/new-note.md"）
        content: 書き込む本文
        overwrite: True なら既存ファイルを上書きする（デフォルト False）

    Returns:
        作成したファイルの絶対パス
    """
    target = _resolve_in_vault(path)
    if target.exists() and not overwrite:
        raise FileExistsError(
            f"既にファイルが存在します（overwrite=true で上書き可）: {path}"
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return str(target)


def main() -> None:
    root = _vault_root()
    if not root.exists():
        print(
            f"[vault-mcp] 警告: Vault パスが存在しません: {root}",
            file=sys.stderr,
        )
    mcp.run()


if __name__ == "__main__":
    main()
