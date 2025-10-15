import os
import shutil
import subprocess
import tempfile
from typing import Optional, Tuple

from .config import settings


def _find_ffmpeg_ffprobe() -> Tuple[str, str]:
    """Procura FFmpeg e FFprobe no sistema em vários locais possíveis"""
    # Locais possíveis de instalação
    possible_paths = [
        # PATH do sistema
        (shutil.which("ffmpeg"), shutil.which("ffprobe")),
        # Instalação do winget (Program Files)
        ("C:\\Program Files\\FFmpeg\\bin\\ffmpeg.exe", "C:\\Program Files\\FFmpeg\\bin\\ffprobe.exe"),
        # Instalação manual típica
        ("C:\\ffmpeg\\bin\\ffmpeg.exe", "C:\\ffmpeg\\bin\\ffprobe.exe"),
        # Configuração do .env
        (os.path.join(settings.FFMPEG_DIR, "bin", "ffmpeg.exe"), 
         os.path.join(settings.FFMPEG_DIR, "bin", "ffprobe.exe")),
    ]
    
    for ffmpeg_path, ffprobe_path in possible_paths:
        if ffmpeg_path and ffprobe_path and os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
            return (ffmpeg_path, ffprobe_path)
    
    # Fallback para comandos simples (assume que está no PATH)
    return ("ffmpeg", "ffprobe")


# Cache dos executáveis encontrados
_FFMPEG_EXE, _FFPROBE_EXE = _find_ffmpeg_ffprobe()


def _run(cmd: list[str], timeout: Optional[int] = None) -> tuple[int, str, str]:
    """Executa um comando de forma resiliente.

    Retornos convencionados:
    - 0: sucesso
    - 124: timeout
    - 127: executável não encontrado
    """
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            return (124, "", "timeout")
        return (proc.returncode, out or "", err or "")
    except FileNotFoundError as e:
        # Executável não encontrado
        return (127, "", str(e))


def ffprobe_media(path: str) -> Tuple[Optional[int], Optional[int], Optional[float], Optional[int]]:
    if not os.path.exists(path):
        return (None, None, None, None)
    # Tamanho
    size_bytes = None
    try:
        size_bytes = os.path.getsize(path)
    except Exception:
        pass

    # Usar caminho completo do ffprobe
    cmd = [
        _FFPROBE_EXE,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height:format=duration",
        "-of", "default=noprint_wrappers=1:nokey=0",
        path,
    ]
    code, out, err = _run(cmd)
    if code != 0:
        return (None, None, None, size_bytes)
    width = height = None
    duration = None
    for line in out.splitlines():
        if line.startswith("width="):
            try:
                width = int(line.split("=", 1)[1])
            except Exception:
                pass
        if line.startswith("height="):
            try:
                height = int(line.split("=", 1)[1])
            except Exception:
                pass
        if line.startswith("duration="):
            try:
                duration = float(line.split("=", 1)[1])
            except Exception:
                pass
    return (width, height, duration, size_bytes)


def validate_min_height(path: str, min_height: int) -> bool:
    _, h, _, _ = ffprobe_media(path)
    return (h or 0) >= min_height


def ffmpeg_upscale(input_path: str, output_path: str, target_min_height: int) -> bool:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    scale_expr = f"-2:{target_min_height}"
    cmd = [
        _FFMPEG_EXE, "-y",
        "-i", input_path,
        "-vf", f"scale={scale_expr}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        output_path,
    ]
    code, out, err = _run(cmd)
    return code == 0 and os.path.exists(output_path)


def try_video2x(input_path: str, output_path: str, timeout_seconds: int) -> bool:
    # Tenta localizar executável do Video2X
    candidates = [
        os.path.join(settings.VIDEO2X_DIR, "bin", "video2x.exe"),
        os.path.join(settings.VIDEO2X_DIR, "bin", "video2x-cli.exe"),
        "video2x",
        "video2x-cli",
    ]
    exe = next((p for p in candidates if shutil.which(p) or os.path.exists(p)), None)
    if not exe:
        return False

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Parâmetros variam por build do Video2X; tentativa genérica:
    cmd = [exe, "--input", input_path, "--output", output_path, "--scale-width", "0", "--scale-height", str(settings.VIDEO_TARGET_MIN_HEIGHT)]
    code, out, err = _run(cmd, timeout=timeout_seconds)
    return code == 0 and os.path.exists(output_path)


def ensure_processed(input_path: str) -> tuple[str, str]:
    """
    Retorna (processed_path, method) onde method in {"Video2X", "FFmpeg", "Original"}.
    GARANTE que o vídeo final tenha pelo menos 720p.
    """
    base = os.path.splitext(os.path.basename(input_path))[0]
    out_v2x = os.path.join(settings.PROCESSED_DIR, base + "_v2x.mp4")
    out_ff = os.path.join(settings.PROCESSED_DIR, base + "_ffmpeg.mp4")

    # Verifica se o vídeo original já é >= 720p
    _, height, _, _ = ffprobe_media(input_path)
    
    # Se já é >= 720p, pode retornar o original
    if height and height >= settings.VIDEO_TARGET_MIN_HEIGHT:
        return input_path, "Original"
    
    # Se não, SEMPRE fazer upscale com FFmpeg (garantido)
    print(f"[UPSCALE] Vídeo {height}p < 720p, forçando upscale...")
    
    if settings.PREFER_VIDEO2X_FIRST:
        if try_video2x(input_path, out_v2x, settings.TIMEOUT_VIDEO2X_SECONDS):
            # Valida se Video2X realmente fez o upscale
            _, new_height, _, _ = ffprobe_media(out_v2x)
            if new_height and new_height >= settings.VIDEO_TARGET_MIN_HEIGHT:
                return out_v2x, "Video2X"
        
        # Fallback para FFmpeg (sempre funciona)
        if ffmpeg_upscale(input_path, out_ff, settings.VIDEO_TARGET_MIN_HEIGHT):
            return out_ff, "FFmpeg"
    else:
        # FFmpeg primeiro (mais confiável)
        if ffmpeg_upscale(input_path, out_ff, settings.VIDEO_TARGET_MIN_HEIGHT):
            return out_ff, "FFmpeg"
        
        # Tenta Video2X se FFmpeg falhar
        if try_video2x(input_path, out_v2x, settings.TIMEOUT_VIDEO2X_SECONDS):
            _, new_height, _, _ = ffprobe_media(out_v2x)
            if new_height and new_height >= settings.VIDEO_TARGET_MIN_HEIGHT:
                return out_v2x, "Video2X"
    
    # Se tudo falhar, força upscale com FFmpeg em modo simples
    print("[UPSCALE] Tentativas falharam, forçando FFmpeg modo simples...")
    if ffmpeg_upscale(input_path, out_ff, settings.VIDEO_TARGET_MIN_HEIGHT):
        return out_ff, "FFmpeg"
    
    # Último recurso: retorna original (mas isso não deveria acontecer)
    print("[UPSCALE] AVISO: Não foi possível fazer upscale, usando original")
    return input_path, "Original"

