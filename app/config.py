import os
import sys
from dataclasses import dataclass
from pathlib import Path

# Detectar se está rodando como executável PyInstaller
def _get_base_path():
    """Retorna o diretório base correto tanto para dev quanto para .exe"""
    if getattr(sys, 'frozen', False):
        # Rodando como executável compilado
        return Path(sys.executable).parent
    else:
        # Rodando como script Python
        return Path(__file__).parent.parent

# Carregar .env automaticamente se existir
def _load_env_file():
    """Carregar arquivo .env manualmente se dotenv não estiver disponível"""
    base_path = _get_base_path()
    env_path = base_path / ".env"
    
    print(f"[CONFIG] Procurando .env em: {env_path}")
    
    if env_path.exists():
        print(f"[CONFIG] ✅ .env encontrado!")
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
                        # Debug (sem mostrar valores sensíveis)
                        if 'TOKEN' not in key and 'PASSWORD' not in key:
                            print(f"[CONFIG] Carregado: {key.strip()}")
            print(f"[CONFIG] ✅ Variáveis carregadas do .env")
        except Exception as e:
            print(f"[CONFIG] ❌ Erro ao ler .env: {e}")
    else:
        print(f"[CONFIG] ⚠️ .env NÃO encontrado em: {env_path}")
        print(f"[CONFIG] Usando variáveis de ambiente do sistema")

try:
    from dotenv import load_dotenv
    base_path = _get_base_path()
    env_path = base_path / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[CONFIG] ✅ .env carregado via dotenv de: {env_path}")
except ImportError:
    # Se dotenv não estiver disponível, usar função manual
    _load_env_file()


def _get_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "y"}


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except Exception:
        return default


@dataclass
class Settings:
    # ============================================
    # CONFIGURAÇÕES HARD-CODED (PREENCHA AQUI!)
    # ============================================
    # Tokens/IDs informados pelo usuário em 17/11/2025
    # Grupo Gabriel
    _HARDCODED_BOT_TOKEN_GABRIEL: str = "8025515620:AAFhsOSaJCEWz8n6hz0ulKYuIPnhOsbMUnQ"
    _HARDCODED_CHAT_ID_GABRIEL: str = "-1003111038846"
    # Grupo Marli
    _HARDCODED_BOT_TOKEN_MARLI: str = "8245552093:AAEHrDhbivDZr9MlQQat17cDH677DXTiCCo"
    # Usuário forneceu '8085332300' — garantir prefixo -100 para canais
    # Atualizado conforme informado pelo usuário (17/11/2025)
    _HARDCODED_CHAT_ID_MARLI: str = "-1003334956052"
    
    # Tokens e IDs - Usa hard-coded se disponível, senão .env
    # Token usado pelo bot que roda em background (padrão: Gabriel se disponível, senão Marli)
    TELEGRAM_BOT_TOKEN: str = _HARDCODED_BOT_TOKEN_GABRIEL or _HARDCODED_BOT_TOKEN_MARLI or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    # Tokens/Chats para envio (específicos por destino)
    TELEGRAM_SEND_TOKEN_GABRIEL: str = _HARDCODED_BOT_TOKEN_GABRIEL if _HARDCODED_BOT_TOKEN_GABRIEL != "SEU_TOKEN_AQUI" else os.environ.get("TELEGRAM_SEND_TOKEN_GABRIEL", "")
    TELEGRAM_CHAT_ID_GABRIEL: str = _HARDCODED_CHAT_ID_GABRIEL if _HARDCODED_CHAT_ID_GABRIEL != "SEU_CHAT_ID_AQUI" else os.environ.get("TELEGRAM_CHAT_ID_GABRIEL", "")

    TELEGRAM_SEND_TOKEN_MARLI: str = _HARDCODED_BOT_TOKEN_MARLI if _HARDCODED_BOT_TOKEN_MARLI != "SEU_TOKEN_AQUI" else os.environ.get("TELEGRAM_SEND_TOKEN_MARLI", "")
    TELEGRAM_CHAT_ID_MARLI: str = _HARDCODED_CHAT_ID_MARLI if _HARDCODED_CHAT_ID_MARLI != "SEU_CHAT_ID_AQUI" else os.environ.get("TELEGRAM_CHAT_ID_MARLI", "")

    # Compatibilidade/legacy: valores genéricos usados em código antigo
    TELEGRAM_SEND_TOKEN: str = TELEGRAM_SEND_TOKEN_MARLI or TELEGRAM_SEND_TOKEN_GABRIEL or os.environ.get("TELEGRAM_SEND_TOKEN", "")
    TELEGRAM_CHAT_ID: str = TELEGRAM_CHAT_ID_MARLI or TELEGRAM_CHAT_ID_GABRIEL or os.environ.get("TELEGRAM_CHAT_ID", "")
    # Seletor de destino de envio (usado pela GUI). Pode ser 'Gabriel' ou 'Marli'.
    SELECTED_SEND_TARGET: str = os.environ.get("SELECTED_SEND_TARGET", "Gabriel")
    TELEGRAM_CHANNEL_ID: str = os.environ.get("TELEGRAM_CHANNEL_ID", "")
    TELEGRAM_ADMIN_USER_ID: str = os.environ.get("TELEGRAM_ADMIN_USER_ID", "")

    # Pastas (criadas automaticamente onde o .exe estiver)
    _base_path: Path = _get_base_path()
    DOWNLOAD_DIR: str = str(_base_path / "downloads")
    PROCESSED_DIR: str = str(_base_path / "processed")

    # Ferramentas (usa do sistema se disponível)
    FFMPEG_DIR: str = os.environ.get("FFMPEG_DIR", r"C:\ffmpeg")
    VIDEO2X_DIR: str = os.environ.get("VIDEO2X_DIR", r"C:\Video2X")

    # Banco de dados (criados automaticamente)
    USE_DUAL_DATABASES: bool = True
    DB_SINGLE_PATH: str = str(_base_path / "data" / "videos.db")
    DB_ORIGINAIS_PATH: str = str(_base_path / "data" / "videos_original.db")
    DB_PROCESSADOS_PATH: str = str(_base_path / "data" / "videos_processados.db")

    # Pipeline
    MAX_RETRIES: int = 2
    VIDEO_TARGET_MIN_HEIGHT: int = 1080
    PREFER_VIDEO2X_FIRST: bool = False
    TIMEOUT_VIDEO2X_SECONDS: int = 900
    # Qualidade/bitrates e duração
    VIDEO_MIN_BITRATE_KBPS: int = 2500
    VIDEO_TARGET_BITRATE_KBPS: int = 3500
    VIDEO_MIN_DURATION_SECONDS: int = 3
    VIDEO_MAX_DURATION_SECONDS: int = 60

    # Exec flags
    ONLY_DOWNLOAD: bool = False
    ONLY_PROCESS: bool = False
    ONLY_VALIDATE: bool = False
    ONLY_SEND: bool = False
    RETRY_FAILED_ONLY: bool = False


settings = Settings()

# Debug: Mostrar configurações importantes
print(f"[CONFIG] Base path: {settings._base_path}")
print(f"[CONFIG] Download dir: {settings.DOWNLOAD_DIR}")
print(f"[CONFIG] Processed dir: {settings.PROCESSED_DIR}")
print(f"[CONFIG] DB Original: {settings.DB_ORIGINAIS_PATH}")
print(f"[CONFIG] DB Processados: {settings.DB_PROCESSADOS_PATH}")
print(f"[CONFIG] Telegram Bot token (ativo): {'✅ Configurado' if settings.TELEGRAM_BOT_TOKEN else '❌ VAZIO'}")
print(f"[CONFIG] Telegram Send token Gabriel: {'✅' if settings.TELEGRAM_SEND_TOKEN_GABRIEL else '❌'} | Chat ID: {settings.TELEGRAM_CHAT_ID_GABRIEL}")
print(f"[CONFIG] Telegram Send token Marli: {'✅' if settings.TELEGRAM_SEND_TOKEN_MARLI else '❌'} | Chat ID: {settings.TELEGRAM_CHAT_ID_MARLI}")
print(f"[CONFIG] Telegram Chat ID (legacy): {'✅ Configurado' if settings.TELEGRAM_CHAT_ID else '❌ VAZIO'}")
print(f"[CONFIG] Vídeo: alvo {settings.VIDEO_TARGET_MIN_HEIGHT}p, bitrate alvo {settings.VIDEO_TARGET_BITRATE_KBPS}k (mín {settings.VIDEO_MIN_BITRATE_KBPS}k), duração {settings.VIDEO_MIN_DURATION_SECONDS}-{settings.VIDEO_MAX_DURATION_SECONDS}s")

# Assegurar diretórios
os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
os.makedirs(Path(settings.DB_ORIGINAIS_PATH).parent, exist_ok=True)
