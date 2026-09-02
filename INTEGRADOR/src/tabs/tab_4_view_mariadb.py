#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABA 4 — Visualizar MariaDB: exibe dados de tabelas no servidor MariaDB."""

import threading
import tkinter as tk
from tkinter import ttk

from common.treeview_sort import make_treeview_sortable

PAGE_SIZE = 200


class Tab4ViewMariaDB(ttk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.cfg    = config
        self._page  = 0
        self._total = 0
        self._create_ui()

    def _create_ui(self):
        # --- Controles ---
        frame_ctrl = ttk.Frame(self)
        frame_ctrl.pack(fill=tk.X, padx=10, pady=(10, 5))

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
        self.lbl_status = ttk.Label(frame_page, text="", foreground="gray")
        self.lbl_status.pack(side=tk.LEFT, padx=12)

    # -------------------------------------------------------------------------

    def _load_tables(self):
        self.lbl_status.config(text="Conectando...", foreground="gray")
        self.update_idletasks()
        threading.Thread(target=self._load_tables_thread, daemon=True).start()

    def _load_tables_thread(self):
        try:
            conn     = self.cfg.connect_mariadb()
            cur      = conn.cursor()
            database = self.cfg.mariadb_database()
            cur.execute(
                "SELECT TABLE_NAME FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA=%s ORDER BY TABLE_NAME",
                (database,),
            )
            tables = [row[0] for row in cur.fetchall()]
            conn.close()

            def upd():
                self.combo_table["values"] = tables
                if tables:
                    self.combo_table.set(tables[0])
                    self._load_page(0)
                self.lbl_status.config(text=f"{len(tables)} tabelas", foreground="gray")

            self.after(0, upd)
        except Exception as exc:
            self.after(0, lambda: self.lbl_status.config(
                text=f"Erro: {exc}", foreground="red"
            ))

    def _load_page(self, page: int):
        table = self.var_table.get().strip()
        if not table:
            return
        flt = self.var_filter.get().strip()
        threading.Thread(
            target=self._fetch_thread, args=(table, page, flt), daemon=True
        ).start()

    def _fetch_thread(self, table, page, flt):
        def q(name):
            return "`" + name.replace("`", "``") + "`"

        try:
            conn     = self.cfg.connect_mariadb()
            cur      = conn.cursor()
            database = self.cfg.mariadb_database()

            # Colunas
            cur.execute(
                "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION",
                (database, table),
            )
            cols = [row[0] for row in cur.fetchall()]

            # Filtro opcional
            tbl          = q(table)
            where        = ""
            params_where = []
            if flt:
                conditions   = " OR ".join(f"CAST({q(c)} AS CHAR) LIKE %s" for c in cols)
                where        = f"WHERE {conditions}"
                params_where = [f"%{flt}%"] * len(cols)

            # Total
            cur.execute(f"SELECT COUNT(*) FROM {tbl} {where}", params_where)
            total = cur.fetchone()[0]

            max_page = max(0, (total - 1) // PAGE_SIZE) if total > 0 else 0
            page     = max(0, min(page, max_page))
            offset   = page * PAGE_SIZE

            col_list = ", ".join(q(c) for c in cols)
            cur.execute(
                f"SELECT {col_list} FROM {tbl} {where} LIMIT {PAGE_SIZE} OFFSET {offset}",
                params_where,
            )
            rows = cur.fetchall()
            conn.close()

            pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

            def upd():
                self._page  = page
                self._total = total
                self._populate_tree(cols, rows)
                self.lbl_page.config(text=f"Página {page + 1} / {pages}")
                self.lbl_status.config(text=f"{total} linhas", foreground="gray")

            self.after(0, upd)

        except Exception as exc:
            self.after(0, lambda: self.lbl_status.config(
                text=f"Erro: {exc}", foreground="red"
            ))

    def _populate_tree(self, cols, rows):
        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120, minwidth=60, stretch=True)
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", tk.END, values=list(row))
        make_treeview_sortable(self.tree)
