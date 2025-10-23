import sys
import traceback
from app.gui_manager import start_gui

if __name__ == "__main__":
    try:
        start_gui()
    except Exception as e:
        # Capturar qualquer exceção não tratada e exibir
        with open("crash_log.txt", "w", encoding="utf-8") as f:
            f.write("=== ERRO CRÍTICO ===\n")
            f.write(f"Erro: {str(e)}\n\n")
            f.write("Traceback completo:\n")
            f.write(traceback.format_exc())
        
        print("\n" + "="*60)
        print("❌ ERRO CRÍTICO - O aplicativo encontrou um problema!")
        print("="*60)
        print(f"Erro: {str(e)}")
        print("\nDetalhes salvos em: crash_log.txt")
        print("\nPressione ENTER para fechar...")
        print("="*60)
        input()
        sys.exit(1)
