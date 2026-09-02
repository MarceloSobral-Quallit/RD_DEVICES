#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABA 2 — Consulta B12: coleta dados completos do B12 (hostname, SO, CIDR, hardware)."""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sqlite3
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from src.common import scan_core
from src.common.config import ConfigManager
from src.common.console_logger import ConsoleLogger
from src.common.scan_runs import finish_scan_run, record_scan_item, start_scan_run
from src.common.treeview_sort import make_treeview_sortable


B12_TRACKED_FIELD_COUNT = 15


class Tab2DetectSSH(ttk.Frame):
    """ABA 2 — Detectar SSH/JAVA por lojas selecionadas."""

    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.parent = parent
        self.config_mgr = ConfigManager()
        self.stop_event = threading.Event()
        self.results = []
        self.scan_targets = []
        self._all_stores = []
        self._create_ui()
        self.after(100, self._load_stores)

    def _create_ui(self):
        # Seleção de lojas
        frame_filter = ttk.LabelFrame(self, text="Selecao de Lojas — Consulta B12", padding=8)
        frame_filter.pack(fill=tk.X, padx=10, pady=(10, 0))

        row1 = ttk.Frame(frame_filter)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Logomarca:").pack(side=tk.LEFT)
        self.var_logo = tk.StringVar(value="TODAS")
        for logo in ("TODAS", "DROGASIL", "RAIA"):
            ttk.Radiobutton(
                row1,
                text=logo,
                variable=self.var_logo,
                value=logo,
                command=self._apply_filter,
            ).pack(side=tk.LEFT, padx=6)

        ttk.Separator(row1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(row1, text="Busca:").pack(side=tk.LEFT)
        self.var_search = tk.StringVar()
        self.var_search.trace_add("write", lambda *_: self._apply_filter())
        ttk.Entry(row1, textvariable=self.var_search, width=28).pack(side=tk.LEFT, padx=4)
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
        self.var_only_offline = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            row1,
            text="Somente offline",
            variable=self.var_only_offline,
            command=self._apply_filter,
        ).pack(side=tk.LEFT, padx=6)
        ttk.Separator(row1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Button(row1, text="Recarregar", command=self._load_stores).pack(side=tk.LEFT, padx=4)

        row2 = ttk.Frame(frame_filter)
        row2.pack(fill=tk.X, pady=(4, 2))
        self.lbl_count = ttk.Label(row2, text="0 lojas", foreground="gray")
        self.lbl_count.pack(side=tk.LEFT, padx=(0, 12))
        ttk.Button(row2, text="Marcar todas", command=self._select_all).pack(side=tk.LEFT, padx=3)
        ttk.Button(row2, text="Desmarcar todas", command=self._deselect_all).pack(side=tk.LEFT, padx=3)
        ttk.Button(row2, text="Inverter", command=self._invert_selection).pack(side=tk.LEFT, padx=3)
        ttk.Button(row2, text="Offline",
                   command=lambda: self._select_by_b12_status("OFFLINE")).pack(side=tk.LEFT, padx=3)
        ttk.Button(row2, text="Nao escaneadas",
                   command=lambda: self._select_by_b12_status("NAO ESCANEADO")).pack(side=tk.LEFT, padx=3)
        ttk.Button(row2, text="Escaneadas",
                   command=lambda: self._select_by_b12_status("ESCANEADO")).pack(side=tk.LEFT, padx=3)
        ttk.Button(row2, text="Pendencias B12",
                   command=self._select_b12_pending).pack(side=tk.LEFT, padx=3)
        self.lbl_selected = ttk.Label(row2, text="0 selecionadas", foreground="blue")
        self.lbl_selected.pack(side=tk.LEFT, padx=12)

        frame_list = ttk.Frame(self)
        frame_list.pack(fill=tk.BOTH, expand=False, padx=10, pady=(4, 0))
        vscroll = ttk.Scrollbar(frame_list, orient=tk.VERTICAL)
        hscroll = ttk.Scrollbar(frame_list, orient=tk.HORIZONTAL)
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        hscroll.pack(side=tk.BOTTOM, fill=tk.X)

        cols = ("filial", "java", "nome", "cidade", "uf", "logo", "ip", "status")
        self.tree_stores = ttk.Treeview(
            frame_list,
            columns=cols,
            show="headings",
            selectmode="extended",
            yscrollcommand=vscroll.set,
            xscrollcommand=hscroll.set,
            height=5,
        )
        self.tree_stores.pack(fill=tk.BOTH, expand=True)
        vscroll.config(command=self.tree_stores.yview)
        hscroll.config(command=self.tree_stores.xview)

        headers = [
            ("filial", "JAVA", 70),
            ("java", "HISTORICO", 90),
            ("nome", "Nome", 200),
            ("cidade", "Cidade", 140),
            ("uf", "UF", 40),
            ("logo", "Logo", 90),
            ("ip", "IP Banco 12", 120),
            ("status", "Status B12", 130),
        ]
        for col, label, width in headers:
            self.tree_stores.heading(col, text=label)
            self.tree_stores.column(col, width=width, anchor=tk.W)
        self._sort_stores = make_treeview_sortable(self.tree_stores)
        self.tree_stores.bind("<<TreeviewSelect>>", self._on_select)

        # Opções de scan
        frame_options = ttk.LabelFrame(self, text="Opcoes de Scan", padding=8)
        frame_options.pack(fill=tk.X, padx=10, pady=4)

        ttk.Label(frame_options, text="Workers:").pack(side=tk.LEFT, padx=(0, 4))
        self.spinbox_workers = ttk.Spinbox(frame_options, from_=1, to=64, width=5)
        self.spinbox_workers.set(16)
        self.spinbox_workers.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(frame_options, text="Timeout (seg):").pack(side=tk.LEFT, padx=(0, 4))
        self.spinbox_timeout = ttk.Spinbox(frame_options, from_=1, to=30, width=5)
        self.spinbox_timeout.set(5)
        self.spinbox_timeout.pack(side=tk.LEFT, padx=(0, 20))

        self.opt_ssh_detail = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame_options,
            text="Coletar hostname SSH",
            variable=self.opt_ssh_detail,
        ).pack(side=tk.LEFT, padx=5)

        self.opt_save_results = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame_options,
            text="Salvar resultados",
            variable=self.opt_save_results,
        ).pack(side=tk.LEFT, padx=5)

        # Resultados
        frame_results = ttk.LabelFrame(self, text="Resultados do Scan", padding=8)
        frame_results.pack(fill=tk.BOTH, expand=False, padx=10, pady=4)
        result_scroll = ttk.Scrollbar(frame_results)
        result_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_results = ttk.Treeview(frame_results, yscrollcommand=result_scroll.set, height=5)
        self.tree_results["columns"] = ("java", "status", "ssh_port", "hostname", "loja")
        self.tree_results.pack(fill=tk.BOTH, expand=True)
        result_scroll.config(command=self.tree_results.yview)

        self.tree_results.column("#0", width=120)
        self.tree_results.column("java", width=80)
        self.tree_results.column("status", width=90)
        self.tree_results.column("ssh_port", width=90)
        self.tree_results.column("hostname", width=180)
        self.tree_results.column("loja", width=240)

        self.tree_results.heading("#0", text="IP")
        self.tree_results.heading("java", text="HISTORICO")
        self.tree_results.heading("status", text="Status")
        self.tree_results.heading("ssh_port", text="SSH")
        self.tree_results.heading("hostname", text="Hostname")
        self.tree_results.heading("loja", text="Loja")
        self._sort_results = make_treeview_sortable(self.tree_results)

        # Console padronizado
        frame_console = ttk.LabelFrame(self, text="Log em Tempo Real", padding=8)
        frame_console.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        self.console_logger = ConsoleLogger(frame_console, height=10, log_name="aba_2_consulta_b12")

        # Ações
        frame_action = ttk.Frame(self)
        frame_action.pack(fill=tk.X, padx=10, pady=(4, 10))
        self.progress = ttk.Progressbar(frame_action, mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.lbl_progress = ttk.Label(frame_action, text="0%", width=16)
        self.lbl_progress.pack(side=tk.LEFT)

        self.lbl_stats = ttk.Label(frame_action, text="Total: 0 | Online: 0 | SSH: 0")
        self.lbl_stats.pack(side=tk.LEFT, padx=12)

        self.btn_scan = ttk.Button(frame_action, text="Iniciar Scan", command=self._start_scan)
        self.btn_scan.pack(side=tk.LEFT, padx=5)
        self.btn_cancel = ttk.Button(
            frame_action,
            text="Cancelar",
            command=self._cancel_scan,
            state=tk.DISABLED,
        )
        self.btn_cancel.pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_action, text="Limpar selecionadas", command=self._clear_selected_scans).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_action, text="Reprocessar", command=self._reprocess_selected).pack(side=tk.LEFT, padx=5)

    def _load_stores(self):
        try:
            conn = self.config_mgr.get_sqlite_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT f.filial, f.historico, f.nome_filial, f.cidade, f.uf, f.logomarca, f.ip_banco_12,
                       CASE
                           WHEN b.collection_status = 'SUCCESS' THEN 'ESCANEADO'
                           WHEN b.collection_status = 'OFFLINE' THEN 'OFFLINE'
                           WHEN b.collection_status IS NOT NULL THEN b.collection_status
                           ELSE 'NAO ESCANEADO'
                       END AS b12_status
                FROM tb_filial f
                LEFT JOIN tb_b12_data_collection_status b
                  ON b.java = f.filial
                 AND b.collection_date = (
                     SELECT MAX(b2.collection_date)
                     FROM tb_b12_data_collection_status b2
                     WHERE b2.java = f.filial
                 )
                WHERE f.ativo = 1 AND f.ip_banco_12 IS NOT NULL AND TRIM(f.ip_banco_12) <> ''
                ORDER BY f.logomarca, CAST(f.filial AS INTEGER)
                """
            )
            loaded_rows = [tuple(row) for row in cur.fetchall()]
            self._all_stores = [row for row in loaded_rows if self._is_valid_b12_ip(row[6])]
            invalid_count = len(loaded_rows) - len(self._all_stores)
            conn.close()
            self._apply_filter()
            self.console_logger.log(f"{len(self._all_stores)} lojas carregadas.", "INFO")
            if invalid_count:
                self.console_logger.log(
                    f"{invalid_count} lojas ignoradas por IP Banco 12 invalido.",
                    "WARNING",
                )
        except Exception as e:
            self.console_logger.log(f"Erro ao carregar lojas: {e}", "ERROR")

    @staticmethod
    def _is_valid_b12_ip(ip):
        try:
            parsed = ipaddress.ip_address(str(ip).strip())
            return parsed.version == 4 and not parsed.is_unspecified
        except ValueError:
            return False

    def _apply_filter(self):
        logo_filter = self.var_logo.get()
        search_filter = self.var_search.get().strip().lower()
        only_offline = self.var_only_offline.get()

        filtered = [
            row
            for row in self._all_stores
            if (logo_filter == "TODAS" or str(row[5]).upper() == logo_filter)
            and (not search_filter or any(search_filter in str(v).lower() for v in row))
            and self._java_in_range(row[0])
            and (not only_offline or str(row[7]).upper() == "OFFLINE")
        ]

        self.tree_stores.delete(*self.tree_stores.get_children())
        for row in filtered:
            self.tree_stores.insert("", tk.END, values=tuple(row))
        self._sort_stores("filial", descending=False)

        self.lbl_count.config(text=f"{len(filtered)} lojas")
        self._update_selected_label()

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
        selected = set(self.tree_stores.selection())
        self.tree_stores.selection_set(list(all_items - selected))
        self._update_selected_label()

    def _select_by_b12_status(self, status):
        matches = [
            iid for iid in self.tree_stores.get_children()
            if str(self.tree_stores.item(iid, "values")[7]).upper() == status
        ]
        self.tree_stores.selection_set(matches)
        self._update_selected_label()

    def _select_b12_pending(self):
        try:
            conn = self.config_mgr.get_sqlite_connection()
            rows = conn.execute(
                """
                SELECT f.filial, f.ip_banco_12
                FROM tb_filial f
                LEFT JOIN tb_b12_data_collection_status b
                  ON b.java = f.filial
                 AND b.collection_date = (
                     SELECT MAX(b2.collection_date)
                     FROM tb_b12_data_collection_status b2
                     WHERE b2.java = f.filial
                 )
                WHERE f.ativo = 1
                  AND f.ip_banco_12 IS NOT NULL
                  AND TRIM(f.ip_banco_12) <> ''
                  AND (
                      b.java IS NULL
                      OR b.collection_status IN ('OFFLINE', 'FAILED', 'PARTIAL', 'AUTH_FAILED')
                      OR f.cidr IS NULL OR TRIM(f.cidr) = ''
                      OR b.hostname_collected = 0
                      OR b.os_collected = 0
                      OR b.kernel_collected = 0
                      OR b.cidr_collected = 0
                      OR b.memory_collected = 0
                      OR b.mac_collected = 0
                      OR b.disk_size_collected = 0
                  )
                """
            ).fetchall()
            conn.close()
            pending = {
                str(row[0])
                for row in rows
                if self._is_valid_b12_ip(row[1])
            }
            matches = [
                iid for iid in self.tree_stores.get_children()
                if str(self.tree_stores.item(iid, "values")[0]) in pending
            ]
            self.tree_stores.selection_set(matches)
            self._update_selected_label()
            self.console_logger.log(
                f"{len(matches)} pendencias B12 selecionadas; IPs invalidos ficaram fora da lista.",
                "INFO",
            )
        except Exception as e:
            self.console_logger.log(f"Erro ao selecionar pendencias B12: {e}", "ERROR")

    def _start_scan(self):
        selected = self.tree_stores.selection()
        if not selected:
            messagebox.showwarning("Atencao", "Selecione ao menos uma loja.")
            return

        self.scan_targets = []
        for iid in selected:
            filial, historico, nome, _cidade, _uf, _logo, ip, _status = self.tree_stores.item(iid, "values")
            if self._is_valid_b12_ip(ip):
                self.scan_targets.append(
                    {
                        "filial": str(filial),
                        "java": str(filial),
                        "historico": str(historico),
                        "nome": str(nome),
                        "ip": str(ip).strip(),
                    }
                )

        if not self.scan_targets:
            messagebox.showwarning("Atencao", "Nenhuma loja selecionada tem IP valido.")
            return

        self.results = []
        self.stop_event.clear()
        self.btn_scan.config(state=tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL)
        self.progress["value"] = 0
        self.lbl_progress.config(text="0%")
        self.tree_results.delete(*self.tree_results.get_children())
        self.console_logger.clear()
        self.console_logger.log(f"Iniciando scan de {len(self.scan_targets)} lojas...", "INFO")

        threading.Thread(target=self._scan_worker).start()

    def _selected_b12_keys(self):
        keys = []
        for iid in self.tree_stores.selection():
            filial, _historico, _nome, _cidade, _uf, _logo, ip, _status = self.tree_stores.item(iid, "values")
            keys.append((str(filial), str(ip).strip()))
        return keys

    def _clear_selected_scans(self, confirm=True, reload_stores=True):
        if str(self.btn_scan["state"]) == "disabled":
            messagebox.showwarning("Atencao", "Aguarde o scan em andamento terminar ou cancele antes de limpar.")
            return False
        keys = self._selected_b12_keys()
        if not keys:
            messagebox.showwarning("Atencao", "Selecione ao menos uma loja para limpar.")
            return False
        if confirm and not messagebox.askyesno(
            "Limpar B12",
            "Esta acao remove os dados B12 ja gravados das lojas selecionadas.\n\n"
            "Tabelas afetadas: tb_devices_detail e tb_b12_data_collection_status.\n"
            "Os arquivos de log nao serao alterados.\n\n"
            "Deseja continuar?",
        ):
            return False
        try:
            conn = self.config_mgr.get_sqlite_connection()
            cur = conn.cursor()
            detail_deleted = 0
            status_deleted = 0
            for java, ip in keys:
                cur.execute("DELETE FROM tb_devices_detail WHERE java = ? OR ip = ?", (java, ip))
                detail_deleted += cur.rowcount if cur.rowcount != -1 else 0
                cur.execute("DELETE FROM tb_b12_data_collection_status WHERE java = ? OR ip_b12 = ?", (java, ip))
                status_deleted += cur.rowcount if cur.rowcount != -1 else 0
            conn.commit()
            conn.close()
            self.console_logger.log(
                f"Limpeza B12 concluida: {detail_deleted} detalhes e {status_deleted} status removidos.",
                "SUCCESS",
            )
            if reload_stores:
                self._load_stores()
            return True
        except Exception as e:
            self.console_logger.log(f"Erro ao limpar B12 selecionadas: {e}", "ERROR")
            return False

    def _reprocess_selected(self):
        if self._clear_selected_scans(confirm=True, reload_stores=False):
            self._start_scan()

    def _cancel_scan(self):
        self.stop_event.set()
        self.console_logger.log("Cancelando scan...", "WARNING")
        self.btn_cancel.config(state=tk.DISABLED)

    def is_scan_running(self):
        return str(self.btn_scan["state"]) == "disabled"

    def request_cancel(self):
        if self.is_scan_running():
            self._cancel_scan()

    def _scan_worker(self):
        run_id = None
        run_status = "SUCCESS"
        run_error = ""
        try:
            timeout = int(self.spinbox_timeout.get())
            workers = max(1, min(int(self.spinbox_workers.get()), len(self.scan_targets)))
            collect_detail = self.opt_ssh_detail.get()
            user, password, ssh_port = self._get_linux_credentials()
            total = len(self.scan_targets)
            run_id = start_scan_run(
                self.config_mgr,
                "B12",
                "aba_2_consulta_b12",
                total_items=total,
                selected_count=total,
            )
            online_count = 0
            ssh_count = 0
            self.console_logger.log(
                f"Credencial Linux: usuario='{user}' | porta={ssh_port} | senha_lida={'sim' if password else 'não'} | tamanho={len(password or '')}",
                "INFO",
            )

            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [
                    executor.submit(
                        scan_core.run_b12_check, target, timeout, user, password, ssh_port,
                        collect_detail, self.console_logger.log,
                    )
                    for target in self.scan_targets
                ]
                for idx, future in enumerate(as_completed(futures), 1):
                    if self.stop_event.is_set():
                        run_status = "CANCELLED"
                        break
                    result, status, level = future.result()
                    self.results.append(result)
                    if result["ssh"]:
                        online_count += 1
                    if result.get("b12_data") and result["b12_data"].get("collection_status") == "SUCCESS":
                        ssh_count += 1
                    elif result["ssh"] and not collect_detail:
                        ssh_count += 1

                    pct = int((idx / total) * 100)
                    loja = f"{result['filial']} - {result['nome']}"
                    self.parent.after(
                        0,
                        self._append_scan_result,
                        result["ip"],
                        (result["java"], status, "Aberta" if result["ssh"] else "Fechada", result["hostname"], loja),
                        pct,
                        f"{pct}% ({idx}/{total})",
                        f"Total: {total} | Online: {online_count} | SSH: {ssh_count}",
                    )
                    self.console_logger.log(
                        f"[{idx:>4}/{total}] JAVA {result['java']:<6} HIST {result.get('historico', ''):<6} {result['ip']:<16} -> {status}",
                        level,
                    )
                    b12_data = result.get("b12_data") or {}
                    record_scan_item(
                        self.config_mgr,
                        run_id,
                        f"{result['java']}|{result['ip']}",
                        filial=result["filial"],
                        ip=result["ip"],
                        device_type="B12",
                        status=b12_data.get("collection_status") or ("SUCCESS" if result.get("ssh") else "OFFLINE"),
                        action="saved" if b12_data else "processed",
                        result_ref="tb_devices_detail,tb_b12_data_collection_status" if b12_data else "",
                        error_message=b12_data.get("ssh_error") or "",
                    )

            if self.opt_save_results.get() and self.results:
                self._save_results(run_id)

            self.console_logger.log(
                f"Concluido: {online_count}/{total} online, {ssh_count} com SSH.",
                "SUCCESS",
            )

        except Exception as e:
            run_status = "FAILED"
            run_error = str(e)
            self.console_logger.log(f"Erro no scan: {e}", "ERROR")

        finally:
            finish_scan_run(self.config_mgr, run_id, run_status, run_error)
            self.parent.after(0, self._scan_done)

    def _get_linux_credentials(self):
        user = self.config_mgr.get("CREDENTIALS_LINUX_STORE", "user", "pdv")
        password = self.config_mgr.get_secret("CREDENTIALS_LINUX_STORE", "password", "")
        port = int(self.config_mgr.get("CREDENTIALS_LINUX_STORE", "port", "22") or 22)
        return user, password, port

    def _append_scan_result(self, ip, values, progress_pct, progress_text, stats_text):
        self.tree_results.insert("", tk.END, text=ip, values=values)
        self._sort_results("java", descending=False)
        self.progress["value"] = progress_pct
        self.lbl_progress.config(text=progress_text)
        self.lbl_stats.config(text=stats_text)

    @staticmethod
    def _safe_int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            try:
                return int(float(str(value).replace(",", ".")))
            except (TypeError, ValueError):
                return default

    def _save_results(self, run_id=None):
        """Salva resultados em tb_devices_detail, tb_b12_data_collection_status e atualiza tb_filial."""
        try:
            conn = self.config_mgr.get_sqlite_connection()
            conn.execute("PRAGMA foreign_keys = OFF")  # Desabilita FK temporariamente
            
            detail_saved_count = 0
            status_saved_count = 0
            skipped_detail_count = 0
            
            for r in self.results:
                if not r.get('b12_data'):
                    continue  # Pula se não há dados SSH ou dados B12
                
                b12_data = r['b12_data']
                ip = r['ip']
                java = r['java']
                filial = r['filial']

                status_saved_count += self._save_collection_status(conn, r, b12_data)

                if b12_data.get('collection_status') != 'SUCCESS':
                    skipped_detail_count += 1
                    self.console_logger.log(
                        f"Detalhes não gravados para {ip}: coleta {b12_data.get('collection_status')} ({b12_data.get('ssh_error') or 'sem detalhes'})",
                        "WARNING",
                    )
                    continue
                
                # 1. Salvar em tb_devices_detail (dados principais do B12)
                try:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    detail_values = (
                        java, ip,
                        b12_data.get('hostname') or b12_data.get('hostname_raw') or 'N/A',
                        'B12',
                        b12_data.get('os') or 'N/A',
                        b12_data.get('kernel'),
                        b12_data.get('cores'),
                        self._safe_int(b12_data.get('memory'), 0),
                        b12_data.get('mac'),
                        b12_data.get('mb_manufacturer'),
                        b12_data.get('mb_product'),
                        b12_data.get('mb_version'),
                        b12_data.get('disk_type'),
                        b12_data.get('disk_model'),
                        self._safe_int(b12_data.get('disk_size'), 0),
                    )
                    conn.execute("""
                        INSERT OR REPLACE INTO tb_devices_detail (
                            java, ip, hostname, tipo_equipamento, sistema_operacional,
                            kernel, cores_fisicos, memoria_total, mac_address,
                            mb_manufacturer, mb_product_name, mb_version,
                            hdd_media_type, hdd_model, hdd_size, data_coleta, data_atualizacao
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, detail_values + (now_str, now_str))
                    detail_saved_count += 1

                    # Historico append-only — nunca sobrescrito, alimenta a comparacao por data no www.
                    conn.execute("""
                        INSERT INTO tb_devices_detail_history (
                            run_id, java, ip, hostname, tipo_equipamento, sistema_operacional,
                            kernel, cores_fisicos, memoria_total, mac_address,
                            mb_manufacturer, mb_product_name, mb_version,
                            hdd_media_type, hdd_model, hdd_size, data_coleta
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(ip, data_coleta) DO NOTHING
                    """, (run_id,) + detail_values + (now_str,))
                except Exception as e:
                    self.console_logger.log(f"Erro ao salvar em tb_devices_detail ({ip}): {e}", "WARNING")
                
                # 3. Atualizar tb_filial com CIDR detectado
                if b12_data.get('cidr'):
                    try:
                        conn.execute("""
                            UPDATE tb_filial SET cidr = ? WHERE filial = ?
                        """, (b12_data['cidr'], filial))
                    except Exception as e:
                        self.console_logger.log(f"Erro ao atualizar CIDR em tb_filial ({filial}): {e}", "WARNING")
                
            conn.commit()
            conn.close()
            self.console_logger.log(
                f"{detail_saved_count} B12s salvos em tb_devices_detail; "
                f"{status_saved_count} status registrados; {skipped_detail_count} detalhes ignorados.",
                "SUCCESS",
            )
        except Exception as e:
            self.console_logger.log(f"Erro ao salvar resultados: {e}", "ERROR")

    def _save_collection_status(self, conn, result, b12_data):
        """Salva rastreamento da coleta B12, inclusive falhas de autenticação."""
        try:
            duration = 0
            if b12_data.get('collection_end') and b12_data.get('collection_start'):
                duration = int((b12_data['collection_end'] - b12_data['collection_start']).total_seconds())

            conn.execute("""
                INSERT OR REPLACE INTO tb_b12_data_collection_status (
                    java, ip_b12, nome_filial, collection_status, collection_date, collection_duration_seconds,
                    hostname_collected, hostname_value,
                    hostname_raw_collected, hostname_raw_value,
                    os_collected, os_value,
                    os_version_collected, os_version_value,
                    kernel_collected, kernel_value,
                    cidr_collected, cidr_value,
                    cores_collected, cores_value,
                    memory_collected, memory_value_bytes,
                    mac_collected, mac_value,
                    mb_manufacturer_collected, mb_manufacturer_value,
                    mb_product_collected, mb_product_value,
                    mb_version_collected, mb_version_value,
                    disk_media_type_collected, disk_media_type_value,
                    disk_model_collected, disk_model_value,
                    disk_size_collected, disk_size_value,
                    fields_collected_count, collection_percentage, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                result['java'], result['ip'], result['nome'], b12_data.get('collection_status', 'PARTIAL'),
                b12_data.get('collection_date'),
                duration,
                1 if b12_data.get('hostname') else 0, b12_data.get('hostname'),
                1 if b12_data.get('hostname_raw') else 0, b12_data.get('hostname_raw'),
                1 if b12_data.get('os') else 0, b12_data.get('os'),
                1 if b12_data.get('os_version') else 0, b12_data.get('os_version'),
                1 if b12_data.get('kernel') else 0, b12_data.get('kernel'),
                1 if b12_data.get('cidr') else 0, b12_data.get('cidr'),
                1 if b12_data.get('cores') else 0, b12_data.get('cores'),
                1 if b12_data.get('memory') else 0, self._safe_int(b12_data.get('memory'), 0),
                1 if b12_data.get('mac') else 0, b12_data.get('mac'),
                1 if b12_data.get('mb_manufacturer') else 0, b12_data.get('mb_manufacturer'),
                1 if b12_data.get('mb_product') else 0, b12_data.get('mb_product'),
                1 if b12_data.get('mb_version') else 0, b12_data.get('mb_version'),
                1 if b12_data.get('disk_type') else 0, b12_data.get('disk_type'),
                1 if b12_data.get('disk_model') else 0, b12_data.get('disk_model'),
                1 if b12_data.get('disk_size') else 0, self._safe_int(b12_data.get('disk_size'), 0),
                b12_data.get('fields_collected', 0),
                (b12_data.get('fields_collected', 0) / B12_TRACKED_FIELD_COUNT * 100) if b12_data.get('fields_collected') else 0,
            ))
            return 1
        except Exception as e:
            self.console_logger.log(f"Erro ao salvar em tb_b12_data_collection_status ({result['ip']}): {e}", "WARNING")
            return 0

    def _scan_done(self):
        self.btn_scan.config(state=tk.NORMAL)
        self.btn_cancel.config(state=tk.DISABLED)
        if self.stop_event.is_set():
            self.lbl_progress.config(text="Cancelado")
        else:
            self.progress["value"] = 100
            self.lbl_progress.config(text="100%")
