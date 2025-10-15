"""
Script para recriar os bancos de dados com schema correto
"""
import os
import sys

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings
from app.db import init_db

def recreate_databases():
    print("=" * 60)
    print("🔧 RECRIANDO BANCOS DE DADOS COM SCHEMA CORRETO")
    print("=" * 60)
    
    if settings.USE_DUAL_DATABASES:
        print(f"\n📦 Modo: DUAL DATABASES")
        print(f"  📁 Banco Original: {settings.DB_ORIGINAIS_PATH}")
        print(f"  📁 Banco Processados: {settings.DB_PROCESSADOS_PATH}")
        
        # Remover bancos antigos se existirem
        if os.path.exists(settings.DB_ORIGINAIS_PATH):
            print(f"\n  🗑️ Removendo banco antigo: videos_original.db")
            os.remove(settings.DB_ORIGINAIS_PATH)
        
        if os.path.exists(settings.DB_PROCESSADOS_PATH):
            print(f"  🗑️ Removendo banco antigo: videos_processados.db")
            os.remove(settings.DB_PROCESSADOS_PATH)
    else:
        print(f"\n📦 Modo: SINGLE DATABASE")
        print(f"  📁 Banco: {settings.DB_SINGLE_PATH}")
        
        if os.path.exists(settings.DB_SINGLE_PATH):
            print(f"\n  🗑️ Removendo banco antigo: videos.db")
            os.remove(settings.DB_SINGLE_PATH)
    
    print("\n✅ Criando novos bancos com schema correto...")
    init_db()
    
    print("\n✅ Bancos recriados com sucesso!")
    print("\n⚠️ ATENÇÃO: Todos os dados antigos foram apagados!")

if __name__ == "__main__":
    response = input("\n⚠️ AVISO: Isso vai APAGAR todos os dados existentes! Continuar? (s/N): ")
    if response.lower() == 's':
        recreate_databases()
    else:
        print("❌ Operação cancelada.")
