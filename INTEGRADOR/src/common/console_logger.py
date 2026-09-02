#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""console_logger.py - Widget de console com logging colorido."""

import tkinter as tk
from tkinter import scrolledtext
import threading
from datetime import datetime
import re
import logging

from common.runtime_paths import logs_dir


def _app_identity_header(log_name):
    try:
        from version import VERSION, BUILD_DATE
    except Exception:
        VERSION = "desconhecida"
        BUILD_DATE = "desconhecida"
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"# Console {log_name} iniciado em {started_at}\n"
        f"# Aplicativo: INTEGRADOR\n"
        f"# Versao: {VERSION}\n"
        f"# Build: {BUILD_DATE}\n"
    )


class ConsoleLogger(tk.Frame):
    """Widget de console para logging colorido."""

    def __init__(self, parent, height=12, log_name=None):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.height = height
        self.log_name = log_name or "console"
        self.log_path = self._create_log_path(self.log_name)
        self.create_widgets()
        self.setup_colors()
        self._write_file(_app_identity_header(self.log_name))

    def _create_log_path(self, log_name):
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", log_name).strip("_").lower() or "console"
        log_dir = logs_dir() / "console"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / f"{datetime.now():%Y%m%d_%H%M%S}_{safe_name}.log"

    def create_widgets(self):
        self.text = scrolledtext.ScrolledText(
            self,
            height=self.height,
            width=1,
            font=("Courier", 10),
            bg="black",
            fg="white",
            state=tk.DISABLED,
        )
        self.text.pack(fill=tk.BOTH, expand=True)

    def setup_colors(self):
        self.text.tag_config("INFO", foreground="white")
        self.text.tag_config("SUCCESS", foreground="green")
        self.text.tag_config("WARNING", foreground="yellow")
        self.text.tag_config("ERROR", foreground="red")

    def log(self, message, level="INFO"):
        if threading.current_thread() is not threading.main_thread():
            try:
                self.after(0, self.log, message, level)
            except tk.TclError:
                pass
            return
        self._append(message, level)

    def _append(self, message, level="INFO"):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._write_file(f"[{ts}] [{level}] {message}\n")
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, message + "\n", level)
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def _write_file(self, line):
        try:
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(line)
        except OSError:
            logging.getLogger(__name__).exception("Falha ao gravar log do console")

    def log_info(self, msg):    self.log(msg, "INFO")
    def log_ok(self, msg):      self.log(msg, "SUCCESS")
    def log_warning(self, msg): self.log(msg, "WARNING")
    def log_error(self, msg):   self.log(msg, "ERROR")

    def clear(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.config(state=tk.DISABLED)
