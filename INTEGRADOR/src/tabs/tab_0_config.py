#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABA 0 — Configuração: edita config.ini e testa conexão MariaDB."""

import tkinter as tk
from tkinter import ttk
import threading
import logging

from common.runtime_paths import default_config_path

logger = logging.getLogger(__name__)


class Tab0Config(ttk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.cfg = config
        self._create_ui()
        self._load_fields()

    def _create_ui(self):
        # --- Frame de conexão ---
        frame_conn = ttk.LabelFrame(self, text="Conexão MariaDB", padding=12)
        frame_conn.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.vars = {
            "host":     tk.StringVar(),
            "port":     tk.StringVar(),
            "user":     tk.StringVar(),
            "database": tk.StringVar(),
            "charset":  tk.StringVar(),
            "password": tk.StringVar(),
        }

        fields = [
            ("host",     "Host:",     False),
            ("port",     "Porta:",    False),
            ("user",     "Usuário:",  False),
            ("database", "Database:", False),
            ("charset",  "Charset:",  False),
            ("password", "Senha:",    True),
        ]

        for i, (key, label, is_pass) in enumerate(fields):
            ttk.Label(frame_conn, text=label, width=12, anchor="e").grid(
                row=i, column=0, sticky="e", padx=(0, 6), pady=4
            )
            kw = {"show": "*"} if is_pass else {}
            ttk.Entry(frame_conn, textvariable=self.vars[key], width=42, **kw).grid(
                row=i, column=1, sticky="w", pady=4
            )

        # --- Botões ---
        frame_btn = ttk.Frame(self)
        frame_btn.pack(fill=tk.X, padx=10, pady=6)
        ttk.Button(frame_btn, text="Salvar configuração", command=self._save).pack(side=tk.LEFT, padx=4)
        ttk.Button(frame_btn, text="Testar conexão",      command=self._test).pack(side=tk.LEFT, padx=4)

        # --- Status de conexão ---
        self.lbl_status = ttk.Label(self, text="", foreground="gray")
        self.lbl_status.pack(anchor="w", padx=14, pady=2)

        # --- Segurança ---
        frame_sec = ttk.LabelFrame(self, text="Segurança", padding=10)
        frame_sec.pack(fill=tk.X, padx=10, pady=5)
        self.lbl_provider = ttk.Label(frame_sec, text="", foreground="gray")
        self.lbl_provider.pack(anchor="w")
        self._refresh_provider()

        # --- Arquivo de configuração ---
        frame_file = ttk.LabelFrame(self, text="Arquivo de configuração", padding=10)
        frame_file.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(frame_file, text=str(default_config_path()), foreground="blue").pack(anchor="w")

    def _refresh_provider(self):
        try:
            provider = self.cfg.secret_provider()
            self.lbl_provider.config(text=f"Provedor de segredo: {provider}")
        except Exception:
            self.lbl_provider.config(text="Provedor: indisponível")

    def _load_fields(self):
        self.vars["host"].set(self.cfg.mariadb_host())
        self.vars["port"].set(str(self.cfg.mariadb_port()))
        self.vars["user"].set(self.cfg.mariadb_user())
        self.vars["database"].set(self.cfg.mariadb_database())
        self.vars["charset"].set(self.cfg.mariadb_charset())
        self.vars["password"].set(self.cfg.mariadb_password())

    def _save(self):
        try:
            self.cfg.save_mariadb_settings(
                host=self.vars["host"].get().strip(),
                port=int(self.vars["port"].get().strip() or "3306"),
                user=self.vars["user"].get().strip(),
                database=self.vars["database"].get().strip(),
                charset=self.vars["charset"].get().strip() or "utf8mb4",
                password=self.vars["password"].get() or None,
            )
            self.lbl_status.config(text="✔ Configuração salva.", foreground="green")
            self._refresh_provider()
        except Exception as exc:
            from tkinter import messagebox
            messagebox.showerror("Erro ao salvar", str(exc))

    def _test(self):
        self.lbl_status.config(text="Testando conexão...", foreground="gray")
        self.update_idletasks()
        pwd = self.vars["password"].get() or None

        def run():
            try:
                conn = self.cfg.connect_mariadb(password=pwd)
                cur = conn.cursor()
                cur.execute("SELECT VERSION()")
                ver = cur.fetchone()[0]
                conn.close()
                self.after(0, lambda: self.lbl_status.config(
                    text=f"✔ Conectado — MariaDB {ver}", foreground="green"
                ))
            except Exception as exc:
                self.after(0, lambda: self.lbl_status.config(
                    text=f"✘ Falha: {exc}", foreground="red"
                ))

        threading.Thread(target=run, daemon=True).start()
