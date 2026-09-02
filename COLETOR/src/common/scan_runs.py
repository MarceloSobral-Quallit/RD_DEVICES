#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registro estruturado de execucoes de scan no SQLite."""

from datetime import datetime


def get_pending_items(config_mgr, scan_type):
    """Retorna o que falta concluir da ultima execucao incompleta de `scan_type`.

    Generaliza a logica que a Aba 4 usava so para hardware
    (`_select_pending_from_last_run`), para ser reaproveitada por qualquer etapa
    (B12, SCAN_LOJA, HARDWARE) — inclusive pelo Autopilot ao retomar apos uma
    interrupcao.

    Retorna dict com:
      run_id: int | None — id da ultima run RUNNING/FAILED/CANCELLED, ou None se
              nao houver nenhuma incompleta.
      pending: set[str] — item_key ja registrados nesta run mas sem SUCCESS.
      done: set[str] — item_key ja registrados com SUCCESS (preservar, nao repetir).
      include_unrecorded: bool — True se a run tinha mais itens esperados do que
              os que chegaram a ser registrados (ex.: interrompida antes de
              registrar todo mundo) — nesse caso, qualquer item fora de `done`
              deve ser tratado como pendente mesmo sem uma linha propria.
    """
    conn = config_mgr.get_sqlite_connection()
    try:
        run = conn.execute(
            """
            SELECT id, total_items
            FROM tb_scan_runs
            WHERE scan_type = ?
              AND status IN ('RUNNING', 'FAILED', 'CANCELLED')
            ORDER BY id DESC
            LIMIT 1
            """,
            (scan_type,),
        ).fetchone()
        if not run:
            return {"run_id": None, "pending": set(), "done": set(), "include_unrecorded": False}

        run_id = run[0]
        expected_total = int(run[1] or 0)
        done = {
            row[0]
            for row in conn.execute(
                "SELECT item_key FROM tb_scan_run_items WHERE run_id = ? AND status = 'SUCCESS'",
                (run_id,),
            )
        }
        candidates = {
            row[0]
            for row in conn.execute(
                "SELECT item_key FROM tb_scan_run_items WHERE run_id = ?",
                (run_id,),
            )
        }
        pending = candidates - done
        include_unrecorded = expected_total > len(candidates)
        return {
            "run_id": run_id,
            "pending": pending,
            "done": done,
            "include_unrecorded": include_unrecorded,
        }
    finally:
        conn.close()


def ensure_scan_tracking(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tb_scan_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_type TEXT NOT NULL,
            source_tab TEXT,
            status TEXT NOT NULL,
            started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            finished_at DATETIME,
            total_items INTEGER DEFAULT 0,
            processed_items INTEGER DEFAULT 0,
            success_items INTEGER DEFAULT 0,
            failed_items INTEGER DEFAULT 0,
            cancelled_items INTEGER DEFAULT 0,
            selected_count INTEGER DEFAULT 0,
            notes TEXT,
            error_message TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tb_scan_run_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            filial TEXT,
            ip TEXT,
            device_type TEXT,
            status TEXT NOT NULL,
            action TEXT,
            result_ref TEXT,
            error_message TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES tb_scan_runs(id),
            UNIQUE (run_id, item_key)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_runs_status ON tb_scan_runs(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_runs_type ON tb_scan_runs(scan_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_items_run ON tb_scan_run_items(run_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_items_filial ON tb_scan_run_items(filial)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_items_ip ON tb_scan_run_items(ip)")


def start_scan_run(config_mgr, scan_type, source_tab, total_items=0, selected_count=0, notes=""):
    conn = config_mgr.get_sqlite_connection()
    ensure_scan_tracking(conn)
    cur = conn.execute(
        """
        INSERT INTO tb_scan_runs (
            scan_type, source_tab, status, started_at, total_items, selected_count, notes
        ) VALUES (?, ?, 'RUNNING', ?, ?, ?, ?)
        """,
        (
            scan_type,
            source_tab,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            int(total_items or 0),
            int(selected_count or 0),
            notes,
        ),
    )
    run_id = cur.lastrowid
    conn.commit()
    conn.close()
    return run_id


def record_scan_item(
    config_mgr,
    run_id,
    item_key,
    filial="",
    ip="",
    device_type="",
    status="PROCESSED",
    action="processed",
    result_ref="",
    error_message="",
):
    if not run_id:
        return
    conn = config_mgr.get_sqlite_connection()
    ensure_scan_tracking(conn)
    conn.execute(
        """
        INSERT INTO tb_scan_run_items (
            run_id, item_key, filial, ip, device_type, status, action, result_ref, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id, item_key) DO UPDATE SET
            filial=excluded.filial,
            ip=excluded.ip,
            device_type=excluded.device_type,
            status=excluded.status,
            action=excluded.action,
            result_ref=excluded.result_ref,
            error_message=excluded.error_message,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            run_id,
            str(item_key),
            str(filial or ""),
            str(ip or ""),
            str(device_type or ""),
            str(status or "PROCESSED"),
            str(action or ""),
            str(result_ref or ""),
            str(error_message or ""),
        ),
    )
    conn.commit()
    conn.close()


def finish_scan_run(config_mgr, run_id, status="SUCCESS", error_message=""):
    if not run_id:
        return
    conn = config_mgr.get_sqlite_connection()
    ensure_scan_tracking(conn)
    cur = conn.cursor()
    cur.execute("SELECT scan_type FROM tb_scan_runs WHERE id = ?", (run_id,))
    row = cur.fetchone()
    scan_type = row[0] if row else ""
    if scan_type == "SCAN_LOJA":
        failed_expr = """
            status IN ('FAILED', 'AUTH_FAILED', 'ERRO')
            OR status LIKE 'ERRO_%'
            OR status LIKE 'ERRO%'
        """
    else:
        failed_expr = """
            status NOT IN ('SUCCESS', 'ESCANEADO', 'PDV Linux', 'TC Linux', 'TC Win', 'IMPRESSORA', 'CANCELLED')
        """
    cur.execute(
        f"""
        SELECT
            COUNT(*),
            SUM(CASE WHEN status IN ('SUCCESS', 'ESCANEADO', 'PDV Linux', 'TC Linux', 'TC Win', 'IMPRESSORA') THEN 1 ELSE 0 END),
            SUM(CASE WHEN {failed_expr} THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'CANCELLED' THEN 1 ELSE 0 END)
        FROM tb_scan_run_items
        WHERE run_id = ?
        """,
        (run_id,),
    )
    processed, success, failed, cancelled = cur.fetchone()
    conn.execute(
        """
        UPDATE tb_scan_runs
           SET status = ?,
               finished_at = ?,
               processed_items = ?,
               success_items = ?,
               failed_items = ?,
               cancelled_items = ?,
               error_message = ?
         WHERE id = ?
        """,
        (
            status,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            processed or 0,
            success or 0,
            failed or 0,
            cancelled or 0,
            str(error_message or ""),
            run_id,
        ),
    )
    conn.commit()
    conn.close()
