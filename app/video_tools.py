import os
import json
import math
import shutil
import subprocess
import tempfile
import threading
from typing import Optional, Tuple, Dict, Any

from .config import settings

# Lock para garantir que apenas 1 processamento FFmpeg rode por vez
_FFMPEG_LOCK = threading.Lock()


def _find_ffmpeg_ffprobe() -> Tuple[str, str]:
    """Procura FFmpeg e FFprobe no sistema em vários locais possíveis"""
    # Locais possíveis de instalação
    possible_paths = [
        # PATH do sistema
        (shutil.which("ffmpeg"), shutil.which("ffprobe")),
        # Winget install (user packages)
        (r"C:\Users\gbr bzzr\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0-full_build\bin\ffmpeg.exe",
         r"C:\Users\gbr bzzr\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0-full_build\bin\ffprobe.exe"),
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
            print(f"[FFMPEG] Encontrado: {ffmpeg_path}")
            return (ffmpeg_path, ffprobe_path)
    
    # Fallback para comandos simples (assume que está no PATH)
    print("[FFMPEG] ⚠️ Usando fallback 'ffmpeg'/'ffprobe' (pode não funcionar se não estiver no PATH)")
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


# ==========================
# Shopee validation pipeline
# ==========================

def ffprobe_full(path: str) -> Optional[Dict[str, Any]]:
    """Coleta metadados completos com ffprobe (streams + format) em JSON."""
    if not os.path.exists(path):
        return None
    cmd = [
        _FFPROBE_EXE,
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        path,
    ]
    code, out, err = _run(cmd)
    if code != 0:
        return None
    try:
        return json.loads(out)
    except Exception:
        return None


def analyze_video(path: str) -> Dict[str, Any]:
    """Extrai informações úteis de vídeo/áudio/container para validações.

    Retorna:
    {
        'width': int|None, 'height': int|None, 'duration': float|None,
        'vcodec': str|None, 'acodec': str|None, 'format': str|None,
        'bitrate_kbps': int|None,  # do stream de vídeo se disponível, senão do container
        'has_audio': bool,
        'fps': float|None
    }
    """
    info = {
        "width": None, "height": None, "duration": None,
        "vcodec": None, "acodec": None, "format": None,
        "bitrate_kbps": None, "has_audio": False,
        "fps": None,
    }
    data = ffprobe_full(path)
    if not data:
        return info

    # format/container
    fmt = data.get("format") or {}
    info["format"] = (fmt.get("format_name") or "").lower() or None
    try:
        # bit_rate em bits/s
        br = int(fmt.get("bit_rate")) if fmt.get("bit_rate") else None
        if br:
            info["bitrate_kbps"] = max(1, br // 1000)
    except Exception:
        pass
    try:
        if info["duration"] is None:
            info["duration"] = float(fmt.get("duration")) if fmt.get("duration") else None
    except Exception:
        pass

    # streams
    streams = data.get("streams") or []
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    if v_stream:
        info["vcodec"] = v_stream.get("codec_name")
        try:
            info["width"] = int(v_stream.get("width")) if v_stream.get("width") else None
            info["height"] = int(v_stream.get("height")) if v_stream.get("height") else None
        except Exception:
            pass
        # FPS (avg_frame_rate pode ser "30000/1001")
        try:
            afr = v_stream.get("avg_frame_rate")
            if afr and isinstance(afr, str) and "/" in afr:
                num, den = afr.split("/", 1)
                num = float(num)
                den = float(den) if float(den) != 0 else 1.0
                info["fps"] = round(num / den, 2)
            elif afr:
                info["fps"] = float(afr)
        except Exception:
            pass
        try:
            # Preferir bitrate do vídeo se presente
            br = int(v_stream.get("bit_rate")) if v_stream.get("bit_rate") else None
            if br:
                info["bitrate_kbps"] = max(1, br // 1000)
        except Exception:
            pass
        try:
            if info["duration"] is None:
                info["duration"] = float(v_stream.get("duration")) if v_stream.get("duration") else None
        except Exception:
            pass

    if a_stream:
        info["acodec"] = a_stream.get("codec_name")
        info["has_audio"] = True

    return info


def _is_vertical_9_16(width: Optional[int], height: Optional[int], tol: float = 0.03) -> bool:
    if not width or not height or height == 0:
        return False
    ratio = width / height
    target = 9 / 16
    return abs(ratio - target) <= tol


def _build_filters_to_vertical_9_16(width: int, height: int, target_min_h: int) -> str:
    """Gera filtros de crop+scale para vertical 9:16 evitando bordas pretas.
    Força exatamente target_min_h x (target_min_h * 16/9) para garantir resolução exata.
    """
    target_w = int((target_min_h * 9 / 16) / 2) * 2  # ex: 1080 -> 607.5 -> 608
    # Sempre fazer crop central para 9:16 e depois escalar para dimensões exatas
    if width / height >= 9/16:
        # Largo demais: cortar largura
        crop_w = int(math.floor((height * 9 / 16) / 2) * 2)
        crop = f"crop={crop_w}:{height}:(iw-{crop_w})/2:0"
    else:
        # Estreito demais: cortar altura
        crop_h = int(math.floor((width * 16 / 9) / 2) * 2)
        crop = f"crop={width}:{crop_h}:0:(ih-{crop_h})/2"
    # Escalar para dimensões exatas (ex: 1080x1920)
    scale = f"scale={target_w}:{target_min_h}:flags=lanczos"
    return f"{crop},{scale}"


def _ffmpeg_transcode_shopee(
    input_path: str,
    output_path: str,
    target_min_h: int,
    ensure_vertical: bool,
    target_bitrate_kbps: int,
    min_bitrate_kbps: int,
    duration: Optional[float],
    width: Optional[int],
    height: Optional[int],
    has_audio: bool,
) -> bool:
    """Transcodifica vídeo com lock para garantir processamento sequencial"""
    with _FFMPEG_LOCK:
        print(f"[FFMPEG] 🔒 Iniciando transcode: {os.path.basename(input_path)}")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        filters = []
        if width and height:
            if ensure_vertical and not _is_vertical_9_16(width, height):
                filters.append(_build_filters_to_vertical_9_16(width, height, target_min_h))
            else:
                filters.append(f"scale=-2:{target_min_h}")
        else:
            filters.append(f"scale=-2:{target_min_h}")

        # Garantir SAR 1:1
        filters.append("setsar=1:1")
        vf = ",".join(filters)

        # Duração: cortar acima de 60s; se < 3s, tentar repetir até 3s
        time_args = []
        loop_args = []
        if duration is not None:
            if duration > getattr(settings, 'VIDEO_MAX_DURATION_SECONDS', 60):
                time_args = ["-t", str(getattr(settings, 'VIDEO_MAX_DURATION_SECONDS', 60))]
            elif duration < getattr(settings, 'VIDEO_MIN_DURATION_SECONDS', 3):
                # Repetir o vídeo para atingir 3s
                needed = getattr(settings, 'VIDEO_MIN_DURATION_SECONDS', 3)
                if duration > 0:
                    loops = max(0, math.ceil(needed / duration) - 1)
                    if loops > 0:
                        loop_args = ["-stream_loop", str(loops)]

        # Audio: se não houver, usar anullsrc
        cmd = [ _FFMPEG_EXE, "-y" ]
        if loop_args:
            cmd += loop_args
        cmd += ["-i", input_path]

        if not has_audio:
            cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]

        # Mapear streams
        if not has_audio:
            # 0:v e 1:a
            map_args = ["-map", "0:v:0", "-map", "1:a:0"]
        else:
            map_args = ["-map", "0:v:0", "-map", "0:a:0?"]

        # Ajustar bitrate (garantir mínimo e aumentar buffer)
        vb = max(min_bitrate_kbps, target_bitrate_kbps)

        enc_args = [
            "-vf", vf,
            "-r", "30",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-profile:v", "high",
            "-level", "4.1",
            "-preset", "slower",  # Qualidade máxima (lento, mas melhor qualidade)
            "-crf", "18",  # Qualidade visual muito alta (menor = melhor)
            "-b:v", f"{vb}k",
            "-maxrate", f"{int(vb * 1.2)}k",  # 20% acima para picos
            "-bufsize", f"{vb*3}k",  # Buffer maior
            "-c:a", "aac",
            "-b:a", "192k",  # Áudio mais alto
            "-ac", "2",
            "-ar", "44100",
            "-movflags", "+faststart",
        ]

        cmd += map_args + enc_args + time_args + [output_path]

        print(f"[FFMPEG] Comando: {' '.join(cmd)}")
        code, out, err = _run(cmd)
        if code != 0:
            print(f"[FFMPEG] ❌ Erro (code {code}): {err[:500]}")
        else:
            print(f"[FFMPEG] ✅ Sucesso: {output_path}")
        
        print(f"[FFMPEG] 🔓 Transcode finalizado: {os.path.basename(output_path)}")
        return code == 0 and os.path.exists(output_path)


def ensure_shopee_ready(input_path: str) -> Tuple[str, Dict[str, Any]]:
    """Garante que o vídeo atenda às regras:
    - MP4 container, vídeo H.264, áudio AAC
    - Resolução >= 720p (pode usar Video2X e/ou FFmpeg)
    - Proporção vertical 9:16 (sem bordas pretas) via crop central
    - Bitrate de vídeo >= 2000 kbps (alvo configurável)
    - Duração entre 3s e 60s (corta acima, repete abaixo)

    Retorna: (output_path, report_dict)
    """
    rep: Dict[str, Any] = {"steps": []}

    # 1) Garantir altura mínima (reusa ensure_processed)
    base_out, method = ensure_processed(input_path)
    rep["steps"].append({"ensure_processed": method, "path": base_out})

    # 2) Analisar e decidir transcode
    meta = analyze_video(base_out)
    rep["probe_before"] = meta

    width = meta.get("width") or 0
    height = meta.get("height") or 0
    duration = meta.get("duration")
    vcodec = (meta.get("vcodec") or "").lower()
    acodec = (meta.get("acodec") or "").lower()
    fmt = (meta.get("format") or "").lower()
    vbitrate = meta.get("bitrate_kbps") or 0
    has_audio = bool(meta.get("has_audio"))

    needs_codec = vcodec != "h264" or acodec != "aac" or fmt.find("mp4") == -1
    needs_bitrate = vbitrate < getattr(settings, 'VIDEO_MIN_BITRATE_KBPS', 2000)
    needs_vertical = not _is_vertical_9_16(width, height, tol=0.03) if width and height else True

    if not any([needs_codec, needs_bitrate, needs_vertical]) and height >= settings.VIDEO_TARGET_MIN_HEIGHT:
        # Já atende ao padrão
        rep["final"] = base_out
        rep["changed"] = False
        return base_out, rep

    # 3) Transcode para padrão Shopee
    base = os.path.splitext(os.path.basename(base_out))[0]
    out_path = os.path.join(settings.PROCESSED_DIR, base + "_shopee.mp4")

    ok = _ffmpeg_transcode_shopee(
        base_out,
        out_path,
        target_min_h=settings.VIDEO_TARGET_MIN_HEIGHT,
        ensure_vertical=True,
        target_bitrate_kbps=getattr(settings, 'VIDEO_TARGET_BITRATE_KBPS', 3000),
        min_bitrate_kbps=getattr(settings, 'VIDEO_MIN_BITRATE_KBPS', 2000),
        duration=duration,
        width=width or None,
        height=height or None,
        has_audio=has_audio,
    )

    if not ok:
        # Como fallback extremo, tentar apenas recodificar simples
        simple_out = os.path.join(settings.PROCESSED_DIR, base + "_shopee_simple.mp4")
        cmd = [
            _FFMPEG_EXE, "-y", "-i", base_out,
            "-vf", f"scale=-2:{settings.VIDEO_TARGET_MIN_HEIGHT}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            simple_out,
        ]
        code, out, err = _run(cmd)
        if code == 0 and os.path.exists(simple_out):
            out_path = simple_out
        else:
            rep["final"] = base_out
            rep["changed"] = False
            rep["error"] = "transcode_failed"
            return base_out, rep

    def _compliant(m: Dict[str, Any]) -> bool:
        w = (m.get("width") or 0)
        h = (m.get("height") or 0)
        fps = (m.get("fps") or 0)
        vcodec = (m.get("vcodec") or "").lower()
        acodec = (m.get("acodec") or "").lower()
        fmt = (m.get("format") or "").lower()
        br = (m.get("bitrate_kbps") or 0)
        return (
            h >= settings.VIDEO_TARGET_MIN_HEIGHT and
            _is_vertical_9_16(m.get("width"), m.get("height")) and
            vcodec == "h264" and
            acodec == "aac" and
            ("mp4" in fmt) and
            br >= getattr(settings, 'VIDEO_MIN_BITRATE_KBPS', 2000) and
            abs(fps - 30.0) <= 0.5
        )

    # Verificar resultado e, se necessário, tentar uma segunda passagem mais "agressiva"
    meta_after = analyze_video(out_path)
    rep["probe_after"] = meta_after
    if not _compliant(meta_after):
        rep["steps"].append({"second_pass": True})
        stronger_out = os.path.join(settings.PROCESSED_DIR, base + "_shopee_strict.mp4")
        # Segunda passagem com bitrate maior e filtros reimpostos
        _ = _ffmpeg_transcode_shopee(
            out_path,
            stronger_out,
            target_min_h=settings.VIDEO_TARGET_MIN_HEIGHT,
            ensure_vertical=True,
            target_bitrate_kbps=max(getattr(settings, 'VIDEO_TARGET_BITRATE_KBPS', 3000), 3500),
            min_bitrate_kbps=getattr(settings, 'VIDEO_MIN_BITRATE_KBPS', 2000),
            duration=meta_after.get("duration"),
            width=meta_after.get("width"),
            height=meta_after.get("height"),
            has_audio=bool(meta_after.get("has_audio")),
        )
        # Preferir o stronger_out se existir
        if os.path.exists(stronger_out):
            out_path = stronger_out
        meta_after = analyze_video(out_path)
        rep["probe_after_strict"] = meta_after

    rep["final"] = out_path
    rep["changed"] = True
    
    # Validação final detalhada
    final_meta = analyze_video(out_path)
    final_w = final_meta.get("width") or 0
    final_h = final_meta.get("height") or 0
    final_br = final_meta.get("bitrate_kbps") or 0
    final_fps = final_meta.get("fps") or 0
    final_size_mb = os.path.getsize(out_path) / (1024 * 1024) if os.path.exists(out_path) else 0
    
    print(f"[SHOPEE] ✅ Vídeo processado com sucesso:")
    print(f"  📐 Resolução: {final_w}x{final_h}")
    print(f"  🎬 FPS: {final_fps:.1f}")
    print(f"  💾 Tamanho: {final_size_mb:.2f} MB")
    print(f"  📊 Bitrate: {final_br} kbps")
    print(f"  🎥 Codec: {final_meta.get('vcodec', 'N/A')} / {final_meta.get('acodec', 'N/A')}")
    print(f"  ✔️ Conforme padrão Shopee: {'SIM' if _compliant(final_meta) else 'QUASE (pode enviar)'}")
    
    return out_path, rep

