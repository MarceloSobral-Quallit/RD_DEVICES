#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Checklist simples da estrutura atual do COLETOR.

Uso:
  python tools/check_project.py
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


REQUIRED_PATHS = [
    "main.py",
    "version.py",
    "requirements.txt",
    "config.ini.template",
    ".gitignore",
    "README.md",
    "docs/README.md",
    "docs/FLUXO_DADOS.md",
    "src/__init__.py",
    "src/main_window.py",
    "src/common/__init__.py",
    "src/common/config.py",
    "src/common/console_logger.py",
    "src/common/db_sync.py",
    "src/common/secure_store.py",
    "src/common/utils.py",
    "src/tabs/__init__.py",
    "src/tabs/tab_0_database.py",
    "src/tabs/tab_1_import_xls.py",
    "src/tabs/tab_2_ssh.py",
    "src/tabs/tab_3_devices.py",
    "src/tabs/tab_4_hardware.py",
    "src/tabs/tab_5_rescan.py",
    "src/tabs/tab_6_credentials.py",
]


FORBIDDEN_PATHS = [
    "_docs",
    "temp",
    "__pycache__",
    "src/__pycache__",
    "src/common/__pycache__",
    "src/tabs/__pycache__",
    "COLETOR.spec",
    "tools/build_release.py",
]


def check_required():
    ok = True
    print("COLETOR - arquivos esperados")
    print("=" * 72)
    for item in REQUIRED_PATHS:
        exists = (ROOT / item).exists()
        print(f"{'OK  ' if exists else 'MISS'} {item}")
        ok = ok and exists
    return ok


def check_forbidden():
    ok = True
    print()
    print("COLETOR - sobras que nao deveriam estar versionadas")
    print("=" * 72)
    for item in FORBIDDEN_PATHS:
        exists = (ROOT / item).exists()
        print(f"{'WARN' if exists else 'OK  '} {item}")
        ok = ok and not exists
    return ok


def main():
    required_ok = check_required()
    forbidden_ok = check_forbidden()
    print()
    if required_ok and forbidden_ok:
        print("OK: estrutura do COLETOR limpa.")
        return 0
    print("WARN: revisar itens marcados acima.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
