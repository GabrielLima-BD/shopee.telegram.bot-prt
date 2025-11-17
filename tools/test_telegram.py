"""Teste simples de envio para os destinos configurados (Gabriel / Marli).

Roda a partir da raiz do projeto:

    python tools/test_telegram.py

Isso tenta enviar uma mensagem de texto usando os tokens/chat configurados em `app.config.settings`.
"""
import os
import sys
import requests

# Garantir que a raiz do projeto esteja no sys.path ao executar este script diretamente
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.config import settings


def test_target(name: str):
    name_key = name.strip().lower()
    if name_key == 'marli':
        token = getattr(settings, 'TELEGRAM_SEND_TOKEN_MARLI', '') or getattr(settings, 'TELEGRAM_SEND_TOKEN', '') or getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        chat_id = getattr(settings, 'TELEGRAM_CHAT_ID_MARLI', '') or getattr(settings, 'TELEGRAM_CHAT_ID', '')
    else:
        # Gabriel: prefer explicit Gabriel send token
        token = getattr(settings, 'TELEGRAM_SEND_TOKEN_GABRIEL', '') or getattr(settings, 'TELEGRAM_SEND_TOKEN', '') or getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        chat_id = getattr(settings, 'TELEGRAM_CHAT_ID_GABRIEL', '') or getattr(settings, 'TELEGRAM_CHAT_ID', '')

    print(f"\n--- Testando destino: {name} ---")
    if not token:
        print("Ignorado: token não configurado")
        return
    if not chat_id:
        print("Ignorado: chat_id não configurado")
        return

    # Checar token com getMe
    try:
        r_me = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        print(f"getMe status: {r_me.status_code} | {r_me.text}")
    except Exception as e:
        print(f"getMe failed: {type(e).__name__}: {e}")

    # Checar chat com getChat
    try:
        r_chat = requests.get(f"https://api.telegram.org/bot{token}/getChat", params={"chat_id": chat_id}, timeout=10)
        print(f"getChat status: {r_chat.status_code} | {r_chat.text}")
    except Exception as e:
        print(f"getChat failed: {type(e).__name__}: {e}")

    # Tentar enviar mensagem curta
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": f"Teste de envio (destino {name})"}
    try:
        r = requests.post(url, data=payload, timeout=15)
        print(f"sendMessage status: {r.status_code} | {r.text}")
    except Exception as e:
        print(f"sendMessage failed: {type(e).__name__}: {e}")


if __name__ == '__main__':
    print("Settings usados:")
    print(f"TELEGRAM_BOT_TOKEN configurado: {'SIM' if settings.TELEGRAM_BOT_TOKEN else 'NÃO'}")
    print(f"TELEGRAM_SEND_TOKEN configurado: {'SIM' if settings.TELEGRAM_SEND_TOKEN else 'NÃO'}")
    print(f"TELEGRAM_CHAT_ID: {settings.TELEGRAM_CHAT_ID}")
    test_target('Gabriel')
    test_target('Marli')
