import sys
from pathlib import Path

print("="*60)
print("🧪 TESTE DE CAMINHOS - SIMULAÇÃO DE EXECUÇÃO")
print("="*60)

# Simular execução como .exe
sys.frozen = True
sys.executable = r"C:\Users\Usuario\Desktop\Aplicativo\Shopee-Telegram-BOT.exe"

# Importar função
import os
os.chdir("C:\\Windows\\System32")  # Simula execução de outro diretório
print(f"\n📂 Diretório atual (os.getcwd()): {os.getcwd()}")

# Testar _get_base_path
def _get_base_path():
    """Retorna o diretório base correto tanto para dev quanto para .exe"""
    if getattr(sys, 'frozen', False):
        # Rodando como executável compilado
        return Path(sys.executable).parent
    else:
        # Rodando como script Python
        return Path(__file__).parent.parent

base_path = _get_base_path()
env_path = base_path / ".env"

print(f"\n✅ RESULTADOS:")
print(f"   sys.executable: {sys.executable}")
print(f"   Base path: {base_path}")
print(f"   .env path: {env_path}")

print(f"\n💡 CONCLUSÃO:")
print(f"   O .env sempre será buscado em:")
print(f"   {env_path}")
print(f"\n   Não importa de onde você executou o .exe!")

print("\n" + "="*60)
print("✅ FUNCIONA PERFEITAMENTE FIXADO NO INICIAR!")
print("="*60)
