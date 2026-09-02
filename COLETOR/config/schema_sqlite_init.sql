-- =============================================================================
-- schema_sqlite_init.sql — Schema inicial do banco SQLite para o COLETOR
-- =============================================================================
-- Uso:
--   sqlite3 work/devices.db < config/schema_sqlite_init.sql
--
-- Tabelas e origem dos dados:
--   tb_filial                     → populada via importação XLS (Aba 1)
--   tb_devices_detail             → populada pela coleta SSH B12 (Aba 2) — inicia vazia
--   tb_b12_data_collection_status → rastreamento de coleta B12 (Aba 2) — inicia vazia
--   tb_detected_devices           → auto-criada pela Aba 3 (incluída aqui para schema completo)
--
-- Gerado em: 2026-06-09
-- =============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- tb_filial
-- Cadastro das filiais/lojas.
-- Populada via importação XLS (Aba 1 do COLETOR). Inicia vazia.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_filial (
    filial              TEXT NOT NULL,
    historico           TEXT NOT NULL,
    nome_filial         TEXT NOT NULL,
    data_inauguracao    TEXT,               -- formato YYYY-MM-DD
    inscricao_estadual  TEXT,
    cnpj                TEXT,
    endereco            TEXT,
    bairro              TEXT,
    cidade              TEXT,
    uf                  TEXT,
    regiao              TEXT,
    logomarca           TEXT,
    telefone            TEXT,
    ip_banco_12         TEXT,
    ativo               INTEGER DEFAULT 1,  -- 0=inativa, 1=ativa
    cidr                TEXT,               -- preenchido pela Aba 2 após detect SSH do B12
    PRIMARY KEY (filial)
);

CREATE INDEX IF NOT EXISTS idx_filial_ativo        ON tb_filial (ativo);
CREATE INDEX IF NOT EXISTS idx_filial_ip_banco_12  ON tb_filial (ip_banco_12);
CREATE INDEX IF NOT EXISTS idx_filial_logomarca    ON tb_filial (logomarca);
CREATE INDEX IF NOT EXISTS idx_filial_uf           ON tb_filial (uf);

-- -----------------------------------------------------------------------------
-- tb_devices_detail
-- Hardware detalhado coletado dos servidores B12 via SSH (Aba 2).
-- Inicia vazia; populada durante as coletas.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_devices_detail (
    detail_job_id       TEXT,
    java                TEXT NOT NULL,
    ip                  TEXT NOT NULL,
    hostname            TEXT NOT NULL,
    tipo_equipamento    TEXT NOT NULL,      -- sempre 'B12' nesta tabela
    sistema_operacional TEXT NOT NULL,
    kernel              TEXT DEFAULT '',
    cores_fisicos       TEXT NOT NULL,
    memoria_total       INTEGER NOT NULL,   -- MemTotal em bytes (/proc/meminfo)
    mac_address         TEXT,
    mb_manufacturer     TEXT,
    mb_product_name     TEXT,
    mb_version          TEXT,
    hdd_media_type      TEXT,               -- 'SSD' ou 'HDD'
    hdd_model           TEXT,
    hdd_size            INTEGER,            -- tamanho em bytes
    data_coleta         DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao    DATETIME,
    PRIMARY KEY (ip)
);

CREATE INDEX IF NOT EXISTS idx_devices_detail_java ON tb_devices_detail (java);
CREATE INDEX IF NOT EXISTS idx_devices_detail_tipo ON tb_devices_detail (tipo_equipamento);

-- -----------------------------------------------------------------------------
-- tb_b12_data_collection_status
-- Rastreamento granular da coleta B12 por filial/IP (Aba 2).
-- Registra quais campos foram coletados com sucesso e percentual de completude.
-- Inicia vazia; populada durante as coletas.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_b12_data_collection_status (
    java                        TEXT NOT NULL,
    ip_b12                      TEXT NOT NULL,
    nome_filial                  TEXT,

    -- Status geral da coleta
    collection_status           TEXT,       -- IN_PROGRESS | SUCCESS | PARTIAL | FAILED
    collection_date             TEXT,
    collection_duration_seconds INTEGER,

    -- Rastreamento por campo: <campo>_collected (0/1) + <campo>_value
    hostname_collected          INTEGER DEFAULT 0,
    hostname_value              TEXT,
    hostname_raw_collected      INTEGER DEFAULT 0,
    hostname_raw_value          TEXT,
    os_collected                INTEGER DEFAULT 0,
    os_value                    TEXT,
    os_version_collected        INTEGER DEFAULT 0,
    os_version_value            TEXT,
    kernel_collected            INTEGER DEFAULT 0,
    kernel_value                TEXT,
    cidr_collected              INTEGER DEFAULT 0,
    cidr_value                  TEXT,
    cores_collected             INTEGER DEFAULT 0,
    cores_value                 TEXT,
    memory_collected            INTEGER DEFAULT 0,
    memory_value_bytes          INTEGER,
    mac_collected               INTEGER DEFAULT 0,
    mac_value                   TEXT,
    mb_manufacturer_collected   INTEGER DEFAULT 0,
    mb_manufacturer_value       TEXT,
    mb_product_collected        INTEGER DEFAULT 0,
    mb_product_value            TEXT,
    mb_version_collected        INTEGER DEFAULT 0,
    mb_version_value            TEXT,
    disk_media_type_collected   INTEGER DEFAULT 0,
    disk_media_type_value       TEXT,
    disk_model_collected        INTEGER DEFAULT 0,
    disk_model_value            TEXT,
    disk_size_collected         INTEGER DEFAULT 0,
    disk_size_value             INTEGER,

    -- Sumário: 18 campos rastreáveis
    fields_collected_count      INTEGER DEFAULT 0,
    collection_percentage       REAL    DEFAULT 0.0,
    updated_at                  DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (java, ip_b12)
);

CREATE INDEX IF NOT EXISTS idx_b12_status_status ON tb_b12_data_collection_status (collection_status);
CREATE INDEX IF NOT EXISTS idx_b12_status_ip     ON tb_b12_data_collection_status (ip_b12);

-- -----------------------------------------------------------------------------
-- tb_detected_devices
-- Dispositivos detectados em scan de rede por filial (Aba 3).
-- Auto-criada pelo COLETOR (tab_3_devices.py) se não existir.
-- Incluída aqui para manter o schema completo em um único script.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_detected_devices (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    filial          TEXT,
    ip              TEXT NOT NULL UNIQUE,
    expected_type   TEXT,           -- B12 | PDV | TC | IMPRESSORA
    ssh             INTEGER DEFAULT 0,
    radmin          INTEGER DEFAULT 0,
    printer         INTEGER DEFAULT 0,
    device_type     TEXT,
    logo            TEXT,
    detected_at     DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Colunas de hardware — adicionadas pela Aba 4 (ALTER TABLE IF NOT EXISTS)
    hw_hostname           TEXT,
    hw_cpu_model          TEXT,
    hw_cores              INTEGER,
    hw_ram_gb             REAL,
    hw_disk_gb            REAL,
    hw_os                 TEXT,
    hw_os_version         TEXT,
    hw_kernel             TEXT,
    hw_cores_fisicos      TEXT,
    hw_memoria_total      INTEGER,
    hw_mac_address        TEXT,
    hw_mb_manufacturer    TEXT,
    hw_mb_product_name    TEXT,
    hw_mb_version         TEXT,
    hw_hdd_media_type     TEXT,
    hw_hdd_model          TEXT,
    hw_hdd_size           INTEGER,
    hw_scanned_at         DATETIME
);

CREATE INDEX IF NOT EXISTS idx_detected_filial      ON tb_detected_devices (filial);
CREATE INDEX IF NOT EXISTS idx_detected_device_type ON tb_detected_devices (device_type);
CREATE INDEX IF NOT EXISTS idx_detected_detected_at ON tb_detected_devices (detected_at);


-- -----------------------------------------------------------------------------
-- tb_devices_detail_history
-- Historico append-only de coletas B12 (Aba 2). Uma linha por IP por coleta;
-- nunca sobrescrita. Chave de deduplicacao: (ip, data_coleta).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_devices_detail_history (
    run_id               INTEGER,
    java                 TEXT NOT NULL,
    ip                   TEXT NOT NULL,
    hostname             TEXT NOT NULL,
    tipo_equipamento     TEXT NOT NULL,
    sistema_operacional  TEXT NOT NULL,
    kernel               TEXT DEFAULT '',
    cores_fisicos        TEXT NOT NULL,
    memoria_total        INTEGER NOT NULL,
    mac_address          TEXT,
    mb_manufacturer      TEXT,
    mb_product_name      TEXT,
    mb_version           TEXT,
    hdd_media_type       TEXT,
    hdd_model            TEXT,
    hdd_size             INTEGER,
    data_coleta          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ip, data_coleta)
);

CREATE INDEX IF NOT EXISTS idx_devdet_hist_java       ON tb_devices_detail_history (java);
CREATE INDEX IF NOT EXISTS idx_devdet_hist_ip         ON tb_devices_detail_history (ip);
CREATE INDEX IF NOT EXISTS idx_devdet_hist_data_coleta ON tb_devices_detail_history (data_coleta);
CREATE INDEX IF NOT EXISTS idx_devdet_hist_run_id     ON tb_devices_detail_history (run_id);

-- -----------------------------------------------------------------------------
-- tb_detected_devices_history
-- Historico append-only de deteccao de rede (Aba 3) e hardware (Aba 4). Uma
-- linha e gravada a cada scan: Aba 3 grava com hw_* nulos; Aba 4 grava um
-- snapshot completo (relido de tb_detected_devices apos o UPDATE). Chave:
-- (ip, snapshot_at).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_detected_devices_history (
    run_id              INTEGER,
    filial              TEXT,
    ip                  TEXT NOT NULL,
    expected_type       TEXT,
    ssh                 INTEGER DEFAULT 0,
    radmin              INTEGER DEFAULT 0,
    printer             INTEGER DEFAULT 0,
    device_type         TEXT,
    logo                TEXT,
    detected_at         DATETIME,

    hw_hostname           TEXT,
    hw_cpu_model          TEXT,
    hw_cores              INTEGER,
    hw_ram_gb             REAL,
    hw_disk_gb            REAL,
    hw_os                 TEXT,
    hw_os_version         TEXT,
    hw_kernel             TEXT,
    hw_cores_fisicos      TEXT,
    hw_memoria_total      INTEGER,
    hw_mac_address        TEXT,
    hw_mb_manufacturer    TEXT,
    hw_mb_product_name    TEXT,
    hw_mb_version         TEXT,
    hw_hdd_media_type     TEXT,
    hw_hdd_model          TEXT,
    hw_hdd_size           INTEGER,
    hw_scanned_at         DATETIME,

    snapshot_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ip, snapshot_at)
);

CREATE INDEX IF NOT EXISTS idx_detdev_hist_filial      ON tb_detected_devices_history (filial);
CREATE INDEX IF NOT EXISTS idx_detdev_hist_ip          ON tb_detected_devices_history (ip);
CREATE INDEX IF NOT EXISTS idx_detdev_hist_snapshot_at ON tb_detected_devices_history (snapshot_at);
CREATE INDEX IF NOT EXISTS idx_detdev_hist_run_id      ON tb_detected_devices_history (run_id);


-- ---------------------------------------------------------------------------
-- tb_scan_runs / tb_scan_run_items
-- Controle estruturado de execuções de scan/coleta. Não substitui nem altera
-- arquivos de log; serve para identificar execuções incompletas e itens
-- processados/inseridos no banco.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tb_scan_runs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_type           TEXT NOT NULL,       -- B12 | SCAN_LOJA | HARDWARE
    source_tab          TEXT,
    status              TEXT NOT NULL,       -- RUNNING | SUCCESS | CANCELLED | FAILED
    started_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at         DATETIME,
    total_items         INTEGER DEFAULT 0,
    processed_items     INTEGER DEFAULT 0,
    success_items       INTEGER DEFAULT 0,
    failed_items        INTEGER DEFAULT 0,
    cancelled_items     INTEGER DEFAULT 0,
    selected_count      INTEGER DEFAULT 0,
    notes               TEXT,
    error_message       TEXT
);

CREATE TABLE IF NOT EXISTS tb_scan_run_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id              INTEGER NOT NULL,
    item_key            TEXT NOT NULL,
    filial              TEXT,
    ip                  TEXT,
    device_type         TEXT,
    status              TEXT NOT NULL,
    action              TEXT,
    result_ref          TEXT,
    error_message       TEXT,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES tb_scan_runs(id),
    UNIQUE (run_id, item_key)
);

CREATE INDEX IF NOT EXISTS idx_scan_runs_status ON tb_scan_runs (status);
CREATE INDEX IF NOT EXISTS idx_scan_runs_type   ON tb_scan_runs (scan_type);
CREATE INDEX IF NOT EXISTS idx_scan_items_run   ON tb_scan_run_items (run_id);
CREATE INDEX IF NOT EXISTS idx_scan_items_filial ON tb_scan_run_items (filial);
CREATE INDEX IF NOT EXISTS idx_scan_items_ip    ON tb_scan_run_items (ip);
