#!/usr/bin/env python3
"""
vault-search: Obsidian Vault のハイブリッド検索 CLI

使い方:
  vault-search index     # インデックスの構築・更新
  vault-search search "クエリ"  # ベクトル + キーワード検索
  vault-search status    # DB の状態を表示
"""

import hashlib
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
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50


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
    # chunk_index カラムが存在しない既存DBへのマイグレーション
    cols = [row[1] for row in conn.execute("PRAGMA table_info(vault_notes)").fetchall()]
    if cols and "chunk_index" not in cols:
        _migrate_add_chunk_index(conn)

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS vault_notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path   TEXT NOT NULL,
            chunk_index INTEGER NOT NULL DEFAULT 0,
            file_name   TEXT NOT NULL,
            type        TEXT,
            concept     TEXT,
            tags        TEXT,
            chunk_text  TEXT NOT NULL,
            file_hash   TEXT,
            embedding   BLOB,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(file_path, chunk_index)
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


def _migrate_add_chunk_index(conn: sqlite3.Connection):
    """既存DBに chunk_index カラムを追加し、UNIQUE制約を張り直す"""
    conn.executescript("""
        ALTER TABLE vault_notes ADD COLUMN chunk_index INTEGER NOT NULL DEFAULT 0;
        ALTER TABLE vault_notes ADD COLUMN file_hash TEXT;
    """)
    # 既存 UNIQUE(file_path) 制約をリネームで解消するため、テーブルを再作成
    conn.executescript("""
        CREATE TABLE vault_notes_new (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path   TEXT NOT NULL,
            chunk_index INTEGER NOT NULL DEFAULT 0,
            file_name   TEXT NOT NULL,
            type        TEXT,
            concept     TEXT,
            tags        TEXT,
            chunk_text  TEXT NOT NULL,
            file_hash   TEXT,
            embedding   BLOB,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(file_path, chunk_index)
        );
        INSERT INTO vault_notes_new
            (id, file_path, chunk_index, file_name, type, concept, tags, chunk_text, file_hash, embedding, updated_at)
        SELECT id, file_path, 0, file_name, type, concept, tags, chunk_text, file_hash, embedding, updated_at
        FROM vault_notes;
        DROP TABLE vault_notes;
        ALTER TABLE vault_notes_new RENAME TO vault_notes;
    """)
    conn.commit()


# ----- 埋め込みモデル -----

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("cl-nagoya/ruri-v3-310m")
    return _model


# ----- リランカー -----

_reranker = None


def _get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")
    return _reranker


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


def _build_meta_prefix(file_name: str, meta: dict) -> str:
    """チャンクに付与するメタデータプレフィックスを生成する"""
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

    return "\n".join(parts)


def _split_into_chunks(file_name: str, meta: dict, body: str) -> list[str]:
    """本文を複数チャンクに分割してメタプレフィックス付きのリストを返す"""
    prefix = _build_meta_prefix(file_name, meta)
    text = body.strip()

    if len(text) <= CHUNK_SIZE:
        chunk = f"{prefix}\n{text}" if text else prefix
        return [chunk]

    # 段落→改行→句点の順で再帰的に分割
    raw_chunks = _recursive_split(text, CHUNK_SIZE, ["\n\n", "\n", "。"])

    result = []
    for i, chunk in enumerate(raw_chunks):
        if i > 0 and CHUNK_OVERLAP > 0:
            # 前チャンクの末尾50文字をオーバーラップとして先頭に付与
            overlap = raw_chunks[i - 1][-CHUNK_OVERLAP:]
            chunk = overlap + chunk
        result.append(f"{prefix}\n{chunk}")

    return result


def _recursive_split(text: str, size: int, separators: list[str]) -> list[str]:
    """指定サイズを超えないようにセパレータ優先度順で再帰分割する"""
    if len(text) <= size:
        return [text]

    sep = separators[0] if separators else ""
    next_seps = separators[1:]

    if not sep:
        # 最後の手段: 強制文字数カット
        return [text[i:i + size] for i in range(0, len(text), size)]

    parts = text.split(sep)
    chunks: list[str] = []
    current = ""

    for part in parts:
        candidate = current + sep + part if current else part
        if len(candidate) <= size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # part 自体がサイズ超の場合は次のセパレータで再分割
            if len(part) > size and next_seps:
                chunks.extend(_recursive_split(part, size, next_seps))
                current = ""
            else:
                current = part

    if current:
        chunks.append(current)

    return chunks if chunks else [text]


def _file_hash(content: str) -> str:
    return hashlib.md5(content.encode("utf-8")).hexdigest()


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
    vault_paths: set[str] = set()

    for rel_path, abs_path in files:
        vault_paths.add(rel_path)
        try:
            content = Path(abs_path).read_text(encoding="utf-8")
        except Exception as e:
            click.echo(f"  読み取りエラー: {rel_path}: {e}", err=True)
            errors += 1
            continue

        content_hash = _file_hash(content)

        # ファイルハッシュで変更チェック（いずれかのチャンクで確認）
        existing_hash = conn.execute(
            "SELECT file_hash FROM vault_notes WHERE file_path = ? AND chunk_index = 0",
            (rel_path,),
        ).fetchone()

        if existing_hash and existing_hash[0] == content_hash:
            continue

        meta, body = _parse_frontmatter(content)
        file_name = Path(rel_path).stem
        chunks = _split_into_chunks(file_name, meta, body)

        tags_json = json.dumps(meta.get("tags", []), ensure_ascii=False) if meta.get("tags") else None
        note_type = meta.get("type")
        concept = meta.get("concept")

        # 既存チャンクを全削除してから再挿入
        existing_ids = conn.execute(
            "SELECT id FROM vault_notes WHERE file_path = ?",
            (rel_path,),
        ).fetchall()
        for (eid,) in existing_ids:
            try:
                conn.execute("DELETE FROM vec_vault_notes WHERE rowid = ?", (eid,))
            except Exception:
                pass
        conn.execute("DELETE FROM vault_notes WHERE file_path = ?", (rel_path,))

        for chunk_index, chunk_text in enumerate(chunks):
            try:
                embedding = _get_embedding(chunk_text)
            except Exception as e:
                click.echo(f"  埋め込みエラー: {rel_path}[{chunk_index}]: {e}", err=True)
                embedding = None

            cursor = conn.execute(
                """INSERT INTO vault_notes (file_path, chunk_index, file_name, type, concept, tags, chunk_text, file_hash, embedding)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (rel_path, chunk_index, file_name, note_type, concept, tags_json, chunk_text, content_hash, embedding),
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
    db_paths = conn.execute("SELECT DISTINCT file_path FROM vault_notes").fetchall()
    deleted = 0
    for (db_path,) in db_paths:
        if db_path not in vault_paths:
            rows = conn.execute("SELECT id FROM vault_notes WHERE file_path = ?", (db_path,)).fetchall()
            for (rid,) in rows:
                try:
                    conn.execute("DELETE FROM vec_vault_notes WHERE rowid = ?", (rid,))
                except Exception:
                    pass
            conn.execute("DELETE FROM vault_notes WHERE file_path = ?", (db_path,))
            deleted += 1

    conn.commit()
    conn.close()

    click.echo(f"\nインデックス完了: {indexed} 件更新/追加, {deleted} 件削除, {errors} 件エラー")


@cli.command()
@click.argument("query")
@click.option("--limit", default=5, help="表示する結果数")
@click.option("--no-rerank", "no_rerank", is_flag=True, help="リランクをスキップ")
def search(query: str, limit: int, no_rerank: bool):
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

    # RRF 上位20件を取得
    top20_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)[:20]

    rows_info = conn.execute(
        f"SELECT id, file_path, file_name, type, concept, tags, chunk_text FROM vault_notes WHERE id IN ({','.join('?' * len(top20_ids))})",
        top20_ids,
    ).fetchall()
    info_map = {r[0]: r for r in rows_info}

    # リランク処理
    if not no_rerank:
        try:
            reranker = _get_reranker()
            pairs = [(query, info_map[row_id][6]) for row_id in top20_ids if row_id in info_map]
            valid_ids = [row_id for row_id in top20_ids if row_id in info_map]
            rerank_scores = reranker.predict(pairs)
            scored_ids = sorted(zip(valid_ids, rerank_scores), key=lambda x: x[1], reverse=True)
            final_order = [(float(score), info_map[row_id]) for row_id, score in scored_ids]
        except Exception as e:
            click.echo(f"リランクをスキップ（エラー: {e}）", err=True)
            no_rerank = True

    if no_rerank:
        final_order = [(rrf_scores[row_id], info_map[row_id]) for row_id in top20_ids if row_id in info_map]

    # チャンク単位スコアを file_path でデデュプ（最高スコアのチャンクで代表）
    best_by_path: dict[str, tuple[float, tuple]] = {}
    for score, r in final_order:
        file_path = r[1]
        if file_path not in best_by_path or score > best_by_path[file_path][0]:
            best_by_path[file_path] = (score, r)

    final_scores = sorted(best_by_path.values(), key=lambda x: x[0], reverse=True)

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

    total_chunks = conn.execute("SELECT COUNT(*) FROM vault_notes").fetchone()[0]
    total_notes = conn.execute("SELECT COUNT(DISTINCT file_path) FROM vault_notes").fetchone()[0]
    with_embedding = conn.execute("SELECT COUNT(*) FROM vault_notes WHERE embedding IS NOT NULL").fetchone()[0]
    types = conn.execute(
        "SELECT type, COUNT(DISTINCT file_path) FROM vault_notes GROUP BY type ORDER BY COUNT(DISTINCT file_path) DESC"
    ).fetchall()
    oldest = conn.execute("SELECT MIN(updated_at) FROM vault_notes").fetchone()[0]
    newest = conn.execute("SELECT MAX(updated_at) FROM vault_notes").fetchone()[0]

    conn.close()

    click.echo(f"\n## vault-search ステータス\n")
    click.echo(f"- DB パス: {DB_PATH}")
    click.echo(f"- Vault パス: {VAULT_PATH}")
    click.echo(f"- 総ノート数: {total_notes}")
    click.echo(f"- 総チャンク数: {total_chunks}")
    click.echo(f"- 埋め込み済み: {with_embedding}")
    click.echo(f"- 最古の更新: {oldest or 'なし'}")
    click.echo(f"- 最新の更新: {newest or 'なし'}")
    click.echo(f"\n### type 別ノート数")
    for note_type, count in types:
        click.echo(f"  - {note_type or '(未設定)'}: {count}")


if __name__ == "__main__":
    cli()
