#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABA 3 — Visualizar SQLite: exibe dados de qualquer tabela do SQLite."""

import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from common.treeview_sort import make_treeview_sortable

PAGE_SIZE = 200


class Tab3ViewSQLite(ttk.Frame):
    def __init__(self, parent, config=None):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self._page  = 0
        self._total = 0
        self._create_ui()

    def _create_ui(self):
        # --- Controles ---
        frame_ctrl = ttk.Frame(self)
        frame_ctrl.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.var_sqlite = tk.StringVar()
        ttk.Entry(frame_ctrl, textvariable=self.var_sqlite, width=40).pack(side=tk.LEFT)
        ttk.Button(frame_ctrl, text="...", width=3, command=self._browse).pack(
            side=tk.LEFT, padx=(2, 8)
        )
        ttk.Button(frame_ctrl, text="Carregar tabelas", command=self._load_tables).pack(
            side=tk.LEFT, padx=4
        )

        self.var_table = tk.StringVar()
        self.combo_table = ttk.Combobox(
            frame_ctrl, textvariable=self.var_table, width=32, state="readonly"
        )
        self.combo_table.pack(side=tk.LEFT, padx=8)
        self.combo_table.bind("<<ComboboxSelected>>", lambda _: self._load_page(0))

        ttk.Label(frame_ctrl, text="Filtro:").pack(side=tk.LEFT, padx=(12, 4))
        self.var_filter = tk.StringVar()
        self.var_filter.trace_add("write", lambda *_: self._load_page(0))
        ttk.Entry(frame_ctrl, textvariable=self.var_filter, width=20).pack(side=tk.LEFT)
        ttk.Button(
            frame_ctrl, text="X", width=2, command=lambda: self.var_filter.set("")
        ).pack(side=tk.LEFT)

        # --- Treeview ---
        frame_tree = ttk.Frame(self)
        frame_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=3)

        self.tree = ttk.Treeview(frame_tree, show="headings")
        sb_y = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL,   command=self.tree.yview)
        sb_x = ttk.Scrollbar(frame_tree, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side=tk.RIGHT,  fill=tk.Y)
        sb_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # --- Paginação ---
        frame_page = ttk.Frame(self)
        frame_page.pack(fill=tk.X, padx=10, pady=3)
        ttk.Button(
            frame_page, text="◄ Anterior",
            command=lambda: self._load_page(self._page - 1),
        ).pack(side=tk.LEFT, padx=3)
        self.lbl_page = ttk.Label(frame_page, text="—")
        self.lbl_page.pack(side=tk.LEFT, padx=6)
        ttk.Button(
            frame_page, text="Próximo ►",
            command=lambda: self._load_page(self._page + 1),
        ).pack(side=tk.LEFT, padx=3)
        self.lbl_count = ttk.Label(frame_page, text="", foreground="gray")
        self.lbl_count.pack(side=tk.LEFT, padx=12)

    # -------------------------------------------------------------------------

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Selecionar SQLite",
            filetypes=[("SQLite", "*.db"), ("Todos", "*.*")],
        )
        if path:
            self.var_sqlite.set(path)
            self._load_tables()

    def _load_tables(self):
        db_path = self.var_sqlite.get().strip()
        if not db_path or not Path(db_path).exists():
            return
        try:
            conn = sqlite3.connect(db_path)
            cur  = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cur.fetchall()]
            conn.close()
            self.combo_table["values"] = tables
            if tables:
                self.combo_table.set(tables[0])
                self._load_page(0)
        except Exception as exc:
            self.lbl_count.config(text=f"Erro: {exc}", foreground="red")

    def _load_page(self, page: int):
        db_path = self.var_sqlite.get().strip()
        table   = self.var_table.get().strip()
        if not db_path or not table or not Path(db_path).exists():
            return

        flt = self.var_filter.get().strip()
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cur  = conn.cursor()

            cur.execute(f'PRAGMA table_info("{table}")')
            cols = [row["name"] for row in cur.fetchall()]

            # Filtro opcional
            where        = ""
            params_where = []
            if flt:
                conditions   = " OR ".join(f'CAST("{c}" AS TEXT) LIKE ?' for c in cols)
                where        = f"WHERE {conditions}"
                params_where = [f"%{flt}%"] * len(cols)

            cur.execute(f'SELECT COUNT(*) FROM "{table}" {where}', params_where)
            self._total = cur.fetchone()[0]

            max_page  = max(0, (self._total - 1) // PAGE_SIZE) if self._total > 0 else 0
            self._page = max(0, min(page, max_page))
            offset    = self._page * PAGE_SIZE

            col_sql = ", ".join(f'"{c}"' for c in cols)
            cur.execute(
                f'SELECT {col_sql} FROM "{table}" {where} LIMIT {PAGE_SIZE} OFFSET {offset}',
                params_where,
            )
            rows = cur.fetchall()
            conn.close()

            self._populate_tree(cols, rows)
            pages = max(1, (self._total + PAGE_SIZE - 1) // PAGE_SIZE)
            self.lbl_page.config(text=f"Página {self._page + 1} / {pages}")
            self.lbl_count.config(text=f"{self._total} linhas", foreground="gray")

        except Exception as exc:
            self.lbl_count.config(text=f"Erro: {exc}", foreground="red")

    def _populate_tree(self, cols, rows):
        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120, minwidth=60, stretch=True)
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", tk.END, values=[row[c] for c in cols])
        make_treeview_sortable(self.tree)
