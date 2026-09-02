#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABA 6 - Configuração de credenciais dos equipamentos."""

import tkinter as tk
from tkinter import ttk, messagebox

from src.common.config import ConfigManager


PROFILE_SECTIONS = [
    ("B12 / PDV / Terminal Linux", "CREDENTIALS_LINUX_STORE", "Credencial compartilhada para equipamentos Linux da loja"),
    ("Terminal Windows Drogasil", "CREDENTIALS_TERMINAL_WINDOWS_DROGASIL", "Credencial Windows por logomarca Drogasil"),
    ("Terminal Windows Raia", "CREDENTIALS_TERMINAL_WINDOWS_RAIA", "Credencial Windows por logomarca Raia"),
]


class Tab6Credentials(ttk.Frame):
    """Tela de configuração de credenciais por tipo de equipamento/bandeira."""

    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.config_mgr = ConfigManager()
        self.rows = {}
        self._create_ui()
        self._load_values()

    def _create_ui(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(
            top,
            text=f"Criptografia local: {self.config_mgr.secret_provider()}",
            foreground="#444",
        ).pack(anchor=tk.W)

        ttk.Label(
            top,
            text=(
                "As senhas são salvas criptografadas no config.ini usando Fernet "
                "com chave local. Sem cryptography, usa b64 apenas como ofuscação."
            ),
            foreground="#444",
            wraplength=900,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(4, 0))

        body = ttk.Frame(self, padding=(10, 0, 10, 10))
        body.pack(fill=tk.BOTH, expand=True)

        for title, section, description in PROFILE_SECTIONS:
            self._add_profile(body, title, section, description)

        actions = ttk.Frame(self, padding=10)
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="Salvar Credenciais", command=self._save_values).pack(side=tk.LEFT)
        ttk.Button(actions, text="Recarregar", command=self._load_values).pack(side=tk.LEFT, padx=8)

    def _add_profile(self, parent, title, section, description):
        frame = ttk.LabelFrame(parent, text=title, padding=8)
        frame.pack(fill=tk.X, pady=5)

        ttk.Label(frame, text=description, foreground="#555").grid(
            row=0, column=0, columnspan=8, sticky=tk.W, pady=(0, 6)
        )

        user_var = tk.StringVar()
        pass_var = tk.StringVar()
        domain_var = tk.StringVar()
        port_var = tk.StringVar()
        timeout_var = tk.StringVar()

        ttk.Label(frame, text="Usuário:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=user_var, width=22).grid(row=1, column=1, padx=(4, 12), sticky=tk.W)

        ttk.Label(frame, text="Senha:").grid(row=1, column=2, sticky=tk.W)
        ttk.Entry(frame, textvariable=pass_var, width=24, show="*").grid(row=1, column=3, padx=(4, 12), sticky=tk.W)

        ttk.Label(frame, text="Domínio:").grid(row=1, column=4, sticky=tk.W)
        ttk.Entry(frame, textvariable=domain_var, width=18).grid(row=1, column=5, padx=(4, 12), sticky=tk.W)

        ttk.Label(frame, text="Porta:").grid(row=1, column=6, sticky=tk.W)
        ttk.Entry(frame, textvariable=port_var, width=7).grid(row=1, column=7, padx=(4, 12), sticky=tk.W)

        ttk.Label(frame, text="Timeout:").grid(row=1, column=8, sticky=tk.W)
        ttk.Entry(frame, textvariable=timeout_var, width=7).grid(row=1, column=9, padx=(4, 0), sticky=tk.W)

        self.rows[section] = {
            "user": user_var,
            "password": pass_var,
            "domain": domain_var,
            "port": port_var,
            "timeout": timeout_var,
        }

    def _load_values(self):
        defaults = {
            "CREDENTIALS_LINUX_STORE": {"user": "pdv", "port": "22", "timeout": "30"},
            "CREDENTIALS_TERMINAL_WINDOWS_DROGASIL": {"user": "drogasil", "port": "135", "timeout": "30"},
            "CREDENTIALS_TERMINAL_WINDOWS_RAIA": {"user": "drogaraia", "port": "135", "timeout": "30"},
        }

        for section, vars_ in self.rows.items():
            section_defaults = defaults.get(section, {})
            for key, var in vars_.items():
                if key == "password":
                    try:
                        var.set(self.config_mgr.get_secret(section, key, ""))
                    except Exception:
                        var.set("")
                    continue
                var.set(self.config_mgr.get(section, key, section_defaults.get(key, "")))

    def _save_values(self):
        try:
            for section, vars_ in self.rows.items():
                for key, var in vars_.items():
                    value = var.get().strip()
                    if key == "password":
                        self.config_mgr.set_secret(section, key, value)
                    else:
                        self.config_mgr.set(section, key, value)
            self.config_mgr.save()
            messagebox.showinfo("Credenciais", "Credenciais salvas com sucesso.")
        except Exception as exc:
            messagebox.showerror("Credenciais", f"Erro ao salvar credenciais: {exc}")
