#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INTEGRADOR GUI - RD Devices Importador SQLite → MariaDB
Ponto de entrada da interface gráfica.
"""

import logging
import sys
import tkinter as tk
from logging.handlers import RotatingFileHandler
from pathlib import Path

# --- Resolver diretório base ------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
    _internal = BASE_DIR / "_internal"
    if (_internal / "src").exists():
        sys.path.insert(0, str(_internal / "src"))
    elif (BASE_DIR / "src").exists():
        sys.path.insert(0, str(BASE_DIR / "src"))
    else:
        sys.path.insert(0, str(_internal))
    # Raiz do bundle (para secure_store, version, etc.)
    sys.path.insert(0, str(_internal) if _internal.exists() else str(BASE_DIR))
else:
    BASE_DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(BASE_DIR / "src"))
    # Raiz do INTEGRADOR (para secure_store.py, version.py)
    sys.path.insert(0, str(BASE_DIR))


# --- Logging ----------------------------------------------------------------
def app_identity():
    try:
        from version import VERSION, BUILD_DATE
    except Exception:
        VERSION = "desconhecida"
        BUILD_DATE = "desconhecida"
    mode = "exe" if getattr(sys, "frozen", False) else "script"
    return {
        "component": "INTEGRADOR",
        "version": VERSION,
        "build_date": BUILD_DATE,
        "mode": mode,
        "base_dir": str(BASE_DIR),
    }


def setup_logging():
    log_dir  = BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "integrador_gui.log"
    fmt      = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    fh = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    root_logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root_logger.addHandler(sh)

    identity = app_identity()
    root_logger.info("=" * 72)
    root_logger.info(
        "Aplicativo: %s | Versao: %s | Build: %s | Modo: %s",
        identity["component"],
        identity["version"],
        identity["build_date"],
        identity["mode"],
    )
    root_logger.info("Base dir: %s", identity["base_dir"])
    root_logger.info("=" * 72)


setup_logging()


# --- Entrada principal -------------------------------------------------------
def main():
    try:
        from main_window import MainWindow

        root = tk.Tk()
        root.title("RD Devices - INTEGRADOR")
        root.geometry("1100x700")
        root.minsize(900, 580)

        MainWindow(root)
        root.mainloop()

    except Exception as exc:
        logging.getLogger(__name__).exception("Falha ao iniciar INTEGRADOR GUI")
        try:
            from tkinter import messagebox
            messagebox.showerror("Erro fatal", str(exc))
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
