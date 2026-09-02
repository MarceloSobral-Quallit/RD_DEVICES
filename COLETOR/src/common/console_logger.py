"""
console_logger.py - Widget de console com logging colorido
FASE 1 do Roadmap - Componentes Comuns
"""

import tkinter as tk
from tkinter import scrolledtext
import logging
import threading
from datetime import datetime
from pathlib import Path
import re

from .runtime_paths import app_dir


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


class ConsoleLogger(tk.Frame):
    """Widget de console para logging colorido."""

    def __init__(self, parent, height=12, log_name=None, max_lines=4000):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.height = height
        self.max_lines = max_lines  # limite do widget; o arquivo .log guarda tudo
        self.log_name = log_name or "console"
        self.log_path = self._create_log_path(self.log_name)
        self.create_widgets()
        self.setup_colors()
        self._write_file(_app_identity_header(self.log_name))

    def _create_log_path(self, log_name):
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", log_name).strip("_").lower() or "console"
        logs_dir = app_dir() / "logs" / "console"
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir / f"{datetime.now():%Y%m%d_%H%M%S}_{safe_name}.log"
    
    def create_widgets(self):
        """Criar widget ScrolledText."""
        self.text = scrolledtext.ScrolledText(
            self,
            height=self.height,
            width=1,
            font=("Courier", 10),
            bg="black",
            fg="white",
            state=tk.DISABLED
        )
        self.text.pack(fill=tk.BOTH, expand=True)
    
    def setup_colors(self):
        """Configurar tags de cores."""
        self.text.tag_config("INFO", foreground="white")
        self.text.tag_config("SUCCESS", foreground="green")
        self.text.tag_config("WARNING", foreground="yellow")
        self.text.tag_config("ERROR", foreground="red")
    
    def log(self, message, level="INFO"):
        """Adicionar linha ao console."""
        if threading.current_thread() is not threading.main_thread():
            try:
                self.after(0, self.log, message, level)
            except tk.TclError:
                pass
            return
        self._append(message, level)

    def _append(self, message, level="INFO"):
        """Adicionar linha ao widget já na thread principal."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._write_file(f"[{ts}] [{level}] {message}\n")
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, message + "\n", level)
        if self.max_lines:
            # int(index) = numero de linhas; corta o excesso pelo topo
            excess = int(self.text.index("end-1c").split(".")[0]) - self.max_lines
            if excess > 0:
                self.text.delete("1.0", f"{excess + 1}.0")
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def _write_file(self, line):
        try:
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(line)
        except OSError:
            logging.getLogger(__name__).exception("Falha ao gravar log do console")

    def log_info(self, message):
        """Compatibilidade com chamadas legadas de INFO."""
        self.log(message, "INFO")

    def log_ok(self, message):
        """Compatibilidade com chamadas legadas de sucesso."""
        self.log(message, "SUCCESS")

    def log_warning(self, message):
        """Compatibilidade com chamadas legadas de aviso."""
        self.log(message, "WARNING")

    def log_error(self, message):
        """Compatibilidade com chamadas legadas de erro."""
        self.log(message, "ERROR")

    def clear(self):
        """Limpar todo o conteúdo do console."""
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.config(state=tk.DISABLED)
