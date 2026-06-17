#!/usr/bin/env python3
"""
vault-search: Obsidian Vault のハイブリッド検索 CLI

使い方:
  vault-search index     # インデックスの構築・更新
  vault-search search "クエリ"  # ベクトル + キーワード検索
  vault-search status    # DB の状態を表示
"""

import os
import re
import json
import sqlite3
import datetime
from pathlib import Path

import click
import yaml
import numpy as np

# ----- 定数 -----

VAULT_PATH = Path.home() / "obsidian" / "my-vault"
DB_DIR = Path.home() / ".local" / "share" / "vault-search"
DB_PATH = DB_DIR / "vault.db"
TARGET_DIRS = ["Wiki", "Areas", "Projects", "Inbox", "Raws"]
CHUNK_BODY_LIMIT = 300


# ----- DB 初期化 -----

def _get_conn() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))

    try:
        import sqlite_vec
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
    except Exception:
        pass

    conn.execute("PRAGMA journal_mode=WAL")
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS vault_notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path   TEXT NOT NULL UNIQUE,
            file_name   TEXT NOT NULL,
            type        TEXT,
            concept     TEXT,
            tags        TEXT,
            chunk_text  TEXT NOT NULL,
            embedding   BLOB,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS vault_notes_fts USING fts5(
            chunk_text,
            content=vault_notes,
            content_rowid=id,
            tokenize='trigram'
        );

        CREATE TRIGGER IF NOT EXISTS vault_notes_ai
        AFTER INSERT ON vault_notes BEGIN
            INSERT INTO vault_notes_fts(rowid, chunk_text)
            VALUES (new.id, new.chunk_text);
        END;

        CREATE TRIGGER IF NOT EXISTS vault_notes_ad
        AFTER DELETE ON vault_notes BEGIN
            INSERT INTO vault_notes_fts(vault_notes_fts, rowid, chunk_text)
            VALUES ('delete', old.id, old.chunk_text);
        END;

        CREATE TRIGGER IF NOT EXISTS vault_notes_au
        AFTER UPDATE ON vault_notes BEGIN
            INSERT INTO vault_notes_fts(vault_notes_fts, rowid, chunk_text)
            VALUES ('delete', old.id, old.chunk_text);
            INSERT INTO vault_notes_fts(rowid, chunk_text)
            VALUES (new.id, new.chunk_text);
        END;
    """)

    try:
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS vec_vault_notes USING vec0(
                embedding float[384]
            )
        """)
    except Exception:
        pass

    conn.commit()


# ----- 埋め込みモデル -----

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("cl-nagoya/ruri-v3-310m")
    return _model


def _get_embedding(text: str) -> bytes:
    model = _get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.astype(np.float32).tobytes()


def _cosine_similarity(a: bytes, b: bytes) -> float:
    arr_a = np.frombuffer(a, dtype=np.float32)
    arr_b = np.frombuffer(b, dtype=np.float32)
    dot = float(np.dot(arr_a, arr_b))
    norm_a = float(np.linalg.norm(arr_a))
    norm_b = float(np.linalg.norm(arr_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ----- フロントマター解析 -----

_FM_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """フロントマターを解析して (metadata, body) を返す"""
    m = _FM_PATTERN.match(content)
    if not m:
        return {}, content

    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        meta = {}

    body = content[m.end():]
    return meta, body


def _build_chunk_text(file_name: str, meta: dict, body: str) -> str:
    """検索用チャンクテキストを構築する"""
    parts = [file_name]

    for key in ("type", "concept", "purpose"):
        val = meta.get(key)
        if val:
            parts.append(f"{key}: {val}")

    tags = meta.get("tags")
    if tags:
        if isinstance(tags, list):
            parts.append("tags: " + ", ".join(str(t) for t in tags))
        else:
            parts.append(f"tags: {tags}")

    sources = meta.get("sources")
    if sources:
        if isinstance(sources, list):
            parts.append("sources: " + ", ".join(str(s) for s in sources))
        else:
            parts.append(f"sources: {sources}")

    body_trimmed = body.strip()[:CHUNK_BODY_LIMIT]
    if body_trimmed:
        parts.append(body_trimmed)

    return "\n".join(parts)


# ----- Vault 走査 -----

def _scan_vault() -> list[tuple[str, str]]:
    """Vault 内の対象ディレクトリから .md ファイルを走査し、(相対パス, 絶対パス) のリストを返す"""
    results = []
    for dir_name in TARGET_DIRS:
        target = VAULT_PATH / dir_name
        if not target.exists():
            continue
        for md_file in target.rglob("*.md"):
            rel_path = str(md_file.relative_to(VAULT_PATH))
            results.append((rel_path, str(md_file)))
    return results


# ----- Click コマンド -----

@click.group()
def cli():
    """Obsidian Vault ハイブリッド検索ツール"""
    pass


@cli.command()
def index():
    """Vault 全体を走査してインデックスを構築・更新する"""
    conn = _get_conn()

    files = _scan_vault()
    click.echo(f"対象ファイル数: {len(files)}")

    indexed = 0
    errors = 0
    vault_paths = set()

    for rel_path, abs_path in files:
        vault_paths.add(rel_path)
        try:
            content = Path(abs_path).read_text(encoding="utf-8")
        except Exception as e:
            click.echo(f"  読み取りエラー: {rel_path}: {e}", err=True)
            errors += 1
            continue

        meta, body = _parse_frontmatter(content)
        file_name = Path(rel_path).stem
        chunk_text = _build_chunk_text(file_name, meta, body)

        tags_json = json.dumps(meta.get("tags", []), ensure_ascii=False) if meta.get("tags") else None
        note_type = meta.get("type")
        concept = meta.get("concept")

        # 既存エントリの確認
        existing = conn.execute(
            "SELECT id, chunk_text FROM vault_notes WHERE file_path = ?",
            (rel_path,),
        ).fetchone()

        if existing and existing[1] == chunk_text:
            # 変更なし
            continue

        try:
            embedding = _get_embedding(chunk_text)
        except Exception as e:
            click.echo(f"  埋め込みエラー: {rel_path}: {e}", err=True)
            embedding = None

        if existing:
            # 更新
            row_id = existing[0]
            conn.execute(
                """UPDATE vault_notes
                   SET file_name=?, type=?, concept=?, tags=?, chunk_text=?, embedding=?, updated_at=CURRENT_TIMESTAMP
                   WHERE id=?""",
                (file_name, note_type, concept, tags_json, chunk_text, embedding, row_id),
            )
            if embedding is not None:
                try:
                    conn.execute("DELETE FROM vec_vault_notes WHERE rowid = ?", (row_id,))
                    conn.execute(
                        "INSERT INTO vec_vault_notes(rowid, embedding) VALUES (?, ?)",
                        (row_id, embedding),
                    )
                except Exception:
                    pass
        else:
            # 新規挿入
            cursor = conn.execute(
                """INSERT INTO vault_notes (file_path, file_name, type, concept, tags, chunk_text, embedding)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (rel_path, file_name, note_type, concept, tags_json, chunk_text, embedding),
            )
            row_id = cursor.lastrowid
            if embedding is not None:
                try:
                    conn.execute(
                        "INSERT INTO vec_vault_notes(rowid, embedding) VALUES (?, ?)",
                        (row_id, embedding),
                    )
                except Exception:
                    pass

        indexed += 1
        if indexed % 100 == 0:
            click.echo(f"  {indexed} 件処理済み...")
            conn.commit()

    conn.commit()

    # DB に存在するが Vault から消えたファイルを削除
    db_paths = conn.execute("SELECT file_path FROM vault_notes").fetchall()
    deleted = 0
    for (db_path,) in db_paths:
        if db_path not in vault_paths:
            row = conn.execute("SELECT id FROM vault_notes WHERE file_path = ?", (db_path,)).fetchone()
            if row:
                try:
                    conn.execute("DELETE FROM vec_vault_notes WHERE rowid = ?", (row[0],))
                except Exception:
                    pass
                conn.execute("DELETE FROM vault_notes WHERE id = ?", (row[0],))
                deleted += 1

    conn.commit()
    conn.close()

    click.echo(f"\nインデックス完了: {indexed} 件更新/追加, {deleted} 件削除, {errors} 件エラー")


@cli.command()
@click.argument("query")
@click.option("--limit", default=5, help="表示する結果数")
def search(query: str, limit: int):
    """クエリテキストでハイブリッド検索する"""
    conn = _get_conn()

    # --- FTS5 キーワード検索 ---
    fts_results: dict[int, int] = {}
    try:
        rows = conn.execute(
            """
            SELECT n.id
            FROM vault_notes n
            JOIN vault_notes_fts fts ON n.id = fts.rowid
            WHERE vault_notes_fts MATCH ?
            ORDER BY rank
            LIMIT 20
            """,
            (query,),
        ).fetchall()
        for rank, row in enumerate(rows, 1):
            fts_results[row[0]] = rank
    except Exception as e:
        click.echo(f"FTS検索エラー: {e}", err=True)

    # --- ベクトル類似検索 ---
    vec_results: dict[int, int] = {}
    try:
        query_embedding = _get_embedding(query)
        try:
            rows = conn.execute(
                """
                SELECT v.rowid, v.distance
                FROM vec_vault_notes v
                WHERE v.embedding MATCH ?
                ORDER BY v.distance
                LIMIT 20
                """,
                (query_embedding,),
            ).fetchall()
            for rank, row in enumerate(rows, 1):
                vec_results[row[0]] = rank
        except Exception:
            # vec0 が使えない場合はフォールバック
            all_rows = conn.execute(
                "SELECT id, embedding FROM vault_notes WHERE embedding IS NOT NULL",
            ).fetchall()
            scored = []
            for row in all_rows:
                sim = _cosine_similarity(query_embedding, row[1])
                scored.append((row[0], sim))
            scored.sort(key=lambda x: x[1], reverse=True)
            for rank, item in enumerate(scored[:20], 1):
                vec_results[item[0]] = rank
    except Exception as e:
        click.echo(f"ベクトル検索エラー: {e}", err=True)

    # --- RRF スコア計算 ---
    k = 60
    all_ids = set(fts_results) | set(vec_results)
    rrf_scores: dict[int, float] = {}
    for row_id in all_ids:
        score = 0.0
        if row_id in fts_results:
            score += 1.0 / (k + fts_results[row_id])
        if row_id in vec_results:
            score += 1.0 / (k + vec_results[row_id])
        rrf_scores[row_id] = score

    if not rrf_scores:
        click.echo("検索結果が見つかりませんでした")
        conn.close()
        return

    # 結果を取得
    rows_info = conn.execute(
        f"SELECT id, file_path, file_name, type, concept, tags, chunk_text FROM vault_notes WHERE id IN ({','.join('?' * len(rrf_scores))})",
        list(rrf_scores.keys()),
    ).fetchall()
    info_map = {r[0]: r for r in rows_info}

    final_scores: list[tuple[float, tuple]] = []
    for row_id, score in rrf_scores.items():
        if row_id in info_map:
            final_scores.append((score, info_map[row_id]))

    final_scores.sort(key=lambda x: x[0], reverse=True)

    click.echo(f"\n## 「{query}」の検索結果（上位 {min(limit, len(final_scores))} 件）\n")

    for i, (score, r) in enumerate(final_scores[:limit], 1):
        row_id, file_path, file_name, note_type, concept, tags, chunk_text = r
        click.echo(f"### {i}. {file_path}  (score: {score:.4f})")
        if note_type:
            click.echo(f"  type: {note_type}")
        if concept:
            click.echo(f"  concept: {concept}")
        if tags:
            click.echo(f"  tags: {tags}")
        preview = chunk_text.replace("\n", " ")[:100]
        click.echo(f"  {preview}...")
        click.echo("")

    conn.close()


@cli.command()
def status():
    """インデックスの状態を表示する"""
    if not DB_PATH.exists():
        click.echo(f"DB が存在しません: {DB_PATH}")
        return

    conn = _get_conn()

    total = conn.execute("SELECT COUNT(*) FROM vault_notes").fetchone()[0]
    with_embedding = conn.execute("SELECT COUNT(*) FROM vault_notes WHERE embedding IS NOT NULL").fetchone()[0]
    types = conn.execute(
        "SELECT type, COUNT(*) FROM vault_notes GROUP BY type ORDER BY COUNT(*) DESC"
    ).fetchall()
    oldest = conn.execute("SELECT MIN(updated_at) FROM vault_notes").fetchone()[0]
    newest = conn.execute("SELECT MAX(updated_at) FROM vault_notes").fetchone()[0]

    conn.close()

    click.echo(f"\n## vault-search ステータス\n")
    click.echo(f"- DB パス: {DB_PATH}")
    click.echo(f"- Vault パス: {VAULT_PATH}")
    click.echo(f"- 総ノート数: {total}")
    click.echo(f"- 埋め込み済み: {with_embedding}")
    click.echo(f"- 最古の更新: {oldest or 'なし'}")
    click.echo(f"- 最新の更新: {newest or 'なし'}")
    click.echo(f"\n### type 別ノート数")
    for note_type, count in types:
        click.echo(f"  - {note_type or '(未設定)'}: {count}")


if __name__ == "__main__":
    cli()
