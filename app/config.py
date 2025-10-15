import os
from dataclasses import dataclass
from pathlib import Path

# Carregar .env automaticamente se existir
def _load_env_file():
    """Carregar arquivo .env manualmente se dotenv não estiver disponível"""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        except Exception:
            pass

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
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
    # Tokens e IDs (NUNCA logar valores)
    TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_SEND_TOKEN: str = os.environ.get("TELEGRAM_SEND_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID", "")
    TELEGRAM_CHANNEL_ID: str = os.environ.get("TELEGRAM_CHANNEL_ID", "")
    TELEGRAM_ADMIN_USER_ID: str = os.environ.get("TELEGRAM_ADMIN_USER_ID", "")

    # Pastas
    DOWNLOAD_DIR: str = os.environ.get("DOWNLOAD_DIR", r"C:\caminho\para\downloads")
    PROCESSED_DIR: str = os.environ.get("PROCESSED_DIR", r"C:\caminho\para\processados")

    # Ferramentas
    FFMPEG_DIR: str = os.environ.get("FFMPEG_DIR", r"C:\ffmpeg")
    VIDEO2X_DIR: str = os.environ.get("VIDEO2X_DIR", r"C:\Video2X")

    # Banco de dados
    USE_DUAL_DATABASES: bool = _get_bool("USE_DUAL_DATABASES", False)
    DB_SINGLE_PATH: str = os.environ.get("DB_SINGLE_PATH", r"C:\caminho\data\videos.db")
    DB_ORIGINAIS_PATH: str = os.environ.get("DB_ORIGINAIS_PATH", r"C:\caminho\data\videos_original.db")
    DB_PROCESSADOS_PATH: str = os.environ.get("DB_PROCESSADOS_PATH", r"C:\caminho\data\videos_processados.db")

    # Pipeline
    MAX_RETRIES: int = _get_int("MAX_RETRIES", 2)
    VIDEO_TARGET_MIN_HEIGHT: int = _get_int("VIDEO_TARGET_MIN_HEIGHT", 720)
    PREFER_VIDEO2X_FIRST: bool = _get_bool("PREFER_VIDEO2X_FIRST", True)
    TIMEOUT_VIDEO2X_SECONDS: int = _get_int("TIMEOUT_VIDEO2X_SECONDS", 900)

    # Exec flags
    ONLY_DOWNLOAD: bool = _get_bool("ONLY_DOWNLOAD", False)
    ONLY_PROCESS: bool = _get_bool("ONLY_PROCESS", False)
    ONLY_VALIDATE: bool = _get_bool("ONLY_VALIDATE", False)
    ONLY_SEND: bool = _get_bool("ONLY_SEND", False)
    RETRY_FAILED_ONLY: bool = _get_bool("RETRY_FAILED_ONLY", False)


settings = Settings()

# Assegurar diretórios
os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
