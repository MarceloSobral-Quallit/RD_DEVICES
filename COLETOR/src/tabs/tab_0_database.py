#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tab_0_database.py - ABA 0: Banco SQLite local

Responsabilidades do coletor:
  - Mostrar status e estatísticas do SQLite local
  - Verificar integridade
  - Criar backup online
  - Exportar uma cópia transportável do banco coletado
"""

import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime

from common.config import ConfigManager
from common.db_sync import SQLiteBackup
from common.runtime_paths import resource_path, resolve_runtime_path, app_dir


def _app_identity_header(log_name):
    try:
        from version import VERSION, BUILD_DATE
    except Exception:
        VERSION = "desconhecida"
        BUILD_DATE = "desconhecida"
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"# Console {log_name} iniciado em {started_at}\n"
        f"# Aplicativo: COLETOR\n"
        f"# Versao: {VERSION}\n"
        f"# Build: {BUILD_DATE}\n"
    )


class Tab0DatabaseManager:
    """ABA 0 - gerenciamento local do SQLite usado pelo coletor."""

    def __init__(self, parent, config: ConfigManager = None):
        self.parent = parent
        self.cfg = config or ConfigManager()
        self._running = False
        self._console_log_path = self._create_console_log_path()
        self._build_ui()
        self._load_saved_config()
        self._refresh_sqlite_status()

    def _build_ui(self):
        root = self.parent
        top_frame = ttk.Frame(root)
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 4))
        self._build_sqlite_section(top_frame)
        self._build_package_section(root)
        self._build_console(root)
        self._build_progress(root)

    def _build_sqlite_section(self, parent):
        grp = ttk.LabelFrame(parent, text="SQLite Local", padding=8)
        grp.pack(fill=tk.X)

        row1 = ttk.Frame(grp)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Banco de dados:").pack(side=tk.LEFT)
        self._sqlite_path_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self._sqlite_path_var, width=70).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 4)
        )
        ttk.Button(row1, text="...", width=3, command=self._browse_sqlite).pack(side=tk.LEFT)

        row2 = ttk.Frame(grp)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Dir. backups:").pack(side=tk.LEFT)
        self._backup_dir_var = tk.StringVar(value="./backups")
        ttk.Entry(row2, textvariable=self._backup_dir_var, width=70).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 4)
        )
        ttk.Button(row2, text="...", width=3, command=self._browse_backup_dir).pack(side=tk.LEFT)

        row3 = ttk.Frame(grp)
        row3.pack(fill=tk.X, pady=(6, 2))
        self._sqlite_status_var = tk.StringVar(value="-")
        ttk.Label(row3, text="Status:").pack(side=tk.LEFT)
        self._sqlite_status_lbl = ttk.Label(
            row3, textvariable=self._sqlite_status_var, foreground="gray"
        )
        self._sqlite_status_lbl.pack(side=tk.LEFT, padx=(6, 20))
        ttk.Button(row3, text="Atualizar", command=self._refresh_sqlite_status).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(row3, text="Verificar Integridade", command=self._check_integrity).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(row3, text="Backup Agora", command=self._do_backup).pack(side=tk.LEFT, padx=4)
        ttk.Button(row3, text="Abrir Backups", command=self._open_backup_dir).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(row3, text="Criar Banco Novo...", command=self._create_new_db).pack(
            side=tk.LEFT, padx=(20, 4)
        )

        self._stats_var = tk.StringVar(value="")
        ttk.Label(
            grp,
            textvariable=self._stats_var,
            foreground="#444",
            wraplength=900,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(4, 0))

    def _build_package_section(self, parent):
        grp = ttk.LabelFrame(parent, text="Pacote para Importador Admin", padding=8)
        grp.pack(fill=tk.X, padx=10, pady=4)

        ttk.Label(
            grp,
            text=(
                "Este coletor não acessa MariaDB. Ao finalizar a coleta, exporte uma cópia "
                "do SQLite e use a pasta INTEGRADOR na máquina admin."
            ),
            foreground="#444",
            wraplength=900,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 8))

        row = ttk.Frame(grp)
        row.pack(fill=tk.X)
        ttk.Button(row, text="Exportar devices.db...", command=self._export_sqlite_package).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(row, text="Salvar Config", command=self._save_config).pack(side=tk.LEFT, padx=4)

    def _build_console(self, parent):
        grp = ttk.LabelFrame(parent, text="Log da Operação", padding=4)
        grp.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        btn_row = ttk.Frame(grp)
        btn_row.pack(anchor=tk.E)
        ttk.Button(btn_row, text="Limpar", command=self._clear_console).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Salvar log...", command=self._save_log).pack(side=tk.LEFT, padx=4)

        from tkinter.scrolledtext import ScrolledText

        self._console = ScrolledText(
            grp, height=10, font=("Courier New", 9),
            bg="#1e1e1e", fg="#d4d4d4", state=tk.DISABLED,
        )
        self._console.pack(fill=tk.BOTH, expand=True)
        self._console.tag_config("INFO", foreground="#d4d4d4")
        self._console.tag_config("OK", foreground="#4ec9b0")
        self._console.tag_config("WARNING", foreground="#dcdcaa")
        self._console.tag_config("ERROR", foreground="#f48771")

    def _build_progress(self, parent):
        pg_frame = ttk.Frame(parent)
        pg_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        self._progress_var = tk.IntVar(value=0)
        self._progress_lbl = tk.StringVar(value="")
        self._progress_bar = ttk.Progressbar(
            pg_frame, variable=self._progress_var, maximum=100, length=500
        )
        self._progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(pg_frame, textvariable=self._progress_lbl, width=40).pack(
            side=tk.LEFT, padx=(8, 0)
        )

    def _load_saved_config(self):
        self._sqlite_path_var.set(self.cfg.get("DATABASE", "path", "./database/devices.db"))
        self._backup_dir_var.set(self.cfg.get("DATABASE", "backup_dir", "./backups"))

    def _save_config(self):
        self.cfg.set("DATABASE", "path", self._sqlite_path_var.get())
        self.cfg.set("DATABASE", "backup_dir", self._backup_dir_var.get())
        self.cfg.save()
        self._log("Configuração SQLite salva.", "OK")

    def _create_console_log_path(self):
        logs_dir = app_dir() / "logs" / "console"
        logs_dir.mkdir(parents=True, exist_ok=True)
        path = logs_dir / f"{datetime.now():%Y%m%d_%H%M%S}_aba_0_sqlite.log"
        path.write_text(_app_identity_header("aba_0_sqlite"), encoding="utf-8")
        return path

    def _log(self, msg: str, level: str = "INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        try:
            file_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self._console_log_path.open("a", encoding="utf-8") as fh:
                fh.write(f"[{file_ts}] [{level}] {msg}\n")
        except OSError:
            pass
        self.parent.after(0, self._console_insert, line, level)

    def _console_insert(self, line: str, level: str):
        self._console.config(state=tk.NORMAL)
        self._console.insert(tk.END, line, level)
        self._console.see(tk.END)
        self._console.config(state=tk.DISABLED)

    def _set_progress(self, pct: int, label: str = ""):
        self.parent.after(0, self._progress_var.set, pct)
        self.parent.after(0, self._progress_lbl.set, label)

    def _clear_console(self):
        self._console.config(state=tk.NORMAL)
        self._console.delete("1.0", tk.END)
        self._console.config(state=tk.DISABLED)

    def _save_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
            title="Salvar log",
        )
        if path:
            content = self._console.get("1.0", tk.END)
            Path(path).write_text(content, encoding="utf-8")
            self._log(f"Log salvo em: {path}", "OK")

    def _browse_sqlite(self):
        path = filedialog.askopenfilename(
            title="Selecionar banco SQLite",
            filetypes=[("SQLite", "*.db *.sqlite *.sqlite3"), ("Todos", "*.*")],
        )
        if path:
            self._sqlite_path_var.set(path)
            self._refresh_sqlite_status()

    def _browse_backup_dir(self):
        path = filedialog.askdirectory(title="Selecionar diretório de backup")
        if path:
            self._backup_dir_var.set(path)

    def _open_backup_dir(self):
        backup_dir = Path(self._backup_dir_var.get())
        backup_dir.mkdir(parents=True, exist_ok=True)
        import os
        import subprocess
        import sys

        if sys.platform == "win32":
            os.startfile(str(backup_dir))
        else:
            subprocess.Popen(["xdg-open", str(backup_dir)])

    def _get_backup_engine(self) -> SQLiteBackup:
        sqlite_path = resolve_runtime_path(self._sqlite_path_var.get(), app_dir())
        backup_dir = resolve_runtime_path(self._backup_dir_var.get(), app_dir())
        return SQLiteBackup(
            sqlite_path=sqlite_path,
            backup_dir=backup_dir,
        )

    def _set_busy(self, busy: bool):
        self._running = busy

    def _refresh_sqlite_status(self):
        sqlite_path = self._sqlite_path_var.get()
        if not sqlite_path:
            self._sqlite_status_var.set("Caminho não definido")
            self._sqlite_status_lbl.config(foreground="orange")
            return

        path = resolve_runtime_path(sqlite_path, app_dir())
        if not path.exists():
            self._sqlite_status_var.set("Arquivo não encontrado")
            self._sqlite_status_lbl.config(foreground="red")
            self._stats_var.set(f"Caminho esperado: {path}")
            return

        size_mb = path.stat().st_size / 1048576
        engine = SQLiteBackup(sqlite_path=path, backup_dir="")
        stats = engine.get_stats()

        if stats:
            n_tables = len(stats.get("tables", {}))
            total_rows = sum(v for v in stats.get("tables", {}).values() if v >= 0)
            self._sqlite_status_var.set(
                f"OK | {size_mb:.2f} MB | {n_tables} tabelas | {total_rows:,} registros"
            )
            self._sqlite_status_lbl.config(foreground="#4ec9b0")
            tbl_info = "  ".join(f"{t}:{n}" for t, n in sorted(stats["tables"].items()))
            self._stats_var.set(f"Tabelas: {tbl_info}")
        else:
            self._sqlite_status_var.set(f"{size_mb:.2f} MB (sem acesso)")
            self._sqlite_status_lbl.config(foreground="orange")
            self._stats_var.set("")

    def _check_integrity(self):
        engine = self._get_backup_engine()
        ok, msg = engine.verify()
        level = "OK" if ok else "ERROR"
        self._log(f"Integridade SQLite: {msg}", level)
        if ok:
            messagebox.showinfo("Verificação de Integridade", msg)
        else:
            messagebox.showerror("Verificação de Integridade", msg)

    def _do_backup(self):
        if self._running:
            return
        self._set_busy(True)
        self._log("Iniciando backup SQLite...", "INFO")

        def _run():
            try:
                self._save_config()
                engine = self._get_backup_engine()
                path = engine.create(progress_cb=lambda pct, lbl: self._set_progress(pct, lbl))
                self._log(f"Backup criado: {path}", "OK")
                self._set_progress(100, "Backup concluído")
                self._log(f"Total de backups disponíveis: {len(engine.list_backups())}", "INFO")
            except Exception as e:
                self._log(f"ERRO no backup: {e}", "ERROR")
            finally:
                self.parent.after(0, self._set_busy, False)

        threading.Thread(target=_run, daemon=True).start()

    def _create_new_db(self):
        """Cria um banco SQLite vazio usando config/schema_sqlite_init.sql."""
        schema_path = resource_path("config", "schema_sqlite_init.sql")
        if not schema_path.exists():
            messagebox.showerror(
                "Criar Banco Novo",
                f"Schema não encontrado:\n{schema_path}",
            )
            return

        target = filedialog.asksaveasfilename(
            title="Criar banco SQLite vazio",
            defaultextension=".db",
            initialfile="devices.db",
            filetypes=[("SQLite", "*.db *.sqlite *.sqlite3"), ("Todos", "*.*")],
        )
        if not target:
            return

        target_path = Path(target)
        if target_path.exists():
            if not messagebox.askyesno(
                "Criar Banco Novo",
                f"O arquivo já existe e será substituído:\n{target_path}\n\nContinuar?",
            ):
                return
            target_path.unlink()

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            sql = schema_path.read_text(encoding="utf-8")
            import sqlite3 as _sqlite3
            conn = _sqlite3.connect(str(target_path))
            conn.executescript(sql)
            conn.close()

            self._sqlite_path_var.set(str(target_path))
            self._save_config()
            self._refresh_sqlite_status()
            self._log(f"Banco criado com sucesso: {target_path}", "OK")
            messagebox.showinfo(
                "Criar Banco Novo",
                f"Banco criado:\n{target_path}\n\nImporte o XLS na Aba 1 para popular tb_filial.",
            )
        except Exception as e:
            self._log(f"ERRO ao criar banco: {e}", "ERROR")
            messagebox.showerror("Criar Banco Novo", str(e))

    def _export_sqlite_package(self):
        source = resolve_runtime_path(self._sqlite_path_var.get(), app_dir())
        if not source.exists():
            messagebox.showerror("Exportar SQLite", "Banco SQLite não encontrado.")
            return

        target = filedialog.asksaveasfilename(
            title="Exportar banco coletado",
            defaultextension=".db",
            initialfile=source.name,
            filetypes=[("SQLite", "*.db *.sqlite *.sqlite3"), ("Todos", "*.*")],
        )
        if not target:
            return

        try:
            self._save_config()
            target_path = Path(target)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target_path)
            self._log(f"SQLite exportado para: {target_path}", "OK")
            messagebox.showinfo(
                "Exportar SQLite",
                "Arquivo exportado. Use este .db com INTEGRADOR na máquina admin.",
            )
        except Exception as e:
            self._log(f"ERRO ao exportar SQLite: {e}", "ERROR")
            messagebox.showerror("Exportar SQLite", str(e))
