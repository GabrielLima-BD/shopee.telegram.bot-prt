"""
Script para verificar o ambiente e dependências
"""
import os
import sys
import shutil

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings

def check_directories():
    print("\n📁 VERIFICANDO DIRETÓRIOS:")
    
    dirs = {
        "Downloads": settings.DOWNLOAD_DIR,
        "Processados": settings.PROCESSED_DIR,
    }
    
    for name, path in dirs.items():
        if os.path.exists(path):
            print(f"  ✅ {name}: {path}")
        else:
            print(f"  ❌ {name} NÃO EXISTE: {path}")
            print(f"     Criando diretório...")
            os.makedirs(path, exist_ok=True)
            print(f"     ✅ Criado!")

def check_tools():
    print("\n🔧 VERIFICANDO FERRAMENTAS:")
    
    # Verificar FFmpeg
    ffmpeg_path = os.path.join(settings.FFMPEG_DIR, "bin", "ffmpeg.exe")
    ffprobe_path = os.path.join(settings.FFMPEG_DIR, "bin", "ffprobe.exe")
    
    if os.path.exists(ffmpeg_path):
        print(f"  ✅ FFmpeg: {ffmpeg_path}")
    else:
        print(f"  ❌ FFmpeg NÃO ENCONTRADO: {ffmpeg_path}")
    
    if os.path.exists(ffprobe_path):
        print(f"  ✅ FFprobe: {ffprobe_path}")
    else:
        print(f"  ❌ FFprobe NÃO ENCONTRADO: {ffprobe_path}")
    
    # Verificar se está no PATH
    ffmpeg_in_path = shutil.which("ffmpeg")
    ffprobe_in_path = shutil.which("ffprobe")
    
    if ffmpeg_in_path:
        print(f"  ✅ FFmpeg no PATH: {ffmpeg_in_path}")
    else:
        print(f"  ⚠️ FFmpeg NÃO está no PATH do sistema")
    
    if ffprobe_in_path:
        print(f"  ✅ FFprobe no PATH: {ffprobe_in_path}")
    else:
        print(f"  ⚠️ FFprobe NÃO está no PATH do sistema")
    
    # Verificar Video2X
    video2x_path = os.path.join(settings.VIDEO2X_DIR, "video2x.exe")
    if os.path.exists(video2x_path):
        print(f"  ✅ Video2X: {video2x_path}")
    else:
        print(f"  ⚠️ Video2X NÃO ENCONTRADO: {video2x_path}")

def check_databases():
    print("\n💾 VERIFICANDO BANCOS DE DADOS:")
    
    if settings.USE_DUAL_DATABASES:
        print("  Modo: DUAL DATABASES")
        
        if os.path.exists(settings.DB_ORIGINAIS_PATH):
            size = os.path.getsize(settings.DB_ORIGINAIS_PATH)
            print(f"  ✅ videos_original.db ({size} bytes)")
        else:
            print(f"  ❌ videos_original.db NÃO EXISTE")
        
        if os.path.exists(settings.DB_PROCESSADOS_PATH):
            size = os.path.getsize(settings.DB_PROCESSADOS_PATH)
            print(f"  ✅ videos_processados.db ({size} bytes)")
        else:
            print(f"  ❌ videos_processados.db NÃO EXISTE")
    else:
        print("  Modo: SINGLE DATABASE")
        if os.path.exists(settings.DB_SINGLE_PATH):
            size = os.path.getsize(settings.DB_SINGLE_PATH)
            print(f"  ✅ videos.db ({size} bytes)")
        else:
            print(f"  ❌ videos.db NÃO EXISTE")

if __name__ == "__main__":
    print("=" * 70)
    print("🔍 DIAGNÓSTICO DO AMBIENTE - Sistema Shopee Telegram")
    print("=" * 70)
    
    check_directories()
    check_tools()
    check_databases()
    
    print("\n" + "=" * 70)
    print("✅ Diagnóstico concluído!")
    print("=" * 70)
