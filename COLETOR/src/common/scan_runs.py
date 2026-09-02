#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registro estruturado de execucoes de scan no SQLite."""

from datetime import datetime


def reconcile_orphan_runs(config_mgr):
    """Marca como FAILED qualquer run que ficou RUNNING de um processo anterior.

    No arranque nenhuma run pode estar legitimamente RUNNING — se esta, o
    processo que a abriu foi encerrado (crash, kill, sleep) sem finalizar.
    Deixar em FAILED permite que o Autopilot a detecte e ofereca retomada, e
    impede que o historico acumule runs eternamente "em andamento".
    Retorna a quantidade de runs reconciliadas.
    """
    try:
        conn = config_mgr.get_sqlite_connection()
    except Exception:
        return 0
    try:
        ensure_scan_tracking(conn)
        cur = conn.execute(
            """
            UPDATE tb_scan_runs
               SET status = 'FAILED',
                   finished_at = COALESCE(finished_at, ?),
                   error_message = CASE
                       WHEN error_message IS NULL OR error_message = ''
                       THEN 'processo encerrado sem finalizar a run'
                       ELSE error_message
                   END
             WHERE status = 'RUNNING'
            """,
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),),
        )
        conn.commit()
        return cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
    except Exception:
        return 0
    finally:
        conn.close()


INCOMPLETE_RUN_STATUSES = ("RUNNING", "FAILED", "CANCELLED")

# Por etapa: statuses de item que representam uma coleta bem-sucedida.
_SUCCESS_ITEM_STATUSES = {
    "B12": {"SUCCESS", "ESCANEADO"},
    "SCAN_LOJA": {"PDV Linux", "TC Linux", "TC Win", "IMPRESSORA", "Offline", "ESCANEADO"},
    "HARDWARE": {"SUCCESS"},
}
# Por etapa: statuses que sao um resultado negativo *definitivo* — ja foram
# verificados (o modo "completar o que faltou" os pula), mas continuam elegiveis
# para o modo "reescanear os que falharam".
_CHECKED_NEGATIVE_ITEM_STATUSES = {
    "B12": {"OFFLINE"},
    "SCAN_LOJA": set(),
    "HARDWARE": set(),
}


def _classify_item(scan_type, status):
    """'success' | 'checked' | 'failed' para um status de tb_scan_run_items."""
    s = (status or "").strip()
    if s in _SUCCESS_ITEM_STATUSES.get(scan_type, {"SUCCESS"}):
        return "success"
    if s in _CHECKED_NEGATIVE_ITEM_STATUSES.get(scan_type, set()):
        return "checked"
    return "failed"


def get_pending_items(config_mgr, scan_type):
    """Retorna o que falta concluir da *ultima* execucao de `scan_type`.

    Generaliza a logica que a Aba 4 usava so para hardware
    (`_select_pending_from_last_run`), para ser reaproveitada por qualquer etapa
    (B12, SCAN_LOJA, HARDWARE) — inclusive pelo Autopilot ao retomar apos uma
    interrupcao.

    Olha SO a run mais recente da etapa (maior id). Se ela terminou (SUCCESS /
    PARTIAL / etc.), a etapa esta concluida e nada fica pendente — runs
    incompletas *mais antigas* (de sessoes anteriores ja substituidas) sao
    historico e nao devem reabrir a etapa.

    Retorna dict com:
      run_id: int | None — id da run mais recente se ela estiver incompleta
              (RUNNING/FAILED/CANCELLED); None caso contrario.
      done: set[str] — item_key a *pular* no modo "completar o que faltou"
              (coleta bem-sucedida ou resultado negativo definitivo).
      pending: set[str] — item_key a *refazer* no modo "reescanear os que
              falharam" (falhas + resultados negativos definitivos).
      include_unrecorded: bool — True se a run esperava mais itens do que os
              registrados (interrompida cedo); nesse caso o Autopilot trata
              qualquer item fora de `done` como pendente.
      complete: bool — True se a ultima run da etapa ja terminou.
    """
    empty = {"run_id": None, "pending": set(), "done": set(),
             "include_unrecorded": False, "complete": False}
    conn = config_mgr.get_sqlite_connection()
    try:
        run = conn.execute(
            """
            SELECT id, total_items, status
            FROM tb_scan_runs
            WHERE scan_type = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (scan_type,),
        ).fetchone()
        if not run:
            return empty

        run_id, expected_total, status = run[0], int(run[1] or 0), run[2]
        rows = conn.execute(
            "SELECT item_key, status FROM tb_scan_run_items WHERE run_id = ?",
            (run_id,),
        ).fetchall()
        candidates = {r[0] for r in rows}

        if status not in INCOMPLETE_RUN_STATUSES:
            # Ultima run terminou: etapa concluida. Nada a refazer; no modo
            # "completar", todos os itens ja registrados sao pulados.
            return {"run_id": None, "pending": set(), "done": set(candidates),
                    "include_unrecorded": False, "complete": True}

        success, checked, failed = set(), set(), set()
        for key, st in rows:
            bucket = _classify_item(scan_type, st)
            (success if bucket == "success" else checked if bucket == "checked" else failed).add(key)

        return {
            "run_id": run_id,
            "done": success | checked,      # "completar o que faltou" pula estes
            "pending": failed | checked,    # "reescanear os que falharam" refaz estes
            "include_unrecorded": expected_total > len(candidates),
            "complete": False,
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
    cur.execute("SELECT scan_type, total_items FROM tb_scan_runs WHERE id = ?", (run_id,))
    row = cur.fetchone()
    scan_type = row[0] if row else ""
    expected_total = int(row[1] or 0) if row else 0
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
    processed = processed or 0
    success = success or 0
    failed = failed or 0
    cancelled = cancelled or 0

    # Status honesto: um "SUCCESS" onde nada foi coletado nao e sucesso.
    # So reclassifica quando o chamador pediu SUCCESS — CANCELLED/FAILED
    # explicitos sao preservados.
    effective_status = status
    if status == "SUCCESS" and processed > 0:
        if success == 0:
            effective_status = "FAILED"
        elif failed > 0:
            effective_status = "PARTIAL"

    # total_items pode ter sido aberto como 0 (ex.: HARDWARE no Autopilot, cujos
    # alvos so sao conhecidos apos o Scan Loja). Nunca deixar abaixo do processado.
    total_fallback = max(int(expected_total or 0), processed)

    conn.execute(
        """
        UPDATE tb_scan_runs
           SET status = ?,
               finished_at = ?,
               total_items = ?,
               processed_items = ?,
               success_items = ?,
               failed_items = ?,
               cancelled_items = ?,
               error_message = ?
         WHERE id = ?
        """,
        (
            effective_status,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_fallback,
            processed,
            success,
            failed,
            cancelled,
            str(error_message or ""),
            run_id,
        ),
    )
    conn.commit()
    conn.close()
