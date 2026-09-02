#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABA 3 — Scan Loja: detecta dispositivos por SSH/Radmin nas lojas selecionadas."""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from src.common import scan_core
from src.common.config import ConfigManager
from src.common.console_logger import ConsoleLogger
from src.common.scan_runs import finish_scan_run, record_scan_item, start_scan_run
from src.common.treeview_sort import make_treeview_sortable
from src.common.utils import get_store_scan_targets


class Tab3DetectDevices(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.parent = parent
        self.config_mgr = ConfigManager()
        self.stop_event = threading.Event()
        self.results = []
        self._all_stores = []
        self._create_ui()
        self.after(100, self._load_stores)

    def _create_ui(self):
        frame_filter = ttk.LabelFrame(self, text="Selecao de Lojas — Scan Loja", padding=8)
        frame_filter.pack(fill=tk.X, padx=10, pady=(10, 0))

        row1 = ttk.Frame(frame_filter)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Logomarca:").pack(side=tk.LEFT)
        self.var_logo = tk.StringVar(value="TODAS")
        for logo in ("TODAS", "DROGASIL", "RAIA"):
            ttk.Radiobutton(row1, text=logo, variable=self.var_logo, value=logo,
                            command=self._apply_filter).pack(side=tk.LEFT, padx=6)
        ttk.Separator(row1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(row1, text="Busca:").pack(side=tk.LEFT)
        self.var_search = tk.StringVar()
        self.var_search.trace_add("write", lambda *_: self._apply_filter())
        ttk.Entry(row1, textvariable=self.var_search, width=25).pack(side=tk.LEFT, padx=4)
        ttk.Button(row1, text="X", width=2, command=lambda: self.var_search.set("")).pack(side=tk.LEFT)
        ttk.Separator(row1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(row1, text="JAVA:").pack(side=tk.LEFT)
        self.var_java_from = tk.StringVar()
        self.var_java_to = tk.StringVar()
        self.var_java_from.trace_add("write", lambda *_: self._apply_filter())
        self.var_java_to.trace_add("write", lambda *_: self._apply_filter())
        ttk.Entry(row1, textvariable=self.var_java_from, width=6).pack(side=tk.LEFT, padx=(4, 2))
        ttk.Label(row1, text="ate").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.var_java_to, width=6).pack(side=tk.LEFT, padx=(2, 4))
        ttk.Separator(row1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        self.var_only_unscanned = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            row1,
            text="Somente nao escaneado",
            variable=self.var_only_unscanned,
            command=self._apply_filter,
        ).pack(side=tk.LEFT, padx=6)
        ttk.Separator(row1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Button(row1, text="Recarregar", command=self._load_stores).pack(side=tk.LEFT, padx=4)

        row2 = ttk.Frame(frame_filter)
        row2.pack(fill=tk.X, pady=(4, 2))
        self.lbl_count = ttk.Label(row2, text="0 lojas", foreground="gray")
        self.lbl_count.pack(side=tk.LEFT, padx=(0, 12))
        ttk.Button(row2, text="Marcar todas",    command=self._select_all).pack(side=tk.LEFT, padx=3)
        ttk.Button(row2, text="Desmarcar todas", command=self._deselect_all).pack(side=tk.LEFT, padx=3)
        ttk.Button(row2, text="Inverter",        command=self._invert_selection).pack(side=tk.LEFT, padx=3)
        ttk.Button(row2, text="Nao escaneadas",
                   command=lambda: self._select_by_scan_status("NAO ESCANEADO")).pack(side=tk.LEFT, padx=3)
        ttk.Button(row2, text="Escaneadas",
                   command=lambda: self._select_by_scan_status("ESCANEADO")).pack(side=tk.LEFT, padx=3)
        self.lbl_selected = ttk.Label(row2, text="0 selecionadas", foreground="blue")
        self.lbl_selected.pack(side=tk.LEFT, padx=12)

        frame_list = ttk.Frame(self)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 0))
        vscroll = ttk.Scrollbar(frame_list, orient=tk.VERTICAL)
        hscroll = ttk.Scrollbar(frame_list, orient=tk.HORIZONTAL)
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        cols = ("filial", "hist", "nome", "cidade", "uf", "logo", "ip", "cidr", "scan")
        self.tree_stores = ttk.Treeview(frame_list, columns=cols, show="headings",
                                        selectmode="extended", yscrollcommand=vscroll.set,
                                        xscrollcommand=hscroll.set, height=5)
        self.tree_stores.pack(fill=tk.BOTH, expand=True)
        vscroll.config(command=self.tree_stores.yview)
        hscroll.config(command=self.tree_stores.xview)
        for col, label, width in [("filial","JAVA",70),("hist","HISTORICO",90),("nome","Nome",200),
                       ("cidade","Cidade",140),("uf","UF",35),("logo","Logo",75),
                       ("ip","IP Banco 12",120),("cidr","CIDR",65),("scan","Status",130)]:
            self.tree_stores.heading(col, text=label)
            self.tree_stores.column(col, width=width, anchor=tk.W)
        self._sort_stores = make_treeview_sortable(self.tree_stores)
        self.tree_stores.bind("<<TreeviewSelect>>", self._on_select)

        frame_options = ttk.LabelFrame(self, text="Opcoes de Scan", padding=8)
        frame_options.pack(fill=tk.X, padx=10, pady=4)
        self.opt_ssh     = tk.BooleanVar(value=True)
        self.opt_radmin  = tk.BooleanVar(value=True)
        self.opt_printer = tk.BooleanVar(value=True)
        self.opt_full_refresh = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_options, text="SSH (22)",          variable=self.opt_ssh).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(frame_options, text="Radmin (7856)",     variable=self.opt_radmin).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(frame_options, text="Impressora (9100)", variable=self.opt_printer).pack(side=tk.LEFT, padx=5)
        ttk.Label(frame_options, text="Workers:").pack(side=tk.LEFT, padx=(20, 4))
        self.spin_workers = ttk.Spinbox(frame_options, from_=1, to=64, width=4)
        self.spin_workers.set(16)
        self.spin_workers.pack(side=tk.LEFT)
        ttk.Label(frame_options, text="Timeout (s):").pack(side=tk.LEFT, padx=(20, 4))
        self.spin_timeout = ttk.Spinbox(frame_options, from_=1, to=10, width=4)
        self.spin_timeout.set(2)
        self.spin_timeout.pack(side=tk.LEFT)
        ttk.Separator(frame_options, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=12)
        ttk.Checkbutton(
            frame_options, text="Full Refresh (sobrescrever existentes)",
            variable=self.opt_full_refresh,
        ).pack(side=tk.LEFT, padx=5)

        frame_console = ttk.LabelFrame(self, text="Log em Tempo Real", padding=8)
        frame_console.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        self.console_logger = ConsoleLogger(frame_console, height=10, log_name="aba_3_scan_loja")

        frame_action = ttk.Frame(self)
        frame_action.pack(fill=tk.X, padx=10, pady=(4, 10))
        self.progress = ttk.Progressbar(frame_action, mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.lbl_progress = ttk.Label(frame_action, text="0%", width=16)
        self.lbl_progress.pack(side=tk.LEFT)
        self.btn_scan = ttk.Button(frame_action, text="Iniciar Scan", command=self._start_scan)
        self.btn_scan.pack(side=tk.LEFT, padx=5)
        self.btn_cancel = ttk.Button(frame_action, text="Cancelar",
                                     command=lambda: self.stop_event.set(), state=tk.DISABLED)
        self.btn_cancel.pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_action, text="Salvar", command=self._save_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_action, text="Limpar selecionadas", command=self._clear_selected_scans).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_action, text="Reprocessar", command=self._reprocess_selected).pack(side=tk.LEFT, padx=5)

    def _load_stores(self):
        try:
            conn = self.config_mgr.get_sqlite_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT f.filial, f.historico, f.nome_filial, f.cidade, f.uf, f.logomarca, f.ip_banco_12,
                       COALESCE(f.cidr, '') AS cidr,
                       CASE
                           WHEN EXISTS (
                               SELECT 1 FROM tb_detected_devices d WHERE d.filial = f.filial
                           ) THEN 'ESCANEADO'
                           ELSE 'NAO ESCANEADO'
                       END AS scan_status
                FROM tb_filial f
                WHERE f.ativo = 1
                ORDER BY logomarca, CAST(filial AS INTEGER)
            """)
            rows = [tuple(row) for row in cur.fetchall()]
            conn.close()
            self._all_stores = rows
            self._apply_filter()
            self.console_logger.log(f"{len(rows)} lojas carregadas.", "INFO")
        except Exception as e:
            self.console_logger.log(f"Erro ao carregar lojas: {e}", "ERROR")

    def _java_in_range(self, value):
        start = self.var_java_from.get().strip()
        end = self.var_java_to.get().strip()
        if not start and not end:
            return True
        try:
            java = int(str(value).strip())
            start_num = int(start) if start else None
            end_num = int(end) if end else None
        except ValueError:
            return False
        if start_num is not None and end_num is not None and start_num > end_num:
            start_num, end_num = end_num, start_num
        if start_num is not None and java < start_num:
            return False
        if end_num is not None and java > end_num:
            return False
        return True

    def _apply_filter(self):
        logo_filter   = self.var_logo.get()
        search_filter = self.var_search.get().strip().lower()
        only_unscanned = self.var_only_unscanned.get()
        filtered = [
            row for row in self._all_stores
            if (logo_filter == "TODAS" or str(row[5]).upper() == logo_filter)
            and (not search_filter or any(search_filter in str(v).lower() for v in row))
            and self._java_in_range(row[0])
            and (not only_unscanned or str(row[8]).upper() == "NAO ESCANEADO")
        ]
        self.tree_stores.delete(*self.tree_stores.get_children())
        for row in filtered:
            self.tree_stores.insert("", tk.END, values=tuple(row))
        self._sort_stores("filial", descending=False)
        self.lbl_count.config(text=f"{len(filtered)} lojas")
        self._update_selected_label()

    def _on_select(self, _event=None):
        self._update_selected_label()

    def _update_selected_label(self):
        n = len(self.tree_stores.selection())
        self.lbl_selected.config(text=f"{n} selecionada{'s' if n != 1 else ''}")

    def _select_all(self):
        self.tree_stores.selection_set(self.tree_stores.get_children())
        self._update_selected_label()

    def _deselect_all(self):
        self.tree_stores.selection_remove(self.tree_stores.get_children())
        self._update_selected_label()

    def _invert_selection(self):
        all_items = set(self.tree_stores.get_children())
        selected  = set(self.tree_stores.selection())
        self.tree_stores.selection_set(list(all_items - selected))
        self._update_selected_label()

    def _select_by_scan_status(self, status):
        matches = [
            iid for iid in self.tree_stores.get_children()
            if str(self.tree_stores.item(iid, "values")[8]).upper() == status
        ]
        self.tree_stores.selection_set(matches)
        self._update_selected_label()

    def _start_scan(self):
        selected = self.tree_stores.selection()
        if not selected:
            messagebox.showwarning("Atencao", "Selecione ao menos uma loja.")
            return
        self.scan_targets = []
        for iid in selected:
            vals = self.tree_stores.item(iid, "values")
            filial, hist, nome, cidade, uf, logo, ip, cidr, scan_status = vals
            ip   = str(ip).strip()
            cidr = str(cidr).strip()
            if ip and ip not in ("", "0", "0.0"):
                for t in get_store_scan_targets(ip, cidr or None):
                    self.scan_targets.append((str(filial), str(nome), t["ip"], t["expected_type"], str(logo)))
        if not self.scan_targets:
            messagebox.showwarning("Atencao", "Nenhuma loja selecionada tem IP Banco 12.")
            return
        self.results = []
        self.stop_event.clear()
        self.btn_scan.config(state=tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL)
        self.progress["value"] = 0
        self.lbl_progress.config(text="0%")
        n_stores = len(selected)
        n_ips    = len(self.scan_targets)
        self.console_logger.log(f"Iniciando scan de {n_stores} loja(s) → {n_ips} IPs...", "INFO")
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _selected_store_ids(self):
        return [
            str(self.tree_stores.item(iid, "values")[0])
            for iid in self.tree_stores.selection()
        ]

    def _clear_selected_scans(self, confirm=True, reload_stores=True):
        if str(self.btn_scan["state"]) == "disabled":
            messagebox.showwarning("Atencao", "Aguarde o scan em andamento terminar ou cancele antes de limpar.")
            return False
        filiais = self._selected_store_ids()
        if not filiais:
            messagebox.showwarning("Atencao", "Selecione ao menos uma loja para limpar.")
            return False
        if confirm and not messagebox.askyesno(
            "Limpar Scan Loja",
            "Esta acao remove os dispositivos detectados das lojas selecionadas.\n\n"
            "Tabela afetada: tb_detected_devices.\n"
            "Dados de hardware associados a esses dispositivos tambem serao descartados.\n"
            "Os arquivos de log nao serao alterados.\n\n"
            "Deseja continuar?",
        ):
            return False
        try:
            conn = self.config_mgr.get_sqlite_connection()
            cur = conn.cursor()
            deleted = 0
            for filial in filiais:
                cur.execute("DELETE FROM tb_detected_devices WHERE filial = ?", (filial,))
                deleted += cur.rowcount if cur.rowcount != -1 else 0
            conn.commit()
            conn.close()
            self.console_logger.log(f"Limpeza Scan Loja concluida: {deleted} dispositivos removidos.", "SUCCESS")
            if reload_stores:
                self._load_stores()
            return True
        except Exception as e:
            self.console_logger.log(f"Erro ao limpar Scan Loja selecionadas: {e}", "ERROR")
            return False

    def _reprocess_selected(self):
        if self._clear_selected_scans(confirm=True, reload_stores=False):
            self._start_scan()

    def _scan_worker(self):
        total       = len(self.scan_targets)
        run_id      = start_scan_run(
            self.config_mgr,
            "SCAN_LOJA",
            "aba_3_scan_loja",
            total_items=total,
            selected_count=total,
        )
        timeout     = int(self.spin_timeout.get())
        workers     = max(1, min(int(self.spin_workers.get()), total))
        ssh_timeout = max(timeout, 5)  # auth SSH precisa de um pouco mais de tempo
        online      = 0

        # Carregar credenciais uma única vez antes do loop
        user_linux    = self.config_mgr.get("CREDENTIALS_LINUX_STORE", "user", "pdv")
        pass_linux    = self.config_mgr.get_secret("CREDENTIALS_LINUX_STORE", "password", "")
        user_win_drog = self.config_mgr.get("CREDENTIALS_TERMINAL_WINDOWS_DROGASIL", "user", "drogasil")
        pass_win_drog = self.config_mgr.get_secret("CREDENTIALS_TERMINAL_WINDOWS_DROGASIL", "password", "")
        user_win_raia = self.config_mgr.get("CREDENTIALS_TERMINAL_WINDOWS_RAIA", "user", "drogaraia")
        pass_win_raia = self.config_mgr.get_secret("CREDENTIALS_TERMINAL_WINDOWS_RAIA", "password", "")
        self.console_logger.log(
            f"Credenciais: Linux usuario='{user_linux}' senha_lida={'sim' if pass_linux else 'não'} tamanho={len(pass_linux or '')}; "
            f"Win Drogasil usuario='{user_win_drog}' senha_lida={'sim' if pass_win_drog else 'não'}; "
            f"Win Raia usuario='{user_win_raia}' senha_lida={'sim' if pass_win_raia else 'não'}",
            "INFO",
        )

        auth_context = {
            "user_linux": user_linux,
            "pass_linux": pass_linux,
            "user_win_drog": user_win_drog,
            "pass_win_drog": pass_win_drog,
            "user_win_raia": user_win_raia,
            "pass_win_raia": pass_win_raia,
            "timeout": timeout,
            "ssh_timeout": ssh_timeout,
            "scan_ssh": self.opt_ssh.get(),
            "scan_radmin": self.opt_radmin.get(),
            "scan_printer": self.opt_printer.get(),
        }
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(scan_core.run_store_scan_target, target, auth_context, self.console_logger.log)
                for target in self.scan_targets
            ]
            for idx, future in enumerate(as_completed(futures), 1):
                if self.stop_event.is_set():
                    self.console_logger.log("Scan cancelado.", "WARNING")
                    break
                result = future.result()
                pct = int((idx / total) * 100)
                if result is None:
                    self.after(0, self._set_scan_progress, pct, f"{pct}% ({idx}/{total})")
                    continue
                self.results.append(result)
                if result["tipo"] != "Offline":
                    online += 1
                metodo = ("RDM" if result["radmin"]
                          else (f"SSH-AUTH:{result['ssh_os']}" if result["ssh_os"]
                                else ("SSH-?" if result["ssh"] else "")))
                flags = (
                    f"SSH:{'S' if result['ssh'] else 'N'}  "
                    f"RDM:{'S' if result['radmin'] else 'N'}  "
                    f"IMP:{'S' if result['printer'] else 'N'}"
                )
                level = "SUCCESS" if result["tipo"] != "Offline" else "INFO"
                self.console_logger.log(
                    f"[{idx:>4}/{total}] {result['ip']:<16} ESPERADO:{result['expected_type']:<12} {flags}  [{metodo}]  -> {result['tipo']}",
                    level)
                record_scan_item(
                    self.config_mgr,
                    run_id,
                    f"{result['filial']}|{result['ip']}",
                    filial=result["filial"],
                    ip=result["ip"],
                    device_type=result["tipo"],
                    status=result["tipo"],
                    action="saved" if result["tipo"] != "Offline" else "ignored",
                    result_ref="tb_detected_devices" if result["tipo"] != "Offline" else "",
                )
                self.after(0, self._set_scan_progress, pct, f"{pct}% ({idx}/{total})")
        if self.results and any(r["tipo"] != "Offline" for r in self.results):
            self._save_results(show_dialog=False, run_id=run_id)
            self.after(0, self._load_stores)
        elif self.results:
            self.console_logger.log("Nenhum dispositivo online para salvar automaticamente.", "INFO")
        self.console_logger.log(f"Concluido -- {online}/{total} IPs com resposta.", "SUCCESS")
        finish_scan_run(self.config_mgr, run_id, "CANCELLED" if self.stop_event.is_set() else "SUCCESS")
        self.after(0, self._finish_scan_progress)

    def _set_scan_progress(self, progress_pct, progress_text=None):
        self.progress["value"] = progress_pct
        self.lbl_progress.config(text=progress_text or f"{progress_pct}%")

    def _finish_scan_progress(self):
        self.btn_scan.config(state=tk.NORMAL)
        self.btn_cancel.config(state=tk.DISABLED)
        if self.stop_event.is_set():
            self.lbl_progress.config(text="Cancelado")
        else:
            self._set_scan_progress(100, "100%")

    def _save_results(self, show_dialog=True, run_id=None):
        if not self.results:
            if show_dialog:
                messagebox.showinfo("Info", "Nenhum resultado para salvar.")
            return
        # Salvar apenas dispositivos detectados (excluir Offline)
        to_save = [r for r in self.results if r["tipo"] != "Offline"]
        if not to_save:
            if show_dialog:
                messagebox.showinfo("Info", "Nenhum dispositivo online para salvar.")
            return
        try:
            conn = self.config_mgr.get_sqlite_connection()
            conn.execute("""CREATE TABLE IF NOT EXISTS tb_detected_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT, filial TEXT, ip TEXT NOT NULL UNIQUE,
                expected_type TEXT, ssh INTEGER DEFAULT 0, radmin INTEGER DEFAULT 0,
                printer INTEGER DEFAULT 0,
                device_type TEXT, logo TEXT,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
            for col_sql in [
                "ALTER TABLE tb_detected_devices ADD COLUMN expected_type TEXT",
                "ALTER TABLE tb_detected_devices ADD COLUMN printer INTEGER DEFAULT 0",
                "ALTER TABLE tb_detected_devices ADD COLUMN logo TEXT",
            ]:
                try:
                    conn.execute(col_sql)
                except Exception:
                    pass
            rows = [
                (r["filial"], r["ip"], r.get("expected_type", ""),
                 int(r["ssh"]), int(r["radmin"]), int(r.get("printer", 0)),
                 r["tipo"], r.get("logo", ""))
                for r in to_save
            ]
            verb = "INSERT OR REPLACE" if self.opt_full_refresh.get() else "INSERT OR IGNORE"
            conn.executemany(
                f"{verb} INTO tb_detected_devices"
                " (filial, ip, expected_type, ssh, radmin, printer, device_type, logo)"
                " VALUES (?,?,?,?,?,?,?,?)",
                rows)

            # Historico append-only — grava mesmo quando o IP ja existia (INSERT OR
            # IGNORE nao gera linha nova no estado atual), pois a comparacao por data
            # no www precisa distinguir "sem mudanca" de "nao escaneado desta vez".
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hist_rows = [(run_id,) + row + (now_str,) for row in rows]
            conn.executemany(
                "INSERT INTO tb_detected_devices_history"
                " (run_id, filial, ip, expected_type, ssh, radmin, printer, device_type, logo, snapshot_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)"
                " ON CONFLICT(ip, snapshot_at) DO NOTHING",
                hist_rows)

            conn.commit()
            conn.close()
            skipped = len(self.results) - len(to_save)
            msg = f"{len(rows)} registros salvos."
            if skipped:
                msg += f" ({skipped} Offline ignorados)"
            self.console_logger.log(msg, "SUCCESS")
        except Exception as e:
            self.console_logger.log(f"Erro ao salvar: {e}", "ERROR")
