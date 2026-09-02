#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABA 7 — Autopilot: pipeline automatico B12 -> Scan Loja -> Hardware por loja.

Cada loja avanca de etapa assim que a etapa anterior termina (sucesso ou
falha, no caso do B12), sem esperar o lote inteiro. Cada etapa tem seu proprio
pool de workers configuravel. Retomada apos interrupcao reaproveita
`tb_scan_runs`/`tb_scan_run_items` (via `scan_runs.get_pending_items`) para
pular o que ja foi concluido com sucesso.
"""

import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

from src.common import scan_core, xls_import
from src.common.config import ConfigManager
from src.common.console_logger import ConsoleLogger
from src.common.scan_runs import finish_scan_run, get_pending_items, record_scan_item, start_scan_run
from src.common.treeview_sort import make_treeview_sortable
from src.common.utils import get_store_scan_targets


class Tab7Autopilot(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.parent = parent
        self.config_mgr = ConfigManager()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self._mute_logs = False          # apos Cancelar, silencia o ruido dos workers em andamento
        self._worker_running = False
        self._pipeline_mode = "fresh"    # fresh | resume | retry_failed (decidido em _start_pipeline)
        self._all_stores = []
        self._store_row_iid = {}
        self._pipeline_selection = []
        self._create_ui()
        self.after(100, self._load_stores)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _create_ui(self):
        frame_xls = ttk.LabelFrame(self, text="Lista de lojas (XLS opcional)", padding=8)
        frame_xls.pack(fill=tk.X, padx=10, pady=(10, 0))
        row_xls = ttk.Frame(frame_xls)
        row_xls.pack(fill=tk.X)
        self.var_xls_path = tk.StringVar()
        ttk.Entry(row_xls, textvariable=self.var_xls_path, width=60).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(row_xls, text="Procurar...", command=self._browse_xls).pack(side=tk.LEFT, padx=3)
        self.var_xls_mode = tk.StringVar(value="upsert")
        ttk.Radiobutton(row_xls, text="Atualizar", variable=self.var_xls_mode, value="upsert").pack(side=tk.LEFT, padx=(12, 3))
        ttk.Radiobutton(row_xls, text="Limpar e importar", variable=self.var_xls_mode, value="truncate").pack(side=tk.LEFT, padx=3)
        ttk.Label(
            row_xls,
            text="(deixe em branco para usar as lojas ja importadas na Aba 1)",
            foreground="gray",
        ).pack(side=tk.LEFT, padx=10)

        frame_filter = ttk.LabelFrame(self, text="Selecao de Lojas", padding=8)
        frame_filter.pack(fill=tk.X, padx=10, pady=(8, 0))
        row1 = ttk.Frame(frame_filter)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Logomarca:").pack(side=tk.LEFT)
        self.var_logo = tk.StringVar(value="TODAS")
        for logo in ("TODAS", "DROGASIL", "RAIA"):
            ttk.Radiobutton(row1, text=logo, variable=self.var_logo, value=logo,
                             command=self._apply_filter).pack(side=tk.LEFT, padx=6)
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
        ttk.Button(row1, text="Recarregar", command=self._load_stores).pack(side=tk.LEFT, padx=4)

        row2 = ttk.Frame(frame_filter)
        row2.pack(fill=tk.X, pady=(4, 2))
        self.lbl_count = ttk.Label(row2, text="0 lojas", foreground="gray")
        self.lbl_count.pack(side=tk.LEFT, padx=(0, 12))
        ttk.Button(row2, text="Marcar todas", command=self._select_all).pack(side=tk.LEFT, padx=3)
        ttk.Button(row2, text="Desmarcar todas", command=self._deselect_all).pack(side=tk.LEFT, padx=3)
        ttk.Button(row2, text="Inverter", command=self._invert_selection).pack(side=tk.LEFT, padx=3)
        self.lbl_selected = ttk.Label(row2, text="0 selecionadas", foreground="blue")
        self.lbl_selected.pack(side=tk.LEFT, padx=12)

        frame_list = ttk.Frame(self)
        frame_list.pack(fill=tk.BOTH, expand=False, padx=10, pady=(4, 0))
        vscroll = ttk.Scrollbar(frame_list, orient=tk.VERTICAL)
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        cols = ("filial", "nome", "uf", "logo", "ip", "cidr")
        self.tree_stores = ttk.Treeview(
            frame_list, columns=cols, show="headings", selectmode="extended",
            yscrollcommand=vscroll.set, height=5,
        )
        self.tree_stores.pack(fill=tk.BOTH, expand=True)
        vscroll.config(command=self.tree_stores.yview)
        for col, label, width in [
            ("filial", "JAVA", 70), ("nome", "Nome", 220), ("uf", "UF", 40),
            ("logo", "Logo", 90), ("ip", "IP Banco 12", 120), ("cidr", "CIDR", 70),
        ]:
            self.tree_stores.heading(col, text=label)
            self.tree_stores.column(col, width=width, anchor=tk.W)
        self._sort_stores = make_treeview_sortable(self.tree_stores)
        self.tree_stores.bind("<<TreeviewSelect>>", lambda _e: self._update_selected_label())

        frame_options = ttk.LabelFrame(self, text="Opcoes do Pipeline", padding=8)
        frame_options.pack(fill=tk.X, padx=10, pady=4)
        # Limites recomendados para o coletor-alvo (VM 10 vCPU, ~8 GB livres,
        # rede direta). Sao os tetos: WMI (Hardware) e o consumidor de memoria.
        ttk.Label(frame_options, text="Workers B12:").pack(side=tk.LEFT)
        self.spin_workers_b12 = ttk.Spinbox(frame_options, from_=1, to=20, width=4)
        self.spin_workers_b12.set(20)
        self.spin_workers_b12.pack(side=tk.LEFT, padx=(2, 10))
        ttk.Label(frame_options, text="Workers Scan:").pack(side=tk.LEFT)
        self.spin_workers_scan = ttk.Spinbox(frame_options, from_=1, to=40, width=4)
        self.spin_workers_scan.set(40)
        self.spin_workers_scan.pack(side=tk.LEFT, padx=(2, 10))
        ttk.Label(frame_options, text="Workers Hardware:").pack(side=tk.LEFT)
        self.spin_workers_hw = ttk.Spinbox(frame_options, from_=1, to=10, width=4)
        self.spin_workers_hw.set(10)
        self.spin_workers_hw.pack(side=tk.LEFT, padx=(2, 10))

        row_opts2 = ttk.Frame(frame_options)
        row_opts2.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(row_opts2, text="Timeout B12 (s):").pack(side=tk.LEFT)
        self.spin_b12_timeout = ttk.Spinbox(row_opts2, from_=1, to=30, width=4)
        self.spin_b12_timeout.set(5)
        self.spin_b12_timeout.pack(side=tk.LEFT, padx=(2, 10))
        ttk.Label(row_opts2, text="Timeout Scan (s):").pack(side=tk.LEFT)
        self.spin_scan_timeout = ttk.Spinbox(row_opts2, from_=1, to=10, width=4)
        self.spin_scan_timeout.set(2)
        self.spin_scan_timeout.pack(side=tk.LEFT, padx=(2, 10))
        self.opt_b12_detail = tk.BooleanVar(value=True)
        ttk.Checkbutton(row_opts2, text="Coletar detalhe B12", variable=self.opt_b12_detail).pack(side=tk.LEFT, padx=8)
        self.opt_ssh = tk.BooleanVar(value=True)
        self.opt_radmin = tk.BooleanVar(value=True)
        self.opt_printer = tk.BooleanVar(value=True)
        ttk.Checkbutton(row_opts2, text="SSH", variable=self.opt_ssh).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(row_opts2, text="Radmin", variable=self.opt_radmin).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(row_opts2, text="Impressora", variable=self.opt_printer).pack(side=tk.LEFT, padx=4)
        ttk.Label(
            row_opts2,
            text="(se a ultima execucao foi interrompida, ao iniciar sera perguntado: "
                 "limpar e recomecar / completar o que faltou / reescanear falhas)",
            foreground="gray",
        ).pack(side=tk.LEFT, padx=12)

        frame_stage = ttk.LabelFrame(self, text="Progresso das Etapas (executam em paralelo)", padding=8)
        frame_stage.pack(fill=tk.X, padx=10, pady=4)
        self._stage_bars = {}
        self._stage_lbls = {}
        for key, label in (("b12", "B12"), ("scan", "Scan Loja"), ("hw", "Hardware")):
            row = ttk.Frame(frame_stage)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=f"{label}:", width=10).pack(side=tk.LEFT)
            bar = ttk.Progressbar(row, mode="determinate", maximum=100)
            bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
            lbl = ttk.Label(row, text="—", width=34, anchor=tk.W)
            lbl.pack(side=tk.LEFT)
            self._stage_bars[key] = bar
            self._stage_lbls[key] = lbl

        frame_progress = ttk.LabelFrame(self, text="Progresso por Loja", padding=8)
        frame_progress.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        prog_scroll = ttk.Scrollbar(frame_progress, orient=tk.VERTICAL)
        prog_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        pcols = ("java", "b12", "scan", "hw")
        self.tree_progress = ttk.Treeview(
            frame_progress, columns=pcols, show="headings",
            yscrollcommand=prog_scroll.set, height=8,
        )
        self.tree_progress.pack(fill=tk.BOTH, expand=True)
        prog_scroll.config(command=self.tree_progress.yview)
        for col, label, width in [
            ("java", "JAVA", 70), ("b12", "B12", 220), ("scan", "Scan Loja", 220), ("hw", "Hardware", 220),
        ]:
            self.tree_progress.heading(col, text=label)
            self.tree_progress.column(col, width=width, anchor=tk.W)
        make_treeview_sortable(self.tree_progress)

        frame_console = ttk.LabelFrame(self, text="Log em Tempo Real", padding=8)
        frame_console.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        self.console_logger = ConsoleLogger(frame_console, height=10, log_name="aba_7_autopilot")

        frame_action = ttk.Frame(self)
        frame_action.pack(fill=tk.X, padx=10, pady=(4, 10))
        self.lbl_status = ttk.Label(frame_action, text="Parado")
        self.lbl_status.pack(side=tk.LEFT, padx=(0, 12))
        self.btn_validate = ttk.Button(frame_action, text="Validar", command=self._run_validation)
        self.btn_validate.pack(side=tk.LEFT, padx=5)
        self.btn_start = ttk.Button(frame_action, text="Iniciar Autopilot", command=self._start_pipeline)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        self.btn_pause = ttk.Button(frame_action, text="Pausar", command=self._toggle_pause, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, padx=5)
        self.btn_cancel = ttk.Button(frame_action, text="Cancelar", command=self._cancel_pipeline, state=tk.DISABLED)
        self.btn_cancel.pack(side=tk.LEFT, padx=5)

    # ------------------------------------------------------------------
    # Selecao de lojas
    # ------------------------------------------------------------------

    def _load_stores(self):
        try:
            conn = self.config_mgr.get_sqlite_connection()
            rows = conn.execute(
                """
                SELECT filial, nome_filial, uf, logomarca, ip_banco_12, COALESCE(cidr, '')
                FROM tb_filial
                WHERE ativo = 1 AND ip_banco_12 IS NOT NULL AND TRIM(ip_banco_12) <> ''
                ORDER BY logomarca, CAST(filial AS INTEGER)
                """
            ).fetchall()
            conn.close()
            self._all_stores = [tuple(r) for r in rows]
            self._apply_filter()
            self.console_logger.log(f"{len(self._all_stores)} lojas carregadas.", "INFO")
        except Exception as e:
            self.console_logger.log(f"Erro ao carregar lojas: {e}", "ERROR")

    def _browse_xls(self):
        path = filedialog.askopenfilename(
            title="Selecionar XLS de lojas",
            filetypes=[("Excel files", "*.xls *.xlsx"), ("Todos", "*.*")],
        )
        if path:
            self.var_xls_path.set(path)

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
        logo_filter = self.var_logo.get()
        filtered = [
            row for row in self._all_stores
            if (logo_filter == "TODAS" or str(row[3]).upper() == logo_filter)
            and self._java_in_range(row[0])
        ]
        self.tree_stores.delete(*self.tree_stores.get_children())
        for row in filtered:
            self.tree_stores.insert("", tk.END, values=tuple(row))
        self._sort_stores("filial", descending=False)
        self.lbl_count.config(text=f"{len(filtered)} lojas")
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

    def _selected_stores(self):
        stores = []
        for iid in self.tree_stores.selection():
            filial, nome, uf, logo, ip, cidr = self.tree_stores.item(iid, "values")
            stores.append({
                "filial": str(filial), "historico": "", "nome": str(nome),
                "logo": str(logo), "ip": str(ip).strip(), "cidr": str(cidr).strip(),
            })
        return stores

    def _query_pipeline_stores(self, filiais=None):
        """Le as lojas ativas direto do SQLite (seguro fora da main thread).

        `filiais`: set de JAVA/filial para filtrar; None = todas. Usado pelo
        worker do pipeline para nao depender da selecao do Treeview, que e
        recriado (e perde a selecao) quando um XLS e reimportado antes de rodar.
        """
        conn = self.config_mgr.get_sqlite_connection()
        try:
            rows = conn.execute(
                """
                SELECT filial, nome_filial, logomarca, ip_banco_12,
                       COALESCE(cidr, ''), COALESCE(historico, '')
                FROM tb_filial
                WHERE ativo = 1 AND ip_banco_12 IS NOT NULL AND TRIM(ip_banco_12) <> ''
                ORDER BY logomarca, CAST(filial AS INTEGER)
                """
            ).fetchall()
        finally:
            conn.close()
        want = {str(f) for f in filiais} if filiais is not None else None
        out = []
        for filial, nome, logo, ip, cidr, historico in rows:
            if want is not None and str(filial) not in want:
                continue
            out.append({
                "filial": str(filial), "historico": str(historico or ""),
                "nome": str(nome or ""), "logo": str(logo or ""),
                "ip": str(ip or "").strip(), "cidr": str(cidr or "").strip(),
            })
        return out

    # ------------------------------------------------------------------
    # Progresso (UI, chamado via self.after)
    # ------------------------------------------------------------------

    def _init_store_row(self, filial):
        if filial in self._store_row_iid:
            return
        iid = self.tree_progress.insert("", tk.END, values=(filial, "aguardando", "-", "-"))
        self._store_row_iid[filial] = iid

    def _update_store_row(self, filial, stage, text):
        iid = self._store_row_iid.get(filial)
        if not iid:
            return
        col_idx = {"b12": 1, "scan": 2, "hw": 3}.get(stage)
        if col_idx is None:
            return
        values = list(self.tree_progress.item(iid, "values"))
        values[col_idx] = text
        self.tree_progress.item(iid, values=values)

    def _update_status_label(self, text):
        self.lbl_status.config(text=text)

    def _set_stage_bar(self, key, done, total, note=""):
        """Atualiza uma das 3 barras de etapa. Chamado sempre via self.after."""
        bar = self._stage_bars.get(key)
        lbl = self._stage_lbls.get(key)
        if bar is None:
            return
        done = int(done or 0)
        total = max(int(total or 0), done)
        pct = (done / total * 100.0) if total else 0.0
        bar["value"] = pct
        # A direita da barra: processados/total (+ % e nota opcional).
        txt = f"{done}/{total}" if total else "0/0"
        if total:
            txt += f"  |  {pct:.0f}%"
        if note:
            txt += f"  {note}"
        lbl.config(text=txt)

    def _refresh_stage_bars(self, b12_done, b12_total, scan_done, scan_total,
                            hw_done, hw_total, hw_final):
        self._set_stage_bar("b12", b12_done, b12_total)
        self._set_stage_bar("scan", scan_done, scan_total)
        self._set_stage_bar(
            "hw", hw_done, hw_total,
            note="" if hw_final else "(parcial - Scan Loja em curso)",
        )

    def _reset_stage_bars(self):
        for key in ("b12", "scan", "hw"):
            self._set_stage_bar(key, 0, 0)

    def _start_bar_ticker(self):
        """Agenda o refresh de 1 s das 3 barras enquanto o pipeline roda."""
        self._tick_bars()

    def _tick_bars(self):
        st = getattr(self, "_live_bar_state", None)
        if st:
            c = st["counts"]
            total_scan = st["total_scan"]
            scan_ok = bool(st["prog"].get("scan_ok")
                           or (total_scan and c["scan_done"] >= total_scan))
            self._refresh_stage_bars(
                c["b12_done"], st["nstores"],
                c["scan_done"], total_scan,
                c["hw_done"], c["hw_total"], scan_ok,
            )
        if self._worker_running:
            self.after(1000, self._tick_bars)

    def _log(self, msg, level="INFO"):
        if self._mute_logs:
            return  # cancelamento em andamento: descarta ruido dos workers ainda vivos
        self.after(0, lambda: self.console_logger.log(msg, level))

    # ------------------------------------------------------------------
    # Controles
    # ------------------------------------------------------------------

    def is_scan_running(self):
        return str(self.btn_start["state"]) == "disabled"

    def request_cancel(self):
        if self.is_scan_running():
            self._cancel_pipeline()

    def _toggle_pause(self):
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.btn_pause.config(text="Pausar")
            self.console_logger.log("Retomando envio de novo trabalho.", "INFO")
        else:
            self.pause_event.set()
            self.btn_pause.config(text="Retomar")
            self.console_logger.log("Pausado — trabalho em andamento sera concluido; nada novo sera iniciado.", "WARNING")

    def _cancel_pipeline(self):
        # Cancelamento imediato: para de aceitar/consumir trabalho, silencia o
        # ruido dos workers que ainda estejam em rede e devolve a UI ao estado
        # ocioso na hora. As threads de rede em voo morrem sozinhas (daemon) e
        # seus resultados sao descartados.
        self.stop_event.set()
        self.pause_event.clear()
        self._mute_logs = True
        self.console_logger.log(
            "Cancelado. Conexoes em andamento sao descartadas; retomavel na proxima execucao (Retomar).",
            "WARNING",
        )
        self.btn_cancel.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.DISABLED)
        self._pipeline_done()  # reabilita "Iniciar" imediatamente

    # ------------------------------------------------------------------
    # Validacao (pre-flight)
    # ------------------------------------------------------------------

    def _validate_preflight(self):
        """Verifica os pre-requisitos do pipeline. Retorna (errors, warnings),
        ambos listas de strings, e loga cada verificacao no console."""
        errors, warnings = [], []
        log = self.console_logger.log

        def _err(msg):
            errors.append(msg)
            log(f"[ERRO]  {msg}", "ERROR")

        def _warn(msg):
            warnings.append(msg)
            log(f"[AVISO] {msg}", "WARNING")

        def _ok(msg):
            log(f"[OK]    {msg}", "SUCCESS")

        log("Validando pre-requisitos do Autopilot...", "INFO")
        xls_path = self.var_xls_path.get().strip()
        selection = list(self._selected_stores())
        selected_filiais = {s["filial"] for s in selection}

        # 1) Entrada: selecao de lojas ou XLS
        if not selection and not xls_path:
            _err("Nenhuma loja marcada e nenhum XLS informado.")
        elif selection:
            _ok(f"{len(selection)} loja(s) marcada(s).")

        # 2) XLS informado
        if xls_path:
            p = Path(xls_path)
            if not p.is_file():
                _err(f"XLS nao encontrado: {xls_path}")
            elif p.suffix.lower() == ".xlsx":
                _err("XLS em .xlsx nao e suportado pelo importador (converta para .xls).")
            elif p.suffix.lower() != ".xls":
                _warn(f"Extensao inesperada no XLS ('{p.suffix}'); esperado .xls.")
            else:
                try:
                    import xlrd  # importador usa xlrd
                    book = xlrd.open_workbook(str(p))
                    sheet = book.sheet_by_index(0)
                    mism = xls_import.validate_header_mapping(sheet.row_values(0))
                    if mism:
                        det = "; ".join(f"col {i}: esperava '{exp}', achou '{cur}'" for i, exp, cur, _ in mism[:4])
                        _err(f"Cabecalho do XLS divergente ({len(mism)}): {det}")
                    else:
                        _ok(f"XLS OK ({p.name}, {max(sheet.nrows - 1, 0)} linha(s)).")
                except ImportError:
                    _err("Biblioteca 'xlrd' ausente — nao e possivel importar XLS.")
                except Exception as e:
                    _err(f"Falha ao ler o XLS: {e}")

        # 3) Banco de dados
        conn = None
        try:
            db_path = self.config_mgr.get_path("DATABASE", "path", "./database/devices.db")
            conn = self.config_mgr.get_sqlite_connection()
        except Exception as e:
            _err(f"Nao foi possivel abrir o banco SQLite: {e}")
        if conn is not None:
            try:
                tables = {r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
                for t in ("tb_filial", "tb_detected_devices", "tb_scan_runs", "tb_scan_run_items"):
                    if t not in tables:
                        _err(f"Tabela ausente no banco: {t} (schema SQLite incompleto).")
                if "tb_filial" in tables:
                    base_sql = ("SELECT COUNT(*) FROM tb_filial WHERE ativo=1 "
                                "AND ip_banco_12 IS NOT NULL AND TRIM(ip_banco_12) <> ''")
                    total_ativas = conn.execute(base_sql).fetchone()[0]
                    if selected_filiais:
                        ph = ",".join("?" * len(selected_filiais))
                        resolviveis = conn.execute(
                            f"{base_sql} AND filial IN ({ph})", tuple(selected_filiais)
                        ).fetchone()[0]
                        faltando = len(selected_filiais) - resolviveis
                        if resolviveis == 0 and not xls_path:
                            _err("Nenhuma das lojas marcadas tem IP valido no banco.")
                        elif faltando > 0 and not xls_path:
                            _warn(f"{faltando} loja(s) marcada(s) sem IP valido serao ignoradas.")
                        else:
                            _ok(f"{resolviveis} loja(s) marcada(s) prontas no banco.")
                    elif not xls_path:
                        if total_ativas == 0:
                            _err("Banco sem lojas ativas com IP; importe um XLS (Aba 1) ou informe um aqui.")
                        else:
                            _ok(f"{total_ativas} loja(s) ativa(s) com IP no banco.")
                log(f"Banco: {db_path}", "INFO")
            except Exception as e:
                _err(f"Erro ao inspecionar o banco: {e}")
            finally:
                conn.close()

        # 4) Credenciais
        try:
            lx_user = (self.config_mgr.get("CREDENTIALS_LINUX_STORE", "user", "") or "").strip()
            lx_pass = self.config_mgr.get_secret("CREDENTIALS_LINUX_STORE", "password", "")
            if not lx_user:
                _err("Credencial Linux (B12/PDV): usuario nao configurado (aba Credenciais).")
            if not lx_pass:
                _err("Credencial Linux (B12/PDV): senha nao configurada (aba Credenciais).")
            if lx_user and lx_pass:
                _ok(f"Credencial Linux configurada (usuario '{lx_user}').")
        except Exception as e:
            _err(f"Falha ao ler/decodificar credencial Linux: {e}")

        for sec, rotulo in (("CREDENTIALS_TERMINAL_WINDOWS_DROGASIL", "Windows Drogasil"),
                            ("CREDENTIALS_TERMINAL_WINDOWS_RAIA", "Windows Raia")):
            try:
                u = (self.config_mgr.get(sec, "user", "") or "").strip()
                pw = self.config_mgr.get_secret(sec, "password", "")
                if not (u and pw):
                    _warn(f"Credencial {rotulo} incompleta: hardware de terminais Windows dessa "
                          "bandeira nao sera coletado.")
            except Exception as e:
                _warn(f"Falha ao ler credencial {rotulo}: {e}")

        if self.opt_printer.get():
            comm = (self.config_mgr.get("CREDENTIALS_SNMP", "community", "") or "").strip()
            if not comm:
                _warn("SNMP community vazia: coleta de impressoras pode falhar.")

        # 5) Parametros do pipeline
        for widget, nome in ((self.spin_workers_b12, "Workers B12"),
                             (self.spin_workers_scan, "Workers Scan"),
                             (self.spin_workers_hw, "Workers Hardware"),
                             (self.spin_b12_timeout, "Timeout B12"),
                             (self.spin_scan_timeout, "Timeout Scan")):
            try:
                v = int(str(widget.get()).strip())
                if v < 1:
                    _err(f"{nome} deve ser >= 1 (atual: {v}).")
            except (ValueError, TypeError):
                _err(f"{nome} invalido: '{widget.get()}'.")

        if errors:
            log(f"Validacao: {len(errors)} erro(s), {len(warnings)} aviso(s).", "ERROR")
        elif warnings:
            log(f"Validacao: OK com {len(warnings)} aviso(s).", "WARNING")
        else:
            log("Validacao: tudo OK.", "SUCCESS")
        return errors, warnings

    def _run_validation(self):
        errors, warnings = self._validate_preflight()
        if errors:
            corpo = "Corrija antes de iniciar:\n\n- " + "\n- ".join(errors)
            if warnings:
                corpo += "\n\nAvisos:\n- " + "\n- ".join(warnings)
            messagebox.showerror("Validacao — pendencias", corpo)
        elif warnings:
            messagebox.showwarning(
                "Validacao — avisos",
                "Pode iniciar, mas verifique:\n\n- " + "\n- ".join(warnings))
        else:
            messagebox.showinfo("Validacao", "Todos os pre-requisitos estao OK.")

    # ------------------------------------------------------------------
    # Modo de execucao (execucao anterior interrompida)
    # ------------------------------------------------------------------

    _COLLECTED_TABLES = (
        "tb_scan_run_items", "tb_scan_runs",
        "tb_devices_detail", "tb_detected_devices", "tb_b12_data_collection_status",
    )

    def _detect_incomplete_run(self):
        """Retorna {run_id, status, started_at} se a *ultima sessao* de Autopilot
        nao terminou, ou None.

        So considera a run mais recente de cada etapa (B12/SCAN_LOJA/HARDWARE) —
        ou seja, a ultima sessao. Runs incompletas de sessoes anteriores ja
        substituidas por uma sessao que terminou sao historico e nao devem
        reabrir o dialogo de retomada.
        """
        try:
            conn = self.config_mgr.get_sqlite_connection()
        except Exception:
            return None
        try:
            row = conn.execute(
                """
                SELECT id, status, started_at
                FROM tb_scan_runs
                WHERE source_tab = 'autopilot'
                  AND id IN (
                      SELECT MAX(id) FROM tb_scan_runs
                      WHERE source_tab = 'autopilot'
                      GROUP BY scan_type
                  )
                  AND status IN ('RUNNING', 'FAILED', 'CANCELLED')
                ORDER BY id DESC LIMIT 1
                """
            ).fetchone()
        except Exception:
            row = None
        finally:
            conn.close()
        if not row:
            return None
        return {"run_id": row[0], "status": row[1], "started_at": row[2]}

    def _ask_restart_mode(self, info):
        """Dialogo modal com as 3 opcoes. Retorna 'fresh'|'resume'|'retry_failed'
        ou None (cancelar)."""
        dlg = tk.Toplevel(self)
        dlg.title("Execucao anterior nao concluida")
        dlg.transient(self.winfo_toplevel())
        dlg.resizable(False, False)
        choice = {"v": None}

        _motivo = {
            "RUNNING": "foi interrompida antes de terminar",
            "CANCELLED": "foi cancelada",
            "FAILED": "terminou com falha",
        }.get(info["status"], "nao terminou")
        msg = (
            f"A ultima execucao do Autopilot {_motivo}\n"
            f"(run #{info['run_id']}, {info['status']}, iniciada em {info['started_at']}).\n\n"
            "Como continuar?"
        )
        ttk.Label(dlg, text=msg, justify=tk.LEFT).pack(anchor=tk.W, padx=14, pady=(14, 8))
        body = ttk.Frame(dlg)
        body.pack(fill=tk.X, padx=14, pady=(0, 14))

        def pick(v):
            choice["v"] = v
            dlg.destroy()

        for text, val in (
            ("Limpar banco e recomecar  (apaga tudo o que foi coletado)", "fresh"),
            ("Completar o que faltou  (pula os itens ja concluidos)", "resume"),
            ("Reescanear apenas os que falharam", "retry_failed"),
        ):
            ttk.Button(body, text=text, width=52, command=lambda v=val: pick(v)).pack(fill=tk.X, pady=3)
        ttk.Button(body, text="Cancelar", command=lambda: pick(None)).pack(fill=tk.X, pady=(10, 0))

        dlg.bind("<Escape>", lambda _e: pick(None))
        dlg.protocol("WM_DELETE_WINDOW", lambda: pick(None))
        dlg.grab_set()
        self.wait_window(dlg)
        return choice["v"]

    def _clear_collected_data(self):
        """Apaga os dados coletados e o rastreio de execucoes (mantem tb_filial
        e as tabelas *_history). Usado no modo 'fresh'."""
        conn = self.config_mgr.get_sqlite_connection()
        try:
            existing = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            apagadas = []
            for t in self._COLLECTED_TABLES:
                if t in existing:
                    conn.execute(f"DELETE FROM {t}")
                    apagadas.append(t)
            conn.commit()
        finally:
            conn.close()
        self._log(f"Banco limpo ({', '.join(apagadas)}).", "WARNING")

    def _start_pipeline(self):
        # Captura a selecao AGORA, na main thread. Se um XLS for reimportado no
        # inicio do pipeline, o Treeview e recriado e a selecao some — por isso
        # nao pode ser lida depois, dentro do worker.
        if self._worker_running:
            messagebox.showinfo("Autopilot", "Aguarde o encerramento da execucao anterior.")
            return
        self._pipeline_selection = self._selected_stores()

        # Execucao anterior interrompida? Pergunta o que fazer.
        incomplete = self._detect_incomplete_run()
        if incomplete:
            mode = self._ask_restart_mode(incomplete)
            if mode is None:
                return
            if mode == "fresh" and not messagebox.askyesno(
                "Confirmar limpeza",
                "Isto APAGA todos os dados ja coletados (B12, Scan Loja, Hardware) "
                "e o historico de execucoes deste banco.\n\nContinuar?",
                icon="warning",
            ):
                return
        else:
            mode = "fresh"
        self._pipeline_mode = mode

        self.console_logger.clear()
        errors, warnings = self._validate_preflight()
        if errors:
            messagebox.showerror(
                "Nao e possivel iniciar o Autopilot",
                "Pendencias:\n\n- " + "\n- ".join(errors))
            return
        if warnings and not messagebox.askyesno(
            "Avisos na validacao",
            "Avisos:\n\n- " + "\n- ".join(warnings) + "\n\nIniciar mesmo assim?"
        ):
            return
        self.stop_event.clear()
        self.pause_event.clear()
        self._mute_logs = False
        self._worker_running = True
        self.btn_validate.config(state=tk.DISABLED)
        self.btn_start.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL, text="Pausar")
        self.btn_cancel.config(state=tk.NORMAL)
        self.tree_progress.delete(*self.tree_progress.get_children())
        self._store_row_iid = {}
        self._reset_stage_bars()
        threading.Thread(target=self._pipeline_worker, daemon=True).start()

    def _pipeline_done(self):
        self.btn_validate.config(state=tk.NORMAL)
        self.btn_start.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED, text="Pausar")
        self.btn_cancel.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Credenciais
    # ------------------------------------------------------------------

    def _get_linux_credentials(self):
        user = self.config_mgr.get("CREDENTIALS_LINUX_STORE", "user", "pdv")
        password = self.config_mgr.get_secret("CREDENTIALS_LINUX_STORE", "password", "")
        port = int(self.config_mgr.get("CREDENTIALS_LINUX_STORE", "port", "22") or 22)
        return user, password, port

    def _build_hw_creds(self):
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

    # ------------------------------------------------------------------
    # Motor do pipeline
    # ------------------------------------------------------------------

    def _pipeline_worker(self):
        run_ids = {}
        pipeline_finalized = False
        try:
            xls_path = self.var_xls_path.get().strip()
            if xls_path:
                self._log(f"Importando XLS: {xls_path}", "INFO")
                stats = xls_import.import_filiais(xls_path, mode=self.var_xls_mode.get(), config_mgr=self.config_mgr)
                if stats.status == "error":
                    self._log(f"Erro ao importar XLS: {stats.error}", "ERROR")
                    return
                self._log(f"XLS importado: {stats.imported}/{stats.total_rows} lojas.", "SUCCESS")
                self.after(0, self._load_stores)  # so atualiza a UI; a logica abaixo le do SQLite

            # Resolve a lista de lojas a partir do SQLite (nao do Treeview, que
            # pode ter sido recriado pela reimportacao do XLS acima).
            selected_filiais = {s["filial"] for s in self._pipeline_selection}
            if selected_filiais:
                stores = self._query_pipeline_stores(selected_filiais)
                found = {s["filial"] for s in stores}
                missing = selected_filiais - found
                if missing:
                    amostra = ", ".join(sorted(missing)[:10])
                    self._log(
                        f"{len(missing)} loja(s) selecionada(s) sem IP valido ou ausente(s) apos importacao "
                        f"(ignoradas): {amostra}",
                        "WARNING",
                    )
            elif xls_path:
                stores = self._query_pipeline_stores()
                self._log(f"Nenhuma loja marcada — usando todas as {len(stores)} lojas ativas importadas.", "INFO")
            else:
                stores = []

            if not stores:
                self._log("Nenhuma loja selecionada para o pipeline.", "WARNING")
                return

            self._log(f"{len(stores)} loja(s) no pipeline.", "INFO")

            # --- Modo de execucao (decidido em _start_pipeline) ---------------
            mode = self._pipeline_mode
            rotulo_modo = {
                "fresh": "limpar banco e recomecar",
                "resume": "completar o que faltou",
                "retry_failed": "reescanear apenas os que falharam",
            }.get(mode, mode)
            self._log(f"Modo: {rotulo_modo}.", "INFO")

            done_b12 = done_scan = done_hw = set()
            retry_b12 = retry_scan = retry_hw = set()
            stage_complete = {"b12": False, "scan": False, "hw": False}
            if mode == "fresh":
                self._clear_collected_data()
            else:
                for scan_type, kind in (("B12", "b12"), ("SCAN_LOJA", "scan"), ("HARDWARE", "hw")):
                    info = get_pending_items(self.config_mgr, scan_type)
                    if not info["run_id"] and not info.get("complete"):
                        continue
                    # `complete`: a ultima run da etapa terminou — no modo "resume"
                    # todos os itens registrados sao pulados; nada fica pendente.
                    stage_complete[kind] = bool(info.get("complete"))
                    if info.get("complete"):
                        done, pend = info["done"], set()
                    else:
                        done = set() if info["include_unrecorded"] else info["done"]
                        pend = info["pending"]
                    if kind == "b12":
                        done_b12, retry_b12 = done, pend
                    elif kind == "scan":
                        done_scan, retry_scan = done, pend
                    else:
                        done_hw, retry_hw = done, pend
                if mode == "retry_failed":
                    retry_filiais = {k.split("|")[0] for k in (retry_b12 | retry_scan | retry_hw)}
                    if not retry_filiais:
                        self._log("Nada falhou na ultima execucao — nada a reescanear.", "SUCCESS")
                        return
                    stores = [s for s in stores if s["filial"] in retry_filiais]
                    self._log(
                        f"Reescaneando {len(stores)} loja(s) com falha "
                        f"(B12 {len(retry_b12)}, Scan Loja {len(retry_scan)}, Hardware {len(retry_hw)}). "
                        "Cada etapa refaz somente os itens ja marcados como falha.",
                        "INFO",
                    )
                elif mode == "resume":
                    if all(stage_complete.values()):
                        self._log(
                            "Todas as etapas da ultima sessao ja terminaram — nada a completar. "
                            "Use 'Limpar e recomecar' para uma coleta nova.",
                            "SUCCESS",
                        )
                        return
                    if done_b12 or done_scan or done_hw:
                        self._log(
                            f"Retomando: {len(done_b12)} B12, {len(done_scan)} Scan Loja, "
                            f"{len(done_hw)} Hardware ja concluidos serao pulados.",
                            "INFO",
                        )

            def keep_item(key, done_set, retry_set):
                if mode == "retry_failed":
                    return key in retry_set
                if mode == "resume":
                    return key not in done_set
                return True  # fresh

            for s in stores:
                self.after(0, self._init_store_row, s['filial'])

            scan_core.ensure_hw_columns(self.config_mgr)

            b12_user, b12_pass, b12_port = self._get_linux_credentials()
            b12_timeout = int(self.spin_b12_timeout.get())
            collect_detail = self.opt_b12_detail.get()

            scan_timeout = int(self.spin_scan_timeout.get())
            ssh_timeout = max(scan_timeout, 5)
            auth_context = {
                "user_linux": b12_user, "pass_linux": b12_pass,
                "user_win_drog": self.config_mgr.get("CREDENTIALS_TERMINAL_WINDOWS_DROGASIL", "user", "drogasil"),
                "pass_win_drog": self.config_mgr.get_secret("CREDENTIALS_TERMINAL_WINDOWS_DROGASIL", "password", ""),
                "user_win_raia": self.config_mgr.get("CREDENTIALS_TERMINAL_WINDOWS_RAIA", "user", "drogaraia"),
                "pass_win_raia": self.config_mgr.get_secret("CREDENTIALS_TERMINAL_WINDOWS_RAIA", "password", ""),
                "timeout": scan_timeout, "ssh_timeout": ssh_timeout,
                "scan_ssh": self.opt_ssh.get(), "scan_radmin": self.opt_radmin.get(),
                "scan_printer": self.opt_printer.get(),
            }
            hw_creds = self._build_hw_creds()

            workers_b12 = max(1, int(self.spin_workers_b12.get()))
            workers_scan = max(1, int(self.spin_workers_scan.get()))
            workers_hw = max(1, int(self.spin_workers_hw.get()))

            store_targets = {}
            total_scan_targets = 0
            for s in stores:
                targets = [
                    (s['filial'], s['nome'], t['ip'], t['expected_type'], s['logo'])
                    for t in get_store_scan_targets(s['ip'], s['cidr'] or None)
                    if t['expected_type'] != 'B12'
                ]
                store_targets[s['filial']] = targets
                total_scan_targets += len(targets)

            run_ids.update({
                "B12": start_scan_run(self.config_mgr, "B12", "autopilot", total_items=len(stores), selected_count=len(stores)),
                "SCAN_LOJA": start_scan_run(self.config_mgr, "SCAN_LOJA", "autopilot", total_items=total_scan_targets, selected_count=total_scan_targets),
                "HARDWARE": start_scan_run(self.config_mgr, "HARDWARE", "autopilot", total_items=0, selected_count=0),
            })

            b12_pool = ThreadPoolExecutor(max_workers=workers_b12)
            scan_pool = ThreadPoolExecutor(max_workers=workers_scan)
            hw_pool = ThreadPoolExecutor(max_workers=workers_hw)

            pending = {}
            scan_remaining = {}
            scan_results = {}
            held_scan = []
            held_hw = []
            # hw_total = total REAL de alvos de hardware — soma dos dispositivos
            # elegiveis das lojas cujo Scan Loja ja terminou (cresce enquanto o
            # Scan roda; vira o total definitivo quando o Scan chega a 100%).
            # hw_submitted = os que foram de fato enfileirados (exclui os pulados
            # nos modos "completar"/"reescanear").
            counts = {"b12_done": 0, "scan_done": 0, "hw_done": 0,
                      "hw_submitted": 0, "hw_total": 0}
            prog = {"last": 0, "b12_ok": False, "scan_ok": False}

            def _scan_finished():
                return bool(prog["scan_ok"]
                            or (total_scan_targets and counts["scan_done"] >= total_scan_targets))

            def _push_bars():
                self.after(
                    0, self._refresh_stage_bars,
                    counts["b12_done"], len(stores),
                    counts["scan_done"], total_scan_targets,
                    counts["hw_done"], counts["hw_total"], _scan_finished(),
                )

            # Estado lido pelo ticker de 1 s (dicts mutados pelo worker; leitura
            # de inteiros entre threads e segura para exibicao).
            self._live_bar_state = {
                "counts": counts, "prog": prog,
                "nstores": len(stores), "total_scan": total_scan_targets,
            }
            self.after(0, self._start_bar_ticker)

            def _log_progress(force=False):
                total = counts["b12_done"] + counts["scan_done"] + counts["hw_done"]
                _push_bars()
                if force or total - prog["last"] >= 20:
                    prog["last"] = total
                    self._log(
                        f"Progresso — B12 {counts['b12_done']}/{len(stores)} | "
                        f"Scan {counts['scan_done']}/{total_scan_targets} | "
                        f"Hardware {counts['hw_done']}/{counts['hw_submitted']}",
                        "INFO",
                    )
                if not prog["b12_ok"] and counts["b12_done"] >= len(stores):
                    prog["b12_ok"] = True
                    self._log(f"Etapa B12 concluida ({len(stores)} loja(s)).", "SUCCESS")
                if (not prog["scan_ok"] and total_scan_targets
                        and counts["scan_done"] >= total_scan_targets):
                    prog["scan_ok"] = True
                    self._log(f"Etapa Scan Loja concluida ({total_scan_targets} alvo(s)).", "SUCCESS")

            def advance_to_scan(s):
                if self.stop_event.is_set():
                    self.after(0, self._update_store_row, s['filial'], 'scan', 'cancelado')
                elif self.pause_event.is_set():
                    held_scan.append(s)
                else:
                    submit_scan_for_store(s)

            def advance_to_hw(s):
                if self.stop_event.is_set():
                    self.after(0, self._update_store_row, s['filial'], 'hw', 'cancelado')
                elif self.pause_event.is_set():
                    held_hw.append(s)
                else:
                    submit_hw_for_store(s)

            def submit_b12():
                for s in stores:
                    if self.stop_event.is_set():
                        return
                    key = f"{s['filial']}|{s['ip']}"
                    if not keep_item(key, done_b12, retry_b12):
                        counts["b12_done"] += 1
                        self.after(0, self._update_store_row, s['filial'], 'b12', 'ja concluido')
                        advance_to_scan(s)
                        continue
                    target = {"filial": s['filial'], "java": s['filial'], "historico": s.get('historico', ''), "nome": s['nome'], "ip": s['ip']}
                    f = b12_pool.submit(scan_core.run_b12_check, target, b12_timeout, b12_user, b12_pass, b12_port, collect_detail, self._log)
                    pending[f] = ("B12", s)

            def submit_scan_for_store(s):
                targets = store_targets.get(s['filial'], [])
                if not targets:
                    self.after(0, self._update_store_row, s['filial'], 'scan', 'sem alvos')
                    advance_to_hw(s)
                    return
                to_submit = [t for t in targets if keep_item(f"{t[0]}|{t[2]}", done_scan, retry_scan)]
                skipped = len(targets) - len(to_submit)
                if skipped:
                    counts["scan_done"] += skipped   # alvos ja verificados contam no total
                if not to_submit:
                    self.after(0, self._update_store_row, s['filial'], 'scan', f'ja concluido ({skipped})')
                    advance_to_hw(s)
                    return
                scan_remaining[s['filial']] = len(to_submit)
                scan_results[s['filial']] = []
                for t in to_submit:
                    f = scan_pool.submit(scan_core.run_store_scan_target, t, auth_context, self._log)
                    pending[f] = ("SCAN", s)

            def submit_hw_for_store(s):
                conn = self.config_mgr.get_sqlite_connection()
                try:
                    rows = conn.execute(
                        "SELECT filial, ip, device_type, logo FROM tb_detected_devices"
                        " WHERE filial=? AND device_type IN ('PDV Linux','TC Linux','TC Win','IMPRESSORA')",
                        (s['filial'],),
                    ).fetchall()
                finally:
                    conn.close()
                devices = [
                    {"filial": str(r[0]), "ip": str(r[1]), "device_type": str(r[2] or ''), "bandeira": str(r[3] or '')}
                    for r in rows
                ]
                counts["hw_total"] += len(devices)   # total REAL de alvos de hardware
                to_submit = [d for d in devices if keep_item(f"{d['filial']}|{d['ip']}", done_hw, retry_hw)]
                skipped = len(devices) - len(to_submit)
                if skipped:
                    counts["hw_done"] += skipped      # dispositivos ja concluidos contam no total
                if not devices:
                    self.after(0, self._update_store_row, s['filial'], 'hw', 'sem dispositivos')
                    return
                if not to_submit:
                    self.after(0, self._update_store_row, s['filial'], 'hw', f'ja concluido ({skipped})')
                    return
                counts["hw_submitted"] += len(to_submit)
                for dev in to_submit:
                    f = hw_pool.submit(scan_core.run_hardware_scan, dev, hw_creds, self._log)
                    pending[f] = ("HW", s)

            self._log(
                f"Etapa B12: iniciando {len(stores)} loja(s) — {workers_b12} workers, "
                f"timeout {b12_timeout}s. (Scan Loja e Hardware avancam por loja em seguida.)",
                "INFO",
            )
            submit_b12()
            self.after(0, self._update_status_label,
                       f"B12: {counts['b12_done']}/{len(stores)} | Scan: 0/{total_scan_targets} | Hardware: 0")
            _push_bars()

            while pending and not self.stop_event.is_set():
                if not self.pause_event.is_set():
                    if held_scan:
                        for s in held_scan:
                            submit_scan_for_store(s)
                        held_scan.clear()
                    if held_hw:
                        for s in held_hw:
                            submit_hw_for_store(s)
                        held_hw.clear()

                done, _ = wait(list(pending.keys()), timeout=1, return_when=FIRST_COMPLETED)
                if not done:
                    continue

                for f in done:
                    stage, s = pending.pop(f)
                    try:
                        result = f.result()
                    except Exception as e:
                        result = None
                        self._log(f"Erro inesperado ({stage}) loja {s['filial']}: {e}", "ERROR")

                    if stage == "B12":
                        counts["b12_done"] += 1
                        if result:
                            res, status_text, _level = result
                            scan_core.save_b12_result(self.config_mgr, res, run_ids["B12"])
                            b12_data = res.get('b12_data') or {}
                            record_scan_item(
                                self.config_mgr, run_ids["B12"], f"{s['filial']}|{s['ip']}",
                                filial=s['filial'], ip=s['ip'], device_type="B12",
                                status=b12_data.get('collection_status') or ('SUCCESS' if res.get('ssh') else 'OFFLINE'),
                                action="saved" if b12_data else "processed",
                                result_ref="tb_devices_detail" if b12_data else "",
                                error_message=b12_data.get('ssh_error') or "",
                            )
                            self.after(0, self._update_store_row, s['filial'], 'b12', status_text)
                        advance_to_scan(s)

                    elif stage == "SCAN":
                        counts["scan_done"] += 1
                        filial = s['filial']
                        if result:
                            scan_results.setdefault(filial, []).append(result)
                            record_scan_item(
                                self.config_mgr, run_ids["SCAN_LOJA"], f"{filial}|{result['ip']}",
                                filial=filial, ip=result['ip'], device_type=result['tipo'],
                                status=result['tipo'],
                                action="saved" if result['tipo'] != "Offline" else "ignored",
                                result_ref="tb_detected_devices" if result['tipo'] != "Offline" else "",
                            )
                        scan_remaining[filial] = scan_remaining.get(filial, 1) - 1
                        if scan_remaining.get(filial, 0) <= 0:
                            saved = scan_core.save_store_scan_results(self.config_mgr, scan_results.get(filial, []), run_ids["SCAN_LOJA"])
                            self.after(0, self._update_store_row, filial, 'scan', f"{saved} dispositivo(s)")
                            self._log(f"[JAVA {filial}] Scan Loja concluido: {saved} dispositivo(s).", "INFO")
                            advance_to_hw(s)

                    elif stage == "HW":
                        counts["hw_done"] += 1
                        if result:
                            scan_core.save_hardware_result(self.config_mgr, result, run_ids["HARDWARE"])
                            ok = scan_core.is_hw_success(result)
                            record_scan_item(
                                self.config_mgr, run_ids["HARDWARE"], f"{s['filial']}|{result['ip']}",
                                filial=s['filial'], ip=result['ip'], device_type=result.get('device_type', ''),
                                status="SUCCESS" if ok else (result.get('os') or 'FAILED'),
                                action="saved" if ok else "ignored",
                                result_ref="tb_detected_devices.hw_*" if ok else "",
                            )
                            self.after(0, self._update_store_row, s['filial'], 'hw', 'ok' if ok else (result.get('os') or 'falhou'))

                self.after(
                    0, self._update_status_label,
                    f"B12: {counts['b12_done']}/{len(stores)} | "
                    f"Scan: {counts['scan_done']}/{total_scan_targets} | Hardware: {counts['hw_done']}",
                )
                _log_progress()

            cancelled = self.stop_event.is_set()
            if cancelled:
                # Nao espera as tarefas em voo: derruba o que esta na fila e
                # deixa as que ja estao em rede morrerem sozinhas (daemon).
                for pool in (b12_pool, scan_pool, hw_pool):
                    try:
                        pool.shutdown(wait=False, cancel_futures=True)
                    except TypeError:  # Python < 3.9
                        pool.shutdown(wait=False)
            else:
                b12_pool.shutdown(wait=True)
                scan_pool.shutdown(wait=True)
                hw_pool.shutdown(wait=True)

            final_status = "CANCELLED" if cancelled else "SUCCESS"
            for stage in ("B12", "SCAN_LOJA", "HARDWARE"):
                finish_scan_run(self.config_mgr, run_ids.get(stage), final_status)
            pipeline_finalized = True
            _push_bars()

            if not cancelled:
                self._log(
                    f"Resumo — B12 {counts['b12_done']}/{len(stores)} | "
                    f"Scan {counts['scan_done']}/{total_scan_targets} | "
                    f"Hardware {counts['hw_done']}/{counts['hw_submitted']}.",
                    "INFO",
                )
                self._log("Pipeline concluido.", "SUCCESS")

        except Exception as e:
            self._log(f"Erro no pipeline: {e}", "ERROR")
        finally:
            # Nao deixar runs abertas (RUNNING) se o worker morreu no meio.
            if not pipeline_finalized:
                for stage in ("B12", "SCAN_LOJA", "HARDWARE"):
                    try:
                        finish_scan_run(self.config_mgr, run_ids.get(stage), "FAILED",
                                        "pipeline interrompido por erro")
                    except Exception:
                        pass
            self._worker_running = False
            self.after(0, self._pipeline_done)
