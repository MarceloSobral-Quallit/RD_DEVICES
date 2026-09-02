#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importador admin: SQLite coletado pelo COLETOR -> MariaDB.

Uso seguro por padrão:
  python import_sqlite_to_mariadb.py --sqlite devices.db

Sem --execute o script faz apenas validação/dry-run. O COLETOR não importa
este arquivo e não depende de MariaDB.
"""

import argparse
import configparser
import getpass
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from secure_store import SecretStore
from version import VERSION


DEFAULT_TABLES = [
    "tb_filial",
    "tb_devices_detail",
    "tb_b12_data_collection_status",
    "tb_detected_devices",
    "tb_scan_runs",
    "tb_scan_run_items",
    "tb_devices_detail_history",
    "tb_detected_devices_history",
]

# Tabelas de historico: append-only, nunca reescritas. A chave de deduplicacao
# e (ip, data_coleta)/(ip, snapshot_at), nao a PK autoincrement do MariaDB —
# reimportar o mesmo SQLite nao duplica linhas, mas o modo e forcado para
# "append" independente do --mode escolhido, para garantir imutabilidade.
APPEND_ONLY_TABLES = {
    "tb_devices_detail_history",
    "tb_detected_devices_history",
}

# Tabelas onde a coluna "id" existe tanto no SQLite (INTEGER PRIMARY KEY
# AUTOINCREMENT local) quanto no MariaDB (AUTO_INCREMENT proprio) sob o mesmo
# nome, mas os valores nao tem relacao entre si e nada depende do valor
# preservado (sem FK apontando para essa tabela) — importar "id" literalmente
# faz o upsert colidir com a PK de uma linha nao relacionada no MariaDB e, ao
# tentar atualiza-la, viola outras UNIQUE KEYs da tabela (ex: idx_ip_unique).
# Deixar o MariaDB atribuir seu proprio id nessas tabelas.
ID_EXCLUDED_TABLES = {
    "tb_detected_devices",
}


@dataclass
class ImportConfig:
    path: Path
    parser: configparser.ConfigParser
    secret_store: SecretStore


def load_config(path):
    config_path = Path(path)
    parser = configparser.ConfigParser()
    if config_path.exists():
        parser.read(config_path, encoding="utf-8")
    return ImportConfig(
        path=config_path,
        parser=parser,
        secret_store=SecretStore(config_path.with_name(".integrador_secret.key")),
    )


def cfg_get(config, section, key, default=None):
    if config.parser.has_option(section, key):
        return config.parser.get(section, key)
    return default


def cfg_getint(config, section, key, default):
    if config.parser.has_option(section, key):
        return config.parser.getint(section, key)
    return default


def resolve_settings(args, config):
    args.host = args.host or cfg_get(config, "MARIADB", "host", "127.0.0.1")
    args.port = args.port or cfg_getint(config, "MARIADB", "port", 3306)
    args.user = args.user or cfg_get(config, "MARIADB", "user")
    args.database = args.database or cfg_get(config, "MARIADB", "database")
    args.charset = args.charset or cfg_get(config, "MARIADB", "charset", "utf8mb4")
    args.mode = args.mode or cfg_get(config, "IMPORT", "mode", "upsert")
    args.batch_size = args.batch_size or cfg_getint(config, "IMPORT", "batch_size", 500)

    if not args.user:
        raise RuntimeError("Usuário MariaDB não informado. Use --user ou configure [MARIADB] user.")
    if not args.database:
        raise RuntimeError("Database MariaDB não informado. Use --database ou configure [MARIADB] database.")

    return args


def save_config(args, config, password):
    if not config.parser.has_section("MARIADB"):
        config.parser.add_section("MARIADB")
    if not config.parser.has_section("IMPORT"):
        config.parser.add_section("IMPORT")

    config.parser.set("MARIADB", "host", str(args.host))
    config.parser.set("MARIADB", "port", str(args.port))
    config.parser.set("MARIADB", "user", str(args.user))
    config.parser.set("MARIADB", "database", str(args.database))
    config.parser.set("MARIADB", "charset", str(args.charset))
    if password:
        config.parser.set("MARIADB", "password", config.secret_store.encrypt(password))
    config.parser.set("IMPORT", "mode", str(args.mode))
    config.parser.set("IMPORT", "batch_size", str(args.batch_size))

    with config.path.open("w", encoding="utf-8") as fh:
        config.parser.write(fh)


def quote_identifier(name):
    return "`" + name.replace("`", "``") + "`"


def open_sqlite(path):
    db_path = Path(path)
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite não encontrado: {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def verify_sqlite(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check")
    result = cur.fetchone()[0]
    if result != "ok":
        raise RuntimeError(f"Integridade SQLite falhou: {result}")


def sqlite_tables(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {row[0] for row in cur.fetchall()}


def get_columns(conn, table):
    cur = conn.cursor()
    cur.execute(f'PRAGMA table_info("{table}")')
    return [row["name"] for row in cur.fetchall()]


def resolve_password(args, config):
    if args.password is not None:
        return args.password

    stored = cfg_get(config, "MARIADB", "password", "")
    if stored:
        return config.secret_store.decrypt(stored)

    return getpass.getpass("Senha MariaDB: ")


def connect_mariadb(args, config):
    try:
        import mysql.connector
    except ImportError as exc:
        raise RuntimeError(
            "mysql-connector-python não instalado. Instale com: "
            "pip install -r requirements.txt"
        ) from exc

    password = resolve_password(args, config)

    conn = mysql.connector.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=password,
        database=args.database,
        charset=args.charset,
    )
    conn.autocommit = False
    if args.save_config:
        save_config(args, config, password)
    return conn


def mariadb_table_exists(conn, database, table):
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s",
        (database, table),
    )
    return cur.fetchone()[0] > 0


def mariadb_columns(conn, database, table):
    cur = conn.cursor()
    cur.execute(
        "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION",
        (database, table),
    )
    return [row[0] for row in cur.fetchall()]


def build_insert_sql(table, columns, mode):
    col_list = ", ".join(quote_identifier(col) for col in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    table_name = quote_identifier(table)

    if mode == "append":
        return f"INSERT IGNORE INTO {table_name} ({col_list}) VALUES ({placeholders})"
    if mode == "replace":
        return f"REPLACE INTO {table_name} ({col_list}) VALUES ({placeholders})"

    updates = ", ".join(
        f"{quote_identifier(col)}=VALUES({quote_identifier(col)})"
        for col in columns
    )
    return (
        f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders}) "
        f"ON DUPLICATE KEY UPDATE {updates}"
    )


def import_table(sqlite_conn, maria_conn, args, table):
    if not mariadb_table_exists(maria_conn, args.database, table):
        print(f"[SKIP] {table}: tabela não existe no MariaDB")
        return {"table": table, "status": "SKIP", "rows": 0}

    sqlite_cols = get_columns(sqlite_conn, table)
    maria_cols = mariadb_columns(maria_conn, args.database, table)
    columns = [col for col in sqlite_cols if col in maria_cols]
    if table in ID_EXCLUDED_TABLES:
        columns = [col for col in columns if col != "id"]

    if not columns:
        print(f"[SKIP] {table}: sem colunas compatíveis")
        return {"table": table, "status": "SKIP", "rows": 0}

    cur_sqlite = sqlite_conn.cursor()
    cur_sqlite.execute(f'SELECT COUNT(*) FROM "{table}"')
    total = cur_sqlite.fetchone()[0]
    print(f"[INFO] {table}: {total} linhas no SQLite, {len(columns)} colunas compatíveis")
    if table in APPEND_ONLY_TABLES and args.mode != "append":
        print(f"[INFO] {table}: histórico append-only — modo forçado para 'append' (ignorando --mode {args.mode})")

    if total == 0:
        return {"table": table, "status": "OK", "rows": 0}
    if not args.execute:
        return {"table": table, "status": "DRY_RUN", "rows": total}

    col_list = ", ".join(f'"{col}"' for col in columns)
    cur_sqlite.execute(f'SELECT {col_list} FROM "{table}"')
    effective_mode = "append" if table in APPEND_ONLY_TABLES else args.mode
    insert_sql = build_insert_sql(table, columns, effective_mode)
    cur_maria = maria_conn.cursor()

    rows_done = 0
    while True:
        batch = cur_sqlite.fetchmany(args.batch_size)
        if not batch:
            break
        cur_maria.executemany(insert_sql, [tuple(row[col] for col in columns) for row in batch])
        rows_done += len(batch)
        print(f"[DATA] {table}: {rows_done}/{total}")

    return {"table": table, "status": "OK", "rows": rows_done}


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Importa um SQLite coletado pelo COLETOR para MariaDB.",
    )
    parser.add_argument("--version", action="version", version=f"INTEGRADOR {VERSION}")
    parser.add_argument("--sqlite", required=True, help="Arquivo .db vindo do coletor")
    parser.add_argument("--config", default="config.ini", help="Arquivo de configuração do importador")
    parser.add_argument("--host", help="Host MariaDB")
    parser.add_argument("--port", type=int, help="Porta MariaDB")
    parser.add_argument("--user", help="Usuário MariaDB")
    parser.add_argument("--password", help="Senha MariaDB; se omitida, usa config criptografado ou solicita")
    parser.add_argument("--database", help="Database MariaDB destino")
    parser.add_argument("--charset", help="Charset de conexão")
    parser.add_argument(
        "--save-config",
        action="store_true",
        help="Salva host/user/database e senha criptografada no config.ini do importador",
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        default=DEFAULT_TABLES,
        help="Tabelas a importar; padrão: tabelas operacionais conhecidas",
    )
    parser.add_argument(
        "--mode",
        choices=("append", "upsert", "replace"),
        default=None,
        help="Modo de escrita no MariaDB",
    )
    parser.add_argument("--batch-size", type=int)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Executa gravação real. Sem esta flag, faz dry-run.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    config = load_config(args.config)
    args = resolve_settings(args, config)
    sqlite_conn = open_sqlite(args.sqlite)
    maria_conn = None

    try:
        verify_sqlite(sqlite_conn)
        available = sqlite_tables(sqlite_conn)
        tables = [table for table in args.tables if table in available]
        missing = [table for table in args.tables if table not in available]

        print(f"[OK] SQLite íntegro: {args.sqlite}")
        if missing:
            print(f"[WARN] Tabelas ausentes no SQLite: {', '.join(missing)}")
        if not tables:
            raise RuntimeError("Nenhuma tabela selecionada existe no SQLite.")

        maria_conn = connect_mariadb(args, config)
        print(f"[OK] Conectado ao MariaDB: {args.host}:{args.port}/{args.database}")
        print(f"[SEC] Segredos: {config.secret_store.provider()}")
        print(f"[MODE] {args.mode} | {'EXECUTE' if args.execute else 'DRY-RUN'}")

        results = []
        for table in tables:
            results.append(import_table(sqlite_conn, maria_conn, args, table))

        if args.execute:
            maria_conn.commit()
            print("[OK] Commit concluído.")
        else:
            maria_conn.rollback()
            print("[OK] Dry-run concluído. Nada foi gravado.")

        ok_rows = sum(item["rows"] for item in results if item["status"] in ("OK", "DRY_RUN"))
        print(f"[SUMMARY] tabelas={len(results)} linhas={ok_rows}")
        return 0
    except Exception as exc:
        if maria_conn:
            maria_conn.rollback()
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    finally:
        sqlite_conn.close()
        if maria_conn:
            maria_conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

