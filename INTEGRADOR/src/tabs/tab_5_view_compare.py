#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABA 5 — Comparar: exibe SQLite e MariaDB lado a lado (somente leitura)."""

import sqlite3
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from common.treeview_sort import make_treeview_sortable

PAGE_SIZE = 100

DEFAULT_TABLES = [
    "tb_filial",
    "tb_devices_detail",
    "tb_b12_data_collection_status",
    "tb_detected_devices",
    "tb_scan_runs",
    "tb_scan_run_items",
    "tb_devices_detail_history",
    "tb_detected_devices_history",
]


class Tab5ViewCompare(ttk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.cfg   = config
        self._page = 0
        self._create_ui()

    def _create_ui(self):
        # --- Controles ---
        frame_ctrl = ttk.Frame(self)
        frame_ctrl.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.var_sqlite = tk.StringVar()
        ttk.Entry(frame_ctrl, textvariable=self.var_sqlite, width=36).pack(side=tk.LEFT)
        ttk.Button(frame_ctrl, text="...", width=3, command=self._browse).pack(
            side=tk.LEFT, padx=(2, 8)
        )

        self.var_table = tk.StringVar()
        self.combo_table = ttk.Combobox(
            frame_ctrl, textvariable=self.var_table, state="readonly", width=30
        )
        self.combo_table["values"] = DEFAULT_TABLES
        self.combo_table.set(DEFAULT_TABLES[0])
        self.combo_table.pack(side=tk.LEFT, padx=4)

        ttk.Button(
            frame_ctrl, text="Carregar", command=lambda: self._load_page(0)
        ).pack(side=tk.LEFT, padx=6)

        self.lbl_status = ttk.Label(frame_ctrl, text="", foreground="gray")
        self.lbl_status.pack(side=tk.LEFT, padx=8)

        # --- PanedWindow lado a lado ---
        pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        frame_left  = ttk.LabelFrame(pane, text="SQLite")
        frame_right = ttk.LabelFrame(pane, text="MariaDB")
        pane.add(frame_left,  weight=1)
        pane.add(frame_right, weight=1)

        self.tree_sqlite = self._make_tree(frame_left)
        self.tree_maria  = self._make_tree(frame_right)

        # --- Paginação ---
        frame_page = ttk.Frame(self)
        frame_page.pack(fill=tk.X, padx=10, pady=3)
        ttk.Button(
            frame_page, text="◄",
            command=lambda: self._load_page(self._page - 1),
        ).pack(side=tk.LEFT, padx=2)
        self.lbl_page = ttk.Label(frame_page, text="—")
        self.lbl_page.pack(side=tk.LEFT, padx=4)
        ttk.Button(
            frame_page, text="►",
            command=lambda: self._load_page(self._page + 1),
        ).pack(side=tk.LEFT, padx=2)

    def _make_tree(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)
        tree = ttk.Treeview(frame, show="headings")
        sb_y = ttk.Scrollbar(frame, orient=tk.VERTICAL,   command=tree.yview)
        sb_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side=tk.RIGHT,  fill=tk.Y)
        sb_x.pack(side=tk.BOTTOM, fill=tk.X)
        tree.pack(fill=tk.BOTH, expand=True)
        return tree

    # -------------------------------------------------------------------------

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Selecionar SQLite",
            filetypes=[("SQLite", "*.db"), ("Todos", "*.*")],
        )
        if path:
            self.var_sqlite.set(path)

    def _load_page(self, page: int):
        db_path = self.var_sqlite.get().strip()
        table   = self.var_table.get().strip()
        if not db_path or not table:
            self.lbl_status.config(text="Selecione SQLite e tabela.", foreground="red")
            return
        self.lbl_status.config(text="Carregando...", foreground="gray")
        threading.Thread(
            target=self._fetch_thread, args=(db_path, table, page), daemon=True
        ).start()

    def _fetch_thread(self, db_path, table, page):
        def q(name):
            return "`" + name.replace("`", "``") + "`"

        sqlite_cols, sqlite_rows, sqlite_total = [], [], 0
        maria_cols,  maria_rows,  maria_total  = [], [], 0

        # --- SQLite ---
        try:
            if Path(db_path).exists():
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cur  = conn.cursor()
                cur.execute(f'PRAGMA table_info("{table}")')
                sqlite_cols  = [r["name"] for r in cur.fetchall()]
                cur.execute(f'SELECT COUNT(*) FROM "{table}"')
                sqlite_total = cur.fetchone()[0]
                max_page = max(0, (sqlite_total - 1) // PAGE_SIZE) if sqlite_total > 0 else 0
                page     = max(0, min(page, max_page))
                offset   = page * PAGE_SIZE
                col_sql  = ", ".join(f'"{c}"' for c in sqlite_cols)
                cur.execute(
                    f'SELECT {col_sql} FROM "{table}" LIMIT {PAGE_SIZE} OFFSET {offset}'
                )
                sqlite_rows = [tuple(r[c] for c in sqlite_cols) for r in cur.fetchall()]
                conn.close()
        except Exception as exc:
            sqlite_cols = [f"Erro SQLite: {exc}"]

        # --- MariaDB ---
        try:
            mconn    = self.cfg.connect_mariadb()
            mcur     = mconn.cursor()
            database = self.cfg.mariadb_database()
            mcur.execute(
                "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION",
                (database, table),
            )
            maria_cols = [r[0] for r in mcur.fetchall()]
            if maria_cols:
                tbl = q(table)
                mcur.execute(f"SELECT COUNT(*) FROM {tbl}")
                maria_total = mcur.fetchone()[0]
                offset      = page * PAGE_SIZE
                col_list    = ", ".join(q(c) for c in maria_cols)
                mcur.execute(
                    f"SELECT {col_list} FROM {tbl} LIMIT {PAGE_SIZE} OFFSET {offset}"
                )
                maria_rows = list(mcur.fetchall())
            mconn.close()
        except Exception as exc:
            maria_cols = [f"Erro MariaDB: {exc}"]

        self._page = page
        s_pages = max(1, (sqlite_total + PAGE_SIZE - 1) // PAGE_SIZE) if sqlite_total else 1
        m_pages = max(1, (maria_total  + PAGE_SIZE - 1) // PAGE_SIZE) if maria_total  else 1
        pages   = max(s_pages, m_pages)

        def upd():
            self._populate_tree(self.tree_sqlite, sqlite_cols, sqlite_rows)
            self._populate_tree(self.tree_maria,  maria_cols,  maria_rows)
            self.lbl_page.config(
                text=(
                    f"Pág. {page + 1}/{pages} | "
                    f"SQLite: {sqlite_total}  MariaDB: {maria_total}"
                )
            )
            self.lbl_status.config(text="", foreground="gray")

        self.after(0, upd)

    def _populate_tree(self, tree, cols, rows):
        tree["columns"] = cols
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=100, minwidth=50, stretch=True)
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", tk.END, values=list(row))
        try:
            make_treeview_sortable(tree)
        except Exception:
            pass
