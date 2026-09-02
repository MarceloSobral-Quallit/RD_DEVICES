"""
config.py - Gerenciador de configurações (config.ini)
"""

import configparser
import sqlite3
from pathlib import Path
import logging
from .secure_store import SecretStore
from .runtime_paths import app_dir, ensure_default_config, resolve_runtime_path, resource_path

logger = logging.getLogger(__name__)


class ConfigManager:
    """Gerenciador de config.ini."""
    
    def __init__(self, config_path=None):
        if config_path is None:
            self.config_path = ensure_default_config()
        else:
            self.config_path = Path(config_path)
        self.config = configparser.ConfigParser()
        self.load()
    
    def load(self):
        """Carregar config.ini."""
        if self.config_path.exists():
            self.config.read(self.config_path)
            logger.info(f"Config loaded from {self.config_path}")
        else:
            logger.warning(f"Config file not found at {self.config_path}")
    
    def get(self, section, key, default=None):
        """Obter valor de configuração."""
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
    
    def set(self, section, key, value):
        """Definir valor de configuração."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
    
    def save(self):
        """Salvar config.ini."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            self.config.write(f)
        logger.info(f"Config saved to {self.config_path}")

    def get_path(self, section, key, default):
        """Obter caminho absoluto resolvendo relativos pela pasta do app."""
        value = self.get(section, key, default)
        return resolve_runtime_path(value, app_dir())

    def get_sqlite_connection(self):
        """Abrir conexão SQLite usando [DATABASE].path."""
        db_path = self.get_path("DATABASE", "path", "./database/devices.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        self._ensure_sqlite_schema(conn)
        return conn

    def _ensure_sqlite_schema(self, conn):
        schema_path = resource_path("config", "schema_sqlite_init.sql")
        if not schema_path.exists():
            logger.warning(f"SQLite schema not found at {schema_path}")
            return
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        conn.commit()

    def set_secret(self, section, key, value):
        """Criptografar e salvar segredo no config.ini."""
        store = SecretStore(self.config_path)
        self.set(section, key, store.protect(value))

    def get_secret(self, section, key, default=""):
        """Ler segredo criptografado; aceita valor legado em claro para migração."""
        raw = self.get(section, key, "")
        if not raw:
            return default
        return SecretStore(self.config_path).unprotect(raw)

    def secret_provider(self):
        return SecretStore(self.config_path).provider_name()
