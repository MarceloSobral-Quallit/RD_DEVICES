#!/usr/bin/env python3
import json
import sqlite3
import sys


def table_exists(conn, table):
    cur = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None


def normalize_status(status, hw_scanned_at):
    status = (status or "").strip()
    lower = status.lower()
    if hw_scanned_at:
        return "Coletado"
    if not status:
        return "Sem hardware"
    if "access is denied" in lower or "-2147024891" in lower:
        return "WMI bloqueado / SSH inativo"
    if "rpc server is unavailable" in lower or "-2147023174" in lower:
        return "WMI/RPC indisponivel"
    if status.startswith("WINDOWS_WMI_BLOQUEADO_SSH_INATIVO"):
        return "WMI bloqueado / SSH inativo"
    if status.startswith("SSH_") or status.startswith("ERRO_SSH"):
        return "SSH indisponivel"
    if status.startswith("SNMP_"):
        return "SNMP sem resposta"
    return status


def fetch_rows(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = []

    if table_exists(conn, "tb_devices_detail"):
        for row in conn.execute(
            """
            SELECT
                java AS filial,
                ip,
                tipo_equipamento AS device_type,
                '' AS expected_type,
                '' AS logo,
                hostname AS hostname,
                sistema_operacional AS os,
                kernel AS os_version,
                cores_fisicos AS cores,
                memoria_total AS mem_bytes,
                mb_manufacturer,
                mb_product_name,
                mb_version,
                hdd_media_type,
                hdd_model,
                hdd_size,
                data_coleta AS scanned_at,
                'tb_devices_detail' AS source,
                'Coletado' AS scan_status
            FROM tb_devices_detail
            """
        ):
            rows.append(dict(row))

    if table_exists(conn, "tb_detected_devices"):
        status_expr = "NULL AS last_status"
        latest_join = ""
        if table_exists(conn, "tb_scan_run_items"):
            status_expr = "lsi.status AS last_status"
            latest_join = """
                LEFT JOIN (
                    SELECT i1.ip, i1.status
                    FROM tb_scan_run_items i1
                    INNER JOIN (
                        SELECT ip, MAX(id) AS id
                        FROM tb_scan_run_items
                        WHERE ip IS NOT NULL AND ip <> ''
                        GROUP BY ip
                    ) last_i ON last_i.id = i1.id
                ) lsi ON lsi.ip = d.ip
            """
        for row in conn.execute(
            f"""
            SELECT
                d.filial,
                d.ip,
                d.device_type,
                d.expected_type,
                d.logo,
                d.hw_hostname AS hostname,
                d.hw_os AS os,
                d.hw_os_version AS os_version,
                d.hw_cores_fisicos AS cores,
                d.hw_memoria_total AS mem_bytes,
                d.hw_mb_manufacturer AS mb_manufacturer,
                d.hw_mb_product_name AS mb_product_name,
                d.hw_mb_version AS mb_version,
                d.hw_hdd_media_type AS hdd_media_type,
                d.hw_hdd_model AS hdd_model,
                d.hw_hdd_size AS hdd_size,
                d.hw_scanned_at AS scanned_at,
                'tb_detected_devices' AS source,
                {status_expr}
            FROM tb_detected_devices d
            {latest_join}
            WHERE NOT EXISTS (
                SELECT 1
                FROM tb_devices_detail dd
                WHERE dd.ip = d.ip
            )
            """
        ):
            item = dict(row)
            item["scan_status"] = normalize_status(item.pop("last_status", ""), item.get("scanned_at"))
            rows.append(item)

    def sort_key(row):
        filial = str(row.get("filial") or "")
        try:
            filial_key = int(filial)
        except ValueError:
            filial_key = 999999999
        return filial_key, str(row.get("ip") or "")

    rows.sort(key=sort_key)
    conn.close()
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: store_export.py <devices.db>")
    print(json.dumps(fetch_rows(sys.argv[1]), ensure_ascii=False))
