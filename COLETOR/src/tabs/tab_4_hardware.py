#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABA 4 — Escanear Hardware"""

import json
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from src.common import scan_core
from src.common.config import ConfigManager
from src.common.console_logger import ConsoleLogger
from src.common.scan_runs import finish_scan_run, record_scan_item, start_scan_run
from src.common.treeview_sort import make_treeview_sortable

try:
    import wmi as wmi_module
except ImportError:
    wmi_module = None

_PYSNMP_OK = scan_core._PYSNMP_OK


class Tab4ScanHardware(ttk.Frame):
    """ABA 4 — Escanear Hardware."""
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.parent, self.config_mgr = parent, ConfigManager()
        self.stop_event, self.results, self._devices_data = threading.Event(), [], []
        self._visible_devices_data = []
        self._scan_devices = []
        self._create_ui()
    
    def _create_ui(self):
        frame_input = ttk.LabelFrame(self, text="🖥️ Seleção de Dispositivos", padding=10)
        frame_input.pack(fill=tk.X, padx=10, pady=10)
        filter_frame = ttk.Frame(frame_input)
        filter_frame.pack(fill=tk.X, pady=3)
        ttk.Label(filter_frame, text="Logomarca:").pack(side=tk.LEFT)
        self.var_hw_logo = tk.StringVar(value="TODAS")
        for logo in ("TODAS", "DROGASIL", "RAIA"):
            ttk.Radiobutton(filter_frame, text=logo, variable=self.var_hw_logo, value=logo,
                            command=self._apply_device_filter).pack(side=tk.LEFT, padx=6)
        ttk.Separator(filter_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(filter_frame, text="Busca:").pack(side=tk.LEFT)
        self.var_hw_search = tk.StringVar()
        self.var_hw_search.trace_add("write", lambda *_: self._apply_device_filter())
        ttk.Entry(filter_frame, textvariable=self.var_hw_search, width=25).pack(side=tk.LEFT, padx=4)
        ttk.Button(filter_frame, text="X", width=2, command=lambda: self.var_hw_search.set("")).pack(side=tk.LEFT)
        ttk.Separator(filter_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(filter_frame, text="JAVA:").pack(side=tk.LEFT)
        self.var_hw_java_from = tk.StringVar()
        self.var_hw_java_to = tk.StringVar()
        self.var_hw_java_from.trace_add("write", lambda *_: self._apply_device_filter())
        self.var_hw_java_to.trace_add("write", lambda *_: self._apply_device_filter())
        ttk.Entry(filter_frame, textvariable=self.var_hw_java_from, width=6).pack(side=tk.LEFT, padx=(4, 2))
        ttk.Label(filter_frame, text="ate").pack(side=tk.LEFT)
        ttk.Entry(filter_frame, textvariable=self.var_hw_java_to, width=6).pack(side=tk.LEFT, padx=(2, 4))
        ttk.Separator(filter_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        self.var_hw_only_unscanned = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            filter_frame,
            text="Somente nao escaneado",
            variable=self.var_hw_only_unscanned,
            command=self._apply_device_filter,
        ).pack(side=tk.LEFT, padx=6)
        ttk.Separator(filter_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Button(filter_frame, text="Recarregar", command=self._load_from_db).pack(side=tk.LEFT, padx=5)

        select_frame = ttk.Frame(frame_input)
        select_frame.pack(fill=tk.X, pady=(3, 5))
        self.lbl_hw_count = ttk.Label(select_frame, text="0 dispositivos", foreground="gray")
        self.lbl_hw_count.pack(side=tk.LEFT, padx=(0, 12))
        ttk.Button(select_frame, text="Marcar todos", command=self._select_all_devices).pack(side=tk.LEFT, padx=3)
        ttk.Button(select_frame, text="Desmarcar todos", command=self._deselect_all_devices).pack(side=tk.LEFT, padx=3)
        ttk.Button(select_frame, text="Inverter", command=self._invert_device_selection).pack(side=tk.LEFT, padx=3)
        ttk.Button(select_frame, text="Nao escaneados",
                   command=lambda: self._select_devices_by_status("NAO ESCANEADO")).pack(side=tk.LEFT, padx=3)
        ttk.Button(select_frame, text="Escaneados",
                   command=lambda: self._select_devices_by_status("ESCANEADO")).pack(side=tk.LEFT, padx=3)
        ttk.Button(select_frame, text="Continuar pendentes",
                   command=self._select_pending_from_last_run).pack(side=tk.LEFT, padx=3)
        self.lbl_hw_selected = ttk.Label(select_frame, text="0 selecionados", foreground="blue")
        self.lbl_hw_selected.pack(side=tk.LEFT, padx=12)
        
        list_frame = ttk.Frame(frame_input)
        list_frame.pack(fill=tk.X, expand=False, pady=5)
        scroll = ttk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox_devices = tk.Listbox(list_frame, yscrollcommand=scroll.set, height=5, selectmode=tk.EXTENDED)
        self.listbox_devices.pack(fill=tk.X, expand=False)
        self.listbox_devices.bind("<<ListboxSelect>>", lambda _event: self._update_device_selected_label())
        scroll.config(command=self.listbox_devices.yview)
        
        frame_results = ttk.LabelFrame(self, text="📊 Especificações", padding=10)
        frame_results.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        rs_vscroll = ttk.Scrollbar(frame_results, orient=tk.VERTICAL)
        rs_hscroll = ttk.Scrollbar(frame_results, orient=tk.HORIZONTAL)
        rs_vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        rs_hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        cols = ('hostname', 'cpu_model', 'cores', 'ram_gb', 'disk_gb', 'os', 'os_version')
        self.tree_results = ttk.Treeview(
            frame_results, columns=cols, show='headings',
            yscrollcommand=rs_vscroll.set, xscrollcommand=rs_hscroll.set,
            height=5,
        )
        self.tree_results.pack(fill=tk.BOTH, expand=True)
        rs_vscroll.config(command=self.tree_results.yview)
        rs_hscroll.config(command=self.tree_results.xview)
        for col, label, width in [
            ('hostname',   'Hostname',   160),
            ('cpu_model',  'CPU',        220),
            ('cores',      'Cores',       55),
            ('ram_gb',     'RAM (GB)',    75),
            ('disk_gb',    'Disco (GB)', 80),
            ('os',         'SO',         180),
            ('os_version', 'Kernel',     130),
        ]:
            self.tree_results.heading(col, text=label)
            self.tree_results.column(col, width=width, anchor=tk.W)
        make_treeview_sortable(self.tree_results)
        
        frame_console = ttk.LabelFrame(self, text="📋 Log", padding=10)
        frame_console.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.console_logger = ConsoleLogger(frame_console, height=10, log_name="aba_4_hardware")
        
        frame_action = ttk.Frame(self)
        frame_action.pack(fill=tk.X, padx=10, pady=10)
        progress_frame = ttk.Frame(frame_action)
        progress_frame.pack(fill=tk.X, pady=5)
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.lbl_progress = ttk.Label(progress_frame, text="0%", width=16)
        self.lbl_progress.pack(side=tk.LEFT)
        
        self.btn_scan = ttk.Button(frame_action, text="Iniciar", command=self._start_scan)
        self.btn_scan.pack(side=tk.LEFT, padx=5)
        self.btn_cancel = ttk.Button(frame_action, text="Cancelar", command=self.request_cancel, state=tk.DISABLED)
        self.btn_cancel.pack(side=tk.LEFT, padx=5)
        ttk.Label(frame_action, text="Workers:").pack(side=tk.LEFT, padx=(12, 4))
        self.spin_workers = ttk.Spinbox(frame_action, from_=1, to=64, width=4)
        self.spin_workers.set(8)
        self.spin_workers.pack(side=tk.LEFT, padx=5)
        self.opt_auto_json = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame_action, text="Gerar JSON ao concluir",
                        variable=self.opt_auto_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_action, text="Exportar JSON", command=self._export_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_action, text="Limpar selecionados", command=self._clear_selected_hw).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_action, text="Reprocessar", command=self._reprocess_selected_hw).pack(side=tk.LEFT, padx=5)
    
    def _load_from_db(self):
        try:
            self._ensure_hw_columns()
            conn = self.config_mgr.get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT filial, ip, device_type, logo,"
                " CASE WHEN hw_scanned_at IS NOT NULL THEN 'ESCANEADO' ELSE 'NAO ESCANEADO' END AS hw_status"
                " FROM tb_detected_devices"
                " WHERE device_type IN"
                "  ('PDV Linux', 'TC Linux', 'TC Win', 'IMPRESSORA')"
                " ORDER BY CAST(filial AS INTEGER), device_type, ip"
            )
            rows = cursor.fetchall()
            conn.close()
            self._devices_data = [
                {"filial": str(r[0]), "ip": str(r[1]),
                 "device_type": str(r[2] or ''), "bandeira": str(r[3] or ''),
                 "status": str(r[4] or 'NAO ESCANEADO')}
                for r in rows
            ]
            self._apply_device_filter()
            counts = {}
            for d in self._devices_data:
                counts[d['device_type']] = counts.get(d['device_type'], 0) + 1
            resumo = '  '.join(f"{t}:{n}" for t, n in sorted(counts.items()))
            self.console_logger.log_ok(f"✓ {len(self._devices_data)} dispositivos carregados  [{resumo}]")
        except Exception as e:
            self.console_logger.log_error(f"Erro: {e}")

    def _clear_filter(self):
        self.var_hw_logo.set("TODAS")
        self.var_hw_search.set("")
        self.var_hw_java_from.set("")
        self.var_hw_java_to.set("")
        self.var_hw_only_unscanned.set(False)
        self._apply_device_filter()

    def _java_in_range(self, value):
        start = self.var_hw_java_from.get().strip()
        end = self.var_hw_java_to.get().strip()
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

    def _apply_device_filter(self):
        logo_filter = self.var_hw_logo.get()
        search_filter = self.var_hw_search.get().strip().lower()
        only_unscanned = self.var_hw_only_unscanned.get()
        self._visible_devices_data = [
            d for d in self._devices_data
            if (logo_filter == "TODAS" or d["bandeira"].upper() == logo_filter)
            and (
                not search_filter
                or search_filter in d["filial"].lower()
                or search_filter in d["ip"].lower()
                or search_filter in d["device_type"].lower()
                or search_filter in d["bandeira"].lower()
                or search_filter in d["status"].lower()
            )
            and self._java_in_range(d["filial"])
            and (not only_unscanned or d["status"].upper() == "NAO ESCANEADO")
        ]
        self._visible_devices_data.sort(
            key=lambda d: (
                (0, int(d["filial"])) if str(d["filial"]).isdigit() else (1, str(d["filial"])),
                d["device_type"],
                d["ip"],
            )
        )
        self.listbox_devices.delete(0, tk.END)
        for d in self._visible_devices_data:
            self.listbox_devices.insert(
                tk.END,
                f"{d['filial']:>6} | {d['ip']:<16} {d['device_type']:<12} {d['bandeira']:<9} {d['status']}",
            )
        self.lbl_hw_count.config(text=f"{len(self._visible_devices_data)} dispositivos")
        self._update_device_selected_label()

    def _update_device_selected_label(self):
        n = len(self.listbox_devices.curselection())
        self.lbl_hw_selected.config(text=f"{n} selecionado{'s' if n != 1 else ''}")

    def _select_all_devices(self):
        self.listbox_devices.selection_set(0, tk.END)
        self._update_device_selected_label()

    def _deselect_all_devices(self):
        self.listbox_devices.selection_clear(0, tk.END)
        self._update_device_selected_label()

    def _invert_device_selection(self):
        selected = set(self.listbox_devices.curselection())
        self.listbox_devices.selection_clear(0, tk.END)
        for idx in range(len(self._visible_devices_data)):
            if idx not in selected:
                self.listbox_devices.selection_set(idx)
        self._update_device_selected_label()

    def _select_devices_by_status(self, status):
        self.listbox_devices.selection_clear(0, tk.END)
        for idx, dev in enumerate(self._visible_devices_data):
            if dev["status"].upper() == status:
                self.listbox_devices.selection_set(idx)
        self._update_device_selected_label()
    
    def _start_scan(self):
        if not self._devices_data:
            messagebox.showwarning("Atenção", "Carregue os dispositivos do banco antes de iniciar.")
            return
        selected = list(self.listbox_devices.curselection())
        if not selected:
            messagebox.showwarning("Atenção", "Selecione ao menos um dispositivo.")
            return
        self._scan_devices = [self._visible_devices_data[idx] for idx in selected]
        self.results = []
        self.stop_event.clear()
        self.btn_scan.config(state=tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL)
        self.progress['value'] = 0
        self.lbl_progress.config(text="0%")
        self.tree_results.delete(*self.tree_results.get_children())
        self.console_logger.clear()
        threading.Thread(target=self._scan_worker).start()

    def _select_pending_from_last_run(self):
        try:
            conn = self.config_mgr.get_sqlite_connection()
            run = conn.execute(
                """
                SELECT id, total_items
                FROM tb_scan_runs
                WHERE scan_type = 'HARDWARE'
                  AND status IN ('RUNNING', 'FAILED', 'CANCELLED')
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
            if not run:
                conn.close()
                self.console_logger.log("Nenhum scan de hardware incompleto encontrado.", "INFO")
                return
            run_id = run[0]
            expected_total = int(run[1] or 0)
            done = {
                row[0]
                for row in conn.execute(
                    """
                    SELECT item_key
                    FROM tb_scan_run_items
                    WHERE run_id = ? AND status = 'SUCCESS'
                    """,
                    (run_id,),
                )
            }
            candidates = {
                row[0]
                for row in conn.execute(
                    """
                    SELECT item_key
                    FROM tb_scan_run_items
                    WHERE run_id = ?
                    """,
                    (run_id,),
                )
            }
            conn.close()
            pending = candidates - done
            include_unrecorded = expected_total > len(candidates)
            self.listbox_devices.selection_clear(0, tk.END)
            selected_count = 0
            for idx, dev in enumerate(self._visible_devices_data):
                key = f"{dev['filial']}|{dev['ip']}"
                if key in pending or (include_unrecorded and key not in done):
                    self.listbox_devices.selection_set(idx)
                    selected_count += 1
            self._update_device_selected_label()
            self.console_logger.log(
                f"Run {run_id}: {selected_count} pendentes selecionados; {len(done)} sucessos preservados.",
                "INFO",
            )
        except Exception as e:
            self.console_logger.log_error(f"Erro ao selecionar pendentes do ultimo scan: {e}")

    def _selected_hw_devices(self):
        return [
            self._visible_devices_data[idx]
            for idx in self.listbox_devices.curselection()
        ]

    def _clear_selected_hw(self, confirm=True, reload_devices=True):
        if str(self.btn_scan["state"]) == "disabled":
            messagebox.showwarning("Atenção", "Aguarde o scan em andamento terminar ou cancele antes de limpar.")
            return False
        devices = self._selected_hw_devices()
        if not devices:
            messagebox.showwarning("Atenção", "Selecione ao menos um dispositivo para limpar.")
            return False
        if confirm and not messagebox.askyesno(
            "Limpar Hardware",
            "Esta ação remove apenas os dados de hardware dos dispositivos selecionados.\n\n"
            "A detecção do Scan Loja será mantida em tb_detected_devices.\n"
            "Campos hw_* e hw_scanned_at serão zerados.\n"
            "Os arquivos de log não serão alterados.\n\n"
            "Deseja continuar?",
        ):
            return False
        try:
            self._ensure_hw_columns()
            conn = self.config_mgr.get_sqlite_connection()
            cur = conn.cursor()
            deleted = 0
            for dev in devices:
                cur.execute(
                    "UPDATE tb_detected_devices SET"
                    " hw_hostname=NULL, hw_cpu_model=NULL, hw_cores=NULL,"
                    " hw_ram_gb=NULL, hw_disk_gb=NULL, hw_os=NULL,"
                    " hw_os_version=NULL, hw_kernel=NULL, hw_cores_fisicos=NULL,"
                    " hw_memoria_total=NULL, hw_mac_address=NULL, hw_mb_manufacturer=NULL,"
                    " hw_mb_product_name=NULL, hw_mb_version=NULL, hw_hdd_media_type=NULL,"
                    " hw_hdd_model=NULL, hw_hdd_size=NULL, hw_scanned_at=NULL"
                    " WHERE ip = ?",
                    (dev["ip"],),
                )
                deleted += cur.rowcount if cur.rowcount != -1 else 0
            conn.commit()
            conn.close()
            self.console_logger.log_ok(f"✓ Limpeza Hardware concluida: {deleted} dispositivos atualizados.")
            if reload_devices:
                self._load_from_db()
            return True
        except Exception as e:
            self.console_logger.log_error(f"Erro ao limpar hardware selecionado: {e}")
            return False

    def _reprocess_selected_hw(self):
        if self._clear_selected_hw(confirm=True, reload_devices=False):
            self._start_scan()

    def is_scan_running(self):
        return str(self.btn_scan["state"]) == "disabled"

    def request_cancel(self):
        if self.is_scan_running():
            self.stop_event.set()
            self.console_logger.log("Cancelando scan de hardware...", "WARNING")
            self.btn_cancel.config(state=tk.DISABLED)

    def _scan_worker(self):
        run_id = None
        run_status = "SUCCESS"
        run_error = ""
        self._ensure_hw_columns()
        try:
            total = len(self._scan_devices)
            run_id = start_scan_run(
                self.config_mgr,
                "HARDWARE",
                "aba_4_hardware",
                total_items=total,
                selected_count=total,
            )
            workers = max(1, min(int(self.spin_workers.get()), total))
            creds_bundle = self._build_creds_bundle()
            self.console_logger.log(
                f"Hardware: Linux usuario='{creds_bundle['linux_user']}' "
                f"senha_lida={'sim' if creds_bundle['linux_pass'] else 'não'} "
                f"tamanho={len(creds_bundle['linux_pass'] or '')}; WMI={'ok' if wmi_module else 'ausente'}; "
                f"SNMP={'ok' if _PYSNMP_OK else 'ausente'}",
                "INFO",
            )
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [
                    executor.submit(scan_core.run_hardware_scan, dev, creds_bundle, self.console_logger.log)
                    for dev in self._scan_devices
                ]
                for idx, future in enumerate(as_completed(futures), 1):
                    if self.stop_event.is_set():
                        run_status = "CANCELLED"
                        self.after(0, lambda: self.console_logger.log("Scan cancelado.", "WARNING"))
                        break
                    result = future.result()
                    filial, ip = result["filial"], result["ip"]
    
                    if scan_core.is_hw_success(result):
                        self._save_hw_result(result, run_id)
                        item_status = "SUCCESS"
                        item_action = "saved"
                        item_ref = "tb_detected_devices.hw_*"
                    else:
                        err_msg = f"  {filial:>6} | {ip:<16} sem dados: {result['os']}"
                        self.after(0, lambda m=err_msg: self.console_logger.log(m, "WARNING"))
                        item_status = result.get("os") or "FAILED"
                        item_action = "ignored"
                        item_ref = ""
                    record_scan_item(
                        self.config_mgr,
                        run_id,
                        f"{filial}|{ip}",
                        filial=filial,
                        ip=ip,
                        device_type=result.get("device_type", ""),
                        status=item_status,
                        action=item_action,
                        result_ref=item_ref,
                        error_message="" if item_status == "SUCCESS" else item_status,
                    )
                    row_values = (
                        result["hostname"], result["cpu_model"], result["cores"],
                        result["ram_gb"],   result["disk_gb"],   result["os"],
                        result["os_version"],
                    )
                    iid = f"{filial}|{ip}"
                    self.after(0, lambda iid=iid, vals=row_values: self.tree_results.insert(
                        '', tk.END, iid=iid, values=vals,
                    ))
                    self.results.append(result)
                    pct = int((idx / total) * 100)
                    self.after(0, self._set_scan_progress, pct, f"{pct}% ({idx}/{total})")
            if self.opt_auto_json.get() and self.results:
                self._export_json(show_empty=False)
            self.after(0, lambda: self.console_logger.log_ok(
                f"✓ Concluido — {len(self.results)}/{total} processados"
            ))
        except Exception as e:
            run_status = "FAILED"
            run_error = str(e)
            self.after(0, lambda e=e: self.console_logger.log_error(f"Erro no scan de hardware: {e}"))
        finally:
            finish_scan_run(self.config_mgr, run_id, run_status, run_error)
            self.after(
                0,
                self._finish_scan_progress,
            )

    def _build_creds_bundle(self):
        """Resolve todas as credenciais uma unica vez antes do pool de workers."""
        return {
            'linux_user': self.config_mgr.get("CREDENTIALS_LINUX_STORE", "user", "pdv"),
            'linux_pass': self.config_mgr.get_secret("CREDENTIALS_LINUX_STORE", "password", ""),
            'linux_timeout': int(self.config_mgr.get("CREDENTIALS_LINUX_STORE", "timeout", "10") or 10),
            'win_drog_user': self.config_mgr.get("CREDENTIALS_TERMINAL_WINDOWS_DROGASIL", "user", ""),
            'win_drog_pass': self.config_mgr.get_secret("CREDENTIALS_TERMINAL_WINDOWS_DROGASIL", "password", ""),
            'win_drog_timeout': int(self.config_mgr.get("CREDENTIALS_TERMINAL_WINDOWS_DROGASIL", "timeout", "30") or 30),
            'win_raia_user': self.config_mgr.get("CREDENTIALS_TERMINAL_WINDOWS_RAIA", "user", ""),
            'win_raia_pass': self.config_mgr.get_secret("CREDENTIALS_TERMINAL_WINDOWS_RAIA", "password", ""),
            'win_raia_timeout': int(self.config_mgr.get("CREDENTIALS_TERMINAL_WINDOWS_RAIA", "timeout", "30") or 30),
            'snmp_community': self.config_mgr.get('CREDENTIALS_SNMP', 'community', 'public'),
            'snmp_port': int(self.config_mgr.get('CREDENTIALS_SNMP', 'port', '161') or 161),
            'snmp_timeout': int(self.config_mgr.get('CREDENTIALS_SNMP', 'timeout', '5') or 5),
        }

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

    def _ensure_hw_columns(self):
        """Garante que as colunas de hardware existem em tb_detected_devices."""
        new_cols = [
            ("hw_hostname",       "TEXT"),
            ("hw_cpu_model",      "TEXT"),
            ("hw_cores",          "INTEGER"),
            ("hw_ram_gb",         "REAL"),
            ("hw_disk_gb",        "REAL"),
            ("hw_os",             "TEXT"),
            ("hw_os_version",     "TEXT"),
            ("hw_kernel",         "TEXT"),
            ("hw_cores_fisicos",  "TEXT"),
            ("hw_memoria_total",  "INTEGER"),
            ("hw_mac_address",    "TEXT"),
            ("hw_mb_manufacturer","TEXT"),
            ("hw_mb_product_name","TEXT"),
            ("hw_mb_version",     "TEXT"),
            ("hw_hdd_media_type", "TEXT"),
            ("hw_hdd_model",      "TEXT"),
            ("hw_hdd_size",       "INTEGER"),
            ("hw_scanned_at",     "DATETIME"),
        ]
        try:
            conn = self.config_mgr.get_sqlite_connection()
            for col, coltype in new_cols:
                try:
                    conn.execute(f"ALTER TABLE tb_detected_devices ADD COLUMN {col} {coltype}")
                except Exception:
                    pass
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _save_hw_result(self, result, run_id=None):
        """Persiste os dados de hardware coletados em tb_detected_devices.
        Sempre sobrescreve — só é chamado após coleta bem-sucedida (_is_hw_success).
        """
        try:
            conn = self.config_mgr.get_sqlite_connection()
            conn.execute(
                "UPDATE tb_detected_devices SET"
                "  hw_hostname=?,    hw_cpu_model=?,     hw_cores=?,"
                "  hw_ram_gb=?,      hw_disk_gb=?,       hw_os=?,"
                "  hw_os_version=?,  hw_kernel=?,        hw_cores_fisicos=?,"
                "  hw_memoria_total=?, hw_mac_address=?, hw_mb_manufacturer=?,"
                "  hw_mb_product_name=?, hw_mb_version=?, hw_hdd_media_type=?,"
                "  hw_hdd_model=?,   hw_hdd_size=?,      hw_scanned_at=CURRENT_TIMESTAMP"
                " WHERE ip=?",
                (
                    result['hostname'],    result['cpu_model'],    result['cores'],
                    result['ram_gb'],      result['disk_gb'],      result['os'],
                    result['os_version'],  result['kernel'],       result['cores_fisicos'],
                    result['memoria_total'], result['mac_address'], result['mb_manufacturer'],
                    result['mb_product_name'], result['mb_version'], result['hdd_media_type'],
                    result['hdd_model'],   result['hdd_size'],
                    result['ip'],
                ),
            )

            # Historico append-only — snapshot completo (relido apos o UPDATE) para
            # que a linha traga tambem os campos de deteccao gravados pela Aba 3.
            row = conn.execute(
                "SELECT * FROM tb_detected_devices WHERE ip = ?", (result['ip'],)
            ).fetchone()
            if row:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute(
                    "INSERT INTO tb_detected_devices_history ("
                    " run_id, filial, ip, expected_type, ssh, radmin, printer, device_type, logo,"
                    " detected_at, hw_hostname, hw_cpu_model, hw_cores, hw_ram_gb, hw_disk_gb, hw_os,"
                    " hw_os_version, hw_kernel, hw_cores_fisicos, hw_memoria_total, hw_mac_address,"
                    " hw_mb_manufacturer, hw_mb_product_name, hw_mb_version, hw_hdd_media_type,"
                    " hw_hdd_model, hw_hdd_size, hw_scanned_at, snapshot_at"
                    ") VALUES (?,?,?,?,?,?,?,?,?, ?,?,?,?,?,?,?, ?,?,?,?,?, ?,?,?,?, ?,?,?,?)"
                    " ON CONFLICT(ip, snapshot_at) DO NOTHING",
                    (
                        run_id, row["filial"], row["ip"], row["expected_type"], row["ssh"], row["radmin"],
                        row["printer"], row["device_type"], row["logo"],
                        row["detected_at"], row["hw_hostname"], row["hw_cpu_model"], row["hw_cores"],
                        row["hw_ram_gb"], row["hw_disk_gb"], row["hw_os"], row["hw_os_version"],
                        row["hw_kernel"], row["hw_cores_fisicos"], row["hw_memoria_total"], row["hw_mac_address"],
                        row["hw_mb_manufacturer"], row["hw_mb_product_name"], row["hw_mb_version"],
                        row["hw_hdd_media_type"], row["hw_hdd_model"], row["hw_hdd_size"],
                        row["hw_scanned_at"], now_str,
                    ),
                )

            conn.commit()
            conn.close()
            msg = (f"  {result.get('filial', ''):>6} | {result['ip']:<16}"
                   f" {result['hostname']:<20} OS:{result['os']}")
            self.after(0, lambda m=msg: self.console_logger.log_ok(m))
        except Exception as e:
            err, ip = str(e), result['ip']
            self.after(0, lambda m=f"Erro ao salvar {ip}: {err}": self.console_logger.log_error(m))

    def _export_json(self, show_empty=True):
        if not self.results:
            if show_empty:
                messagebox.showinfo("Info", "Nenhum resultado para exportar.")
            return
        try:
            fn = f"scan_hw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(fn, 'w') as f: json.dump(self.results, f, indent=2)
            self.console_logger.log_ok(f"✓ Exportado: {fn}")
        except Exception as e: self.console_logger.log_error(f"Erro: {e}")
