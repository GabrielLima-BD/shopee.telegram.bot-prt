import os
import shutil
import time
import requests
from typing import Optional, Callable

from .config import settings
from .db import (
    init_db,
    select_pending_or_failed,
    get_original_record,
    update_original_path,
    insert_or_update_processed,
    increment_retry,
)
from .video_tools import ensure_processed, ensure_shopee_ready, validate_min_height, ffprobe_media


SESSION = requests.Session()


def _download_from_url(url: str, dest_dir: str) -> Optional[str]:
    try:
        os.makedirs(dest_dir, exist_ok=True)
        # Nome baseado em timestamp com fallback
        local = os.path.join(dest_dir, str(int(time.time() * 1000)) + ".mp4")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Referer": "https://shopee.com.br/",
        }
        with SESSION.get(url, stream=True, timeout=90, headers=headers) as r:
            r.raise_for_status()
            with open(local, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return local
    except Exception as e:
        print(f"[DL] erro: {e}")
        return None


def _download_from_telegram_file_id(file_id: str, dest_dir: str) -> Optional[str]:
    # API getFile
    try:
        os.makedirs(dest_dir, exist_ok=True)
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            print("[DL] token não configurado para download do Telegram.")
            return None
        url = f"https://api.telegram.org/bot{token}/getFile"
        resp = SESSION.get(url, params={"file_id": file_id}, timeout=30)
        data = resp.json()
        if not data.get("ok"):
            print("[DL] getFile falhou")
            return None
        file_path = data["result"]["file_path"]
        # download do arquivo - NÃO logar a URL completa
        file_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
        local = os.path.join(dest_dir, os.path.basename(file_path))
        with SESSION.get(file_url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(local, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return local
    except Exception as e:
        print(f"[DL] erro TG: {e}")
        return None


def _send_to_telegram(video_path: str, caption: Optional[str] = None) -> tuple[bool, Optional[str]]:
    try:
        # Escolher token/chat de envio de acordo com a seleção (Gabriel or Marli)
        # Uso getattr para evitar AttributeError caso variáveis específicas não existam
        target = str(getattr(settings, "SELECTED_SEND_TARGET", "Gabriel"))
        if target.strip().lower() == "marli":
            token = getattr(settings, "TELEGRAM_SEND_TOKEN_MARLI", "") or getattr(settings, "TELEGRAM_SEND_TOKEN", "")
            chat_id = getattr(settings, "TELEGRAM_CHAT_ID_MARLI", "") or getattr(settings, "TELEGRAM_CHAT_ID", "")
        else:
            # Gabriel por padrão. Usar token de envio específico do Gabriel primeiro,
            # depois fallback para token genérico ou token do bot.
            token = getattr(settings, "TELEGRAM_SEND_TOKEN_GABRIEL", "") or getattr(settings, "TELEGRAM_SEND_TOKEN", "") or getattr(settings, "TELEGRAM_BOT_TOKEN", "")
            chat_id = getattr(settings, "TELEGRAM_CHAT_ID_GABRIEL", "") or getattr(settings, "TELEGRAM_CHAT_ID", "")
        
        # Debug detalhado
        print(f"[SEND] Iniciando envio...")
        print(f"[SEND] Vídeo: {video_path}")
        size_mb = os.path.getsize(video_path) / (1024*1024)
        print(f"[SEND] Tamanho: {size_mb:.2f} MB")
        print(f"[SEND] Token configurado: {'SIM' if token else 'NÃO'} (target={target})")
        print(f"[SEND] Chat ID: {chat_id if chat_id else 'NÃO CONFIGURADO'}")
        
        if not token or not chat_id:
            err = "token/chat_id não configurados"
            print(f"[SEND] ❌ ERRO: {err}.")
            return False, err

        # Limite comum do Bot API para upload direto é ~50MB; avisar cedo
        if size_mb > 49.5:
            err = f"arquivo muito grande ({size_mb:.2f} MB) > 50MB"
            print(f"[SEND] ❌ ERRO: {err}")
            return False, err
        
        url = f"https://api.telegram.org/bot{token}/sendVideo"
        print(f"[SEND] URL: https://api.telegram.org/bot...{token[-10:]}/sendVideo")
        
        with open(video_path, "rb") as f:
            files = {"video": (os.path.basename(video_path), f, "video/mp4")}
            data = {"chat_id": chat_id, "caption": caption or ""}
            
            print(f"[SEND] Caption: {caption[:50] if caption else 'vazio'}...")
            print(f"[SEND] Fazendo POST para Telegram API...")
            
            r = SESSION.post(url, data=data, files=files, timeout=180)
            
            print(f"[SEND] Status Code: {r.status_code}")
            
            if r.status_code == 200:
                json_response = r.json()
                if json_response.get("ok"):
                    msg_id = json_response.get("result", {}).get("message_id")
                    print(f"[SEND] ✅ Enviado com sucesso! Message ID: {msg_id}")
                    return True, None
                else:
                    print(f"[SEND] ❌ Telegram retornou ok=false")
                    print(f"[SEND] Response: {json_response}")
                    # Capturar descrição de erro se existir
                    err = json_response.get('description') or 'ok=false'
                    return False, err
            else:
                print(f"[SEND] ❌ Erro HTTP {r.status_code}")
                print(f"[SEND] Response: {r.text[:200]}")
                err = f"HTTP {r.status_code}: {r.text[:180]}"
                return False, err
    except Exception as e:
        print(f"[SEND] ❌ Exceção: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False, f"{type(e).__name__}: {e}"


def _process_record(record_id: int, progress_cb: Optional[Callable[[int, str, str], None]] = None):
    rec = get_original_record(record_id)
    if not rec:
        return

    original_path = rec["original_path"] if "original_path" in rec.keys() else None
    source_type = rec["source_type"] if "source_type" in rec.keys() else None
    source_url = rec["source_url"] if "source_url" in rec.keys() else None
    telegram_file_id = rec["telegram_file_id"] if "telegram_file_id" in rec.keys() else None
    link_produto = rec["link_produto"] if "link_produto" in rec.keys() else None
    descricao = rec["descricao"] if "descricao" in rec.keys() else None

    # ONLY_* flags
    if settings.ONLY_DOWNLOAD:
        if not original_path:
            path = None
            if source_type == "url" and source_url:
                path = _download_from_url(source_url, settings.DOWNLOAD_DIR)
            elif source_type == "telegram" and telegram_file_id:
                path = _download_from_telegram_file_id(telegram_file_id, settings.DOWNLOAD_DIR)
            if path:
                update_original_path(record_id, path)
                w, h, d, s = ffprobe_media(path)
                insert_or_update_processed(record_id, None, "pending", None, (w, h, d, s), link_produto, descricao)
                print(f"[DL] ok: {path}")
            else:
                insert_or_update_processed(record_id, None, "failed", "download_failed", (None, None, None, None), link_produto, descricao)
                increment_retry(record_id)
        return

    # Baixar se necessário
    if not original_path:
        print("[DL] iniciando download...")
        if progress_cb:
            progress_cb(record_id, "download", "start")
        if source_type == "url" and source_url:
            original_path = _download_from_url(source_url, settings.DOWNLOAD_DIR)
        elif source_type == "telegram" and telegram_file_id:
            original_path = _download_from_telegram_file_id(telegram_file_id, settings.DOWNLOAD_DIR)
        if original_path:
            update_original_path(record_id, original_path)
            w, h, d, s = ffprobe_media(original_path)
            insert_or_update_processed(record_id, None, "pending", None, (w, h, d, s), link_produto, descricao)
            print(f"[DL] ok: {original_path}")
            if progress_cb:
                progress_cb(record_id, "download", "ok")
        else:
            insert_or_update_processed(record_id, None, "failed", "download_failed", (None, None, None, None), link_produto, descricao)
            increment_retry(record_id)
            if progress_cb:
                progress_cb(record_id, "download", "fail")
            return

    if settings.ONLY_VALIDATE:
        ok = validate_min_height(original_path, settings.VIDEO_TARGET_MIN_HEIGHT)
        print(f"[VAL] {'ok' if ok else 'baixo'}")
        return

    # Processamento
    if not settings.ONLY_SEND:
        if progress_cb:
            progress_cb(record_id, "process", "start")
        processed_path, report = ensure_shopee_ready(original_path)
        changed = report.get("changed")
        print(f"[PROC] Shopee-ready | alterado={changed}; arquivo={os.path.basename(processed_path)}")
        if progress_cb:
            progress_cb(record_id, "process", "ok")
    else:
        processed_path = original_path
        # mantido comportamento de pular processamento

    # Validação (apenas loga; envio não será bloqueado por altura)
    ok = validate_min_height(processed_path, settings.VIDEO_TARGET_MIN_HEIGHT)
    print(f"[VAL] height >= {settings.VIDEO_TARGET_MIN_HEIGHT}? {'sim' if ok else 'não'}")

    # Enviar
    if progress_cb:
        progress_cb(record_id, "send", "start")
    
    # Obter resolução final do vídeo
    w, h, d, s = ffprobe_media(processed_path)
    resolution_text = f"{h}p" if h else "N/A"
    
    # Monta caption com descrição e resolução
    caption_parts = []
    if descricao:
        caption_parts.append(f"{descricao} | {resolution_text}")
    else:
        caption_parts.append(resolution_text)
    
    if link_produto:
        caption_parts.append(str(link_produto))
    
    caption = "\n\n".join(caption_parts) if caption_parts else ""
    sent, send_err = _send_to_telegram(processed_path, caption=caption)
    print(f"[SEND] {'ok' if sent else 'erro'}")
    if not sent and send_err:
        print(f"[SEND] Motivo da falha: {send_err}")
    if progress_cb:
        progress_cb(record_id, "send", "ok" if sent else "fail")

    # Atualizar status
    status = "processed" if sent else "failed"
    err = None if sent else (send_err or "send_failed")
    insert_or_update_processed(record_id, processed_path, status, err, (w, h, d, s), link_produto, descricao)
    if not sent:
        increment_retry(record_id)
    print(f"[DONE] {status} (retries atualizado se falha)")


def process_all_videos(progress_cb: Optional[Callable[[int, str, str], None]] = None):
    init_db()
    rows = select_pending_or_failed(settings.RETRY_FAILED_ONLY)
    ids = [r[0] for r in rows]
    for rid in ids:
        try:
            _process_record(rid, progress_cb=progress_cb)
        except Exception as e:
            print(f"[ERR] id={rid} exceção: {e}")
            increment_retry(rid)

