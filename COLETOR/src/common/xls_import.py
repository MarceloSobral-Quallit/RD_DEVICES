#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xls_import.py - Import nao-interativo de XLS de lojas para tb_filial.

Espelha o mapeamento e as regras de validacao da Aba 1 (tab_1_import_xls.py),
mas sem dialogo/preview — pensado para ser chamado programaticamente pela Aba
Autopilot (informar um caminho de XLS e seguir direto para o pipeline). A Aba 1
continua com sua propria UI/fluxo interativo, inalterada.
"""

import re
import unicodedata
from dataclasses import dataclass, field

try:
    import xlrd
except ImportError:
    xlrd = None


# Mapeamento fixo XLS -> tb_filial (indice, cabecalho esperado, coluna destino)
FIELD_MAPPING = [
    (0, "Filial", "filial"),
    (1, "Hist.", "historico"),
    (2, "Nome Filial", "nome_filial"),
    (3, "Dt. Inauguração", "data_inauguracao"),
    (4, "Insc. Estadual", "inscricao_estadual"),
    (5, "CNPJ", "cnpj"),
    (6, "Endereço", "endereco"),
    (7, "Bairro", "bairro"),
    (8, "Cidade", "cidade"),
    (9, "UF", "uf"),
    (10, "Região", "regiao"),
    (11, "Logomarca", "logomarca"),
    (12, "Telefone", "telefone"),
    (13, "IP Banco 12", "ip_banco_12"),
]


@dataclass
class ImportStats:
    total_rows: int = 0
    imported: int = 0
    warnings: list = field(default_factory=list)
    header_mismatches: list = field(default_factory=list)
    status: str = "success"  # success | error
    error: str = ""


def _norm(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()


def _validate_ip(ip):
    if not ip or ip == '0.0.0.0':
        return False
    match = re.match(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$', str(ip))
    if not match:
        return False
    try:
        octets = [int(x) for x in match.groups()]
        return all(0 <= o <= 255 for o in octets) and octets[0] not in (0, 127)
    except Exception:
        return False


def _convert_date(value, datemode):
    if not value:
        return None
    try:
        if isinstance(value, float):
            t = xlrd.xldate_as_tuple(value, datemode)
            if t[0] == 0:
                return None
            return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"
        if isinstance(value, str) and '/' in value:
            parts = value.split('/')
            if len(parts) == 3:
                return f"{int(parts[2]):04d}-{int(parts[1]):02d}-{int(parts[0]):02d}"
    except Exception:
        pass
    return None


def _clean_numeric(value):
    if not value:
        return None
    clean = ''.join(c for c in str(value) if c.isdigit())
    return clean or None


def _clean_text(value):
    if not value:
        return None
    return str(value).strip()


def validate_header_mapping(headers):
    """Retorna lista de divergencias (vazia = mapeamento OK)."""
    mismatches = []
    if not headers:
        return mismatches
    for idx, expected_header, dest_col in FIELD_MAPPING:
        current = str(headers[idx]).strip() if idx < len(headers) else ""
        if _norm(current) != _norm(expected_header):
            mismatches.append((idx, expected_header, current, dest_col))
    return mismatches


def import_filiais(path, mode="upsert", config_mgr=None):
    """Le um XLS de lojas e grava/atualiza tb_filial. Retorna ImportStats.

    mode: 'upsert' (INSERT OR REPLACE) ou 'truncate' (limpa tb_filial antes).
    config_mgr: ConfigManager ja existente (reaproveita conexao/config); se
                None, cria um novo (`from src.common.config import ConfigManager`).
    """
    stats = ImportStats()

    if xlrd is None:
        stats.status = "error"
        stats.error = "xlrd nao instalado"
        return stats

    if config_mgr is None:
        from src.common.config import ConfigManager
        config_mgr = ConfigManager()

    try:
        wb = xlrd.open_workbook(path)
        ws = wb.sheet_by_index(0)
        datemode = wb.datemode

        headers = None
        rows = []
        for row_idx in range(ws.nrows):
            row_values = ws.row_values(row_idx)
            if row_idx == 0:
                headers = row_values
                continue
            if not any(row_values):
                continue
            rows.append(row_values)

        stats.header_mismatches = validate_header_mapping(headers)
        stats.total_rows = len(rows)

        col_mapping = {idx: dest for idx, _header, dest in FIELD_MAPPING}
        records = []
        for row_idx, row in enumerate(rows, 1):
            record = {}
            for col_idx, col_name in col_mapping.items():
                value = row[col_idx] if col_idx < len(row) else None
                if col_name == 'data_inauguracao':
                    value = _convert_date(value, datemode)
                elif col_name in ('cnpj', 'inscricao_estadual'):
                    value = _clean_numeric(value)
                else:
                    value = _clean_text(value)
                record[col_name] = value

            ip = record.get('ip_banco_12') or ''
            record['ativo'] = 1 if _validate_ip(ip.strip()) else 0
            if not record.get('filial'):
                stats.warnings.append(f"Linha {row_idx}: Filial vazia")
            if record.get('ip_banco_12') and not _validate_ip(record['ip_banco_12']):
                stats.warnings.append(f"Linha {row_idx}: IP invalido: {record['ip_banco_12']}")

            records.append(record)

        conn = config_mgr.get_sqlite_connection()
        cursor = conn.cursor()
        try:
            if mode == "truncate":
                cursor.execute("DELETE FROM tb_filial")

            for record in records:
                cols = list(record.keys())
                values = tuple(record.values())
                placeholders = ",".join(["?" for _ in cols])
                sql = f"INSERT OR REPLACE INTO tb_filial ({','.join(cols)}) VALUES ({placeholders})"
                cursor.execute(sql, values)
                stats.imported += 1

            conn.commit()
        except Exception as e:
            conn.rollback()
            stats.status = "error"
            stats.error = str(e)
        finally:
            conn.close()

    except Exception as e:
        stats.status = "error"
        stats.error = str(e)

    return stats
