#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_window.py - Janela Principal do COLETOR
Data: 08/06/2026
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common.config import ConfigManager
from version import VERSION, BUILD_DATE
from tabs.tab_0_database import Tab0DatabaseManager
from tabs.tab_1_import_xls import Tab1ImportXLS
from tabs.tab_2_ssh import Tab2DetectSSH
from tabs.tab_3_devices import Tab3DetectDevices
from tabs.tab_4_hardware import Tab4ScanHardware
from tabs.tab_5_rescan import Tab5ReScan
from tabs.tab_6_credentials import Tab6Credentials
from tabs.tab_7_autopilot import Tab7Autopilot

logger = logging.getLogger(__name__)


class ScrollableTab(ttk.Frame):
    """Frame de aba com rolagem vertical e corpo com largura cheia."""

    def __init__(self, parent):
        super().__init__(parent)

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.body = ttk.Frame(self.canvas)
        self._window_id = self.canvas.create_window((0, 0), window=self.body, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.body.bind("<Configure>", self._on_body_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.body.bind("<MouseWheel>", self._on_mousewheel)

    def _on_body_configure(self, _event=None):
        self._sync_body_size()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._sync_body_size(event.width, event.height)

    def _sync_body_size(self, width=None, height=None):
        width = width or self.canvas.winfo_width()
        height = height or self.canvas.winfo_height()
        requested_height = self.body.winfo_reqheight()
        self.canvas.itemconfigure(
            self._window_id,
            width=width,
            height=max(height, requested_height),
        )

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class MainWindow:
    """Janela principal com abas do coletor."""
    
    def __init__(self, root):
        self.root = root
        self.cfg = ConfigManager()
        self.tab_instances = []
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        logger.info("MainWindow initialized")
    
    def setup_ui(self):
        """Criar interface com menu, abas, status bar."""
        # Menu
        self.create_menu()
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook (abas)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Criar abas
        self.tabs = []
        self.create_tabs()
        
        # Status bar
        self.create_status_bar()
    
    def create_menu(self):
        """Criar menu principal."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Sair", command=self.on_close)
        
        # Menu Ajuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self.show_about)
    
    def create_tabs(self):
        """Criar abas."""
        tab_names = [
            "SQLite",
            "📥 Import XLS",
            "🔍 B12",
            "🖥 Scan Loja",
            "🔧 Hardware",
            "🔄 Re-Scan",
            "Credenciais",
            "🚀 Autopilot",
        ]

        for i, name in enumerate(tab_names):
            frame = ScrollableTab(self.notebook)
            self.notebook.add(frame, text=name)
            self.tabs.append(frame.body)

        # Instanciar cada aba com tratamento de erro individual
        tab_constructors = [
            ("SQLite", lambda f: Tab0DatabaseManager(f, config=self.cfg)),
            ("Import XLS",       lambda f: Tab1ImportXLS(f)),
            ("Consulta B12",  lambda f: Tab2DetectSSH(f)),
            ("Scan Loja", lambda f: Tab3DetectDevices(f)),
            ("Escanear Hardware",     lambda f: Tab4ScanHardware(f)),
            ("Re-Scan",               lambda f: Tab5ReScan(f)),
            ("Credenciais",           lambda f: Tab6Credentials(f)),
            ("Autopilot",             lambda f: Tab7Autopilot(f)),
        ]

        for i, (name, constructor) in enumerate(tab_constructors):
            try:
                instance = constructor(self.tabs[i])
                self.tab_instances.append(instance)
                logger.info(f"ABA {i} ({name}) carregada com sucesso")
            except Exception as e:
                logger.error(f"ABA {i} ({name}) falhou ao carregar: {e}", exc_info=True)
                self._render_tab_error(self.tabs[i], i, name, e)

    def on_close(self):
        running = [
            tab for tab in self.tab_instances
            if hasattr(tab, "is_scan_running") and tab.is_scan_running()
        ]
        if running:
            if not messagebox.askyesno(
                "Encerrar COLETOR",
                "Existe scan em andamento. O COLETOR vai cancelá-lo antes de sair.\n\n"
                "Deseja cancelar o scan em andamento?",
            ):
                return
            for tab in running:
                if hasattr(tab, "request_cancel"):
                    tab.request_cancel()
            still_running = [
                tab for tab in running
                if hasattr(tab, "is_scan_running") and tab.is_scan_running()
            ]
            if still_running:
                messagebox.showinfo(
                    "Cancelamento solicitado",
                    "Aguarde o scan finalizar como cancelado antes de fechar o COLETOR.",
                )
                return
        self.root.destroy()
    
    def _render_tab_error(self, frame, index, name, error):
        """Exibe mensagem de erro dentro da aba que falhou ao carregar."""
        import traceback
        tb = traceback.format_exc()

        container = ttk.Frame(frame, padding=20)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container,
                  text=f"⚠️  ABA {index} — {name}",
                  font=("Segoe UI", 13, "bold"),
                  foreground="red").pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(container,
                  text="Erro ao carregar esta aba:",
                  font=("Segoe UI", 10)).pack(anchor=tk.W)

        # Caixa com traceback scrollável
        txt_frame = ttk.Frame(container)
        txt_frame.pack(fill=tk.BOTH, expand=True, pady=8)
        sb = ttk.Scrollbar(txt_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt = tk.Text(txt_frame, yscrollcommand=sb.set, height=18,
                      font=("Consolas", 9), wrap=tk.WORD,
                      background="#1e1e1e", foreground="#ff6b6b",
                      insertbackground="white")
        txt.pack(fill=tk.BOTH, expand=True)
        sb.config(command=txt.yview)

        txt.insert(tk.END, f"Erro: {error}\n\n{tb}")
        txt.config(state=tk.DISABLED)

    def create_status_bar(self):
        """Criar barra de status."""
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto")
        
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            height=1
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def show_about(self):
        """Mostrar dialog 'Sobre'."""
        about_text = f"""
COLETOR
RD Devices Collector

Versão: {VERSION}
Data: {BUILD_DATE}
Status: MVP em Desenvolvimento

Documentação: docs/README.md
        """
        from tkinter import messagebox
        messagebox.showinfo("Sobre COLETOR", about_text)


if __name__ == '__main__':
    root = tk.Tk()
    root.title("COLETOR - RD Devices")
    root.geometry("1010x610")
    root.minsize(1010, 610)
    app = MainWindow(root)
    root.mainloop()
