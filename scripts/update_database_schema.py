"""
Script para atualizar o schema dos bancos de dados adicionando colunas faltantes
Inclui: link_produto e descricao em videos_original e videos_processados
"""
import sqlite3
import os
import sys

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings


def _ensure_column(con: sqlite3.Connection, table: str, column: str, coltype: str):
    cur = con.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cur.fetchall()]
    if column not in columns:
        print(f"  ➕ Adicionando coluna '{column}' em {table}...")
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
        con.commit()


def update_single_db():
    """Atualizar banco single"""
    print(f"📦 Atualizando banco single: {settings.DB_SINGLE_PATH}")
    
    if not os.path.exists(settings.DB_SINGLE_PATH):
        print("  ⚠️ Banco não existe, pulando...")
        return
    
    with sqlite3.connect(settings.DB_SINGLE_PATH) as con:
        _ensure_column(con, "videos", "link_produto", "TEXT")
        _ensure_column(con, "videos", "descricao", "TEXT")
        print("  ✅ Banco single atualizado!")


def update_dual_db():
    """Atualizar bancos dual"""
    print(f"📦 Atualizando banco original: {settings.DB_ORIGINAIS_PATH}")
    
    if not os.path.exists(settings.DB_ORIGINAIS_PATH):
        print("  ⚠️ Banco não existe, pulando...")
    else:
        with sqlite3.connect(settings.DB_ORIGINAIS_PATH) as con:
            _ensure_column(con, "videos_original", "link_produto", "TEXT")
            _ensure_column(con, "videos_original", "descricao", "TEXT")
            print("  ✅ Banco original atualizado!")
    
    print(f"📦 Atualizando banco processados: {settings.DB_PROCESSADOS_PATH}")
    
    if not os.path.exists(settings.DB_PROCESSADOS_PATH):
        print("  ⚠️ Banco não existe, pulando...")
    else:
        with sqlite3.connect(settings.DB_PROCESSADOS_PATH) as con:
            _ensure_column(con, "videos_processados", "link_produto", "TEXT")
            _ensure_column(con, "videos_processados", "descricao", "TEXT")
            print("  ✅ Banco processados atualizado!")


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 ATUALIZAÇÃO DE SCHEMA DO BANCO DE DADOS")
    print("=" * 60)
    
    if settings.USE_DUAL_DATABASES:
        print("Modo: DUAL DATABASES")
        update_dual_db()
    else:
        print("Modo: SINGLE DATABASE")
        update_single_db()
    
    print("\n✅ Atualização concluída!")
