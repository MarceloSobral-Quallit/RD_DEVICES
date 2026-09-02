#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compilacao total do RD Devices.

Pipeline fixo, sem opcoes para desligar etapas: SEMPRE faz tudo.

  1. limpa __pycache__/bytecode do repo (inicio)
  2. incrementa a versao em version_info.txt (--bump build) e sincroniza os version.py
  3. PyInstaller onefile de COLETOR e INTEGRADOR
  4. assinatura Authenticode (PFX Quallit)
  5. pacotes RD_DEVICES_RELEASE-*.zip e RD_DEVICES_BACKUP-*.zip em release/ e release/backup/
  6. publica RD-COLETOR.zip (COLETOR.exe + config.ini) no download server de config/config.ini
  7. limpa __pycache__/bytecode do repo (fim)

Uso:
  python tools/build_all.py
  python tools/build_all.py --release-dir D:\\out --backup-dir D:\\out\\bkp   (so redireciona os ZIPs)

Para builds parciais (sem bump, sem assinatura, sem publicacao, so um componente, etc.)
use diretamente tools/build_release.py com as flags correspondentes.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RELEASE_DIR = ROOT / "release"
DEFAULT_BACKUP_DIR = ROOT / "release" / "backup"

# Pipeline completo e imutavel: bump + build dos dois componentes + assinatura.
# ZIPs RELEASE/BACKUP e publicacao no download server acontecem no build_release.
FIXED_ARGV = ["--component", "all", "--build-type", "onefile", "--bump", "build", "--sign"]


def main(cli=None):
    parser = argparse.ArgumentParser(
        prog="build_all.py",
        description="Compilacao total do RD Devices: sempre bump + build + assinatura + ZIPs + publicacao.",
    )
    parser.add_argument("--release-dir", default=str(DEFAULT_RELEASE_DIR),
                        help="Destino dos ZIPs RELEASE (padrao: <repo>/release).")
    parser.add_argument("--backup-dir", default=str(DEFAULT_BACKUP_DIR),
                        help="Destino dos ZIPs BACKUP (padrao: <repo>/release/backup).")
    args = parser.parse_args(cli if cli is not None else sys.argv[1:])

    release_dir = Path(args.release_dir).resolve()
    backup_dir = Path(args.backup_dir).resolve()
    release_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    # build_release.py le PROJECT_RELEASE / PROJECT_BACKUP no momento do import,
    # entao o ambiente precisa estar definido ANTES de importa-lo.
    os.environ["PROJECT_RELEASE"] = str(release_dir)
    os.environ["PROJECT_BACKUP"] = str(backup_dir)
    sys.path.insert(0, str(ROOT / "tools"))
    import build_release  # noqa: E402

    bar = "=" * 72
    print(bar)
    print("  RD DEVICES - COMPILACAO TOTAL (bump + build + assinatura + ZIPs + publicacao)")
    print(f"  RELEASE -> {release_dir}")
    print(f"  BACKUP  -> {backup_dir}")
    print(f"  cmd     -> python tools/build_release.py {' '.join(FIXED_ARGV)}")
    print(bar)

    rc = build_release.main(list(FIXED_ARGV))

    print(bar)
    if rc == 0:
        print("  RESULTADO: OK")
        artefatos = sorted(
            [p for p in release_dir.glob("*") if p.is_file()]
            + [p for p in backup_dir.glob("*") if p.is_file()]
        )
        for p in artefatos:
            size_mb = p.stat().st_size / (1024 * 1024)
            try:
                shown = p.relative_to(ROOT)
            except ValueError:
                shown = p
            print(f"    {shown}  ({size_mb:.1f} MB)")
    else:
        print(f"  RESULTADO: FALHOU (rc={rc})")
    print(bar)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
