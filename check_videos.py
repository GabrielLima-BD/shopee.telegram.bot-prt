import sqlite3
import os
from pathlib import Path

print("="*60)
print("🔍 DIAGNÓSTICO DE VÍDEOS PROCESSADOS")
print("="*60)

# Conectar ao banco processados
db_path = Path("data/videos_processados.db")
if not db_path.exists():
    print("❌ Banco de dados não encontrado!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Total de vídeos
cursor.execute("SELECT COUNT(*) FROM videos_processados")
total = cursor.fetchone()[0]
print(f"\n📊 Total de vídeos no banco: {total}")

# Por status
cursor.execute("SELECT status, COUNT(*) FROM videos_processados GROUP BY status")
status_counts = cursor.fetchall()
print(f"\n📈 Status dos vídeos:")
for status, count in status_counts:
    print(f"   {status}: {count}")

# Vídeos processados mas não enviados
cursor.execute("""
    SELECT id, processed_path, status, error_message, retries, 
           width, height, size_bytes, link_produto, descricao
    FROM videos_processados 
    WHERE status != 'processed' OR status IS NULL
    ORDER BY id DESC
    LIMIT 20
""")

failed = cursor.fetchall()
print(f"\n❌ Vídeos com problemas (últimos 20):")
print("-" * 60)

for row in failed:
    vid_id, path, status, error, retries, w, h, size_bytes, link, desc = row
    print(f"\n🎬 ID: {vid_id}")
    print(f"   Status: {status or 'NULL'}")
    print(f"   Erro: {error or 'nenhum'}")
    print(f"   Tentativas: {retries}")
    if path:
        exists = os.path.exists(path)
        print(f"   Path: {path}")
        print(f"   Arquivo existe: {'✅ SIM' if exists else '❌ NÃO'}")
        if exists:
            file_size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"   Tamanho arquivo: {file_size_mb:.2f} MB")
            if file_size_mb > 50:
                print(f"   ⚠️ ALERTA: Arquivo maior que 50 MB (limite do Telegram)")
    if w and h:
        print(f"   Resolução: {w}x{h}")
    if size_bytes:
        print(f"   Tamanho DB: {size_bytes / (1024*1024):.2f} MB")
    if link:
        print(f"   Link produto: {link[:50]}...")
    if desc:
        print(f"   Descrição: {desc[:50]}...")

# Vídeos enviados com sucesso
cursor.execute("""
    SELECT COUNT(*) FROM videos_processados 
    WHERE status = 'processed'
""")
success_count = cursor.fetchone()[0]
print(f"\n✅ Vídeos enviados com sucesso: {success_count}")

# Verificar vídeos muito grandes
cursor.execute("""
    SELECT id, processed_path, size_bytes, width, height
    FROM videos_processados 
    WHERE size_bytes > 52428800
    ORDER BY size_bytes DESC
    LIMIT 10
""")

large_videos = cursor.fetchall()
if large_videos:
    print(f"\n⚠️ VÍDEOS MAIORES QUE 50 MB:")
    print("-" * 60)
    for vid_id, path, size_bytes, w, h in large_videos:
        size_mb = size_bytes / (1024 * 1024)
        print(f"   ID {vid_id}: {size_mb:.2f} MB ({w}x{h})")
        print(f"      Path: {path}")

conn.close()

print("\n" + "="*60)
print("📝 DIAGNÓSTICO COMPLETO!")
print("="*60)
print("\n💡 DICAS:")
print("   1. Vídeos > 50 MB não podem ser enviados via Bot API")
print("   2. Use compressão para reduzir tamanho se necessário")
print("   3. Verifique se os arquivos existem no disco")
print("   4. Olhe os logs da GUI para mais detalhes")
print("="*60)
