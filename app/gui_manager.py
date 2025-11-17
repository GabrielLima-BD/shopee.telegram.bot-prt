import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
from typing import Optional
import sqlite3

from .config import settings
from .simple_processor import process_all_videos, _process_record
from .db import init_db, insert_original, select_pending_or_failed, get_original_record, get_conn
from .bot_ingest import run_bot_asyncio


class LogTerminal:
    """Terminal de logs integrado na GUI"""
    def __init__(self, text_widget: scrolledtext.ScrolledText):
        self.widget = text_widget
        self.stats = {
            "baixados": 0,
            "processados": 0,
            "enviados": 0,
            "falhas": 0
        }
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "INFO": "#00d4ff",      # Azul ciano brilhante
            "SUCCESS": "#00ff88",    # Verde brilhante
            "ERROR": "#ff3366",      # Vermelho brilhante
            "WARNING": "#ffaa00",    # Laranja brilhante
            "PROCESSING": "#aa88ff"  # Roxo brilhante
        }
        
        self.widget.configure(state='normal')
        self.widget.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.widget.insert(tk.END, f"{message}\n", level.lower())
        self.widget.see(tk.END)
        self.widget.configure(state='disabled')
        
        # Configurar tags de cores com fonte maior
        self.widget.tag_config("timestamp", foreground="#888888", font=("Consolas", 10, "bold"))
        for tag, color in color_map.items():
            self.widget.tag_config(tag.lower(), foreground=color, font=("Consolas", 10))
    
    def update_stats(self, baixados=0, processados=0, enviados=0, falhas=0):
        if baixados: self.stats["baixados"] += baixados
        if processados: self.stats["processados"] += processados
        if enviados: self.stats["enviados"] += enviados
        if falhas: self.stats["falhas"] += falhas
        
        stats_msg = f"📊 Estatísticas: {self.stats['baixados']} baixados | {self.stats['processados']} processados | {self.stats['enviados']} enviados | {self.stats['falhas']} falhas"
        self.log(stats_msg, "INFO")
    
    def clear(self):
        self.widget.configure(state='normal')
        self.widget.delete(1.0, tk.END)
        self.widget.configure(state='disabled')


class VideoFormWindow:
    """Janela modal para adicionar/editar vídeos"""
    def __init__(self, parent, log_terminal: LogTerminal, current_id: int = 1):
        self.window = tk.Toplevel(parent)
        self.window.title("Gerenciar Vídeos")
        self.window.geometry("850x650")  # Aumentado
        self.window.configure(bg="#1e1e1e")  # Tema escuro
        self.window.transient(parent)
        # Removido grab_set() para permitir minimizar
        
        self.log_terminal = log_terminal
        self.current_id = current_id
        self.video_entries = []
        self._entry_by_db_id = {}
        
        self._build_ui()
    
    def _build_ui(self):
        # Frame principal com scroll
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Estilo para tema escuro
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TFrame', background='#1e1e1e')
        style.configure('Dark.TLabel', background='#1e1e1e', foreground='#ffffff')
        style.configure('Dark.TLabelframe', background='#2d2d2d', foreground='#ffffff', bordercolor='#444444')
        style.configure('Dark.TLabelframe.Label', background='#2d2d2d', foreground='#00d4ff', font=('Arial', 10, 'bold'))
        style.configure('Dark.TButton', background='#3d3d3d', foreground='#ffffff', bordercolor='#555555')
        style.map('Dark.TButton', background=[('active', '#4d4d4d')])
        
        main_frame.configure(style='Dark.TFrame')
        
        # Canvas + Scrollbar para múltiplos vídeos
        canvas = tk.Canvas(main_frame, bg="#1e1e1e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style='Dark.TFrame')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Habilitar scroll com mouse wheel e touchpad
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_mousewheel)
        canvas.bind('<Leave>', _unbind_mousewheel)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Adicionar primeiro formulário
        self._add_video_form()
        
        # Frame de botões (aumentado e reorganizado)
        btn_frame = ttk.Frame(self.window, padding=15, style='Dark.TFrame')
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Linha 1 de botões
        btn_row1 = ttk.Frame(btn_frame, style='Dark.TFrame')
        btn_row1.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Button(btn_row1, text="➕ Adicionar Mais 1", command=self._add_video_form, style='Dark.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_row1, text="➕➕ Adicionar Vários", command=self._add_multiple_forms, style='Dark.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_row1, text="▶️ Processar Todos", command=self._processar_todos, style='Dark.TButton').pack(side=tk.LEFT, padx=5)
        
        # Linha 2 de botões
        btn_row2 = ttk.Frame(btn_frame, style='Dark.TFrame')
        btn_row2.pack(fill=tk.X)
        
        ttk.Button(btn_row2, text="⏭️ Processar por Etapas", command=self._processar_etapas, style='Dark.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_row2, text="⚠️ Ver Falhas", command=self._ver_falhas, style='Dark.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_row2, text="🔄 Reprocessar Falhas", command=self._mandar_falhas, style='Dark.TButton').pack(side=tk.LEFT, padx=5)
        
        # Botões de controle da janela (direita)
        ttk.Button(btn_row2, text="🗕 Minimizar", command=self.window.iconify, style='Dark.TButton').pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_row2, text="❌ Fechar", command=self.window.destroy, style='Dark.TButton').pack(side=tk.RIGHT, padx=5)
    
    def _add_video_form(self):
        frame = ttk.LabelFrame(self.scrollable_frame, text=f"Vídeo ID: {self.current_id}", padding=10, style='Dark.TLabelframe')
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Configurar grid com 3 colunas principais
        frame.columnconfigure(1, weight=1)
        
        # Link do vídeo MP4
        ttk.Label(frame, text="🎬 Link do Vídeo (.mp4):", style='Dark.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        video_link = ttk.Entry(frame, width=60, font=("Arial", 10))
        video_link.grid(row=0, column=1, pady=5, padx=5, sticky=tk.EW)
        
        # Link do produto
        ttk.Label(frame, text="🛒 Link do Produto:", style='Dark.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        produto_link = ttk.Entry(frame, width=60, font=("Arial", 10))
        produto_link.grid(row=1, column=1, pady=5, padx=5, sticky=tk.EW)
        
        # Descrição (uma linha apenas)
        ttk.Label(frame, text="📝 Descrição:", style='Dark.TLabel').grid(row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        descricao = ttk.Entry(frame, width=60, font=("Arial", 10))
        descricao.grid(row=2, column=1, pady=5, padx=5, sticky=tk.EW)
        
        # Frame de status ao lado direito
        status_frame = ttk.Frame(frame, style='Dark.TFrame')
        status_frame.grid(row=0, column=2, rowspan=3, padx=(15, 0), sticky=tk.N)
        
        # Indicadores de etapa em linha vertical compacta
        lbl_download_icon = ttk.Label(status_frame, text="📥", style='Dark.TLabel', font=("Arial", 12))
        lbl_download_icon.grid(row=0, column=0, sticky=tk.W, pady=2)
        lbl_download = ttk.Label(status_frame, text="◻️", style='Dark.TLabel', font=("Arial", 14))
        lbl_download.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        lbl_process_icon = ttk.Label(status_frame, text="🛠️", style='Dark.TLabel', font=("Arial", 12))
        lbl_process_icon.grid(row=1, column=0, sticky=tk.W, pady=2)
        lbl_process = ttk.Label(status_frame, text="◻️", style='Dark.TLabel', font=("Arial", 14))
        lbl_process.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        lbl_send_icon = ttk.Label(status_frame, text="📤", style='Dark.TLabel', font=("Arial", 12))
        lbl_send_icon.grid(row=2, column=0, sticky=tk.W, pady=2)
        lbl_send = ttk.Label(status_frame, text="◻️", style='Dark.TLabel', font=("Arial", 14))
        lbl_send.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # Botão Retry compacto
        retry_btn = ttk.Button(status_frame, text="↻", width=3, style='Dark.TButton')
        retry_btn.grid(row=3, column=0, columnspan=2, pady=(8, 0), sticky=tk.EW)
        try:
            retry_btn.state(["disabled"])  # só habilita quando falhar
        except Exception:
            pass

        self.video_entries.append({
            "id": self.current_id,
            "frame": frame,
            "video_link": video_link,
            "produto_link": produto_link,
            "descricao": descricao,
            "lbl_download": lbl_download,
            "lbl_process": lbl_process,
            "lbl_send": lbl_send,
            "retry_btn": retry_btn,
            "db_id": None,
        })

        # Ligar retry ao item
        entry_ref = self.video_entries[-1]
        retry_btn.configure(command=lambda e=entry_ref: self._retry_entry(e))

        self.current_id += 1
    
    def _add_multiple_forms(self):
        """Adicionar múltiplos formulários de uma vez"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Adicionar Vários Cards")
        dialog.geometry("350x150")
        dialog.configure(bg="#1e1e1e")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Centralizar dialog
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - dialog.winfo_width()) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding=20, style='Dark.TFrame')
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Quantos cards deseja adicionar?", font=("Arial", 12), style='Dark.TLabel').pack(pady=(0, 15))
        
        quantity_var = tk.IntVar(value=5)
        spin = ttk.Spinbox(frame, from_=1, to=100, textvariable=quantity_var, width=15, font=("Arial", 12))
        spin.pack(pady=(0, 15))
        
        def add_cards():
            count = quantity_var.get()
            for _ in range(count):
                self._add_video_form()
            dialog.destroy()
        
        btn_frame = ttk.Frame(frame, style='Dark.TFrame')
        btn_frame.pack()
        
        ttk.Button(btn_frame, text="✅ Adicionar", command=add_cards, style='Dark.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", command=dialog.destroy, style='Dark.TButton').pack(side=tk.LEFT, padx=5)
    
    def _processar_todos(self):
        """Salvar todos os vídeos no banco e processar"""
        if not self.video_entries:
            messagebox.showwarning("Aviso", "Nenhum vídeo para processar!")
            return
        
        self.log_terminal.log("=== INICIANDO PROCESSAMENTO DE TODOS OS VÍDEOS ===", "PROCESSING")
        
        ids_inseridos = []
        videos_validos = 0
        for idx, entry in enumerate(self.video_entries, 1):
            video_link = entry["video_link"].get().strip()
            produto_link = entry["produto_link"].get().strip()
            descricao = entry["descricao"].get().strip()
            
            self.log_terminal.log(f"📝 Verificando Vídeo {idx}: link='{video_link[:50]}...' (len={len(video_link)})", "INFO")
            
            # Validar: pelo menos o link do vídeo deve estar preenchido
            if not video_link:
                self.log_terminal.log(f"⚠️ Vídeo {idx} está vazio, pulando...", "WARNING")
                continue
            
            videos_validos += 1
            try:
                rec_id = insert_original(
                    source_type="url",
                    source_url=video_link,
                    telegram_file_id=None,
                    original_path=None,
                    link_produto=produto_link if produto_link else None,
                    descricao=descricao if descricao else None
                )
                ids_inseridos.append(rec_id)
                # Mapear entry <-> id do banco para atualizar UI por callbacks
                entry["db_id"] = rec_id
                self._entry_by_db_id[rec_id] = entry
                self.log_terminal.log(f"✅ Vídeo ID {rec_id} adicionado à fila", "SUCCESS")
            except Exception as e:
                self.log_terminal.log(f"❌ Erro ao adicionar vídeo {idx}: {e}", "ERROR")
        
        self.log_terminal.log(f"📊 Total verificado: {len(self.video_entries)} | Válidos: {videos_validos} | Inseridos: {len(ids_inseridos)}", "INFO")
        
        if ids_inseridos:
            # Processar em thread separada mantendo a janela aberta
            threading.Thread(target=self._process_videos_thread, args=(ids_inseridos,), daemon=True).start()
        else:
            messagebox.showwarning("Aviso", f"Nenhum vídeo foi adicionado!\n\nTotal verificado: {len(self.video_entries)}\nVálidos encontrados: {videos_validos}\n\nVerifique os logs para mais detalhes.")
    
    def _process_videos_thread(self, ids: list):
        """Processar vídeos em background com logs detalhados"""
        for vid_id in ids:
            try:
                self.log_terminal.log(f"🔄 Processando ID {vid_id}...", "PROCESSING")
                
                # Etapa 1: Download
                self.log_terminal.log(f"  📥 [ID {vid_id}] Iniciando download...", "INFO")
                rec = get_original_record(vid_id)
                if not rec:
                    self.log_terminal.log(f"  ❌ [ID {vid_id}] Registro não encontrado!", "ERROR")
                    self.log_terminal.update_stats(falhas=1)
                    continue
                
                # Callback de progresso -> atualiza ícones
                def progress_cb(record_id: int, stage: str, status: str):
                    self._progress_ui(record_id, stage, status)

                # Processar o registro completo
                try:
                    _process_record(vid_id, progress_cb=progress_cb)
                    
                    # Pequeno delay para garantir que o banco foi atualizado
                    import time
                    time.sleep(0.2)
                    
                    # Verificar se realmente foi enviado checando o status no banco
                    from .config import settings
                    import sqlite3
                    db_conn = sqlite3.connect(settings.DB_PROCESSADOS_PATH)
                    cursor = db_conn.cursor()
                    cursor.execute("SELECT status, error_message FROM videos_processados WHERE id = ?", (vid_id,))
                    result = cursor.fetchone()
                    db_conn.close()
                    
                    if result and result[0] == "processed":
                        self.log_terminal.log(f"  ✅ [ID {vid_id}] Processamento concluído com sucesso!", "SUCCESS")
                        self.log_terminal.update_stats(baixados=1, processados=1, enviados=1)
                    else:
                        status_txt = result[0] if result else 'desconhecido'
                        err_txt = result[1] if result and len(result) > 1 and result[1] else 'sem detalhe'
                        self.log_terminal.log(f"  ⚠️ [ID {vid_id}] Status final: {status_txt} | Erro: {err_txt if err_txt else 'nenhum'}", "WARNING")
                        self.log_terminal.update_stats(baixados=1, processados=1, falhas=1)
                        
                except Exception as e:
                    self.log_terminal.log(f"  ❌ [ID {vid_id}] Falha: {str(e)}", "ERROR")
                    self.log_terminal.update_stats(falhas=1)
                    
            except Exception as e:
                self.log_terminal.log(f"❌ Erro geral no ID {vid_id}: {e}", "ERROR")
                self.log_terminal.update_stats(falhas=1)
        
        self.log_terminal.log("=== PROCESSAMENTO FINALIZADO ===", "SUCCESS")
    
    def _process_by_stages_thread(self, ids: list):
        """Processar por etapas: 1) Baixar todos → 2) Processar todos → 3) Enviar todos"""
        from .video_tools import ensure_shopee_ready, validate_min_height, ffprobe_media
        from .db import update_original_path, insert_or_update_processed, increment_retry
        
        self.log_terminal.log("=== ETAPA 1: BAIXANDO TODOS OS VÍDEOS ===", "PROCESSING")
        
        # Callback de progresso
        def progress_cb(record_id: int, stage: str, status: str):
            self._progress_ui(record_id, stage, status)
        
        # ETAPA 1: Baixar todos
        downloaded = {}
        for vid_id in ids:
            try:
                progress_cb(vid_id, "download", "start")
                rec = get_original_record(vid_id)
                if not rec:
                    self.log_terminal.log(f"❌ ID {vid_id} não encontrado", "ERROR")
                    progress_cb(vid_id, "download", "fail")
                    continue
                
                source_type = rec["source_type"] if "source_type" in rec.keys() else None
                source_url = rec["source_url"] if "source_url" in rec.keys() else None
                telegram_file_id = rec["telegram_file_id"] if "telegram_file_id" in rec.keys() else None
                link_produto = rec["link_produto"] if "link_produto" in rec.keys() else None
                descricao = rec["descricao"] if "descricao" in rec.keys() else None
                
                # Baixar
                from .simple_processor import _download_from_url, _download_from_telegram_file_id
                original_path = None
                if source_type == "url" and source_url:
                    original_path = _download_from_url(source_url, settings.DOWNLOAD_DIR)
                elif source_type == "telegram" and telegram_file_id:
                    original_path = _download_from_telegram_file_id(telegram_file_id, settings.DOWNLOAD_DIR)
                
                if original_path:
                    update_original_path(vid_id, original_path)
                    w, h, d, s = ffprobe_media(original_path)
                    insert_or_update_processed(vid_id, None, "pending", None, (w, h, d, s), link_produto, descricao)
                    downloaded[vid_id] = {"path": original_path, "link_produto": link_produto, "descricao": descricao}
                    self.log_terminal.log(f"✅ ID {vid_id} baixado", "SUCCESS")
                    progress_cb(vid_id, "download", "ok")
                else:
                    self.log_terminal.log(f"❌ Falha no download do ID {vid_id}", "ERROR")
                    insert_or_update_processed(vid_id, None, "failed", "download_failed", (None, None, None, None), link_produto, descricao)
                    increment_retry(vid_id)
                    progress_cb(vid_id, "download", "fail")
            except Exception as e:
                self.log_terminal.log(f"❌ Erro no download ID {vid_id}: {e}", "ERROR")
                progress_cb(vid_id, "download", "fail")
        
        self.log_terminal.log(f"=== ETAPA 2: PROCESSANDO {len(downloaded)} VÍDEOS ===", "PROCESSING")
        
        # ETAPA 2: Processar todos
        processed = {}
        for vid_id, data in downloaded.items():
            try:
                progress_cb(vid_id, "process", "start")
                processed_path, report = ensure_shopee_ready(data["path"])
                ok = validate_min_height(processed_path, settings.VIDEO_TARGET_MIN_HEIGHT)

                w, h, d, s = ffprobe_media(processed_path)
                insert_or_update_processed(vid_id, processed_path, "pending", None, (w, h, d, s), data["link_produto"], data["descricao"])
                processed[vid_id] = {"path": processed_path, "link_produto": data["link_produto"], "descricao": data["descricao"]}
                if ok:
                    self.log_terminal.log(f"✅ ID {vid_id} processado (Shopee-ready)", "SUCCESS")
                else:
                    self.log_terminal.log(f"⚠️ ID {vid_id} processado, mas ainda abaixo de {settings.VIDEO_TARGET_MIN_HEIGHT}p (envio permitido)", "WARNING")
                progress_cb(vid_id, "process", "ok")
            except Exception as e:
                self.log_terminal.log(f"❌ Erro no processamento ID {vid_id}: {e}", "ERROR")
                progress_cb(vid_id, "process", "fail")
        
        self.log_terminal.log(f"=== ETAPA 3: ENVIANDO {len(processed)} VÍDEOS ===", "PROCESSING")
        
        # ETAPA 3: Enviar todos
        for vid_id, data in processed.items():
            try:
                progress_cb(vid_id, "send", "start")
                
                # Obter resolução do vídeo processado
                w, h, d, s = ffprobe_media(data["path"])
                resolution_text = f"{h}p" if h else "N/A"
                
                # Montar caption com descrição + resolução, depois link do produto
                caption_parts = []
                if data["descricao"]:
                    caption_parts.append(f"{data['descricao']} | {resolution_text}")
                else:
                    caption_parts.append(resolution_text)
                
                if data["link_produto"]:
                    caption_parts.append(str(data["link_produto"]))
                
                caption = "\n\n".join(caption_parts) if caption_parts else ""
                
                from .simple_processor import _send_to_telegram
                sent_ok, err = _send_to_telegram(data["path"], caption=caption)
                
                if sent_ok:
                    insert_or_update_processed(vid_id, data["path"], "processed", None, (w, h, d, s), data["link_produto"], data["descricao"])
                    self.log_terminal.log(f"✅ ID {vid_id} enviado", "SUCCESS")
                    progress_cb(vid_id, "send", "ok")
                    self.log_terminal.update_stats(enviados=1)
                else:
                    insert_or_update_processed(vid_id, data["path"], "failed", err or "send_failed", (None, None, None, None), data["link_produto"], data["descricao"])
                    increment_retry(vid_id)
                    self.log_terminal.log(f"❌ Falha no envio do ID {vid_id}", "ERROR")
                    progress_cb(vid_id, "send", "fail")
            except Exception as e:
                self.log_terminal.log(f"❌ Erro no envio ID {vid_id}: {e}", "ERROR")
                progress_cb(vid_id, "send", "fail")
        
        self.log_terminal.log("=== PROCESSAMENTO POR ETAPAS FINALIZADO ===", "SUCCESS")
    
    def _processar_etapas(self):
        if not self.video_entries:
            messagebox.showwarning("Aviso", "Nenhum vídeo para adicionar!")
            return
        
        self.log_terminal.log("=== PROCESSAMENTO POR ETAPAS INICIADO ===", "PROCESSING")
        
        ids_inseridos = []
        videos_validos = 0
        for idx, entry in enumerate(self.video_entries, 1):
            video_link = entry["video_link"].get().strip()
            produto_link = entry["produto_link"].get().strip()
            descricao = entry["descricao"].get().strip()
            
            if not video_link:
                self.log_terminal.log(f"⚠️ Vídeo {idx} está vazio, pulando...", "WARNING")
                continue
            
            videos_validos += 1
            try:
                rec_id = insert_original(
                    source_type="url",
                    source_url=video_link,
                    telegram_file_id=None,
                    original_path=None,
                    link_produto=produto_link if produto_link else None,
                    descricao=descricao if descricao else None
                )
                ids_inseridos.append(rec_id)
                entry["db_id"] = rec_id
                self._entry_by_db_id[rec_id] = entry
                self.log_terminal.log(f"✅ Vídeo ID {rec_id} adicionado à fila", "SUCCESS")
            except Exception as e:
                self.log_terminal.log(f"❌ Erro ao adicionar vídeo {idx}: {e}", "ERROR")
        
        if ids_inseridos:
            threading.Thread(target=self._process_by_stages_thread, args=(ids_inseridos,), daemon=True).start()
        else:
            messagebox.showwarning("Aviso", f"Nenhum vídeo foi adicionado!\n\nTotal verificado: {len(self.video_entries)}\nVálidos encontrados: {videos_validos}")
    
    def _ver_falhas(self):
        """Mostrar vídeos que falharam"""
        from .db import get_conn
        import sqlite3
        
        try:
            with get_conn() as con:
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                cur.execute("SELECT id, source_url, error_message, retries FROM videos WHERE status='failed'")
                falhas = cur.fetchall()
            
            if not falhas:
                messagebox.showinfo("Falhas", "Nenhuma falha registrada! 🎉")
                return
            
            # Mostrar janela com lista de falhas
            falhas_win = tk.Toplevel(self.window)
            falhas_win.title("Vídeos com Falha")
            falhas_win.geometry("800x400")
            
            text = scrolledtext.ScrolledText(falhas_win, width=90, height=20)
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            for f in falhas:
                text.insert(tk.END, f"ID: {f['id']} | Tentativas: {f['retries']}\n")
                text.insert(tk.END, f"URL: {f['source_url']}\n")
                text.insert(tk.END, f"Erro: {f['error_message']}\n")
                text.insert(tk.END, "-" * 80 + "\n\n")
            
            text.configure(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar falhas: {e}")
    
    def _mandar_falhas(self):
        """Reprocessar vídeos que falharam"""
        import os
        self.log_terminal.log("🔄 Reprocessando vídeos com falha...", "PROCESSING")
        
        def reprocess():
            try:
                os.environ["RETRY_FAILED_ONLY"] = "true"
                process_all_videos()
                self.log_terminal.log("✅ Reprocessamento de falhas concluído!", "SUCCESS")
            except Exception as e:
                self.log_terminal.log(f"❌ Erro ao reprocessar falhas: {e}", "ERROR")
            finally:
                if "RETRY_FAILED_ONLY" in os.environ:
                    del os.environ["RETRY_FAILED_ONLY"]
        
        threading.Thread(target=reprocess, daemon=True).start()

    def _progress_ui(self, record_id: int, stage: str, status: str):
        """Atualiza os ícones de status por etapa na thread da UI."""
        def _set():
            entry = self._entry_by_db_id.get(record_id)
            if not entry:
                return
            icon = "⏳" if status == "start" else ("✅" if status == "ok" else "❌")
            if stage == "download":
                entry["lbl_download"].config(text=icon)
            elif stage == "process":
                entry["lbl_process"].config(text=icon)
            elif stage == "send":
                entry["lbl_send"].config(text=icon)
                if status == "fail":
                    try:
                        entry["retry_btn"].state(["!disabled"])
                    except Exception:
                        pass
            # Se todas etapas OK, desabilitar retry
            if (entry["lbl_download"].cget("text") == "✅" and
                entry["lbl_process"].cget("text") == "✅" and
                entry["lbl_send"].cget("text") == "✅"):
                try:
                    entry["retry_btn"].state(["disabled"])
                except Exception:
                    pass
        try:
            self.window.after(0, _set)
        except Exception:
            pass

    def _retry_entry(self, entry: dict):
        """Reprocessar um único item ao clicar no botão Retry."""
        db_id = entry.get("db_id")
        if not db_id:
            messagebox.showwarning("Aviso", "Este item ainda não foi inserido no banco.")
            return
        # Resetar ícones
        entry["lbl_download"].config(text="◻️")
        entry["lbl_process"].config(text="◻️")
        entry["lbl_send"].config(text="◻️")
        try:
            entry["retry_btn"].state(["disabled"])  # desabilitar enquanto processa
        except Exception:
            pass
        
        def run_one():
            try:
                self.log_terminal.log(f"↻ Reprocessando ID {db_id}...", "PROCESSING")
                _process_record(db_id, progress_cb=lambda rid, stg, sts: self._progress_ui(rid, stg, sts))
                self.log_terminal.log(f"✅ Reprocessamento do ID {db_id} concluído.", "SUCCESS")
            except Exception as e:
                self.log_terminal.log(f"❌ Falha ao reprocessar ID {db_id}: {e}", "ERROR")
                try:
                    entry["retry_btn"].state(["!disabled"])
                except Exception:
                    pass
        threading.Thread(target=run_one, daemon=True).start()


class DatabaseViewerWindow:
    """Janela para visualizar e gerenciar banco de dados"""
    def __init__(self, parent, db_name: str, log_terminal: LogTerminal):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Gerenciar Banco de Dados - {db_name}")
        self.window.geometry("1100x700")
        self.window.configure(bg="#1e1e1e")
        self.window.transient(parent)
        
        self.db_name = db_name
        self.log_terminal = log_terminal
        self.is_dual = settings.USE_DUAL_DATABASES
        
        self._build_ui()
        self._load_data()
    
    def _build_ui(self):
        # Estilo
        style = ttk.Style()
        style.configure('DB.Treeview', background='#2d2d2d', foreground='#ffffff', fieldbackground='#2d2d2d', font=('Arial', 9))
        style.configure('DB.Treeview.Heading', background='#1a1a1a', foreground='#00d4ff', font=('Arial', 10, 'bold'))
        style.map('DB.Treeview', background=[('selected', '#00d4ff')], foreground=[('selected', '#000000')])
        
        # Frame principal
        main_frame = ttk.Frame(self.window, padding=15, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text=f"📊 {self.db_name}",
            font=("Arial", 18, "bold"),
            foreground="#00d4ff",
            background="#1e1e1e"
        )
        title_label.pack(pady=(0, 15))
        
        # Frame da tabela
        table_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        
        # Treeview (tabela)
        if self.db_name == "Banco de Vídeos Originais":
            columns = ("ID", "Tipo", "URL/File ID", "Path", "Link Produto", "Descrição", "Data")
        elif self.db_name == "Banco de Vídeos Processados":
            columns = ("ID", "ID Ref", "Path", "Status", "Retries", "Erro", "Resolução", "Data")
        else:  # Banco único
            columns = ("ID", "URL", "Path Original", "Path Processado", "Status", "Retries", "Link Produto", "Data")
        
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='tree headings',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style='DB.Treeview',
            height=20
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configurar colunas
        self.tree.column("#0", width=0, stretch=tk.NO)
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "ID" or col == "ID Ref" or col == "Retries":
                self.tree.column(col, width=60, anchor=tk.CENTER)
            elif col == "Resolução":
                self.tree.column(col, width=100, anchor=tk.CENTER)
            elif col == "Status":
                self.tree.column(col, width=100, anchor=tk.CENTER)
            elif col == "Descrição" or col == "Erro":
                self.tree.column(col, width=200)
            else:
                self.tree.column(col, width=150)
        
        # Pack scrollbars e treeview
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Contador de registros
        self.count_label = ttk.Label(
            main_frame,
            text="Total de registros: 0",
            font=("Arial", 10),
            foreground="#888888",
            background="#1e1e1e"
        )
        self.count_label.pack(pady=(0, 10))
        
        # Frame de botões
        btn_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(
            btn_frame,
            text="🔄 Atualizar",
            command=self._load_data,
            style='Dark.TButton'
        ).pack(side=tk.LEFT, padx=5, ipadx=10, ipady=5)
        
        ttk.Button(
            btn_frame,
            text="🗑️ Limpar Tudo",
            command=self._clear_all,
            style='Dark.TButton'
        ).pack(side=tk.LEFT, padx=5, ipadx=10, ipady=5)
        
        ttk.Button(
            btn_frame,
            text="❌ Voltar",
            command=self.window.destroy,
            style='Dark.TButton'
        ).pack(side=tk.RIGHT, padx=5, ipadx=10, ipady=5)
    
    def _load_data(self):
        """Carregar dados do banco"""
        # Limpar dados existentes
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            if self.db_name == "Banco de Vídeos Originais":
                with get_conn(False) as con:
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute("SELECT * FROM videos_original ORDER BY id DESC")
                    rows = cur.fetchall()
                    
                    for row in rows:
                        desc = (row['descricao'] or '')[:50] + "..." if row['descricao'] and len(row['descricao']) > 50 else (row['descricao'] or '')
                        self.tree.insert('', 'end', values=(
                            row['id'],
                            row['source_type'],
                            (row['source_url'] or row['telegram_file_id'] or '')[:30],
                            (row['original_path'] or '')[:40],
                            (row['link_produto'] or '')[:30],
                            desc,
                            row['created_at']
                        ))
                    
                    self.count_label.config(text=f"Total de registros: {len(rows)}")
                    self.log_terminal.log(f"✅ Carregados {len(rows)} registros do banco de originais", "SUCCESS")
            
            elif self.db_name == "Banco de Vídeos Processados":
                with get_conn(True) as con:
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute("SELECT * FROM videos_processados ORDER BY id DESC")
                    rows = cur.fetchall()
                    
                    for row in rows:
                        resolucao = f"{row['width']}x{row['height']}" if row['width'] and row['height'] else "N/A"
                        erro = (row['error_message'] or '')[:50] + "..." if row['error_message'] and len(row['error_message']) > 50 else (row['error_message'] or '')
                        self.tree.insert('', 'end', values=(
                            row['id'],
                            row['id_ref_original'],
                            (row['processed_path'] or '')[:40],
                            row['status'],
                            row['retries'],
                            erro,
                            resolucao,
                            row['updated_at']
                        ))
                    
                    self.count_label.config(text=f"Total de registros: {len(rows)}")
                    self.log_terminal.log(f"✅ Carregados {len(rows)} registros do banco de processados", "SUCCESS")
            
            else:  # Banco único
                with get_conn() as con:
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute("SELECT * FROM videos ORDER BY id DESC")
                    rows = cur.fetchall()
                    
                    for row in rows:
                        self.tree.insert('', 'end', values=(
                            row['id'],
                            (row['source_url'] or '')[:30],
                            (row['original_path'] or '')[:30],
                            (row['processed_path'] or '')[:30],
                            row['status'],
                            row['retries'],
                            (row['link_produto'] or '')[:30],
                            row['created_at']
                        ))
                    
                    self.count_label.config(text=f"Total de registros: {len(rows)}")
                    self.log_terminal.log(f"✅ Carregados {len(rows)} registros do banco único", "SUCCESS")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados: {e}")
            self.log_terminal.log(f"❌ Erro ao carregar banco: {e}", "ERROR")
    
    def _clear_all(self):
        """Limpar todos os dados do banco"""
        result = messagebox.askyesno(
            "Confirmação",
            f"⚠️ Tem certeza que deseja LIMPAR TODOS os dados do {self.db_name}?\n\nEsta ação NÃO pode ser desfeita!",
            icon='warning'
        )
        
        if not result:
            return
        
        try:
            if self.db_name == "Banco de Vídeos Originais":
                with get_conn(False) as con:
                    con.execute("DELETE FROM videos_original")
                    con.commit()
                self.log_terminal.log("🗑️ Banco de originais limpo com sucesso!", "WARNING")
            
            elif self.db_name == "Banco de Vídeos Processados":
                with get_conn(True) as con:
                    con.execute("DELETE FROM videos_processados")
                    con.commit()
                self.log_terminal.log("🗑️ Banco de processados limpo com sucesso!", "WARNING")
            
            else:  # Banco único
                with get_conn() as con:
                    con.execute("DELETE FROM videos")
                    con.commit()
                self.log_terminal.log("🗑️ Banco único limpo com sucesso!", "WARNING")
            
            # Recarregar dados
            self._load_data()
            messagebox.showinfo("Sucesso", f"{self.db_name} foi limpo com sucesso!")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao limpar banco: {e}")
            self.log_terminal.log(f"❌ Erro ao limpar banco: {e}", "ERROR")


def _run_bot():
    try:
        run_bot_asyncio()
    except Exception as e:
        print(f"[BOT] erro: {e}")


def start_gui():
    init_db()
    
    root = tk.Tk()
    root.title("Sistema Shopee Telegram - Gerenciador de Vídeos")
    root.geometry("1200x750")  # Aumentado
    root.configure(bg="#0d0d0d")  # Tema escuro
    
    # Estilo global
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('Dark.TFrame', background='#0d0d0d')
    style.configure('Dark.TLabel', background='#0d0d0d', foreground='#ffffff')
    style.configure('Dark.TLabelframe', background='#1e1e1e', foreground='#ffffff', bordercolor='#333333')
    style.configure('Dark.TLabelframe.Label', background='#1e1e1e', foreground='#00d4ff', font=('Arial', 11, 'bold'))
    style.configure('Accent.TButton', background='#00d4ff', foreground='#000000', font=('Arial', 10, 'bold'), borderwidth=0)
    style.map('Accent.TButton', background=[('active', '#00aacc')])
    style.configure('Dark.TButton', background='#2d2d2d', foreground='#ffffff', borderwidth=1)
    style.map('Dark.TButton', background=[('active', '#3d3d3d')])
    
    # Frame principal
    main_frame = ttk.Frame(root, padding=10, style='Dark.TFrame')
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Título
    title_frame = ttk.Frame(main_frame, style='Dark.TFrame')
    title_frame.pack(fill=tk.X, pady=(0, 10))
    
    title = ttk.Label(
        title_frame,
        text="🎬 Sistema Shopee Telegram",
        font=("Arial", 22, "bold"),
        foreground="#00d4ff",
        background="#0d0d0d"
    )
    title.pack(side=tk.LEFT)
    
    status_label = ttk.Label(
        title_frame,
        text="🟢 Bot ativo",
        font=("Arial", 11, "bold"),
        foreground="#00ff88",
        background="#0d0d0d"
    )
    status_label.pack(side=tk.RIGHT)
    
    # Frame de controles
    control_frame = ttk.LabelFrame(main_frame, text="⚙️ Controles", padding=12, style='Dark.TLabelframe')
    control_frame.pack(fill=tk.X, pady=(0, 10))
    
    # Terminal de logs
    log_frame = ttk.LabelFrame(main_frame, text="📊 Terminal de Logs e Estatísticas", padding=10, style='Dark.TLabelframe')
    log_frame.pack(fill=tk.BOTH, expand=True)
    
    log_text = scrolledtext.ScrolledText(
        log_frame,
        width=120,
        height=28,
        bg="#0a0a0a",  # Preto mais profundo
        fg="#ffffff",
        font=("Consolas", 10),
        state='disabled',
        insertbackground="white",
        selectbackground="#00d4ff",
        selectforeground="#000000",
        borderwidth=0,
        highlightthickness=0
    )
    log_text.pack(fill=tk.BOTH, expand=True)
    
    # Criar terminal de logs
    log_terminal = LogTerminal(log_text)
    log_terminal.log("╔═══════════════════════════════════════════════════════════╗", "INFO")
    log_terminal.log("║  Sistema Shopee Telegram - Inicializado com Sucesso! 🚀  ║", "SUCCESS")
    log_terminal.log("╚═══════════════════════════════════════════════════════════╝", "INFO")
    log_terminal.log("Bot do Telegram rodando em background...", "INFO")
    log_terminal.update_stats()  # Mostrar estatísticas iniciais
    
    # Botão principal
    def open_video_form():
        VideoFormWindow(root, log_terminal)
    
    btn_processar = ttk.Button(
        control_frame,
        text="➕ Adicionar e Processar Vídeos",
        command=open_video_form,
        style="Accent.TButton"
    )
    btn_processar.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=5)
    
    btn_limpar_logs = ttk.Button(
        control_frame,
        text="🗑️ Limpar Logs",
        command=log_terminal.clear,
        style='Dark.TButton'
    )
    btn_limpar_logs.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=5)

    # Seletor do destino de envio (Bot 1 / Bot 2)
    try:
        target_label = ttk.Label(control_frame, text="Destino:", style='Dark.TLabel')
        target_label.pack(side=tk.LEFT, padx=(10, 2))

        send_target_var = tk.StringVar(value=str(settings.SELECTED_SEND_TARGET))

        def _on_target_change(event=None):
            # Atualiza a configuração em runtime
            settings.SELECTED_SEND_TARGET = send_target_var.get()
            try:
                log_terminal.log(f"🔁 Destino de envio escolhido: {settings.SELECTED_SEND_TARGET}", "INFO")
            except Exception:
                pass

        target_combo = ttk.Combobox(control_frame, values=("Gabriel", "Marli"), width=8, textvariable=send_target_var, state="readonly")
        target_combo.bind("<<ComboboxSelected>>", _on_target_change)
        target_combo.pack(side=tk.LEFT, padx=2)
    except Exception:
        pass
    
    # Botões de banco de dados
    if settings.USE_DUAL_DATABASES:
        ttk.Button(
            control_frame,
            text="📊 Ver Banco Originais",
            command=lambda: DatabaseViewerWindow(root, "Banco de Vídeos Originais", log_terminal),
            style='Dark.TButton'
        ).pack(side=tk.LEFT, padx=5, ipadx=10, ipady=5)
        
        ttk.Button(
            control_frame,
            text="📊 Ver Banco Processados",
            command=lambda: DatabaseViewerWindow(root, "Banco de Vídeos Processados", log_terminal),
            style='Dark.TButton'
        ).pack(side=tk.LEFT, padx=5, ipadx=10, ipady=5)
    else:
        ttk.Button(
            control_frame,
            text="📊 Ver Banco de Dados",
            command=lambda: DatabaseViewerWindow(root, "Banco de Dados Único", log_terminal),
            style='Dark.TButton'
        ).pack(side=tk.LEFT, padx=5, ipadx=10, ipady=5)
    
    # Informações
    info_label = ttk.Label(
        control_frame,
        text="ℹ️  Clique em 'Adicionar e Processar Vídeos' para começar",
        font=("Arial", 9),
        foreground="#888888",
        background="#1e1e1e"
    )
    info_label.pack(side=tk.RIGHT, padx=10)
    
    # Iniciar bot em thread
    threading.Thread(target=_run_bot, daemon=True).start()
    
    root.mainloop()

