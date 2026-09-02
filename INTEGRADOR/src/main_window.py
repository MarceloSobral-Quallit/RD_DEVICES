#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""main_window.py - Janela Principal do INTEGRADOR GUI."""

import tkinter as tk
from tkinter import ttk
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common.config import IntegradorConfig
from version import VERSION, BUILD_DATE
from tabs.tab_0_config import Tab0Config
from tabs.tab_1_import import Tab1Import
from tabs.tab_2_count import Tab2Count
from tabs.tab_3_view_sqlite import Tab3ViewSQLite
from tabs.tab_4_view_mariadb import Tab4ViewMariaDB
from tabs.tab_5_view_compare import Tab5ViewCompare

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
    """Janela principal do INTEGRADOR com abas."""

    def __init__(self, root):
        self.root = root
        self.cfg = IntegradorConfig()
        self.setup_ui()
        logger.info("INTEGRADOR MainWindow inicializado")

    def setup_ui(self):
        self.create_menu()
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tabs = []
        self.create_tabs()
        self.create_status_bar()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Sair", command=self.root.quit)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self.show_about)

    def create_tabs(self):
        tab_names = [
            "⚙ Configuração",
            "📤 Importar",
            "📊 Contagem",
            "🗄 SQLite",
            "🛢 MariaDB",
            "↔ Comparar",
        ]
        constructors = [
            ("Configuração", lambda f: Tab0Config(f, config=self.cfg)),
            ("Importar",     lambda f: Tab1Import(f, config=self.cfg)),
            ("Contagem",     lambda f: Tab2Count(f, config=self.cfg)),
            ("Ver SQLite",   lambda f: Tab3ViewSQLite(f, config=self.cfg)),
            ("Ver MariaDB",  lambda f: Tab4ViewMariaDB(f, config=self.cfg)),
            ("Comparar",     lambda f: Tab5ViewCompare(f, config=self.cfg)),
        ]

        for name in tab_names:
            frame = ScrollableTab(self.notebook)
            self.notebook.add(frame, text=name)
            self.tabs.append(frame.body)

        for i, (name, constructor) in enumerate(constructors):
            try:
                constructor(self.tabs[i])
                logger.info("Aba %d (%s) carregada", i, name)
            except Exception as exc:
                logger.error("Aba %d (%s) falhou: %s", i, name, exc, exc_info=True)
                self._render_tab_error(self.tabs[i], i, name, exc)

    def _render_tab_error(self, frame, index, name, error):
        import traceback
        tb = traceback.format_exc()

        container = ttk.Frame(frame, padding=20)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text=f"⚠  ABA {index} — {name}",
            font=("Segoe UI", 13, "bold"),
            foreground="red",
        ).pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(container, text="Erro ao carregar esta aba:", font=("Segoe UI", 10)).pack(anchor=tk.W)

        txt_frame = ttk.Frame(container)
        txt_frame.pack(fill=tk.BOTH, expand=True, pady=8)
        sb = ttk.Scrollbar(txt_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt = tk.Text(
            txt_frame, yscrollcommand=sb.set, height=18, font=("Consolas", 9),
            wrap=tk.WORD, background="#1e1e1e", foreground="#ff6b6b", insertbackground="white",
        )
        txt.pack(fill=tk.BOTH, expand=True)
        sb.config(command=txt.yview)
        txt.insert(tk.END, f"Erro: {error}\n\n{tb}")
        txt.config(state=tk.DISABLED)

    def create_status_bar(self):
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = tk.Label(
            self.root, textvariable=self.status_var,
            relief=tk.SUNKEN, anchor=tk.W, height=1,
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def show_about(self):
        from tkinter import messagebox
        messagebox.showinfo(
            "Sobre",
            f"INTEGRADOR\nRD Devices — Importador SQLite → MariaDB\n"
            f"Versão: {VERSION}\nBuild: {BUILD_DATE}",
        )
