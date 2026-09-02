#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Armazenamento local de segredos para o importador MariaDB.

Usa Fernet com chave local criada ao lado do config.ini. Se cryptography não
estiver disponível, usa b64 apenas como fallback de ofuscação.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path


class SecretStore:
    PREFIX_LEGACY = "dpapi:"
    PREFIX_FERNET = "fernet:"
    PREFIX_B64 = "b64:"

    def __init__(self, key_file: Path):
        self.key_file = Path(key_file)

    def provider(self) -> str:
        try:
            self._fernet()
            return "Fernet local key"
        except RuntimeError:
            return "b64 fallback (ofuscação)"

    def encrypt(self, value: str) -> str:
        if value == "":
            return ""
        try:
            return self.PREFIX_FERNET + self._fernet().encrypt(value.encode("utf-8")).decode("ascii")
        except RuntimeError:
            token = base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii")
            return self.PREFIX_B64 + token

    def decrypt(self, value: str) -> str:
        if not value:
            return ""
        if value.startswith(self.PREFIX_LEGACY):
            raise RuntimeError("Formato legado de senha não suportado pela configuração portátil atual.")
        if value.startswith(self.PREFIX_FERNET):
            return self._fernet().decrypt(value[len(self.PREFIX_FERNET):].encode("ascii")).decode("utf-8")
        if value.startswith(self.PREFIX_B64):
            return base64.urlsafe_b64decode(value[len(self.PREFIX_B64):].encode("ascii")).decode("utf-8")
        return value

    def _fernet(self):
        try:
            from cryptography.fernet import Fernet
        except ImportError as exc:
            raise RuntimeError(
                "cryptography não instalado. Instale com: pip install -r requirements.txt"
            ) from exc

        if not self.key_file.exists():
            self.key_file.write_bytes(Fernet.generate_key())
            try:
                os.chmod(self.key_file, 0o600)
            except OSError:
                pass
        return Fernet(self.key_file.read_bytes())
