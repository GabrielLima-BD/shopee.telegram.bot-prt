import sqlite3, os
DB_ORIGINAIS = os.environ.get("DB_ORIGINAIS_PATH", r"C:\\caminho\\data\\videos_original.db")
DB_PROCESSADOS = os.environ.get("DB_PROCESSADOS_PATH", r"C:\\caminho\\data\\videos_processados.db")
os.makedirs(os.path.dirname(DB_ORIGINAIS), exist_ok=True)
os.makedirs(os.path.dirname(DB_PROCESSADOS), exist_ok=True)
schema_original = """
CREATE TABLE IF NOT EXISTS videos_original (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_type TEXT,
  source_url TEXT,
  telegram_file_id TEXT,
  original_path TEXT NOT NULL,
  width INTEGER,
  height INTEGER,
  duration_seconds REAL,
  size_bytes INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""
schema_processados = """
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
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""
with sqlite3.connect(DB_ORIGINAIS) as con: con.executescript(schema_original)
with sqlite3.connect(DB_PROCESSADOS) as con: con.executescript(schema_processados)
print("[OK] Bancos criados:", DB_ORIGINAIS, DB_PROCESSADOS)
