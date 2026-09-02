#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABA 1 — Importar: transfere dados de um SQLite (COLETOR) para MariaDB."""

import sqlite3
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from common.console_logger import ConsoleLogger

DEFAULT_TABLES = [
    "tb_filial",
    "tb_devices_detail",
    "tb_b12_data_collection_status",
    "tb_detected_devices",
    "tb_scan_runs",
    "tb_scan_run_items",
]


class Tab1Import(ttk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.cfg = config
        self._running = False
        self._create_ui()

    def _create_ui(self):
        # --- Arquivo SQLite ---
        frame_file = ttk.LabelFrame(self, text="Arquivo SQLite (COLETOR)", padding=8)
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

        # --- Opções ---
        frame_opts = ttk.LabelFrame(self, text="Opções", padding=8)
        frame_opts.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(frame_opts, text="Modo:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.var_mode = tk.StringVar(value="upsert")
        for col, mode in enumerate(("append", "upsert", "replace")):
            ttk.Radiobutton(
                frame_opts, text=mode, variable=self.var_mode, value=mode
            ).grid(row=0, column=col + 1, sticky="w", padx=4)

        ttk.Label(frame_opts, text="Batch:").grid(row=0, column=5, sticky="w", padx=(16, 4))
        self.var_batch = tk.StringVar(value="500")
        ttk.Entry(frame_opts, textvariable=self.var_batch, width=7).grid(
            row=0, column=6, sticky="w"
        )

        # --- Seleção de tabelas ---
        frame_tables = ttk.LabelFrame(self, text="Tabelas", padding=8)
        frame_tables.pack(fill=tk.X, padx=10, pady=5)

        self.table_vars = {}
        cols_per_row = 4
        for i, t in enumerate(DEFAULT_TABLES):
            var = tk.BooleanVar(value=True)
            self.table_vars[t] = var
            ttk.Checkbutton(frame_tables, text=t, variable=var).grid(
                row=i // cols_per_row, column=i % cols_per_row,
                sticky="w", padx=8, pady=2,
            )

        row_sel = ttk.Frame(frame_tables)
        row_sel.grid(
            row=(len(DEFAULT_TABLES) - 1) // cols_per_row + 1,
            column=0, columnspan=cols_per_row, sticky="w", pady=(6, 0),
        )
        ttk.Button(row_sel, text="Marcar todas",    command=lambda: self._set_all(True)).pack(side=tk.LEFT, padx=3)
        ttk.Button(row_sel, text="Desmarcar todas", command=lambda: self._set_all(False)).pack(side=tk.LEFT, padx=3)

        # --- Botões de ação ---
        frame_actions = ttk.Frame(self)
        frame_actions.pack(fill=tk.X, padx=10, pady=6)

        self.btn_dryrun  = ttk.Button(frame_actions, text="Dry-run",         command=lambda: self._run(execute=False))
        self.btn_execute = ttk.Button(frame_actions, text="Executar (gravar)", command=lambda: self._run(execute=True))
        self.btn_stop    = ttk.Button(frame_actions, text="Parar",            command=self._stop, state=tk.DISABLED)
        self.lbl_prog    = ttk.Label(frame_actions, text="", foreground="gray")

        self.btn_dryrun.pack(side=tk.LEFT, padx=4)
        self.btn_execute.pack(side=tk.LEFT, padx=4)
        self.btn_stop.pack(side=tk.LEFT, padx=4)
        self.lbl_prog.pack(side=tk.LEFT, padx=8)

        # --- Console de log ---
        frame_console = ttk.LabelFrame(self, text="Log", padding=4)
        frame_console.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.console = ConsoleLogger(frame_console, height=12, log_name="import")

    # -------------------------------------------------------------------------

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Selecionar SQLite do COLETOR",
            filetypes=[("SQLite", "*.db"), ("Todos", "*.*")],
        )
        if path:
            self.var_sqlite.set(path)

    def _set_all(self, value: bool):
        for var in self.table_vars.values():
            var.set(value)

    def _set_buttons(self, running: bool):
        state_run  = tk.DISABLED if running else tk.NORMAL
        state_stop = tk.NORMAL   if running else tk.DISABLED
        self.btn_dryrun.config(state=state_run)
        self.btn_execute.config(state=state_run)
        self.btn_stop.config(state=state_stop)

    def _stop(self):
        self._running = False
        self.console.log("Importação interrompida pelo usuário.", "WARNING")

    def _run(self, execute: bool):
        db_path = self.var_sqlite.get().strip()
        if not db_path:
            self.console.log("Selecione o arquivo SQLite antes de continuar.", "ERROR")
            return
        tables = [t for t, v in self.table_vars.items() if v.get()]
        if not tables:
            self.console.log("Selecione ao menos uma tabela.", "ERROR")
            return

        self._running = True
        self._set_buttons(running=True)
        label = "EXECUTE" if execute else "DRY-RUN"
        self.lbl_prog.config(text=f"{label}...")
        self.console.clear()
        self.console.log(f"Iniciando {label} — modo={self.var_mode.get()}", "INFO")

        threading.Thread(
            target=self._import_thread,
            args=(db_path, tables, execute),
            daemon=True,
        ).start()

    # -------------------------------------------------------------------------
    # Thread de importação
    # -------------------------------------------------------------------------

    def _import_thread(self, db_path, tables, execute):
        def log(msg, lvl="INFO"):
            self.console.log(msg, lvl)

        sqlite_conn = None
        maria_conn  = None

        try:
            if not Path(db_path).exists():
                log(f"SQLite não encontrado: {db_path}", "ERROR")
                return

            sqlite_conn = sqlite3.connect(db_path)
            sqlite_conn.row_factory = sqlite3.Row

            # Verificar integridade
            cur = sqlite_conn.cursor()
            cur.execute("PRAGMA integrity_check")
            if cur.fetchone()[0] != "ok":
                log("Falha na verificação de integridade do SQLite.", "ERROR")
                return
            log(f"SQLite íntegro: {db_path}", "SUCCESS")

            # Tabelas disponíveis
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            available = {row[0] for row in cur.fetchall()}
            missing    = [t for t in tables if t not in available]
            run_tables = [t for t in tables if t in available]

            if missing:
                log(f"Ausentes no SQLite: {', '.join(missing)}", "WARNING")
            if not run_tables:
                log("Nenhuma tabela selecionada existe no SQLite.", "ERROR")
                return

            # Conectar MariaDB
            try:
                maria_conn = self.cfg.connect_mariadb()
                log(
                    f"Conectado MariaDB: {self.cfg.mariadb_host()}:{self.cfg.mariadb_port()}"
                    f"/{self.cfg.mariadb_database()}",
                    "SUCCESS",
                )
            except Exception as exc:
                log(f"Falha ao conectar MariaDB: {exc}", "ERROR")
                return

            mode       = self.var_mode.get()
            batch_size = int(self.var_batch.get() or "500")
            database   = self.cfg.mariadb_database()
            log(f"Modo: {mode} | {'EXECUTE' if execute else 'DRY-RUN'}", "INFO")

            results = []
            for table in run_tables:
                if not self._running:
                    break
                results.append(
                    self._import_table(
                        sqlite_conn, maria_conn, table,
                        mode, batch_size, database, execute, log,
                    )
                )

            if execute and self._running:
                maria_conn.commit()
                log("Commit concluído.", "SUCCESS")
            else:
                maria_conn.rollback()
                msg = "Dry-run concluído — nada foi gravado." if not execute else "Rollback — operação interrompida."
                log(msg, "INFO" if not execute else "WARNING")

            ok_rows = sum(r["rows"] for r in results if r["status"] in ("OK", "DRY_RUN"))
            log(f"RESUMO: tabelas={len(results)}  linhas={ok_rows}", "SUCCESS")

        except Exception as exc:
            log(f"Erro inesperado: {exc}", "ERROR")
            if maria_conn:
                try:
                    maria_conn.rollback()
                except Exception:
                    pass
        finally:
            if sqlite_conn:
                try:
                    sqlite_conn.close()
                except Exception:
                    pass
            if maria_conn:
                try:
                    maria_conn.close()
                except Exception:
                    pass
            self._running = False
            self.after(0, self._set_buttons, False)
            self.after(0, lambda: self.lbl_prog.config(text=""))

    def _import_table(self, sqlite_conn, maria_conn, table, mode, batch_size, database, execute, log):
        mcur = maria_conn.cursor()

        # Verificar se tabela existe no MariaDB
        mcur.execute(
            "SELECT COUNT(*) FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s",
            (database, table),
        )
        if mcur.fetchone()[0] == 0:
            log(f"[SKIP] {table}: não existe no MariaDB", "WARNING")
            return {"table": table, "status": "SKIP", "rows": 0}

        # Colunas SQLite
        scur = sqlite_conn.cursor()
        scur.execute(f'PRAGMA table_info("{table}")')
        sqlite_cols = [row[1] for row in scur.fetchall()]

        # Colunas MariaDB
        mcur.execute(
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION",
            (database, table),
        )
        maria_set = {row[0] for row in mcur.fetchall()}
        columns   = [c for c in sqlite_cols if c in maria_set]

        if not columns:
            log(f"[SKIP] {table}: sem colunas compatíveis", "WARNING")
            return {"table": table, "status": "SKIP", "rows": 0}

        scur.execute(f'SELECT COUNT(*) FROM "{table}"')
        total = scur.fetchone()[0]
        log(f"[INFO] {table}: {total} linhas | {len(columns)} colunas compatíveis", "INFO")

        if total == 0:
            return {"table": table, "status": "OK", "rows": 0}
        if not execute:
            return {"table": table, "status": "DRY_RUN", "rows": total}

        def q(name):
            return "`" + name.replace("`", "``") + "`"

        col_list_sql   = ", ".join(f'"{c}"' for c in columns)
        col_list_maria = ", ".join(q(c) for c in columns)
        placeholders   = ", ".join(["%s"] * len(columns))
        tbl            = q(table)

        if mode == "append":
            sql = f"INSERT IGNORE INTO {tbl} ({col_list_maria}) VALUES ({placeholders})"
        elif mode == "replace":
            sql = f"REPLACE INTO {tbl} ({col_list_maria}) VALUES ({placeholders})"
        else:  # upsert
            updates = ", ".join(f"{q(c)}=VALUES({q(c)})" for c in columns)
            sql = (
                f"INSERT INTO {tbl} ({col_list_maria}) VALUES ({placeholders}) "
                f"ON DUPLICATE KEY UPDATE {updates}"
            )

        scur.execute(f'SELECT {col_list_sql} FROM "{table}"')
        rows_done = 0
        while self._running:
            batch = scur.fetchmany(batch_size)
            if not batch:
                break
            mcur.executemany(sql, [tuple(row[c] for c in columns) for row in batch])
            rows_done += len(batch)
            log(f"[DATA] {table}: {rows_done}/{total}", "INFO")

        return {"table": table, "status": "OK", "rows": rows_done}
