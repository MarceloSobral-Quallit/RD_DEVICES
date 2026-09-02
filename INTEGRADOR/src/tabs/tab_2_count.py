#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABA 2 — Contagem de Linhas: compara SQLite × MariaDB por tabela."""

import sqlite3
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from common.treeview_sort import make_treeview_sortable

DEFAULT_TABLES = [
    "tb_filial",
    "tb_devices_detail",
    "tb_b12_data_collection_status",
    "tb_detected_devices",
    "tb_scan_runs",
    "tb_scan_run_items",
]


class Tab2Count(ttk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.cfg = config
        self._create_ui()

    def _create_ui(self):
        # --- Arquivo SQLite ---
        frame_file = ttk.LabelFrame(self, text="Arquivo SQLite", padding=8)
        frame_file.pack(fill=tk.X, padx=10, pady=(10, 5))

        row_file = ttk.Frame(frame_file)
        row_file.pack(fill=tk.X)
        self.var_sqlite = tk.StringVar()
        ttk.Entry(row_file, textvariable=self.var_sqlite, width=64).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(row_file, text="...", width=3, command=self._browse).pack(
            side=tk.LEFT, padx=(4, 0)
        )

        # --- Botão e status ---
        frame_btn = ttk.Frame(self)
        frame_btn.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(frame_btn, text="Atualizar contagem", command=self._refresh).pack(side=tk.LEFT)
        self.lbl_status = ttk.Label(frame_btn, text="", foreground="gray")
        self.lbl_status.pack(side=tk.LEFT, padx=10)

        # --- Treeview ---
        frame_tree = ttk.Frame(self)
        frame_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("tabela", "sqlite", "mariadb", "diferenca")
        self.tree = ttk.Treeview(frame_tree, columns=cols, show="headings", height=16)

        headers = {
            "tabela":    "Tabela",
            "sqlite":    "SQLite",
            "mariadb":   "MariaDB",
            "diferenca": "Diferença",
        }
        widths = {"tabela": 280, "sqlite": 110, "mariadb": 110, "diferenca": 110}
        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(
                c, width=widths[c],
                anchor="w" if c == "tabela" else "center",
            )

        sb = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        make_treeview_sortable(self.tree)

        self.tree.tag_configure("ok",   foreground="green")
        self.tree.tag_configure("diff", foreground="orange")
        self.tree.tag_configure("skip", foreground="gray")

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Selecionar SQLite",
            filetypes=[("SQLite", "*.db"), ("Todos", "*.*")],
        )
        if path:
            self.var_sqlite.set(path)

    def _refresh(self):
        db_path = self.var_sqlite.get().strip()
        if not db_path:
            self.lbl_status.config(text="Selecione o arquivo SQLite.", foreground="red")
            return
        self.lbl_status.config(text="Consultando...", foreground="gray")
        self.tree.delete(*self.tree.get_children())
        threading.Thread(target=self._count_thread, args=(db_path,), daemon=True).start()

    def _count_thread(self, db_path):
        sqlite_counts: dict = {}
        maria_counts: dict  = {}
        error = None

        # --- SQLite ---
        try:
            if Path(db_path).exists():
                conn = sqlite3.connect(db_path)
                cur  = conn.cursor()
                for t in DEFAULT_TABLES:
                    try:
                        cur.execute(f'SELECT COUNT(*) FROM "{t}"')
                        sqlite_counts[t] = cur.fetchone()[0]
                    except Exception:
                        sqlite_counts[t] = None
                conn.close()
        except Exception as exc:
            error = f"SQLite: {exc}"

        # --- MariaDB ---
        try:
            mconn    = self.cfg.connect_mariadb()
            mcur     = mconn.cursor()
            database = self.cfg.mariadb_database()
            for t in DEFAULT_TABLES:
                try:
                    mcur.execute(
                        f"SELECT COUNT(*) FROM `{database}`.`{t}`"
                    )
                    maria_counts[t] = mcur.fetchone()[0]
                except Exception:
                    maria_counts[t] = None
            mconn.close()
        except Exception as exc:
            error = f"MariaDB: {exc}"

        # --- Montar linhas ---
        rows = []
        for t in DEFAULT_TABLES:
            s = sqlite_counts.get(t)
            m = maria_counts.get(t)
            s_str = str(s) if s is not None else "—"
            m_str = str(m) if m is not None else "—"
            if s is None or m is None:
                diff_str, tag = "—", "skip"
            else:
                diff     = s - m
                diff_str = f"{diff:+d}" if diff != 0 else "0"
                tag      = "ok" if diff == 0 else "diff"
            rows.append((t, s_str, m_str, diff_str, tag))

        def update_ui():
            self.tree.delete(*self.tree.get_children())
            for t, s_str, m_str, diff_str, tag in rows:
                self.tree.insert("", tk.END, values=(t, s_str, m_str, diff_str), tags=(tag,))
            if error:
                self.lbl_status.config(text=f"Aviso: {error}", foreground="orange")
            else:
                self.lbl_status.config(text="Atualizado.", foreground="green")

        self.after(0, update_ui)
