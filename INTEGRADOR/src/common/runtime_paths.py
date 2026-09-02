#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""runtime_paths.py - Caminhos persistentes do INTEGRADOR."""

from pathlib import Path
import sys


def app_dir() -> Path:
    """Diretório persistente do app: pasta do exe ou raiz do INTEGRADOR."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # INTEGRADOR/src/common/runtime_paths.py → parents[2] = INTEGRADOR/
    return Path(__file__).resolve().parents[2]


def bundle_dir() -> Path:
    """Diretório de recursos empacotados pelo PyInstaller."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return app_dir()


def default_config_path() -> Path:
    return app_dir() / "config.ini"


def key_path() -> Path:
    return app_dir() / ".integrador_secret.key"


def logs_dir() -> Path:
    return app_dir() / "logs"
