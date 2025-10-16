"""
CONFIGURAR TOKENS - EXECUTE UMA VEZ ANTES DE COMPILAR

Este script modifica app/config.py para embutir seus tokens.
Depois disso, compile o .exe e ele funcionará em qualquer lugar!
"""

import os
from pathlib import Path

# Perguntar tokens
print("=" * 60)
print("  CONFIGURAR SHOPEE TELEGRAM BOT")
print("=" * 60)
print()
print("Digite suas credenciais:")
print()

token = input("TELEGRAM_BOT_TOKEN: ").strip()
chat_id = input("TELEGRAM_CHAT_ID: ").strip()

print()
print("Verificando...")

if not token or token == "":
    print("❌ Token não pode estar vazio!")
    input("Pressione Enter para sair...")
    exit(1)

if not chat_id or chat_id == "":
    print("❌ Chat ID não pode estar vazio!")
    input("Pressione Enter para sair...")
    exit(1)

# Modificar config.py
config_path = Path(__file__).parent / "app" / "config.py"

print(f"Lendo: {config_path}")

with open(config_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Substituir placeholders
content = content.replace('_HARDCODED_BOT_TOKEN: str = "SEU_TOKEN_AQUI"', 
                         f'_HARDCODED_BOT_TOKEN: str = "{token}"')
content = content.replace('_HARDCODED_CHAT_ID: str = "SEU_CHAT_ID_AQUI"', 
                         f'_HARDCODED_CHAT_ID: str = "{chat_id}"')

# Salvar
with open(config_path, 'w', encoding='utf-8') as f:
    f.write(content)

print()
print("✅ Tokens configurados com sucesso!")
print()
print("PRÓXIMO PASSO:")
print("Execute: pyinstaller --noconfirm --onefile --windowed --name \"Shopee-Telegram-BOT\" --add-data \"app;app\" --hidden-import=tkinter --hidden-import=telegram --hidden-import=telegram.ext --hidden-import=requests --collect-all telegram main_app.py")
print()
print("Depois, pegue o .exe da pasta dist/ e envie para qualquer pessoa!")
print("Não precisa enviar mais NADA junto!")
print()
input("Pressione Enter para fechar...")
