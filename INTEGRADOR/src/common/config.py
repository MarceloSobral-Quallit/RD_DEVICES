#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""config.py - Gerenciador de configurações do INTEGRADOR GUI."""

import configparser
import logging
from pathlib import Path

from common.runtime_paths import default_config_path, key_path

logger = logging.getLogger(__name__)


class IntegradorConfig:
    """Lê/escreve config.ini e gerencia credenciais MariaDB."""

    def __init__(self, path: Path | None = None):
        self.config_path = Path(path) if path else default_config_path()
        self._parser = configparser.ConfigParser()
        self._load()

    def _load(self):
        if self.config_path.exists():
            self._parser.read(self.config_path, encoding="utf-8")
            logger.info("Config carregado: %s", self.config_path)

    def _secret_store(self):
        from secure_store import SecretStore
        return SecretStore(key_path())

    def get(self, section, key, default=None):
        try:
            return self._parser.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def getint(self, section, key, default=0):
        try:
            return self._parser.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default

    def set(self, section, key, value):
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        self._parser.set(section, key, str(value))

    def save(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as fh:
            self._parser.write(fh)
        logger.info("Config salvo: %s", self.config_path)

    # --- Accessors MariaDB --------------------------------------------------

    def mariadb_host(self):     return self.get("MARIADB", "host", "127.0.0.1")
    def mariadb_port(self):     return self.getint("MARIADB", "port", 3306)
    def mariadb_user(self):     return self.get("MARIADB", "user", "")
    def mariadb_database(self): return self.get("MARIADB", "database", "")
    def mariadb_charset(self):  return self.get("MARIADB", "charset", "utf8mb4")

    def mariadb_password(self) -> str:
        raw = self.get("MARIADB", "password", "")
        if not raw:
            return ""
        return self._secret_store().decrypt(raw)

    def secret_provider(self) -> str:
        return self._secret_store().provider()

    def save_mariadb_settings(self, host, port, user, database, charset, password=None):
        self.set("MARIADB", "host", host)
        self.set("MARIADB", "port", str(port))
        self.set("MARIADB", "user", user)
        self.set("MARIADB", "database", database)
        self.set("MARIADB", "charset", charset)
        if password:
            encrypted = self._secret_store().encrypt(password)
            self.set("MARIADB", "password", encrypted)
        self.save()

    def connect_mariadb(self, password: str | None = None):
        """Abre conexão com MariaDB. Lança RuntimeError se conector não instalado."""
        try:
            import mysql.connector
        except ImportError as exc:
            raise RuntimeError(
                "mysql-connector-python não instalado. "
                "Execute: pip install -r requirements.txt"
            ) from exc

        pwd = password if password is not None else self.mariadb_password()
        conn = mysql.connector.connect(
            host=self.mariadb_host(),
            port=self.mariadb_port(),
            user=self.mariadb_user(),
            password=pwd,
            database=self.mariadb_database(),
            charset=self.mariadb_charset(),
        )
        conn.autocommit = False
        return conn
