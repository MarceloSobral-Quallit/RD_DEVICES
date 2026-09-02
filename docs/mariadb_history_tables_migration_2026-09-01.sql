-- =============================================================================
-- mariadb_history_tables_migration_2026-09-01.sql
-- Adiciona tabelas de historico (append-only) para comparacao "antes x depois"
-- por data de coleta, por loja (java/filial). Nao substitui nem altera
-- tb_devices_detail / tb_detected_devices (estado atual).
--
-- Uso:
--   mysql -h <host> -P <port> -u <admin> -p rd_devices_dev < mariadb_history_tables_migration_2026-09-01.sql
-- =============================================================================

CREATE TABLE IF NOT EXISTS `tb_devices_detail_history` (
  `id`                  BIGINT(20) NOT NULL AUTO_INCREMENT,
  `run_id`              INT(11) DEFAULT NULL,
  `java`                VARCHAR(50) NOT NULL,
  `ip`                  VARCHAR(15) NOT NULL,
  `hostname`            VARCHAR(100) NOT NULL,
  `tipo_equipamento`    VARCHAR(20) NOT NULL,
  `sistema_operacional` VARCHAR(100) NOT NULL,
  `kernel`              VARCHAR(100) NOT NULL DEFAULT '',
  `cores_fisicos`       VARCHAR(50) NOT NULL,
  `memoria_total`       BIGINT(20) NOT NULL,
  `mac_address`         VARCHAR(17) DEFAULT NULL,
  `mb_manufacturer`     VARCHAR(100) DEFAULT NULL,
  `mb_product_name`     VARCHAR(100) DEFAULT NULL,
  `mb_version`          VARCHAR(50) DEFAULT NULL,
  `hdd_media_type`      VARCHAR(50) DEFAULT NULL,
  `hdd_model`           VARCHAR(100) DEFAULT NULL,
  `hdd_size`            BIGINT(20) DEFAULT NULL,
  `data_coleta`         DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_devdet_hist_ip_data` (`ip`, `data_coleta`),
  KEY `idx_devdet_hist_java`   (`java`),
  KEY `idx_devdet_hist_data`   (`data_coleta`),
  KEY `idx_devdet_hist_run`    (`run_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='Historico append-only de coletas B12 (uma linha por IP por coleta)';

CREATE TABLE IF NOT EXISTS `tb_detected_devices_history` (
  `id`                 BIGINT(20) NOT NULL AUTO_INCREMENT,
  `run_id`             INT(11) DEFAULT NULL,
  `filial`             VARCHAR(10) DEFAULT NULL,
  `ip`                 VARCHAR(15) NOT NULL,
  `expected_type`      VARCHAR(20) DEFAULT NULL,
  `ssh`                TINYINT(1) DEFAULT 0,
  `radmin`             TINYINT(1) DEFAULT 0,
  `printer`            TINYINT(1) DEFAULT 0,
  `device_type`        VARCHAR(50) DEFAULT NULL,
  `logo`               VARCHAR(20) DEFAULT NULL,
  `detected_at`        DATETIME DEFAULT NULL,
  `hw_hostname`        VARCHAR(100) DEFAULT NULL,
  `hw_cpu_model`       VARCHAR(200) DEFAULT NULL,
  `hw_cores`           INT(11) DEFAULT NULL,
  `hw_ram_gb`          FLOAT DEFAULT NULL,
  `hw_disk_gb`         FLOAT DEFAULT NULL,
  `hw_os`              VARCHAR(100) DEFAULT NULL,
  `hw_os_version`      VARCHAR(100) DEFAULT NULL,
  `hw_kernel`          VARCHAR(100) DEFAULT NULL,
  `hw_cores_fisicos`   VARCHAR(50) DEFAULT NULL,
  `hw_memoria_total`   BIGINT(20) DEFAULT NULL,
  `hw_mac_address`     VARCHAR(17) DEFAULT NULL,
  `hw_mb_manufacturer` VARCHAR(100) DEFAULT NULL,
  `hw_mb_product_name` VARCHAR(100) DEFAULT NULL,
  `hw_mb_version`      VARCHAR(50) DEFAULT NULL,
  `hw_hdd_media_type`  VARCHAR(20) DEFAULT NULL,
  `hw_hdd_model`       VARCHAR(100) DEFAULT NULL,
  `hw_hdd_size`        BIGINT(20) DEFAULT NULL,
  `hw_scanned_at`      DATETIME DEFAULT NULL,
  `snapshot_at`        DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_detdev_hist_ip_snap` (`ip`, `snapshot_at`),
  KEY `idx_detdev_hist_filial` (`filial`),
  KEY `idx_detdev_hist_snap`   (`snapshot_at`),
  KEY `idx_detdev_hist_run`    (`run_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Historico append-only de deteccao de rede + hardware (snapshot completo por scan)';
