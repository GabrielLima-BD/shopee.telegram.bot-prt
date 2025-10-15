import os
import sqlite3
from contextlib import contextmanager
from typing import Optional, Tuple, Iterable, Any
from .config import settings

DB_SINGLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_type TEXT,
  source_url TEXT,
  telegram_file_id TEXT,
  original_path TEXT,
  processed_path TEXT,
  status TEXT,
  retries INTEGER DEFAULT 0,
  error_message TEXT,
  width INTEGER,
  height INTEGER,
  duration_seconds REAL,
  size_bytes INTEGER,
  link_produto TEXT,
  descricao TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

DB_ORIGINAIS_SCHEMA = """
CREATE TABLE IF NOT EXISTS videos_original (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_type TEXT,
  source_url TEXT,
  telegram_file_id TEXT,
  original_path TEXT,
  status TEXT DEFAULT 'pending',
  width INTEGER,
  height INTEGER,
  duration_seconds REAL,
  size_bytes INTEGER,
  link_produto TEXT,
  descricao TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

DB_PROCESSADOS_SCHEMA = """
CREATE TABLE IF NOT EXISTS videos_processados (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  id_ref_original INTEGER NOT NULL,
  processed_path TEXT,
  status TEXT,
  retries INTEGER DEFAULT 0,
  error_message TEXT,
  width INTEGER,
  height INTEGER,
  duration_seconds REAL,
  size_bytes INTEGER,
    link_produto TEXT,
    descricao TEXT,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def _ensure_column(con: sqlite3.Connection, table: str, column: str, coltype: str):
    cur = con.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if column not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
        con.commit()


def init_db():
    if settings.USE_DUAL_DATABASES:
        os.makedirs(os.path.dirname(settings.DB_ORIGINAIS_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(settings.DB_PROCESSADOS_PATH), exist_ok=True)
        with sqlite3.connect(settings.DB_ORIGINAIS_PATH) as con:
            con.executescript(DB_ORIGINAIS_SCHEMA)
            # Garante colunas opcionais existirem
            _ensure_column(con, "videos_original", "link_produto", "TEXT")
            _ensure_column(con, "videos_original", "descricao", "TEXT")
        with sqlite3.connect(settings.DB_PROCESSADOS_PATH) as con:
            con.executescript(DB_PROCESSADOS_SCHEMA)
            # Garante colunas opcionais existirem
            _ensure_column(con, "videos_processados", "link_produto", "TEXT")
            _ensure_column(con, "videos_processados", "descricao", "TEXT")
    else:
        os.makedirs(os.path.dirname(settings.DB_SINGLE_PATH), exist_ok=True)
        with sqlite3.connect(settings.DB_SINGLE_PATH) as con:
            con.executescript(DB_SINGLE_SCHEMA)
            _ensure_column(con, "videos", "link_produto", "TEXT")
            _ensure_column(con, "videos", "descricao", "TEXT")


@contextmanager
def get_conn(processed: bool = False):
    if settings.USE_DUAL_DATABASES:
        path = settings.DB_PROCESSADOS_PATH if processed else settings.DB_ORIGINAIS_PATH
    else:
        path = settings.DB_SINGLE_PATH
    con = sqlite3.connect(path)
    try:
        yield con
    finally:
        con.close()


def insert_original(source_type: str, source_url: Optional[str], telegram_file_id: Optional[str], original_path: Optional[str], link_produto: Optional[str] = None, descricao: Optional[str] = None) -> int:
    if settings.USE_DUAL_DATABASES:
        with get_conn(False) as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO videos_original (source_type, source_url, telegram_file_id, original_path, link_produto, descricao) VALUES (?,?,?,?,?,?)",
                (source_type, source_url, telegram_file_id, original_path, link_produto, descricao),
            )
            con.commit()
            # lastrowid deve ser int
            return int(cur.lastrowid or 0)
    else:
        with get_conn() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO videos (source_type, source_url, telegram_file_id, original_path, status, link_produto, descricao) VALUES (?,?,?,?,?,?,?)",
                (source_type, source_url, telegram_file_id, original_path, "pending", link_produto, descricao),
            )
            con.commit()
            return int(cur.lastrowid or 0)


def update_original_path(record_id: int, original_path: str):
    if settings.USE_DUAL_DATABASES:
        with get_conn(False) as con:
            con.execute("UPDATE videos_original SET original_path=? WHERE id=?", (original_path, record_id))
            con.commit()
    else:
        with get_conn() as con:
            con.execute("UPDATE videos SET original_path=? WHERE id=?", (original_path, record_id))
            con.commit()


def insert_or_update_processed(id_ref_original: int, processed_path: Optional[str], status: str, error_message: Optional[str], meta: Tuple[Optional[int], Optional[int], Optional[float], Optional[int]], link_produto: Optional[str] = None, descricao: Optional[str] = None):
    width, height, duration, size_bytes = meta
    if settings.USE_DUAL_DATABASES:
        with get_conn(True) as con:
            cur = con.cursor()
            # Se já existe, atualiza; senão cria
            cur.execute("SELECT id, retries FROM videos_processados WHERE id_ref_original=?", (id_ref_original,))
            row = cur.fetchone()
            retries = 0
            if row:
                pid, retries = row
                cur.execute(
                    "UPDATE videos_processados SET processed_path=?, status=?, error_message=?, width=?, height=?, duration_seconds=?, size_bytes=?, link_produto=?, descricao=?, updated_at=CURRENT_TIMESTAMP WHERE id= ?",
                    (processed_path, status, error_message, width, height, duration, size_bytes, link_produto, descricao, pid),
                )
            else:
                cur.execute(
                    "INSERT INTO videos_processados (id_ref_original, processed_path, status, error_message, width, height, duration_seconds, size_bytes, link_produto, descricao) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (id_ref_original, processed_path, status, error_message, width, height, duration, size_bytes, link_produto, descricao),
                )
            con.commit()
    else:
        with get_conn() as con:
            con.execute(
                "UPDATE videos SET processed_path=?, status=?, error_message=?, width=?, height=?, duration_seconds=?, size_bytes=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (processed_path, status, error_message, width, height, duration, size_bytes, id_ref_original),
            )
            con.commit()


def increment_retry(id_ref_original: int):
    if settings.USE_DUAL_DATABASES:
        with get_conn(True) as con:
            con.execute("UPDATE videos_processados SET retries=retries+1, updated_at=CURRENT_TIMESTAMP WHERE id_ref_original=?", (id_ref_original,))
            con.commit()
    else:
        with get_conn() as con:
            con.execute("UPDATE videos SET retries=retries+1, updated_at=CURRENT_TIMESTAMP WHERE id=?", (id_ref_original,))
            con.commit()


def select_pending_or_failed(retry_only_failed: bool) -> Iterable[Tuple[Any, ...]]:
    if settings.USE_DUAL_DATABASES:
        # left join dos originais com processados
        with get_conn(False) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            if retry_only_failed:
                cur.execute("""
                    SELECT vo.id AS id
                    FROM videos_original vo
                    JOIN videos_processados vp ON vp.id_ref_original = vo.id
                    WHERE vp.status = 'failed' AND vp.retries < ?
                """, (settings.MAX_RETRIES,))
            else:
                # Todos os originais sem registro em processados OU com failed
                cur.execute("""
                    SELECT vo.id AS id
                    FROM videos_original vo
                    LEFT JOIN videos_processados vp ON vp.id_ref_original = vo.id
                    WHERE vp.id IS NULL OR vp.status = 'failed'
                """)
            return [(r["id"],) for r in cur.fetchall()]
    else:
        with get_conn() as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            if retry_only_failed:
                cur.execute("SELECT id FROM videos WHERE status='failed' AND retries < ?", (settings.MAX_RETRIES,))
            else:
                cur.execute("SELECT id FROM videos WHERE IFNULL(status,'pending') IN ('pending','failed')")
            return [(r["id"],) for r in cur.fetchall()]


def get_original_record(record_id: int) -> Optional[sqlite3.Row]:
    if settings.USE_DUAL_DATABASES:
        with get_conn(False) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM videos_original WHERE id=?", (record_id,))
            return cur.fetchone()
    else:
        with get_conn() as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM videos WHERE id=?", (record_id,))
            return cur.fetchone()
