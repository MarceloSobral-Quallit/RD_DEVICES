#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db_sync.py - Utilitários locais de SQLite para o COLETOR.

Este módulo não acessa MariaDB. A sincronização/importação para MariaDB fica
fora do COLETOR, na pasta INTEGRADOR, para manter o coletor
compatível com ambientes restritos.
"""

import logging
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class SQLiteBackup:
    """Gerencia backups e verificações do banco SQLite local."""

    def __init__(self, sqlite_path: str, backup_dir: str):
        self.sqlite_path = Path(sqlite_path)
        self.backup_dir = Path(backup_dir) if backup_dir else Path(".")

    def ensure_backup_dir(self):
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create(self, progress_cb: Optional[Callable] = None) -> Path:
        """
        Cria um backup usando sqlite3 online backup API.
        É seguro mesmo quando o banco está aberto pela aplicação.
        """
        if not self.sqlite_path.exists():
            raise FileNotFoundError(f"Banco SQLite não encontrado: {self.sqlite_path}")

        self.ensure_backup_dir()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{ts}.db"

        def _progress(_status, remaining, total):
            if progress_cb and total > 0:
                pct = int((1 - remaining / total) * 100)
                progress_cb(pct, f"Backup: {total - remaining}/{total} páginas")

        src_conn = sqlite3.connect(str(self.sqlite_path))
        dst_conn = sqlite3.connect(str(backup_path))
        try:
            src_conn.backup(dst_conn, progress=_progress)
        finally:
            src_conn.close()
            dst_conn.close()

        logger.info("Backup criado: %s", backup_path)
        return backup_path

    def list_backups(self) -> list:
        if not self.backup_dir.exists():
            return []
        files = sorted(self.backup_dir.glob("backup_*.db"), reverse=True)
        return [
            {
                "path": file,
                "size_mb": file.stat().st_size / 1048576,
                "ts": file.stem.replace("backup_", ""),
            }
            for file in files
        ]

    def verify(self) -> tuple:
        if not self.sqlite_path.exists():
            return False, f"Arquivo não encontrado: {self.sqlite_path}"
        try:
            conn = sqlite3.connect(str(self.sqlite_path))
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check")
            result = cur.fetchone()
            conn.close()
            if result and result[0] == "ok":
                return True, "Integridade OK"
            return False, f"Integridade falhou: {result}"
        except Exception as e:
            return False, f"Erro: {e}"

    def get_stats(self) -> dict:
        if not self.sqlite_path.exists():
            return {}
        try:
            conn = sqlite3.connect(str(self.sqlite_path))
            cur = conn.cursor()
            stats = {
                "path": str(self.sqlite_path),
                "size_mb": self.sqlite_path.stat().st_size / 1048576,
                "tables": {},
            }
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cur.fetchall()]
            for table in tables:
                try:
                    cur.execute(f'SELECT COUNT(*) FROM "{table}"')
                    stats["tables"][table] = cur.fetchone()[0]
                except Exception:
                    stats["tables"][table] = -1
            conn.close()
            return stats
        except Exception as e:
            logger.error("Erro ao obter stats: %s", e)
            return {}

