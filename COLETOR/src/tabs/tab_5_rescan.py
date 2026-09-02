#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABA 5 — Re-Scan e Comparação"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from src.common.config import ConfigManager
from src.common.console_logger import ConsoleLogger
from src.common.treeview_sort import make_treeview_sortable

class Tab5ReScan(ttk.Frame):
    """ABA 5 — Re-Scan e Comparação."""
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.parent, self.config_mgr = parent, ConfigManager()
        self.stop_event = threading.Event()
        self._create_ui()
    
    def _create_ui(self):
        frame_select = ttk.LabelFrame(self, text="📊 Comparação de Scans", padding=10)
        frame_select.pack(fill=tk.X, padx=10, pady=10)
        btn_frame = ttk.Frame(frame_select)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Carregar Histórico", command=self._load_history).pack(side=tk.LEFT, padx=5)
        
        select_frame = ttk.Frame(frame_select)
        select_frame.pack(fill=tk.X, pady=5)
        ttk.Label(select_frame, text="Scan Base:").pack(side=tk.LEFT)
        self.combo_base = ttk.Combobox(select_frame, width=30, state='readonly')
        self.combo_base.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Label(select_frame, text="Scan Novo:").pack(side=tk.LEFT, padx=(20, 0))
        self.combo_new = ttk.Combobox(select_frame, width=30, state='readonly')
        self.combo_new.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        frame_results = ttk.LabelFrame(self, text="📋 Resultados da Comparação", padding=10)
        frame_results.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        result_scroll = ttk.Scrollbar(frame_results)
        result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_results = ttk.Treeview(frame_results, yscrollcommand=result_scroll.set, height=5)
        self.tree_results['columns'] = ('status', 'anterior', 'novo', 'mudanca')
        self.tree_results.pack(fill=tk.BOTH, expand=True)
        self.tree_results.column('#0', width=120)
        self.tree_results.column('status', width=80)
        self.tree_results.column('anterior', width=100)
        self.tree_results.column('novo', width=100)
        self.tree_results.column('mudanca', width=150)
        
        # Configurar headings
        self.tree_results.heading('#0', text='IP')
        self.tree_results.heading('status', text='Status')
        self.tree_results.heading('anterior', text='Anterior')
        self.tree_results.heading('novo', text='Novo')
        self.tree_results.heading('mudanca', text='Mudança')
        make_treeview_sortable(self.tree_results)
        
        frame_console = ttk.LabelFrame(self, text="📋 Log", padding=10)
        frame_console.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.console_logger = ConsoleLogger(frame_console, height=10, log_name="aba_5_rescan")
        
        frame_action = ttk.Frame(self)
        frame_action.pack(fill=tk.X, padx=10, pady=10)
        progress_frame = ttk.Frame(frame_action)
        progress_frame.pack(fill=tk.X, pady=5)
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.lbl_progress = ttk.Label(progress_frame, text="0%", width=16)
        self.lbl_progress.pack(side=tk.LEFT)
        
        stats_frame = ttk.Frame(frame_action)
        stats_frame.pack(fill=tk.X, pady=5)
        self.lbl_stats = ttk.Label(stats_frame, text="Novos: 0 | Removidos: 0")
        self.lbl_stats.pack(side=tk.LEFT)
        
        btn_action = ttk.Frame(frame_action)
        btn_action.pack(fill=tk.X, pady=10)
        self.btn_compare = ttk.Button(btn_action, text="Comparar", command=self._start_compare)
        self.btn_compare.pack(side=tk.LEFT, padx=5)
        self.btn_cancel = ttk.Button(btn_action, text="Cancelar", command=lambda: self.stop_event.set(), state=tk.DISABLED)
        self.btn_cancel.pack(side=tk.LEFT, padx=5)
    
    def _load_history(self):
        try:
            conn = self.config_mgr.get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT detected_at FROM tb_detected_devices ORDER BY detected_at DESC LIMIT 10")
            scans = [row[0] for row in cursor.fetchall()]
            conn.close()
            self.combo_base['values'] = scans
            self.combo_new['values'] = scans
            self.console_logger.log_ok(f"✓ {len(scans)} scans")
        except Exception as e: self.console_logger.log_error(f"Erro: {e}")
    
    def _start_compare(self):
        if not self.combo_base.get() or not self.combo_new.get(): return
        self.stop_event.clear()
        self.base_scan = self.combo_base.get()
        self.new_scan = self.combo_new.get()
        self.btn_compare.config(state=tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL)
        self.progress['value'] = 0
        self.lbl_progress.config(text="0%")
        self.tree_results.delete(*self.tree_results.get_children())
        self.console_logger.clear()
        threading.Thread(target=self._compare_worker, daemon=True).start()
    
    def _compare_worker(self):
        try:
            conn = self.config_mgr.get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ip FROM tb_detected_devices WHERE detected_at = ?", (self.base_scan,))
            base_ips = set(row[0] for row in cursor.fetchall())
            self.parent.after(0, self._set_compare_progress, 25, "25% base")
            if self.stop_event.is_set():
                conn.close()
                return
            cursor.execute("SELECT ip FROM tb_detected_devices WHERE detected_at = ?", (self.new_scan,))
            new_ips = set(row[0] for row in cursor.fetchall())
            self.parent.after(0, self._set_compare_progress, 50, "50% novo")
            conn.close()

            if self.stop_event.is_set():
                return
            
            novos, removidos, mantidos = new_ips - base_ips, base_ips - new_ips, new_ips & base_ips
            rows = []
            rows.extend((ip, ("NOVO", "-", ip, "Adicionado")) for ip in novos)
            rows.extend((ip, ("REMOVIDO", ip, "-", "Removido")) for ip in removidos)
            rows.extend((ip, ("MANTIDO", ip, ip, "Sem mudança")) for ip in mantidos)
            self.parent.after(
                0,
                self._render_compare_results,
                rows,
                f"Novos: {len(novos)} | Removidos: {len(removidos)} | Mantidos: {len(mantidos)}",
            )
            self.console_logger.log_ok(f"✓ {len(novos)} novos, {len(removidos)} removidos")
        except Exception as e:
            self.console_logger.log_error(f"Erro: {e}")
            self.parent.after(0, lambda: self.lbl_progress.config(text="Erro"))
        finally:
            self.parent.after(0, self._finish_compare)

    def _render_compare_results(self, rows, stats_text):
        total = len(rows)
        for idx, (ip, values) in enumerate(rows, 1):
            self.tree_results.insert('', tk.END, text=ip, values=values)
            if idx == total or idx % 100 == 0:
                pct = 50 + int((idx / total) * 50) if total else 100
                self._set_compare_progress(pct, f"{pct}% ({idx}/{total})")
        self.lbl_stats.config(text=stats_text)
        if self.stop_event.is_set():
            self.lbl_progress.config(text="Cancelado")
        else:
            self._set_compare_progress(100, "100%")

    def _set_compare_progress(self, progress_pct, progress_text=None):
        self.progress['value'] = progress_pct
        self.lbl_progress.config(text=progress_text or f"{progress_pct}%")

    def _finish_compare(self):
        self.btn_compare.config(state=tk.NORMAL)
        self.btn_cancel.config(state=tk.DISABLED)
        if self.stop_event.is_set():
            self.lbl_progress.config(text="Cancelado")
