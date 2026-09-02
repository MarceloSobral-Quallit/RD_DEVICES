#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Armazenamento local de segredos para o coletor."""

import base64
import os
from pathlib import Path


class SecretStore:
    """Criptografa segredos para gravação no config.ini.

    Preferência:
      1. Fernet com chave local ao lado do config.ini.
      2. b64 como fallback de ofuscação quando cryptography não existe.
    """

    def __init__(self, config_path):
        self.config_path = Path(config_path)

    def protect(self, value):
        if not value:
            return ""
        encrypted = self._protect_fernet(value)
        if encrypted:
            return encrypted
        return self._protect_b64(value)

    def unprotect(self, value):
        if not value:
            return ""
        if value.startswith("dpapi:"):
            raise RuntimeError("Formato legado de senha não suportado pela configuração portátil atual.")
        if value.startswith("fernet:"):
            return self._unprotect_fernet(value)
        if value.startswith("b64:"):
            return self._unprotect_b64(value)
        return value

    def provider_name(self):
        if self._fernet_available():
            return "Fernet com chave local"
        return "b64 fallback (ofuscação)"

    def _fernet_available(self):
        try:
            from cryptography.fernet import Fernet  # noqa: F401
            return True
        except Exception:
            return False

    def _key_path(self):
        base = self.config_path.parent if self.config_path.parent else Path(".")
        return base / ".coletor_secret.key"

    def _load_or_create_fernet_key(self):
        from cryptography.fernet import Fernet

        key_path = self._key_path()
        if key_path.exists():
            return key_path.read_bytes()
        key = Fernet.generate_key()
        key_path.write_bytes(key)
        try:
            os.chmod(key_path, 0o600)
        except Exception:
            pass
        return key

    def _protect_fernet(self, value):
        if not self._fernet_available():
            return None
        from cryptography.fernet import Fernet

        key = self._load_or_create_fernet_key()
        return "fernet:" + Fernet(key).encrypt(value.encode("utf-8")).decode("ascii")

    def _unprotect_fernet(self, value):
        if not self._fernet_available():
            raise RuntimeError("Senha protegida por Fernet não pode ser lida neste ambiente.")
        from cryptography.fernet import Fernet

        key = self._load_or_create_fernet_key()
        token = value.split(":", 1)[1].encode("ascii")
        return Fernet(key).decrypt(token).decode("utf-8")

    def _protect_b64(self, value):
        token = base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii")
        return "b64:" + token

    def _unprotect_b64(self, value):
        token = value.split(":", 1)[1].encode("ascii")
        return base64.urlsafe_b64decode(token).decode("utf-8")
