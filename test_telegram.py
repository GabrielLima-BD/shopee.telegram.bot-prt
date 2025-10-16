import os
import sys
import requests
from pathlib import Path

print("="*60)
print("🔍 DIAGNÓSTICO DO TELEGRAM BOT")
print("="*60)

# Carregar .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    print(f"✅ Arquivo .env encontrado: {env_path}")
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
else:
    print("❌ Arquivo .env NÃO encontrado!")
    sys.exit(1)

# Pegar credenciais
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_SEND_TOKEN = os.environ.get("TELEGRAM_SEND_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

print("\n📋 CREDENCIAIS:")
print(f"   TELEGRAM_BOT_TOKEN: {'✅ Configurado' if TELEGRAM_BOT_TOKEN else '❌ VAZIO'}")
if TELEGRAM_BOT_TOKEN:
    print(f"      Primeiros 10 chars: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"      Tamanho: {len(TELEGRAM_BOT_TOKEN)} caracteres")

print(f"   TELEGRAM_SEND_TOKEN: {'✅ Configurado' if TELEGRAM_SEND_TOKEN else '❌ VAZIO (usará BOT_TOKEN)'}")
if TELEGRAM_SEND_TOKEN:
    print(f"      Primeiros 10 chars: {TELEGRAM_SEND_TOKEN[:10]}...")
    print(f"      Tamanho: {len(TELEGRAM_SEND_TOKEN)} caracteres")

print(f"   TELEGRAM_CHAT_ID: {'✅ Configurado' if TELEGRAM_CHAT_ID else '❌ VAZIO'}")
if TELEGRAM_CHAT_ID:
    print(f"      Chat ID: {TELEGRAM_CHAT_ID}")

# Token a ser usado
TOKEN_TO_USE = TELEGRAM_SEND_TOKEN or TELEGRAM_BOT_TOKEN

if not TOKEN_TO_USE or not TELEGRAM_CHAT_ID:
    print("\n❌ ERRO: Token ou Chat ID não configurados!")
    sys.exit(1)

print("\n" + "="*60)
print("🧪 TESTE 1: Verificar se o bot está ativo")
print("="*60)

try:
    url = f"https://api.telegram.org/bot{TOKEN_TO_USE}/getMe"
    r = requests.get(url, timeout=10)
    print(f"Status Code: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        if data.get("ok"):
            bot_info = data.get("result", {})
            print(f"✅ Bot ativo!")
            print(f"   Nome: {bot_info.get('first_name')}")
            print(f"   Username: @{bot_info.get('username')}")
            print(f"   ID: {bot_info.get('id')}")
        else:
            print(f"❌ Bot retornou ok=false")
            print(f"   Response: {data}")
    else:
        print(f"❌ Erro no request")
        print(f"   Response: {r.text}")
except Exception as e:
    print(f"❌ Exceção: {e}")

print("\n" + "="*60)
print("🧪 TESTE 2: Enviar mensagem de teste")
print("="*60)

try:
    url = f"https://api.telegram.org/bot{TOKEN_TO_USE}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "🧪 TESTE DE ENVIO - Sistema Shopee Telegram Bot\n\nSe você recebeu esta mensagem, o envio está funcionando! ✅"
    }
    r = requests.post(url, data=data, timeout=10)
    print(f"Status Code: {r.status_code}")
    
    if r.status_code == 200:
        resp_data = r.json()
        if resp_data.get("ok"):
            print(f"✅ Mensagem enviada com sucesso!")
            print(f"   Message ID: {resp_data.get('result', {}).get('message_id')}")
        else:
            print(f"❌ Telegram retornou ok=false")
            print(f"   Response: {resp_data}")
    else:
        print(f"❌ Erro no request")
        print(f"   Response: {r.text}")
except Exception as e:
    print(f"❌ Exceção: {e}")

print("\n" + "="*60)
print("🧪 TESTE 3: Verificar se o chat existe e você tem permissão")
print("="*60)

try:
    url = f"https://api.telegram.org/bot{TOKEN_TO_USE}/getChat"
    data = {"chat_id": TELEGRAM_CHAT_ID}
    r = requests.post(url, data=data, timeout=10)
    print(f"Status Code: {r.status_code}")
    
    if r.status_code == 200:
        resp_data = r.json()
        if resp_data.get("ok"):
            chat_info = resp_data.get("result", {})
            print(f"✅ Chat encontrado!")
            print(f"   Type: {chat_info.get('type')}")
            if chat_info.get('title'):
                print(f"   Title: {chat_info.get('title')}")
            if chat_info.get('username'):
                print(f"   Username: @{chat_info.get('username')}")
        else:
            print(f"❌ Telegram retornou ok=false")
            print(f"   Erro: {resp_data.get('description')}")
            print(f"   Dica: Você enviou /start para o bot?")
    else:
        print(f"❌ Erro no request")
        print(f"   Response: {r.text}")
except Exception as e:
    print(f"❌ Exceção: {e}")

print("\n" + "="*60)
print("📝 DIAGNÓSTICO COMPLETO!")
print("="*60)
print("\n✅ PRÓXIMOS PASSOS:")
print("   1. Verifique se recebeu a mensagem de teste no Telegram")
print("   2. Se não recebeu, envie /start para o bot")
print("   3. Verifique se o CHAT_ID está correto")
print("   4. Teste enviar um vídeo manualmente pela GUI")
print("="*60)
