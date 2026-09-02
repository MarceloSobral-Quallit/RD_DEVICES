#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COLETOR - RD Devices Collector GUI
Data: 08/06/2026
Versão: 1.0 (MVP)

Ponto de entrada principal da aplicação.
"""

import sys
import tkinter as tk
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Resolver o diretório base corretamente dentro e fora do PyInstaller
if getattr(sys, 'frozen', False):
    # Executando como .exe (PyInstaller)
    BASE_DIR = Path(sys.executable).parent
    # No onedir, os módulos ficam na pasta _internal ou na raiz do bundle
    _internal = BASE_DIR / '_internal'
    if (_internal / 'src').exists():
        sys.path.insert(0, str(_internal / 'src'))
    elif (BASE_DIR / 'src').exists():
        sys.path.insert(0, str(BASE_DIR / 'src'))
    else:
        # fallback: adicionar o próprio _internal ao path
        sys.path.insert(0, str(_internal))
else:
    # Executando como script Python normal
    BASE_DIR = Path(__file__).parent
    sys.path.insert(0, str(BASE_DIR / 'src'))


def app_identity():
    """Retorna identificacao curta para cabecalho dos logs."""
    try:
        from version import VERSION, BUILD_DATE
    except Exception:
        VERSION = "desconhecida"
        BUILD_DATE = "desconhecida"
    mode = "exe" if getattr(sys, "frozen", False) else "script"
    return {
        "component": "COLETOR",
        "version": VERSION,
        "build_date": BUILD_DATE,
        "mode": mode,
        "base_dir": str(BASE_DIR),
    }


def setup_logging():
    """Configura log persistente ao lado do executavel."""
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "coletor.log"
    fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    root_logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    root_logger.addHandler(stream_handler)

    # paramiko emite um INFO por conexao ("Connected (version 2.0...)",
    # "Authentication (password) successful!"). Num scan de milhares de hosts
    # isso domina o coletor.log e esconde os erros reais.
    for noisy in ("paramiko", "paramiko.transport", "paramiko.transport.sftp"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

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

def main():
    """Função principal - inicia a aplicação."""
    try:
        # Importar após adicionar ao path
        from main_window import MainWindow
        
        # Criar janela principal
        root = tk.Tk()
        root.title("RD Devices - COLETOR")
        root.geometry("1010x610")
        root.minsize(1010, 610)
        
        # Inicializar aplicação
        app = MainWindow(root)
        
        # Iniciar loop
        root.mainloop()
        
    except Exception as e:
        logging.error(f"Erro ao iniciar aplicação: {e}", exc_info=True)
        
        # Mostrar erro visível mesmo sem console (útil no .exe)
        msg = (
            f"Erro ao iniciar aplicação:\n\n{e}\n\n"
            f"sys.path:\n" + "\n".join(sys.path[:5]) +
            f"\n\nfrozen={getattr(sys, 'frozen', False)}\n"
            f"BASE_DIR={BASE_DIR}"
        )
        try:
            import tkinter.messagebox as mb
            _r = tk.Tk(); _r.withdraw()
            mb.showerror("Erro de Inicialização", msg)
            _r.destroy()
        except Exception:
            pass
        
        sys.exit(1)

if __name__ == '__main__':
    main()
