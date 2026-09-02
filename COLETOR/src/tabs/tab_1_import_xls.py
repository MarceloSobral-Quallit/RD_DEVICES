#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABA 1 — Import XLS

Funcionalidades:
  ✓ Seleção de arquivo XLS com diálogo
  ✓ Preview dos dados antes de importar
  ✓ Opções de importação (TRUNCATE, DRY-RUN, UPSERT)
  ✓ Progress bar com logging em tempo real
  ✓ Threading para UI responsiva
  ✓ Validação de dados

Mapeamento XLS → tb_filial:
  [0]  Filial           → filial
  [1]  Hist.            → historico
  [2]  Nome Filial      → nome_filial
  [3]  Dt. Inauguração  → data_inauguracao  (DD/MM/YYYY → YYYY-MM-DD)
  [4]  Insc. Estadual   → inscricao_estadual
  [5]  CNPJ             → cnpj              (apenas dígitos)
  [6]  Endereço         → endereco
  [7]  Bairro           → bairro
  [8]  Cidade           → cidade
  [9]  UF               → uf
  [10] Região           → regiao
  [11] Logomarca        → logomarca
  [12] Telefone         → telefone
  [13] IP Banco 12      → ip_banco_12
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
import sqlite3
from datetime import datetime
import re

try:
    import xlrd
except ImportError:
    xlrd = None

from src.common.config import ConfigManager
from src.common.console_logger import ConsoleLogger
from src.common.treeview_sort import make_treeview_sortable


class Tab1ImportXLS(ttk.Frame):
    """ABA 1 — Importar dados de arquivo XLS."""

    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.parent = parent
        
        # Config
        self.config_mgr = ConfigManager()
        
        # Threading
        self.stop_event = threading.Event()
        self.worker_thread = None
        
        # Estado
        self.xls_path = None
        self.xls_data = None
        self.xls_datemode = None
        self.xls_headers = None
        self.import_status = "idle"

        # Mapeamento fixo XLS -> tb_filial (indice, cabecalho esperado, coluna destino)
        self.field_mapping = [
            (0,  "Filial",           "filial"),
            (1,  "Hist.",            "historico"),
            (2,  "Nome Filial",      "nome_filial"),
            (3,  "Dt. Inauguração",  "data_inauguracao"),
            (4,  "Insc. Estadual",   "inscricao_estadual"),
            (5,  "CNPJ",             "cnpj"),
            (6,  "Endereço",         "endereco"),
            (7,  "Bairro",           "bairro"),
            (8,  "Cidade",           "cidade"),
            (9,  "UF",               "uf"),
            (10, "Região",           "regiao"),
            (11, "Logomarca",        "logomarca"),
            (12, "Telefone",         "telefone"),
            (13, "IP Banco 12",      "ip_banco_12"),
        ]
        
        self._create_ui()

    def _create_ui(self):
        """Cria interface da ABA 1."""

        # ── Rodapé fixo (progress + botões) — empacotado PRIMEIRO como BOTTOM ──
        frame_action = ttk.Frame(self)
        frame_action.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=6)

        progress_frame = ttk.Frame(frame_action)
        progress_frame.pack(fill=tk.X, pady=2)
        ttk.Label(progress_frame, text="Progresso:", width=12).pack(side=tk.LEFT)
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.lbl_progress = ttk.Label(progress_frame, text="0%", width=16)
        self.lbl_progress.pack(side=tk.LEFT)

        btn_action = ttk.Frame(frame_action)
        btn_action.pack(fill=tk.X, pady=4)
        self.btn_import = ttk.Button(btn_action, text="🚀 Importar",
                                     command=self._start_import, state=tk.DISABLED)
        self.btn_import.pack(side=tk.LEFT, padx=5)
        self.btn_cancel = ttk.Button(btn_action, text="⛔ Cancelar",
                                     command=self._cancel_import, state=tk.DISABLED)
        self.btn_cancel.pack(side=tk.LEFT, padx=5)

        # ── Seção 1: Arquivo (fixo no topo) ──────────────────────────────────
        frame_file = ttk.LabelFrame(self, text="📄 Seleção de Arquivo", padding=8)
        frame_file.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(8, 2))

        file_frame = ttk.Frame(frame_file)
        file_frame.pack(fill=tk.X, pady=3)
        ttk.Label(file_frame, text="Arquivo:").pack(side=tk.LEFT)
        self.lbl_file = ttk.Label(file_frame, text="(Nenhum arquivo selecionado)", foreground="gray")
        self.lbl_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 12))
        self.btn_browse = ttk.Button(file_frame, text="Procurar...", command=self._browse_file)
        self.btn_browse.pack(side=tk.LEFT, padx=3)
        self.btn_preview = ttk.Button(file_frame, text="Carregar XLS", command=self._preview_xls, state=tk.DISABLED)
        self.btn_preview.pack(side=tk.LEFT, padx=3)
        self.btn_clear = ttk.Button(file_frame, text="Limpar", command=self._clear_file)
        self.btn_clear.pack(side=tk.LEFT, padx=(3, 0))

        # ── Seção 2: Opções (fixo) ────────────────────────────────────────────
        frame_options = ttk.LabelFrame(self, text="⚙️ Opções de Importação", padding=8)
        frame_options.pack(side=tk.TOP, fill=tk.X, padx=10, pady=2)

        options_row = ttk.Frame(frame_options)
        options_row.pack(fill=tk.X, pady=3)
        ttk.Label(options_row, text="Modo:").pack(side=tk.LEFT)
        self.import_mode = tk.StringVar(value="upsert")
        ttk.Radiobutton(options_row, text="Atualizar dados",
                        variable=self.import_mode, value="upsert").pack(side=tk.LEFT, padx=(8, 6))
        ttk.Radiobutton(options_row, text="Limpar dados",
                        variable=self.import_mode, value="truncate").pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(options_row, text="Opções:").pack(side=tk.LEFT)
        self.opt_dry_run = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_row, text="Simular",
                        variable=self.opt_dry_run).pack(side=tk.LEFT, padx=(8, 6))
        self.opt_skip_validation = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_row, text="Pular verificação",
                        variable=self.opt_skip_validation).pack(side=tk.LEFT, padx=(0, 6))

        # ── PanedWindow: Preview (cima) + Log (baixo) — ocupa o resto ────────
        paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(4, 2))

        # Preview — painel superior
        frame_preview = ttk.LabelFrame(paned, text="� Verificação do Arquivo", padding=6)
        preview_scroll_v = ttk.Scrollbar(frame_preview)
        preview_scroll_v.pack(side=tk.RIGHT, fill=tk.Y)
        preview_scroll_h = ttk.Scrollbar(frame_preview, orient=tk.HORIZONTAL)
        preview_scroll_h.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree_preview = ttk.Treeview(frame_preview,
                                         yscrollcommand=preview_scroll_v.set,
                                         xscrollcommand=preview_scroll_h.set,
                                         height=5)
        self.tree_preview.pack(fill=tk.BOTH, expand=True)
        preview_scroll_v.config(command=self.tree_preview.yview)
        preview_scroll_h.config(command=self.tree_preview.xview)
        self._sort_preview = make_treeview_sortable(self.tree_preview)
        paned.add(frame_preview, weight=1)

        # Log — painel inferior
        frame_console = ttk.LabelFrame(paned, text="📋 Log em Tempo Real", padding=6)
        self.console_logger = ConsoleLogger(frame_console, height=10, log_name="aba_1_import_xls")
        paned.add(frame_console, weight=2)

    def _browse_file(self):
        """Abre diálogo para selecionar arquivo XLS."""
        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo XLS",
            filetypes=[("Excel files", "*.xls *.xlsx"), ("Todos", "*.*")],
            initialdir=str(Path.home() / "Downloads")
        )
        
        if file_path:
            self.xls_path = file_path
            self.lbl_file.config(text=str(Path(file_path).name), foreground="black")
            self.btn_preview.config(state=tk.NORMAL)
            self.btn_import.config(state=tk.NORMAL)
            self.console_logger.log(f"Arquivo selecionado: {file_path}")

    def _clear_file(self):
        """Limpa arquivo selecionado."""
        self.xls_path = None
        self.xls_data = None
        self.xls_datemode = None
        self.lbl_file.config(text="(Nenhum arquivo selecionado)", foreground="gray")
        self.btn_preview.config(state=tk.DISABLED)
        self.btn_import.config(state=tk.DISABLED)
        self.tree_preview.delete(*self.tree_preview.get_children())
        self.console_logger.log("Arquivo limpo")

    def _preview_xls(self):
        """Faz preview dos dados do XLS."""
        if not self.xls_path:
            messagebox.showerror("Erro", "Nenhum arquivo selecionado")
            return
        
        if not xlrd:
            self.console_logger.log("xlrd não instalado: pip install xlrd", "ERROR")
            return
        
        try:
            self.console_logger.log(f"Lendo arquivo: {self.xls_path}")
            
            wb = xlrd.open_workbook(self.xls_path)
            ws = wb.sheet_by_index(0)
            self.xls_datemode = wb.datemode
            
            self.console_logger.log(f"Sheet: '{ws.name}' | Linhas: {ws.nrows} | Colunas: {ws.ncols}")
            
            # Lê dados
            self.xls_data = []
            headers = None
            
            for row_idx in range(ws.nrows):
                row_values = ws.row_values(row_idx)
                
                if row_idx == 0:
                    headers = row_values
                    self.xls_headers = headers
                    continue
                
                # Ignora linhas vazias
                if not any(row_values):
                    continue
                
                self.xls_data.append(row_values)
            
            self.console_logger.log(f"✓ {len(self.xls_data)} registros lidos", "SUCCESS")

            # Valida mapeamento XLS -> tb_filial
            self._validate_header_mapping(headers)
            
            # Exibe preview no Treeview
            self._update_preview(headers, self.xls_data[:10])
            
        except Exception as e:
            self.console_logger.log(f"Erro ao ler XLS: {e}", "ERROR")

    def _update_preview(self, headers, data):
        """Atualiza preview no Treeview."""
        self.tree_preview.delete(*self.tree_preview.get_children())
        
        cols = [str(h) for h in headers[:5]]
        self.tree_preview['columns'] = cols
        self.tree_preview.column('#0', width=50)
        
        for col in cols:
            self.tree_preview.column(col, width=150)
            self.tree_preview.heading(col, text=str(col))
        self._sort_preview = make_treeview_sortable(self.tree_preview)
        
        for idx, row in enumerate(data, 1):
            values = [str(row[i] if i < len(row) else '') for i in range(len(cols))]
            self.tree_preview.insert('', tk.END, text=str(idx), values=values)
        if cols and str(cols[0]).strip().lower() in ("filial", "java"):
            self._sort_preview(cols[0], descending=False)
        
        self.console_logger.log(f"Preview de {len(data)} primeiros registros", "INFO")

    def _start_import(self):
        """Inicia importação em thread separada."""
        if not self.xls_path or not self.xls_data:
            messagebox.showerror("Erro", "Nenhum arquivo válido para importar")
            return
        
        self.stop_event.clear()
        self.btn_import.config(state=tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL)
        self.btn_browse.config(state=tk.DISABLED)
        self.btn_preview.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.lbl_progress.config(text="0%")
        self.import_status = "running"
        self.console_logger.clear()
        
        self.console_logger.log("Iniciando importação...", "INFO")
        self.console_logger.log(f"Modo: {self.import_mode.get()}", "INFO")
        self.console_logger.log("Tabela: tb_filial", "INFO")
        self.console_logger.log(f"DRY-RUN: {self.opt_dry_run.get()}", "INFO")

        # Revalida mapeamento antes de importar
        if self.xls_headers:
            self._validate_header_mapping(self.xls_headers)
        
        self.worker_thread = threading.Thread(target=self._import_worker, daemon=True)
        self.worker_thread.start()

    def _cancel_import(self):
        """Cancela importação."""
        self.stop_event.set()
        self.console_logger.log("Cancelando importação...", "WARNING")
        self.btn_cancel.config(state=tk.DISABLED)

    def _import_worker(self):
        """Worker para importação (thread)."""
        try:
            mode = self.import_mode.get()
            dry_run = self.opt_dry_run.get()
            skip_validation = self.opt_skip_validation.get()
            
            # Mapeamento de colunas XLS -> tb_filial
            col_mapping = {idx: dest for idx, _header, dest in self.field_mapping}
            
            # Mapeia dados do XLS
            records = []
            total_rows = len(self.xls_data)
            for row_idx, row in enumerate(self.xls_data, 1):
                if self.stop_event.is_set():
                    break
                
                record = {}
                for col_idx, col_name in col_mapping.items():
                    value = row[col_idx] if col_idx < len(row) else None
                    
                    if col_name == 'data_inauguracao':
                        value = self._convert_date(value)
                    elif col_name in ['cnpj', 'inscricao_estadual']:
                        value = self._clean_numeric(value)
                    else:
                        value = self._clean_text(value)
                    
                    record[col_name] = value

                # ativo = 1 somente se ip_banco_12 for válido (≠ 0.0.0.0 e formato correto)
                ip = record.get('ip_banco_12') or ''
                record['ativo'] = 1 if self._validate_ip(ip.strip()) else 0

                records.append(record)

                if row_idx == total_rows or row_idx % 100 == 0:
                    progress_pct = self._phase_progress(row_idx, total_rows, 0, 25)
                    self.parent.after(
                        0,
                        self._set_import_progress,
                        progress_pct,
                        f"{progress_pct}% ({row_idx}/{total_rows})",
                    )
            
            self.console_logger.log(f"Registros mapeados: {len(records)}", "INFO")

            if self.stop_event.is_set():
                self.import_status = "cancelled"
                self.console_logger.log("Importação cancelada durante o mapeamento", "WARNING")
                return
            
            if not skip_validation:
                self._validate_records(records, base_pct=25, span_pct=15)
            else:
                self.parent.after(0, self._set_import_progress, 40, "40%")

            if self.stop_event.is_set():
                self.import_status = "cancelled"
                return
            
            # Importação no banco (sempre tb_filial)
            self.import_status = self._import_to_filial(records, mode, dry_run, base_pct=40, span_pct=60)
            
        except Exception as e:
            self.import_status = "error"
            self.console_logger.log(f"Erro na importação: {e}", "ERROR")
        
        finally:
            self.parent.after(0, self._import_done)

    def _convert_date(self, value):
        """Converte data Excel → YYYY-MM-DD."""
        if not value:
            return None
        try:
            if isinstance(value, float):
                import xlrd
                t = xlrd.xldate_as_tuple(value, self.xls_datemode)
                if t[0] == 0:
                    return None
                return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"
            elif isinstance(value, str):
                if '/' in value:
                    parts = value.split('/')
                    if len(parts) == 3:
                        return f"{int(parts[2]):04d}-{int(parts[1]):02d}-{int(parts[0]):02d}"
        except Exception:
            pass
        return None

    def _clean_numeric(self, value):
        """Remove caracteres não-dígitos."""
        if not value:
            return None
        clean = ''.join(c for c in str(value) if c.isdigit())
        return clean if clean else None

    def _clean_text(self, value):
        """Limpa texto."""
        if not value:
            return None
        return str(value).strip()

    def _validate_records(self, records, base_pct=0, span_pct=100):
        """Valida registros."""
        self.console_logger.log("Validando registros...", "INFO")
        warnings = 0
        total = len(records)
        for idx, record in enumerate(records, 1):
            if self.stop_event.is_set():
                break
            if not record.get('filial'):
                self.console_logger.log(f"Linha {idx}: Filial vazia", "WARNING")
                warnings += 1
            if record.get('ip_banco_12'):
                if not self._validate_ip(record['ip_banco_12']):
                    self.console_logger.log(f"Linha {idx}: IP inválido: {record['ip_banco_12']}", "WARNING")
                    warnings += 1
            if idx == total or idx % 100 == 0:
                progress_pct = self._phase_progress(idx, total, base_pct, span_pct)
                self.parent.after(
                    0,
                    self._set_import_progress,
                    progress_pct,
                    f"{progress_pct}% ({idx}/{total})",
                )
        if self.stop_event.is_set():
            self.console_logger.log("Validação cancelada", "WARNING")
            return
        if warnings > 0:
            self.console_logger.log(f"Total de avisos: {warnings}", "WARNING")
        else:
            self.console_logger.log("✓ Validação completa sem avisos", "SUCCESS")

    def _validate_header_mapping(self, headers):
        """Valida se o cabeçalho do XLS bate com o mapeamento esperado para tb_filial."""
        if not headers:
            self.console_logger.log("Cabeçalho do XLS não encontrado para validação de mapeamento", "WARNING")
            return

        mismatches = 0
        for idx, expected_header, dest_col in self.field_mapping:
            current = str(headers[idx]).strip() if idx < len(headers) else ""
            # Normaliza acentos para comparação
            import unicodedata
            def norm(s):
                return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
            if norm(current) == norm(expected_header):
                self.console_logger.log(f"Mapeamento OK [{idx}] '{current}' -> {dest_col}", "INFO")
            else:
                mismatches += 1
                self.console_logger.log(
                    f"Mapeamento DIF [{idx}] esperado '{expected_header}', encontrado '{current}' -> {dest_col}",
                    "WARNING"
                )

        if mismatches == 0:
            self.console_logger.log("✓ Mapeamento XLS -> tb_filial validado com sucesso", "SUCCESS")
        else:
            self.console_logger.log(
                f"Mapeamento com {mismatches} divergência(s). Revise o layout do XLS antes da importação",
                "WARNING"
            )

    def _validate_ip(self, ip):
        """Valida IP."""
        if not ip or ip == '0.0.0.0':
            return False
        import re
        pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(pattern, str(ip))
        if not match:
            return False
        try:
            octets = [int(x) for x in match.groups()]
            return all(0 <= o <= 255 for o in octets) and octets[0] not in (0, 127)
        except Exception:
            return False

    def _import_to_filial(self, records, mode, dry_run, base_pct=0, span_pct=100):
        """Importa dados para tb_filial."""
        conn = None
        cursor = None
        try:
            db_path = self.config_mgr.get_path('DATABASE', 'path', './database/devices.db')
            conn = self.config_mgr.get_sqlite_connection()
            cursor = conn.cursor()
            
            self.console_logger.log(f"Conectado ao banco SQLite: {db_path}", "INFO")
            
            if mode == "truncate":
                if not dry_run:
                    cursor.execute("DELETE FROM tb_filial")
                    self.console_logger.log("tb_filial será limpa na mesma transação da importação", "INFO")
                else:
                    self.console_logger.log("[DRY-RUN] DELETE FROM tb_filial", "INFO")
            
            insert_count = 0
            total = len(records)
            cancelled = False
            
            for idx, record in enumerate(records, 1):
                if self.stop_event.is_set():
                    cancelled = True
                    break
                
                progress_pct = self._phase_progress(idx, total, base_pct, span_pct)
                self.parent.after(
                    0,
                    self._set_import_progress,
                    progress_pct,
                    f"{progress_pct}% ({idx}/{total})",
                )
                
                cols   = list(record.keys())
                values = tuple(record.values())
                placeholders = ",".join(["?" for _ in cols])
                
                if mode == "upsert":
                    sql = f"INSERT OR REPLACE INTO tb_filial ({','.join(cols)}) VALUES ({placeholders})"
                else:
                    sql = f"INSERT INTO tb_filial ({','.join(cols)}) VALUES ({placeholders})"
                
                if not dry_run:
                    cursor.execute(sql, values)
                    insert_count += 1
                else:
                    if idx <= 3:
                        self.console_logger.log(f"[DRY-RUN] {sql}", "INFO")
                
                if idx % 100 == 0:
                    self.console_logger.log(f"Processados: {idx}/{total}", "INFO")
            
            if cancelled:
                if not dry_run:
                    conn.rollback()
                self.console_logger.log("Importação cancelada; alterações revertidas", "WARNING")
                return "cancelled"
            elif not dry_run:
                conn.commit()
                self.console_logger.log(f"✓ Importação concluída: {insert_count} registros inseridos", "SUCCESS")
                return "success"
            else:
                self.console_logger.log("[DRY-RUN] Simulação concluída (não gravou)", "SUCCESS")
                return "dry_run"
            
        except Exception as e:
            if conn is not None and not dry_run:
                conn.rollback()
            self.console_logger.log(f"Erro ao importar: {e}", "ERROR")
            return "error"
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()

    def _phase_progress(self, done, total, base_pct, span_pct):
        if total <= 0:
            return min(100, base_pct + span_pct)
        return min(100, base_pct + int((done / total) * span_pct))

    def _set_import_progress(self, progress_pct, label=None):
        self.progress['value'] = progress_pct
        self.lbl_progress.config(text=label or f"{progress_pct}%")

    def _import_done(self):
        """Chamado quando importação termina."""
        self.btn_import.config(state=tk.NORMAL)
        self.btn_cancel.config(state=tk.DISABLED)
        self.btn_browse.config(state=tk.NORMAL)
        self.btn_preview.config(state=tk.NORMAL)
        if self.import_status in ("success", "dry_run"):
            self._set_import_progress(100, "100%")
            self.console_logger.log("✓ Importação finalizada", "SUCCESS")
        elif self.import_status == "cancelled":
            self.lbl_progress.config(text="Cancelado")
            self.console_logger.log("Importação finalizada com cancelamento", "WARNING")
        else:
            self.lbl_progress.config(text="Erro")
            self.console_logger.log("Importação finalizada com erro", "ERROR")
