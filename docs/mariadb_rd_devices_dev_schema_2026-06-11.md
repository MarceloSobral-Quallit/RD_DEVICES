# MariaDB rd_devices_dev - Schema Reference

- Data de referência: 2026-06-11
- Servidor: `<mariadb-host>:3306`
- Database: `rd_devices_dev`
- Versão reportada: `11.8.6-MariaDB-0+deb13u1 from Debian-log`
- Dump SQL completo: `docs/mariadb_rd_devices_dev_schema_2026-06-11.sql`
- SQLite usado na comparação: `temp/Preventiva-Coletor-4/database/devices.db`
- Ajuste aplicado em 2026-06-11: `tb_scan_runs` e `tb_scan_run_items` foram criadas no MariaDB para compatibilidade com o COLETOR atual.
- Status: schema compatível com as tabelas operacionais atuais do COLETOR após ajuste de 2026-06-11.

## Inventário
- Tabelas base: 30
- Views: 19

### Tabelas Base
| Tabela | Linhas estimadas | Engine | Collation | Colunas |
|---|---:|---|---|---:|
| `tb_alerts` | 0 | InnoDB | utf8mb4_unicode_ci | 15 |
| `tb_audit_config` | 0 | InnoDB | utf8mb4_unicode_ci | 7 |
| `tb_audit_log` | 0 | InnoDB | utf8mb4_unicode_ci | 15 |
| `tb_b12_data_collection_status` | 0 | InnoDB | utf8mb4_unicode_ci | 39 |
| `tb_detected_devices` | 0 | InnoDB | utf8mb4_unicode_ci | 28 |
| `tb_devices` | 0 | InnoDB | utf8mb3_general_ci | 21 |
| `tb_devices_catalog` | 0 | InnoDB | utf8mb4_general_ci | 2 |
| `tb_devices_detail` | 48252 | InnoDB | utf8mb4_general_ci | 18 |
| `tb_devices_detail_log` | 35640 | InnoDB | utf8mb4_general_ci | 15 |
| `tb_filial` | 3587 | InnoDB | utf8mb4_unicode_ci | 19 |
| `tb_hardware_historico` | 48882 | InnoDB | utf8mb4_general_ci | 19 |
| `tb_log_execucao` | 0 | InnoDB | utf8mb4_general_ci | 6 |
| `tb_network_ips` | 0 | InnoDB | utf8mb4_general_ci | 18 |
| `tb_network_ports` | 220139 | InnoDB | utf8mb4_general_ci | 9 |
| `tb_network_ports_backup_20251211` | 206659 | InnoDB | utf8mb4_uca1400_ai_ci | 9 |
| `tb_network_subnets` | 3578 | InnoDB | utf8mb4_general_ci | 6 |
| `tb_network_subnets_type` | 3546 | InnoDB | utf8mb4_general_ci | 27 |
| `tb_performance_metrics` | 0 | InnoDB | utf8mb4_unicode_ci | 7 |
| `tb_scan_control` | 0 | InnoDB | utf8mb3_general_ci | 9 |
| `tb_scan_control_backup_20251211` | 0 | InnoDB | utf8mb4_uca1400_ai_ci | 9 |
| `tb_scan_details` | 0 | InnoDB | utf8mb4_unicode_ci | 16 |
| `tb_scan_java_log` | 0 | InnoDB | utf8mb4_general_ci | 10 |
| `tb_scan_status` | 4 | InnoDB | utf8mb4_unicode_ci | 18 |
| `tb_scan_status_backup_20251211` | 4 | InnoDB | utf8mb4_uca1400_ai_ci | 18 |
| `tb_usb_devices` | 0 | InnoDB | utf8mb4_general_ci | 5 |
| `tb_vpn_monitor` | 578 | InnoDB | utf8mb4_unicode_ci | 14 |
| `tb_vpn_status` | 1 | InnoDB | utf8mb4_unicode_ci | 8 |
| `tb_web_access_log` | 3418 | InnoDB | utf8mb4_uca1400_ai_ci | 10 |
| `tb_web_users` | 5 | InnoDB | utf8mb4_uca1400_ai_ci | 7 |
| `tb_web_user_page_permissions` | 16 | InnoDB | utf8mb4_uca1400_ai_ci | 6 |

### Views
| View | Colunas |
|---|---:|
| `cs_devices` | 14 |
| `cs_scan_control` | 9 |
| `cs_service` | 18 |
| `cs_service3` | 11 |
| `cs_service4` | 11 |
| `cs_service5` | 9 |
| `v_active_alerts` | 10 |
| `v_b12_auth_errors` | 13 |
| `v_b12_never_connected` | 10 |
| `v_current_scan_status` | 11 |
| `v_hardware_auth_errors` | 10 |
| `v_hardware_errors_stats` | 7 |
| `v_hardware_never_success` | 8 |
| `v_hardware_recurring_errors` | 9 |
| `v_scan_items_for_retry` | 10 |
| `v_scan_monitoring` | 19 |
| `v_scan_stuck_processes` | 8 |
| `v_scan_summary` | 7 |
| `v_ssh_errors_stats` | 5 |

## Compatibilidade Com O SQLite Do COLETOR

Tabelas operacionais esperadas pelo fluxo COLETOR -> INTEGRADOR -> WWW:

| Tabela | SQLite | MariaDB | Colunas SQLite | Colunas MariaDB | Status |
|---|---:|---:|---:|---:|---|
| `tb_filial` | sim | sim | 16 | 19 | MariaDB tem colunas extras: id, data_criacao, data_atualizacao |
| `tb_devices_detail` | sim | sim | 18 | 18 | OK |
| `tb_b12_data_collection_status` | sim | sim | 39 | 39 | OK |
| `tb_detected_devices` | sim | sim | 28 | 28 | OK |
| `tb_scan_runs` | sim | sim | 14 | 14 | OK após ajuste de 2026-06-11 |
| `tb_scan_run_items` | sim | sim | 12 | 12 | OK após ajuste de 2026-06-11 |

### Divergências Relevantes

- `tb_scan_runs` e `tb_scan_run_items` existiam no SQLite do COLETOR, mas não existiam no MariaDB no primeiro levantamento. As duas tabelas foram criadas em 2026-06-11 para preservar o histórico estruturado de execuções no fluxo de importação.
- `tb_filial` no MariaDB tem `id`, `data_criacao` e `data_atualizacao` extras. Isso é compatível com importação por interseção de colunas, desde que `filial` continue `UNIQUE`.
- `tb_devices_detail`, `tb_detected_devices` e `tb_b12_data_collection_status` estão compatíveis em nomes de colunas com o SQLite de referência.
- O MariaDB já contém tabelas históricas/legadas (`tb_devices`, `tb_network_ports`, `tb_hardware_historico`, `tb_scan_status`, etc.) que não existem no SQLite novo. Elas devem ser tratadas como legado ou camada complementar, não como destino direto do COLETOR atual.
- O modo `upsert` do INTEGRADOR atual não remove do MariaDB registros que sumiram do SQLite. Para publicações completas, decidir entre `replace/truncate+insert` por tabela operacional ou manter histórico incremental explicitamente.

## SQL De Ajuste Necessário Para Receber O COLETOR Atual

```sql
CREATE TABLE IF NOT EXISTS tb_scan_runs (
    id                  INTEGER PRIMARY KEY AUTO_INCREMENT,
    scan_type           VARCHAR(50) NOT NULL,
    source_tab          VARCHAR(100),
    status              VARCHAR(30) NOT NULL,
    started_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at         DATETIME NULL,
    total_items         INTEGER DEFAULT 0,
    processed_items     INTEGER DEFAULT 0,
    success_items       INTEGER DEFAULT 0,
    failed_items        INTEGER DEFAULT 0,
    cancelled_items     INTEGER DEFAULT 0,
    selected_count      INTEGER DEFAULT 0,
    notes               TEXT,
    error_message       TEXT,
    INDEX idx_scan_runs_status (status),
    INDEX idx_scan_runs_type (scan_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tb_scan_run_items (
    id                  INTEGER PRIMARY KEY AUTO_INCREMENT,
    run_id              INTEGER NOT NULL,
    item_key            VARCHAR(255) NOT NULL,
    filial              VARCHAR(50),
    ip                  VARCHAR(45),
    device_type         VARCHAR(100),
    status              TEXT NOT NULL,
    action              VARCHAR(100),
    result_ref          VARCHAR(255),
    error_message       TEXT,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_scan_run_item (run_id, item_key),
    INDEX idx_scan_items_run (run_id),
    INDEX idx_scan_items_filial (filial),
    INDEX idx_scan_items_ip (ip),
    CONSTRAINT fk_scan_items_run FOREIGN KEY (run_id) REFERENCES tb_scan_runs(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## Colunas Por Tabela

### `tb_alerts` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `bigint(20)` | NO | `` | PRI | auto_increment |
| `alert_type` | `enum('ERROR','WARNING','INFO','SUCCESS')` | NO | `` | MUL |  |
| `severity` | `enum('LOW','MEDIUM','HIGH','CRITICAL')` | NO | `'MEDIUM'` | MUL |  |
| `title` | `varchar(255)` | NO | `` |  |  |
| `message` | `text` | NO | `` |  |  |
| `script_name` | `varchar(100)` | YES | `NULL` |  |  |
| `scan_id` | `varchar(100)` | YES | `NULL` |  |  |
| `ip` | `varchar(15)` | YES | `NULL` |  |  |
| `java` | `varchar(20)` | YES | `NULL` |  |  |
| `status` | `enum('ACTIVE','ACKNOWLEDGED','RESOLVED','IGNORED')` | NO | `'ACTIVE'` | MUL |  |
| `created_at` | `datetime` | YES | `current_timestamp()` | MUL |  |
| `acknowledged_at` | `datetime` | YES | `NULL` |  |  |
| `acknowledged_by` | `varchar(100)` | YES | `NULL` |  |  |
| `resolved_at` | `datetime` | YES | `NULL` |  |  |
| `resolved_by` | `varchar(100)` | YES | `NULL` |  |  |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_alert_type` (INDEX): `alert_type`
- `idx_alerts_type_status_created` (INDEX): `alert_type`, `status`, `created_at`
- `idx_created_at` (INDEX): `created_at`
- `idx_severity` (INDEX): `severity`
- `idx_status` (INDEX): `status`

Constraints:
- `PRIMARY`: PRIMARY KEY

### `tb_audit_config` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `int(11)` | NO | `` | PRI | auto_increment |
| `config_key` | `varchar(100)` | NO | `` | UNI |  |
| `config_value` | `text` | NO | `` |  |  |
| `description` | `text` | YES | `NULL` |  |  |
| `is_active` | `tinyint(1)` | YES | `1` |  |  |
| `created_at` | `datetime` | YES | `current_timestamp()` |  |  |
| `updated_at` | `datetime` | YES | `current_timestamp()` |  | on update current_timestamp() |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `config_key` (UNIQUE): `config_key`

Constraints:
- `config_key`: UNIQUE
- `PRIMARY`: PRIMARY KEY

### `tb_audit_log` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `bigint(20)` | NO | `` | PRI | auto_increment |
| `timestamp` | `datetime` | NO | `current_timestamp()` | MUL |  |
| `script_name` | `varchar(100)` | NO | `` | MUL |  |
| `script_version` | `varchar(20)` | YES | `NULL` |  |  |
| `level` | `enum('INFO','WARNING','ERROR','CRITICAL')` | NO | `'INFO'` | MUL |  |
| `action` | `varchar(100)` | NO | `` | MUL |  |
| `description` | `text` | YES | `NULL` |  |  |
| `ip` | `varchar(15)` | YES | `NULL` | MUL |  |
| `java` | `varchar(20)` | YES | `NULL` | MUL |  |
| `bandeira` | `varchar(50)` | YES | `NULL` |  |  |
| `status` | `varchar(50)` | YES | `NULL` | MUL |  |
| `duration_ms` | `int(11)` | YES | `NULL` |  |  |
| `user_agent` | `varchar(255)` | YES | `NULL` |  |  |
| `session_id` | `varchar(100)` | YES | `NULL` |  |  |
| `metadata` | `longtext` | YES | `NULL` |  |  |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_action` (INDEX): `action`
- `idx_audit_level_timestamp` (INDEX): `level`, `timestamp`
- `idx_audit_script_timestamp` (INDEX): `script_name`, `timestamp`
- `idx_ip` (INDEX): `ip`
- `idx_java` (INDEX): `java`
- `idx_level` (INDEX): `level`
- `idx_script` (INDEX): `script_name`
- `idx_status` (INDEX): `status`
- `idx_timestamp` (INDEX): `timestamp`

Constraints:
- `metadata`: CHECK
- `PRIMARY`: PRIMARY KEY

### `tb_b12_data_collection_status` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `java` | `varchar(50)` | NO | `` | PRI |  |
| `ip_b12` | `varchar(15)` | NO | `` | PRI |  |
| `nome_filial` | `varchar(100)` | YES | `NULL` |  |  |
| `collection_status` | `varchar(20)` | YES | `NULL` | MUL |  |
| `collection_date` | `datetime` | YES | `NULL` |  |  |
| `collection_duration_seconds` | `int(11)` | YES | `NULL` |  |  |
| `hostname_collected` | `tinyint(1)` | YES | `0` |  |  |
| `hostname_value` | `varchar(100)` | YES | `NULL` |  |  |
| `hostname_raw_collected` | `tinyint(1)` | YES | `0` |  |  |
| `hostname_raw_value` | `varchar(100)` | YES | `NULL` |  |  |
| `os_collected` | `tinyint(1)` | YES | `0` |  |  |
| `os_value` | `varchar(100)` | YES | `NULL` |  |  |
| `os_version_collected` | `tinyint(1)` | YES | `0` |  |  |
| `os_version_value` | `varchar(100)` | YES | `NULL` |  |  |
| `kernel_collected` | `tinyint(1)` | YES | `0` |  |  |
| `kernel_value` | `varchar(100)` | YES | `NULL` |  |  |
| `cidr_collected` | `tinyint(1)` | YES | `0` |  |  |
| `cidr_value` | `varchar(20)` | YES | `NULL` |  |  |
| `cores_collected` | `tinyint(1)` | YES | `0` |  |  |
| `cores_value` | `varchar(50)` | YES | `NULL` |  |  |
| `memory_collected` | `tinyint(1)` | YES | `0` |  |  |
| `memory_value_bytes` | `bigint(20)` | YES | `NULL` |  |  |
| `mac_collected` | `tinyint(1)` | YES | `0` |  |  |
| `mac_value` | `varchar(17)` | YES | `NULL` |  |  |
| `mb_manufacturer_collected` | `tinyint(1)` | YES | `0` |  |  |
| `mb_manufacturer_value` | `varchar(100)` | YES | `NULL` |  |  |
| `mb_product_collected` | `tinyint(1)` | YES | `0` |  |  |
| `mb_product_value` | `varchar(100)` | YES | `NULL` |  |  |
| `mb_version_collected` | `tinyint(1)` | YES | `0` |  |  |
| `mb_version_value` | `varchar(50)` | YES | `NULL` |  |  |
| `disk_media_type_collected` | `tinyint(1)` | YES | `0` |  |  |
| `disk_media_type_value` | `varchar(20)` | YES | `NULL` |  |  |
| `disk_model_collected` | `tinyint(1)` | YES | `0` |  |  |
| `disk_model_value` | `varchar(100)` | YES | `NULL` |  |  |
| `disk_size_collected` | `tinyint(1)` | YES | `0` |  |  |
| `disk_size_value` | `bigint(20)` | YES | `NULL` |  |  |
| `fields_collected_count` | `int(11)` | YES | `0` |  |  |
| `collection_percentage` | `float` | YES | `0` |  |  |
| `updated_at` | `datetime` | YES | `current_timestamp()` | MUL | on update current_timestamp() |

Índices:
- `PRIMARY` (UNIQUE): `java`, `ip_b12`
- `idx_collection_status` (INDEX): `collection_status`
- `idx_ip_b12` (INDEX): `ip_b12`
- `idx_updated_at` (INDEX): `updated_at`

Constraints:
- `PRIMARY`: PRIMARY KEY

### `tb_detected_devices` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `int(11)` | NO | `` | PRI | auto_increment |
| `filial` | `varchar(10)` | YES | `NULL` | MUL |  |
| `ip` | `varchar(15)` | NO | `` | UNI |  |
| `expected_type` | `varchar(20)` | YES | `NULL` | MUL |  |
| `device_type` | `varchar(50)` | YES | `NULL` | MUL |  |
| `logo` | `varchar(20)` | YES | `NULL` | MUL |  |
| `ssh` | `tinyint(1)` | YES | `0` |  |  |
| `radmin` | `tinyint(1)` | YES | `0` |  |  |
| `printer` | `tinyint(1)` | YES | `0` |  |  |
| `detected_at` | `datetime` | YES | `current_timestamp()` | MUL |  |
| `hw_hostname` | `varchar(100)` | YES | `NULL` |  |  |
| `hw_cpu_model` | `varchar(200)` | YES | `NULL` |  |  |
| `hw_cores` | `int(11)` | YES | `NULL` |  |  |
| `hw_ram_gb` | `float` | YES | `NULL` |  |  |
| `hw_disk_gb` | `float` | YES | `NULL` |  |  |
| `hw_os` | `varchar(100)` | YES | `NULL` |  |  |
| `hw_os_version` | `varchar(100)` | YES | `NULL` |  |  |
| `hw_kernel` | `varchar(100)` | YES | `NULL` |  |  |
| `hw_cores_fisicos` | `varchar(50)` | YES | `NULL` |  |  |
| `hw_memoria_total` | `bigint(20)` | YES | `NULL` |  |  |
| `hw_mac_address` | `varchar(17)` | YES | `NULL` |  |  |
| `hw_mb_manufacturer` | `varchar(100)` | YES | `NULL` |  |  |
| `hw_mb_product_name` | `varchar(100)` | YES | `NULL` |  |  |
| `hw_mb_version` | `varchar(50)` | YES | `NULL` |  |  |
| `hw_hdd_media_type` | `varchar(20)` | YES | `NULL` |  |  |
| `hw_hdd_model` | `varchar(100)` | YES | `NULL` |  |  |
| `hw_hdd_size` | `bigint(20)` | YES | `NULL` |  |  |
| `hw_scanned_at` | `datetime` | YES | `NULL` | MUL |  |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_detected_at` (INDEX): `detected_at`
- `idx_device_type` (INDEX): `device_type`
- `idx_expected_type` (INDEX): `expected_type`
- `idx_filial` (INDEX): `filial`
- `idx_hw_scanned_at` (INDEX): `hw_scanned_at`
- `idx_ip_unique` (UNIQUE): `ip`
- `idx_logo` (INDEX): `logo`

Constraints:
- `idx_ip_unique`: UNIQUE
- `PRIMARY`: PRIMARY KEY

### `tb_devices` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `job_id` | `int(11)` | NO | `` | PRI | auto_increment |
| `java` | `int(11)` | YES | `0` | MUL |  |
| `ip` | `varchar(15)` | NO | `` | MUL |  |
| `device_id` | `varchar(50)` | YES | `''` | MUL |  |
| `device_name` | `varchar(255)` | YES | `''` |  |  |
| `device_description` | `text` | YES | `''` |  |  |
| `scan_date` | `datetime` | YES | `current_timestamp()` | MUL |  |
| `hostname` | `varchar(255)` | YES | `''` |  |  |
| `groupname` | `varchar(255)` | YES | `''` |  |  |
| `bandeira` | `varchar(255)` | YES | `''` |  |  |
| `cpu` | `varchar(255)` | YES | `''` |  |  |
| `cores` | `int(11)` | YES | `0` |  |  |
| `ram_gb` | `float` | YES | `0` |  |  |
| `disk_gb` | `float` | YES | `0` |  |  |
| `os` | `varchar(255)` | YES | `''` |  |  |
| `os_version` | `varchar(100)` | YES | `''` |  |  |
| `tcprinterservice` | `text` | YES | `NULL` |  |  |
| `tcscannerservice` | `text` | YES | `NULL` |  |  |
| `tcbiometriaservice` | `text` | YES | `NULL` |  |  |
| `tccontroladosprinterservice` | `text` | YES | `NULL` |  |  |
| `detail_job_id` | `varchar(50)` | YES | `NULL` |  |  |

Índices:
- `PRIMARY` (UNIQUE): `job_id`
- `idx_device_id` (INDEX): `device_id`
- `idx_ip` (INDEX): `ip`
- `idx_java` (INDEX): `java`
- `idx_scan_date` (INDEX): `scan_date`

Constraints:
- `java`: CHECK
- `PRIMARY`: PRIMARY KEY

### `tb_devices_catalog` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `device_id` | `varchar(255)` | NO | `` | PRI |  |
| `device_name` | `varchar(255)` | NO | `` | PRI |  |

Índices:
- `PRIMARY` (UNIQUE): `device_id`, `device_name`

Constraints:
- `PRIMARY`: PRIMARY KEY

### `tb_devices_detail` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `detail_job_id` | `varchar(50)` | YES | `NULL` |  |  |
| `java` | `varchar(50)` | NO | `` |  |  |
| `ip` | `varchar(15)` | NO | `` | PRI |  |
| `hostname` | `varchar(100)` | NO | `` |  |  |
| `tipo_equipamento` | `varchar(20)` | NO | `` | MUL |  |
| `sistema_operacional` | `varchar(100)` | NO | `` |  |  |
| `kernel` | `varchar(100)` | NO | `''` |  |  |
| `cores_fisicos` | `varchar(50)` | NO | `` |  |  |
| `memoria_total` | `bigint(20)` | NO | `` |  |  |
| `mac_address` | `varchar(17)` | YES | `NULL` |  |  |
| `mb_manufacturer` | `varchar(100)` | YES | `NULL` |  |  |
| `mb_product_name` | `varchar(100)` | YES | `NULL` |  |  |
| `mb_version` | `varchar(50)` | YES | `NULL` |  |  |
| `hdd_media_type` | `varchar(50)` | YES | `NULL` |  |  |
| `hdd_model` | `varchar(100)` | YES | `NULL` |  |  |
| `hdd_size` | `bigint(20)` | YES | `NULL` |  |  |
| `data_coleta` | `datetime` | NO | `current_timestamp()` | MUL |  |
| `data_atualizacao` | `datetime` | YES | `NULL` |  |  |

Índices:
- `PRIMARY` (UNIQUE): `ip`
- `idx_data_coleta` (INDEX): `data_coleta`
- `idx_ip_unique` (UNIQUE): `ip`
- `idx_tipo_equipamento` (INDEX): `tipo_equipamento`
- `ip` (UNIQUE): `ip`

Constraints:
- `idx_ip_unique`: UNIQUE
- `ip`: UNIQUE
- `PRIMARY`: PRIMARY KEY

### `tb_devices_detail_log` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `int(11)` | NO | `` | PRI | auto_increment |
| `data_scan` | `datetime` | NO | `` | MUL |  |
| `detail_job_id` | `varchar(50)` | YES | `NULL` |  |  |
| `java` | `varchar(10)` | YES | `NULL` | MUL |  |
| `ip` | `varchar(15)` | NO | `` | MUL |  |
| `hostname` | `varchar(100)` | YES | `NULL` |  |  |
| `tipo_equipamento` | `varchar(50)` | YES | `NULL` |  |  |
| `status` | `enum('success','auth_failed','auth_user_invalid','auth_password_invalid','connection_timeout','connection_refused','no_route','port_closed','ssh_auth_failed','ssh_timeout','ssh_command_failed','wmi_not_available','wmi_auth_failed','wmi_timeout','wmi_query_failed','snmp_no_response','snmp_timeout','snmp_community_invalid','snmp_oid_not_found','data_collection_failed','hardware_info_missing','database_insert_failed','unknown')` | NO | `'unknown'` | MUL |  |
| `mensagem` | `text` | YES | `NULL` |  |  |
| `error_type` | `enum('success','auth_failed','auth_user_invalid','auth_password_invalid','connection_timeout','connection_refused','no_route','port_closed','ssh_auth_failed','ssh_timeout','ssh_command_failed','wmi_not_available','wmi_auth_failed','wmi_timeout','wmi_query_failed','snmp_no_response','snmp_timeout','snmp_community_invalid','snmp_oid_not_found','data_collection_failed','hardware_info_missing','database_insert_failed','unknown')` | YES | `NULL` | MUL |  |
| `error_code` | `varchar(50)` | YES | `NULL` |  |  |
| `error_details` | `text` | YES | `NULL` |  |  |
| `protocol_used` | `enum('SSH','WMI','SNMP','MIXED')` | YES | `NULL` | MUL |  |
| `attempt_number` | `int(11)` | YES | `1` |  |  |
| `last_success_scan` | `datetime` | YES | `NULL` | MUL |  |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_data_scan` (INDEX): `data_scan`
- `idx_error_type` (INDEX): `error_type`
- `idx_ip` (INDEX): `ip`
- `idx_ip_data_scan` (INDEX): `ip`, `data_scan`
- `idx_java_ip_error` (INDEX): `java`, `ip`, `error_type`
- `idx_last_success_scan` (INDEX): `last_success_scan`
- `idx_protocol_used` (INDEX): `protocol_used`
- `idx_status` (INDEX): `status`
- `idx_status_error_type` (INDEX): `status`, `error_type`

Constraints:
- `PRIMARY`: PRIMARY KEY

### `tb_filial` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `int(11)` | NO | `` | PRI | auto_increment |
| `filial` | `varchar(10)` | NO | `` | UNI |  |
| `historico` | `varchar(10)` | NO | `` |  |  |
| `nome_filial` | `varchar(100)` | NO | `` | MUL |  |
| `data_inauguracao` | `date` | YES | `NULL` |  |  |
| `inscricao_estadual` | `varchar(20)` | YES | `NULL` |  |  |
| `cnpj` | `varchar(20)` | YES | `NULL` |  |  |
| `endereco` | `varchar(200)` | NO | `` |  |  |
| `bairro` | `varchar(100)` | NO | `` |  |  |
| `cidade` | `varchar(100)` | NO | `` | MUL |  |
| `uf` | `char(2)` | NO | `` | MUL |  |
| `regiao` | `varchar(50)` | NO | `` | MUL |  |
| `logomarca` | `varchar(20)` | NO | `` | MUL |  |
| `telefone` | `varchar(30)` | YES | `NULL` |  |  |
| `ip_banco_12` | `varchar(15)` | YES | `NULL` | MUL |  |
| `cidr` | `varchar(20)` | YES | `NULL` | MUL |  |
| `data_criacao` | `timestamp` | YES | `current_timestamp()` |  |  |
| `data_atualizacao` | `timestamp` | YES | `current_timestamp()` |  | on update current_timestamp() |
| `ativo` | `tinyint(1)` | YES | `1` | MUL |  |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_ativo` (INDEX): `ativo`
- `idx_cidade` (INDEX): `cidade`
- `idx_filial` (UNIQUE): `filial`
- `idx_filial_cidr` (INDEX): `cidr`
- `idx_ip_banco_12` (INDEX): `ip_banco_12`
- `idx_logomarca` (INDEX): `logomarca`
- `idx_nome_filial` (INDEX): `nome_filial`
- `idx_regiao` (INDEX): `regiao`
- `idx_uf` (INDEX): `uf`

Constraints:
- `idx_filial`: UNIQUE
- `PRIMARY`: PRIMARY KEY

### `tb_hardware_historico` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `bigint(20)` | NO | `` | PRI | auto_increment |
| `job_id` | `varchar(50)` | NO | `` | MUL |  |
| `java` | `varchar(50)` | NO | `` |  |  |
| `ip` | `varchar(15)` | NO | `` |  |  |
| `hostname` | `varchar(100)` | NO | `` |  |  |
| `tipo_equipamento` | `varchar(20)` | NO | `` |  |  |
| `sistema_operacional` | `varchar(100)` | NO | `` |  |  |
| `kernel` | `varchar(100)` | NO | `` |  |  |
| `cores_fisicos` | `varchar(50)` | NO | `` |  |  |
| `memoria_total` | `bigint(20)` | NO | `` |  |  |
| `mac_address` | `varchar(17)` | NO | `` |  |  |
| `mb_manufacturer` | `varchar(100)` | YES | `NULL` |  |  |
| `mb_product_name` | `varchar(100)` | YES | `NULL` |  |  |
| `mb_version` | `varchar(50)` | YES | `NULL` |  |  |
| `hdd_media_type` | `varchar(50)` | YES | `NULL` |  |  |
| `hdd_model` | `varchar(100)` | YES | `NULL` |  |  |
| `hdd_size` | `bigint(20)` | YES | `NULL` |  |  |
| `data_coleta` | `datetime` | NO | `` |  |  |
| `data_atualizacao` | `datetime` | NO | `current_timestamp()` |  |  |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_job_id` (INDEX): `job_id`

Constraints:
- `PRIMARY`: PRIMARY KEY

### `tb_log_execucao` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `bigint(20)` | NO | `` | PRI | auto_increment |
| `data_inicio` | `datetime` | YES | `NULL` | MUL |  |
| `data_fim` | `datetime` | YES | `NULL` |  |  |
| `tipo_scan` | `varchar(50)` | YES | `NULL` | MUL |  |
| `status` | `varchar(50)` | YES | `NULL` |  |  |
| `mensagem` | `text` | YES | `NULL` |  |  |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_data` (INDEX): `data_inicio`
- `idx_tipo` (INDEX): `tipo_scan`

Constraints:
- `PRIMARY`: PRIMARY KEY

### `tb_network_ips` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `int(11)` | NO | `` | PRI | auto_increment |
| `ip` | `varchar(15)` | NO | `` | UNI |  |
| `is_active` | `tinyint(1)` | YES | `0` |  |  |
| `last_seen` | `timestamp` | YES | `NULL` | MUL |  |
| `port_22` | `tinyint(1)` | YES | `NULL` |  |  |
| `port_80` | `tinyint(1)` | YES | `NULL` |  |  |
| `port_135` | `tinyint(1)` | YES | `NULL` |  |  |
| `port_443` | `tinyint(1)` | YES | `NULL` |  |  |
| `port_445` | `tinyint(1)` | YES | `NULL` |  |  |
| `port_161` | `tinyint(1)` | YES | `NULL` |  |  |
| `port_7856` | `tinyint(1)` | YES | `NULL` |  |  |
| `hostname` | `varchar(255)` | YES | `NULL` |  |  |
| `os_info` | `text` | YES | `NULL` |  |  |
| `device_type` | `enum('router','switch','server','printer','workstation','unknown')` | YES | `'unknown'` | MUL |  |
| `snmp_community` | `varchar(50)` | YES | `NULL` |  |  |
| `subnet_id` | `int(11)` | YES | `NULL` | MUL |  |
| `created_at` | `timestamp` | YES | `current_timestamp()` |  |  |
| `updated_at` | `timestamp` | YES | `current_timestamp()` |  | on update current_timestamp() |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_device_type` (INDEX): `device_type`
- `idx_last_seen` (INDEX): `last_seen`
- `subnet_id` (INDEX): `subnet_id`
- `unique_ip` (UNIQUE): `ip`

Constraints:
- `PRIMARY`: PRIMARY KEY
- `tb_network_ips_ibfk_1`: FOREIGN KEY
- `unique_ip`: UNIQUE

### `tb_network_ports` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `int(11)` | NO | `` | PRI | auto_increment |
| `network_id` | `int(11)` | NO | `` | MUL |  |
| `ip` | `varchar(15)` | NO | `` |  |  |
| `ssh_open` | `tinyint(1)` | YES | `0` |  |  |
| `radmin_open` | `tinyint(1)` | YES | `0` |  |  |
| `snmp_open` | `tinyint(1)` | YES | `0` |  |  |
| `java` | `varchar(10)` | YES | `NULL` |  |  |
| `last_scan` | `datetime` | YES | `current_timestamp()` |  |  |
| `status_scan_hardware` | `enum('PENDING','PROCESSING','SUCCESS','ERROR','OFFLINE','FAILED','SKIPPED')` | NO | `'PENDING'` | MUL |  |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_status_scan_hardware` (INDEX): `status_scan_hardware`
- `idx_status_scan_java` (INDEX): `status_scan_hardware`, `java`
- `unique_ip` (UNIQUE): `network_id`, `ip`

Constraints:
- `PRIMARY`: PRIMARY KEY
- `unique_ip`: UNIQUE

### `tb_network_ports_backup_20251211` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `int(11)` | NO | `0` |  |  |
| `network_id` | `int(11)` | NO | `` |  |  |
| `ip` | `varchar(15)` | NO | `` |  |  |
| `ssh_open` | `tinyint(1)` | YES | `0` |  |  |
| `radmin_open` | `tinyint(1)` | YES | `0` |  |  |
| `snmp_open` | `tinyint(1)` | YES | `0` |  |  |
| `java` | `varchar(10)` | YES | `NULL` |  |  |
| `last_scan` | `datetime` | YES | `current_timestamp()` |  |  |
| `status_scan_hardware` | `varchar(20)` | YES | `'pending'` |  |  |

### `tb_network_subnets` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `int(11)` | NO | `0` | PRI |  |
| `subnet_ip` | `varchar(15)` | NO | `` |  |  |
| `b12_ip` | `varchar(15)` | NO | `` | MUL |  |
| `ultima_verificacao` | `datetime` | YES | `NULL` |  |  |
| `scan_status` | `enum('PENDING','PROCESSING','SUCCESS','FAILED','SKIPPED')` | YES | `'PENDING'` | MUL |  |
| `last_scan` | `timestamp` | YES | `NULL` |  |  |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_b12_ip` (INDEX): `b12_ip`
- `idx_scan_status` (INDEX): `scan_status`

Constraints:
- `PRIMARY`: PRIMARY KEY

### `tb_network_subnets_type` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `int(11)` | NO | `0` |  |  |
| `subnet_ip` | `varchar(15)` | NO | `` |  |  |
| `b12_ip` | `varchar(15)` | NO | `` | MUL |  |
| `net_type` | `enum('nao_verificada','plana','segmentada','desconectada')` | NO | `'nao_verificada'` | MUL |  |
| `hostname` | `varchar(255)` | YES | `NULL` |  |  |
| `hostname_raw` | `varchar(255)` | YES | `NULL` |  |  |
| `os_info` | `varchar(255)` | YES | `NULL` |  |  |
| `java` | `varchar(10)` | YES | `NULL` |  |  |
| `version_id` | `varchar(50)` | YES | `NULL` |  |  |
| `ssh_status` | `varchar(255)` | YES | `NULL` |  |  |
| `data_registro` | `datetime` | YES | `current_timestamp()` |  |  |
| `cidr` | `varchar(20)` | YES | `NULL` | MUL |  |
| `bandeira` | `varchar(50)` | YES | `NULL` | MUL |  |
| `filial` | `varchar(10)` | YES | `NULL` | MUL |  |
| `usuario` | `varchar(50)` | YES | `NULL` |  |  |
| `nome_maquina` | `varchar(100)` | YES | `NULL` |  |  |
| `terminal` | `varchar(20)` | YES | `NULL` |  |  |
| `imagem_so` | `varchar(100)` | YES | `NULL` |  |  |
| `tipo` | `varchar(20)` | YES | `NULL` |  |  |
| `script2_processado` | `datetime` | YES | `NULL` |  |  |
| `script3_processado` | `datetime` | YES | `NULL` |  |  |
| `ssh_error_type` | `enum('success','auth_failed','auth_user_invalid','auth_password_invalid','timeout','connection_refused','no_route','port_closed','unknown')` | YES | `NULL` | MUL |  |
| `ssh_error_message` | `text` | YES | `NULL` |  |  |
| `ssh_error_timestamp` | `datetime` | YES | `NULL` | MUL |  |
| `ssh_last_success` | `datetime` | YES | `NULL` | MUL |  |
| `script2_status` | `enum('PENDING','PROCESSING','SUCCESS','FAILED','SKIPPED')` | YES | `'PENDING'` | MUL |  |
| `script3_status` | `enum('PENDING','PROCESSING','SUCCESS','FAILED','SKIPPED')` | YES | `'PENDING'` | MUL |  |

Índices:
- `idx_b12_data` (INDEX): `b12_ip`, `data_registro`
- `idx_bandeira` (INDEX): `bandeira`
- `idx_cidr` (INDEX): `cidr`
- `idx_filial` (INDEX): `filial`
- `idx_net_type` (INDEX): `net_type`
- `idx_script2_status` (INDEX): `script2_status`
- `idx_script3_status` (INDEX): `script3_status`
- `idx_ssh_error_timestamp` (INDEX): `ssh_error_timestamp`
- `idx_ssh_error_type` (INDEX): `ssh_error_type`
- `idx_ssh_last_success` (INDEX): `ssh_last_success`

### `tb_performance_metrics` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `bigint(20)` | NO | `` | PRI | auto_increment |
| `script_name` | `varchar(100)` | NO | `` | MUL |  |
| `metric_name` | `varchar(100)` | NO | `` | MUL |  |
| `metric_value` | `decimal(15,4)` | NO | `` |  |  |
| `metric_unit` | `varchar(20)` | YES | `NULL` |  |  |
| `timestamp` | `datetime` | NO | `current_timestamp()` | MUL |  |
| `context` | `longtext` | YES | `NULL` |  |  |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_metric` (INDEX): `metric_name`
- `idx_script` (INDEX): `script_name`
- `idx_timestamp` (INDEX): `timestamp`

Constraints:
- `context`: CHECK
- `PRIMARY`: PRIMARY KEY

### `tb_scan_control` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `scan_id` | `int(11)` | NO | `` | PRI | auto_increment |
| `java` | `varchar(255)` | NO | `` |  |  |
| `bandeira` | `varchar(255)` | YES | `''` |  |  |
| `ip` | `varchar(15)` | YES | `''` |  |  |
| `start_time` | `datetime` | NO | `` |  |  |
| `end_time` | `datetime` | YES | `current_timestamp()` |  |  |
| `status` | `enum('PENDING','PROCESSING','SUCCESS','FAILED')` | YES | `'PENDING'` |  |  |
| `attempts` | `int(11)` | YES | `0` |  |  |
| `last_attempt` | `datetime` | YES | `current_timestamp()` |  |  |

Índices:
- `PRIMARY` (UNIQUE): `scan_id`

Constraints:
- `PRIMARY`: PRIMARY KEY

### `tb_scan_control_backup_20251211` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `scan_id` | `int(11)` | NO | `0` |  |  |
| `java` | `varchar(255)` | NO | `` |  |  |
| `bandeira` | `varchar(255)` | YES | `''` |  |  |
| `ip` | `varchar(15)` | YES | `''` |  |  |
| `start_time` | `datetime` | NO | `` |  |  |
| `end_time` | `datetime` | YES | `current_timestamp()` |  |  |
| `status` | `enum('Pendente','Em Andamento','Conclu�do','Falhou')` | YES | `'Pendente'` |  |  |
| `attempts` | `int(11)` | YES | `0` |  |  |
| `last_attempt` | `datetime` | YES | `current_timestamp()` |  |  |

### `tb_scan_details` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `bigint(20)` | NO | `` | PRI | auto_increment |
| `scan_id` | `varchar(100)` | NO | `` | MUL |  |
| `item_type` | `enum('IP','NETWORK','DEVICE','PORT')` | NO | `` | MUL |  |
| `item_identifier` | `varchar(255)` | NO | `` | MUL |  |
| `status` | `enum('PENDING','PROCESSING','SUCCESS','FAILED','SKIPPED')` | NO | `'PENDING'` | MUL |  |
| `start_time` | `datetime` | YES | `NULL` |  |  |
| `end_time` | `datetime` | YES | `NULL` |  |  |
| `duration_ms` | `int(11)` | YES | `NULL` |  |  |
| `error_message` | `text` | YES | `NULL` |  |  |
| `result_data` | `longtext` | YES | `NULL` |  |  |
| `attempts` | `int(11)` | YES | `0` |  |  |
| `max_attempts` | `int(11)` | YES | `3` |  |  |
| `created_at` | `datetime` | YES | `current_timestamp()` |  |  |
| `updated_at` | `datetime` | YES | `current_timestamp()` |  | on update current_timestamp() |
| `last_heartbeat` | `datetime` | YES | `NULL` | MUL |  |
| `hostname` | `varchar(255)` | YES | `NULL` |  |  |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_heartbeat` (INDEX): `last_heartbeat`
- `idx_identifier` (INDEX): `item_identifier`
- `idx_item_type` (INDEX): `item_type`
- `idx_item_type_status` (INDEX): `item_type`, `status`
- `idx_scan_details_scan_status` (INDEX): `scan_id`, `status`
- `idx_scan_id` (INDEX): `scan_id`
- `idx_scan_status_attempts` (INDEX): `scan_id`, `status`, `attempts`
- `idx_status` (INDEX): `status`
- `idx_status_attempts` (INDEX): `status`, `attempts`

Constraints:
- `PRIMARY`: PRIMARY KEY
- `result_data`: CHECK
- `tb_scan_details_ibfk_1`: FOREIGN KEY

### `tb_scan_java_log` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `int(11)` | NO | `` | PRI | auto_increment |
| `ip` | `varchar(15)` | NO | `` | MUL |  |
| `java` | `varchar(50)` | NO | `` |  |  |
| `bandeira` | `varchar(50)` | NO | `` |  |  |
| `status` | `enum('PENDING','PROCESSING','SUCCESS','FAILED','SKIPPED')` | YES | `'PENDING'` | MUL |  |
| `attempts` | `int(11)` | YES | `1` |  |  |
| `start_time` | `timestamp` | YES | `NULL` |  |  |
| `end_time` | `timestamp` | YES | `NULL` |  |  |
| `created_at` | `timestamp` | YES | `current_timestamp()` |  |  |
| `updated_at` | `timestamp` | YES | `current_timestamp()` |  | on update current_timestamp() |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_status_java` (INDEX): `status`, `java`
- `unique_ip_java` (UNIQUE): `ip`, `java`

Constraints:
- `PRIMARY`: PRIMARY KEY
- `unique_ip_java`: UNIQUE

### `tb_scan_status` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `bigint(20)` | NO | `` | PRI | auto_increment |
| `scan_id` | `varchar(100)` | NO | `` | UNI |  |
| `script_name` | `varchar(100)` | NO | `` | MUL |  |
| `start_time` | `datetime` | NO | `` | MUL |  |
| `end_time` | `datetime` | YES | `NULL` |  |  |
| `status` | `enum('STARTED','PROCESSING','SUCCESS','FAILED','CANCELLED')` | YES | `'STARTED'` |  |  |
| `total_items` | `int(11)` | YES | `0` |  |  |
| `processed_items` | `int(11)` | YES | `0` |  |  |
| `failed_items` | `int(11)` | YES | `0` |  |  |
| `success_rate` | `decimal(5,2)` | YES | `0.00` |  |  |
| `error_message` | `text` | YES | `NULL` |  |  |
| `parameters` | `longtext` | YES | `NULL` |  |  |
| `progress_percentage` | `decimal(5,2)` | YES | `0.00` |  |  |
| `estimated_completion` | `datetime` | YES | `NULL` |  |  |
| `created_at` | `datetime` | YES | `current_timestamp()` |  |  |
| `updated_at` | `datetime` | YES | `current_timestamp()` |  | on update current_timestamp() |
| `process_pid` | `int(11)` | YES | `NULL` |  |  |
| `server_hostname` | `varchar(255)` | YES | `NULL` |  |  |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_scan_id` (INDEX): `scan_id`
- `idx_scan_status_script_start` (INDEX): `script_name`, `start_time`
- `idx_script` (INDEX): `script_name`
- `idx_start_time` (INDEX): `start_time`
- `idx_status_start` (INDEX): `start_time`
- `scan_id` (UNIQUE): `scan_id`

Constraints:
- `parameters`: CHECK
- `PRIMARY`: PRIMARY KEY
- `scan_id`: UNIQUE

### `tb_scan_status_backup_20251211` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `bigint(20)` | NO | `0` |  |  |
| `scan_id` | `varchar(100)` | NO | `` |  |  |
| `script_name` | `varchar(100)` | NO | `` |  |  |
| `start_time` | `datetime` | NO | `` |  |  |
| `end_time` | `datetime` | YES | `NULL` |  |  |
| `status` | `enum('INICIADO','EM_ANDAMENTO','CONCLUIDO','FALHOU','CANCELADO')` | NO | `'INICIADO'` |  |  |
| `total_items` | `int(11)` | YES | `0` |  |  |
| `processed_items` | `int(11)` | YES | `0` |  |  |
| `failed_items` | `int(11)` | YES | `0` |  |  |
| `success_rate` | `decimal(5,2)` | YES | `0.00` |  |  |
| `error_message` | `text` | YES | `NULL` |  |  |
| `parameters` | `longtext` | YES | `NULL` |  |  |
| `progress_percentage` | `decimal(5,2)` | YES | `0.00` |  |  |
| `estimated_completion` | `datetime` | YES | `NULL` |  |  |
| `created_at` | `datetime` | YES | `current_timestamp()` |  |  |
| `updated_at` | `datetime` | YES | `current_timestamp()` |  | on update current_timestamp() |
| `process_pid` | `int(11)` | YES | `NULL` |  |  |
| `server_hostname` | `varchar(255)` | YES | `NULL` |  |  |

Constraints:
- `parameters`: CHECK

### `tb_usb_devices` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `vendor_id` | `varchar(10)` | NO | `` | PRI |  |
| `product_id` | `varchar(10)` | NO | `` | PRI |  |
| `manufacturer_name` | `varchar(255)` | YES | `NULL` |  |  |
| `product_description` | `varchar(255)` | YES | `NULL` |  |  |
| `device_id` | `varchar(21)` | YES | `NULL` |  | STORED GENERATED |

Índices:
- `PRIMARY` (UNIQUE): `vendor_id`, `product_id`

Constraints:
- `PRIMARY`: PRIMARY KEY

### `tb_vpn_monitor` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `int(11)` | NO | `` | PRI | auto_increment |
| `ping_time` | `datetime` | YES | `NULL` | MUL |  |
| `ping_status` | `varchar(10)` | YES | `NULL` | MUL |  |
| `interface_status` | `varchar(10)` | YES | `NULL` | MUL |  |
| `interface_name` | `varchar(50)` | YES | `NULL` |  |  |
| `target_ip` | `varchar(15)` | NO | `'10.1.1.140'` | MUL |  |
| `monitor_active` | `tinyint(1)` | YES | `0` | MUL |  |
| `bytes_sent` | `bigint(20)` | YES | `NULL` |  |  |
| `bytes_recv` | `bigint(20)` | YES | `NULL` |  |  |
| `total_bytes` | `bigint(20)` | YES | `NULL` |  |  |
| `bytes_sent_delta` | `bigint(20)` | YES | `0` |  |  |
| `bytes_recv_delta` | `bigint(20)` | YES | `0` |  |  |
| `total_bytes_delta` | `bigint(20)` | YES | `0` |  |  |
| `created_at` | `timestamp` | YES | `current_timestamp()` |  |  |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_interface_status` (INDEX): `interface_status`
- `idx_monitor_active` (INDEX): `monitor_active`
- `idx_ping_status` (INDEX): `ping_status`
- `idx_ping_time` (INDEX): `ping_time`
- `idx_target_ip` (INDEX): `target_ip`

Constraints:
- `PRIMARY`: PRIMARY KEY

### `tb_vpn_status` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `int(11)` | NO | `1` | PRI |  |
| `ping_status` | `enum('UP','DOWN')` | NO | `'DOWN'` |  |  |
| `interface_status` | `enum('UP','DOWN','NOT_FOUND')` | NO | `'DOWN'` |  |  |
| `last_ping_time` | `datetime` | YES | `NULL` |  |  |
| `last_update` | `timestamp` | YES | `current_timestamp()` |  | on update current_timestamp() |
| `monitor_active` | `tinyint(1)` | YES | `0` |  |  |
| `error_count` | `int(11)` | YES | `0` |  |  |
| `last_error` | `text` | YES | `NULL` |  |  |

Índices:
- `PRIMARY` (UNIQUE): `id`

Constraints:
- `chk_single_row`: CHECK
- `PRIMARY`: PRIMARY KEY

### `tb_web_access_log` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `bigint(20) unsigned` | NO | `` | PRI | auto_increment |
| `user_id` | `int(10) unsigned` | YES | `NULL` | MUL |  |
| `username` | `varchar(64)` | YES | `NULL` | MUL |  |
| `ip` | `varchar(64)` | YES | `NULL` |  |  |
| `user_agent` | `varchar(255)` | YES | `NULL` |  |  |
| `action` | `varchar(64)` | NO | `` |  |  |
| `success` | `tinyint(1)` | NO | `0` |  |  |
| `details` | `varchar(255)` | YES | `NULL` |  |  |
| `path` | `varchar(255)` | YES | `NULL` |  |  |
| `created_at` | `datetime` | NO | `current_timestamp()` | MUL |  |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_access_created_at` (INDEX): `created_at`
- `idx_access_user_id` (INDEX): `user_id`
- `idx_access_username` (INDEX): `username`

Constraints:
- `fk_access_user`: FOREIGN KEY
- `PRIMARY`: PRIMARY KEY

### `tb_web_users` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `int(10) unsigned` | NO | `` | PRI | auto_increment |
| `username` | `varchar(64)` | NO | `` | UNI |  |
| `password_hash` | `varchar(255)` | NO | `` |  |  |
| `role` | `varchar(32)` | NO | `'user'` |  |  |
| `active` | `tinyint(1)` | NO | `1` |  |  |
| `created_at` | `datetime` | NO | `current_timestamp()` |  |  |
| `updated_at` | `datetime` | YES | `NULL` |  | on update current_timestamp() |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `uq_web_users_username` (UNIQUE): `username`

Constraints:
- `PRIMARY`: PRIMARY KEY
- `uq_web_users_username`: UNIQUE

### `tb_web_user_page_permissions` (BASE TABLE)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `bigint(20) unsigned` | NO | `` | PRI | auto_increment |
| `user_id` | `int(10) unsigned` | NO | `` | MUL |  |
| `page` | `varchar(64)` | NO | `` |  |  |
| `allowed` | `tinyint(1)` | NO | `0` |  |  |
| `created_at` | `datetime` | NO | `current_timestamp()` |  |  |
| `updated_at` | `datetime` | YES | `NULL` |  | on update current_timestamp() |

Índices:
- `PRIMARY` (UNIQUE): `id`
- `idx_user_id` (INDEX): `user_id`
- `uq_user_page` (UNIQUE): `user_id`, `page`

Constraints:
- `fk_perm_user`: FOREIGN KEY
- `PRIMARY`: PRIMARY KEY
- `uq_user_page`: UNIQUE

### `cs_devices` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `java` | `int(11)` | YES | `0` |  |  |
| `ip` | `varchar(15)` | NO | `` |  |  |
| `device_id` | `varchar(255)` | NO | `` |  |  |
| `device_name` | `varchar(255)` | YES | `''` |  |  |
| `hostname` | `varchar(255)` | YES | `''` |  |  |
| `groupname` | `varchar(255)` | YES | `''` |  |  |
| `bandeira` | `varchar(255)` | YES | `''` |  |  |
| `cpu` | `varchar(255)` | YES | `''` |  |  |
| `cores` | `int(11)` | YES | `0` |  |  |
| `ram_gb` | `float` | YES | `0` |  |  |
| `disk_gb` | `float` | YES | `0` |  |  |
| `os` | `varchar(255)` | YES | `''` |  |  |
| `os_version` | `varchar(100)` | YES | `''` |  |  |
| `scan_date` | `datetime` | YES | `current_timestamp()` |  |  |

### `cs_scan_control` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `scan_id` | `int(11)` | NO | `0` |  |  |
| `java` | `varchar(255)` | NO | `` |  |  |
| `bandeira` | `varchar(255)` | YES | `''` |  |  |
| `ip` | `varchar(15)` | YES | `''` |  |  |
| `start_time` | `datetime` | NO | `` |  |  |
| `end_time` | `datetime` | YES | `current_timestamp()` |  |  |
| `status` | `enum('PENDING','PROCESSING','SUCCESS','FAILED')` | YES | `'PENDING'` |  |  |
| `attempts` | `int(11)` | YES | `0` |  |  |
| `last_attempt` | `datetime` | YES | `current_timestamp()` |  |  |

### `cs_service` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `java` | `int(11)` | YES | `0` |  |  |
| `ip` | `varchar(15)` | NO | `` |  |  |
| `device_id` | `varchar(255)` | NO | `` |  |  |
| `device_name` | `varchar(255)` | YES | `''` |  |  |
| `hostname` | `varchar(255)` | YES | `''` |  |  |
| `groupname` | `varchar(255)` | YES | `''` |  |  |
| `bandeira` | `varchar(255)` | YES | `''` |  |  |
| `cpu` | `varchar(255)` | YES | `''` |  |  |
| `cores` | `int(11)` | YES | `0` |  |  |
| `ram_gb` | `float` | YES | `0` |  |  |
| `disk_gb` | `float` | YES | `0` |  |  |
| `os` | `varchar(255)` | YES | `''` |  |  |
| `os_version` | `varchar(100)` | YES | `''` |  |  |
| `scan_date` | `datetime` | YES | `current_timestamp()` |  |  |
| `tcprinterservice` | `text` | YES | `NULL` |  |  |
| `tcscannerservice` | `text` | YES | `NULL` |  |  |
| `tcbiometriaservice` | `text` | YES | `NULL` |  |  |
| `tccontroladosprinterservice` | `text` | YES | `NULL` |  |  |

### `cs_service3` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `java` | `int(11)` | YES | `0` |  |  |
| `ip` | `varchar(15)` | NO | `` |  |  |
| `device_id` | `varchar(255)` | NO | `` |  |  |
| `device_name` | `varchar(255)` | YES | `''` |  |  |
| `hostname` | `varchar(255)` | YES | `''` |  |  |
| `groupname` | `varchar(255)` | YES | `''` |  |  |
| `bandeira` | `varchar(255)` | YES | `''` |  |  |
| `tcprinterservice` | `text` | YES | `NULL` |  |  |
| `tcscannerservice` | `text` | YES | `NULL` |  |  |
| `tcbiometriaservice` | `text` | YES | `NULL` |  |  |
| `tccontroladosprinterservice` | `text` | YES | `NULL` |  |  |

### `cs_service4` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `java` | `int(11)` | YES | `0` |  |  |
| `ip` | `varchar(15)` | NO | `` |  |  |
| `device_id` | `varchar(255)` | NO | `` |  |  |
| `device_name` | `varchar(255)` | YES | `''` |  |  |
| `hostname` | `varchar(255)` | YES | `''` |  |  |
| `groupname` | `varchar(255)` | YES | `''` |  |  |
| `bandeira` | `varchar(255)` | YES | `''` |  |  |
| `tcprinterservice` | `text` | YES | `NULL` |  |  |
| `tcscannerservice` | `text` | YES | `NULL` |  |  |
| `tcbiometriaservice` | `text` | YES | `NULL` |  |  |
| `tccontroladosprinterservice` | `text` | YES | `NULL` |  |  |

### `cs_service5` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `java` | `int(11)` | YES | `0` |  |  |
| `ip` | `varchar(15)` | NO | `` |  |  |
| `hostname` | `varchar(255)` | YES | `''` |  |  |
| `groupname` | `varchar(255)` | YES | `''` |  |  |
| `bandeira` | `varchar(255)` | YES | `''` |  |  |
| `tcprinterservice` | `text` | YES | `NULL` |  |  |
| `tcscannerservice` | `text` | YES | `NULL` |  |  |
| `tcbiometriaservice` | `text` | YES | `NULL` |  |  |
| `tccontroladosprinterservice` | `text` | YES | `NULL` |  |  |

### `v_active_alerts` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `bigint(20)` | NO | `0` |  |  |
| `alert_type` | `enum('ERROR','WARNING','INFO','SUCCESS')` | NO | `` |  |  |
| `severity` | `enum('LOW','MEDIUM','HIGH','CRITICAL')` | NO | `'MEDIUM'` |  |  |
| `title` | `varchar(255)` | NO | `` |  |  |
| `message` | `text` | NO | `` |  |  |
| `script_name` | `varchar(100)` | YES | `NULL` |  |  |
| `ip` | `varchar(15)` | YES | `NULL` |  |  |
| `java` | `varchar(20)` | YES | `NULL` |  |  |
| `created_at` | `datetime` | YES | `current_timestamp()` |  |  |
| `age_minutes` | `bigint(21)` | YES | `NULL` |  |  |

### `v_b12_auth_errors` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `int(11)` | NO | `0` |  |  |
| `b12_ip` | `varchar(15)` | NO | `` |  |  |
| `subnet_ip` | `varchar(15)` | NO | `` |  |  |
| `ssh_status` | `varchar(255)` | YES | `NULL` |  |  |
| `ssh_error_type` | `enum('success','auth_failed','auth_user_invalid','auth_password_invalid','timeout','connection_refused','no_route','port_closed','unknown')` | YES | `NULL` |  |  |
| `ssh_error_message` | `text` | YES | `NULL` |  |  |
| `ssh_error_timestamp` | `datetime` | YES | `NULL` |  |  |
| `ssh_last_success` | `datetime` | YES | `NULL` |  |  |
| `net_type` | `enum('nao_verificada','plana','segmentada','desconectada')` | NO | `'nao_verificada'` |  |  |
| `java` | `varchar(10)` | YES | `NULL` |  |  |
| `hostname` | `varchar(255)` | YES | `NULL` |  |  |
| `data_registro` | `datetime` | YES | `current_timestamp()` |  |  |
| `hours_since_error` | `bigint(21)` | YES | `NULL` |  |  |

### `v_b12_never_connected` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `id` | `int(11)` | NO | `0` |  |  |
| `b12_ip` | `varchar(15)` | NO | `` |  |  |
| `subnet_ip` | `varchar(15)` | NO | `` |  |  |
| `ssh_status` | `varchar(255)` | YES | `NULL` |  |  |
| `ssh_error_type` | `enum('success','auth_failed','auth_user_invalid','auth_password_invalid','timeout','connection_refused','no_route','port_closed','unknown')` | YES | `NULL` |  |  |
| `ssh_error_message` | `text` | YES | `NULL` |  |  |
| `ssh_error_timestamp` | `datetime` | YES | `NULL` |  |  |
| `net_type` | `enum('nao_verificada','plana','segmentada','desconectada')` | NO | `'nao_verificada'` |  |  |
| `data_registro` | `datetime` | YES | `current_timestamp()` |  |  |
| `days_since_error` | `bigint(21)` | YES | `NULL` |  |  |

### `v_current_scan_status` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `scan_id` | `varchar(100)` | NO | `` |  |  |
| `script_name` | `varchar(100)` | NO | `` |  |  |
| `start_time` | `datetime` | NO | `` |  |  |
| `status` | `enum('STARTED','PROCESSING','SUCCESS','FAILED','CANCELLED')` | YES | `'STARTED'` |  |  |
| `total_items` | `int(11)` | YES | `0` |  |  |
| `processed_items` | `int(11)` | YES | `0` |  |  |
| `failed_items` | `int(11)` | YES | `0` |  |  |
| `success_rate` | `decimal(5,2)` | YES | `0.00` |  |  |
| `progress_percentage` | `decimal(5,2)` | YES | `0.00` |  |  |
| `estimated_completion` | `datetime` | YES | `NULL` |  |  |
| `duration_minutes` | `bigint(21)` | YES | `NULL` |  |  |

### `v_hardware_auth_errors` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `java` | `varchar(10)` | YES | `NULL` |  |  |
| `ip` | `varchar(15)` | NO | `` |  |  |
| `tipo_equipamento` | `varchar(50)` | YES | `NULL` |  |  |
| `error_type` | `enum('success','auth_failed','auth_user_invalid','auth_password_invalid','connection_timeout','connection_refused','no_route','port_closed','ssh_auth_failed','ssh_timeout','ssh_command_failed','wmi_not_available','wmi_auth_failed','wmi_timeout','wmi_query_failed','snmp_no_response','snmp_timeout','snmp_community_invalid','snmp_oid_not_found','data_collection_failed','hardware_info_missing','database_insert_failed','unknown')` | YES | `NULL` |  |  |
| `error_message` | `text` | YES | `NULL` |  |  |
| `protocol_used` | `enum('SSH','WMI','SNMP','MIXED')` | YES | `NULL` |  |  |
| `attempt_number` | `int(11)` | YES | `1` |  |  |
| `scan_timestamp` | `datetime` | NO | `` |  |  |
| `last_success_scan` | `datetime` | YES | `NULL` |  |  |
| `hours_since_error` | `bigint(21)` | YES | `NULL` |  |  |

### `v_hardware_errors_stats` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `error_type` | `enum('success','auth_failed','auth_user_invalid','auth_password_invalid','connection_timeout','connection_refused','no_route','port_closed','ssh_auth_failed','ssh_timeout','ssh_command_failed','wmi_not_available','wmi_auth_failed','wmi_timeout','wmi_query_failed','snmp_no_response','snmp_timeout','snmp_community_invalid','snmp_oid_not_found','data_collection_failed','hardware_info_missing','database_insert_failed','unknown')` | YES | `NULL` |  |  |
| `protocol_used` | `enum('SSH','WMI','SNMP','MIXED')` | YES | `NULL` |  |  |
| `total_errors` | `bigint(21)` | NO | `0` |  |  |
| `dispositivos_afetados` | `bigint(21)` | NO | `0` |  |  |
| `primeiro_erro` | `datetime` | YES | `` |  |  |
| `ultimo_erro` | `datetime` | YES | `` |  |  |
| `media_tentativas` | `decimal(14,4)` | YES | `NULL` |  |  |

### `v_hardware_never_success` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `java` | `varchar(10)` | YES | `NULL` |  |  |
| `ip` | `varchar(15)` | NO | `` |  |  |
| `tipo_equipamento` | `varchar(50)` | YES | `NULL` |  |  |
| `ultima_tentativa` | `datetime` | YES | `` |  |  |
| `total_tentativas` | `bigint(21)` | NO | `0` |  |  |
| `tipos_erro` | `mediumtext` | YES | `NULL` |  |  |
| `protocolos_tentados` | `mediumtext` | YES | `NULL` |  |  |
| `days_since_last_attempt` | `bigint(21)` | YES | `NULL` |  |  |

### `v_hardware_recurring_errors` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `java` | `varchar(10)` | YES | `NULL` |  |  |
| `ip` | `varchar(15)` | NO | `` |  |  |
| `tipo_equipamento` | `varchar(50)` | YES | `NULL` |  |  |
| `error_type` | `enum('success','auth_failed','auth_user_invalid','auth_password_invalid','connection_timeout','connection_refused','no_route','port_closed','ssh_auth_failed','ssh_timeout','ssh_command_failed','wmi_not_available','wmi_auth_failed','wmi_timeout','wmi_query_failed','snmp_no_response','snmp_timeout','snmp_community_invalid','snmp_oid_not_found','data_collection_failed','hardware_info_missing','database_insert_failed','unknown')` | YES | `NULL` |  |  |
| `protocol_used` | `enum('SSH','WMI','SNMP','MIXED')` | YES | `NULL` |  |  |
| `total_tentativas` | `bigint(21)` | NO | `0` |  |  |
| `ultima_tentativa` | `datetime` | YES | `` |  |  |
| `primeira_tentativa` | `datetime` | YES | `` |  |  |
| `duracao_horas` | `bigint(21)` | YES | `NULL` |  |  |

### `v_scan_items_for_retry` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `scan_id` | `varchar(100)` | NO | `` |  |  |
| `item_type` | `enum('IP','NETWORK','DEVICE','PORT')` | NO | `` |  |  |
| `item_identifier` | `varchar(255)` | NO | `` |  |  |
| `hostname` | `varchar(255)` | YES | `NULL` |  |  |
| `status` | `enum('PENDING','PROCESSING','SUCCESS','FAILED','SKIPPED')` | NO | `'PENDING'` |  |  |
| `attempts` | `int(11)` | YES | `0` |  |  |
| `max_attempts` | `int(11)` | YES | `3` |  |  |
| `error_message` | `text` | YES | `NULL` |  |  |
| `updated_at` | `datetime` | YES | `current_timestamp()` |  |  |
| `minutes_since_last_attempt` | `bigint(21)` | YES | `NULL` |  |  |

### `v_scan_monitoring` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `scan_id` | `varchar(100)` | NO | `` |  |  |
| `script_name` | `varchar(100)` | NO | `` |  |  |
| `status` | `enum('STARTED','PROCESSING','SUCCESS','FAILED','CANCELLED')` | YES | `'STARTED'` |  |  |
| `start_time` | `datetime` | NO | `` |  |  |
| `end_time` | `datetime` | YES | `NULL` |  |  |
| `total_items` | `int(11)` | YES | `0` |  |  |
| `processed_items` | `int(11)` | YES | `0` |  |  |
| `failed_items` | `int(11)` | YES | `0` |  |  |
| `progress_percentage` | `decimal(5,2)` | YES | `0.00` |  |  |
| `estimated_completion` | `datetime` | YES | `NULL` |  |  |
| `process_pid` | `int(11)` | YES | `NULL` |  |  |
| `server_hostname` | `varchar(255)` | YES | `NULL` |  |  |
| `duration_minutes` | `bigint(21)` | YES | `NULL` |  |  |
| `pending_items` | `bigint(21)` | YES | `NULL` |  |  |
| `processing_items` | `bigint(21)` | YES | `NULL` |  |  |
| `success_items` | `bigint(21)` | YES | `NULL` |  |  |
| `failed_items_detail` | `bigint(21)` | YES | `NULL` |  |  |
| `skipped_items` | `bigint(21)` | YES | `NULL` |  |  |
| `stuck_items` | `bigint(21)` | YES | `NULL` |  |  |

### `v_scan_stuck_processes` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `scan_id` | `varchar(100)` | NO | `` |  |  |
| `item_type` | `enum('IP','NETWORK','DEVICE','PORT')` | NO | `` |  |  |
| `item_identifier` | `varchar(255)` | NO | `` |  |  |
| `hostname` | `varchar(255)` | YES | `NULL` |  |  |
| `start_time` | `datetime` | YES | `NULL` |  |  |
| `last_heartbeat` | `datetime` | YES | `NULL` |  |  |
| `minutes_without_heartbeat` | `bigint(21)` | YES | `NULL` |  |  |
| `total_processing_minutes` | `bigint(21)` | YES | `NULL` |  |  |

### `v_scan_summary` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `script_name` | `varchar(100)` | NO | `` |  |  |
| `scan_date` | `date` | YES | `NULL` |  |  |
| `total_scans` | `bigint(21)` | NO | `0` |  |  |
| `successful_scans` | `decimal(22,0)` | YES | `NULL` |  |  |
| `failed_scans` | `decimal(22,0)` | YES | `NULL` |  |  |
| `avg_success_rate` | `decimal(9,6)` | YES | `NULL` |  |  |
| `avg_duration_seconds` | `decimal(24,4)` | YES | `NULL` |  |  |

### `v_ssh_errors_stats` (VIEW)
| Coluna | Tipo | Null | Default | Key | Extra |
|---|---|---|---|---|---|
| `ssh_error_type` | `enum('success','auth_failed','auth_user_invalid','auth_password_invalid','timeout','connection_refused','no_route','port_closed','unknown')` | YES | `NULL` |  |  |
| `total_errors` | `bigint(21)` | NO | `0` |  |  |
| `b12s_afetados` | `bigint(21)` | NO | `0` |  |  |
| `primeiro_erro` | `datetime` | YES | `NULL` |  |  |
| `ultimo_erro` | `datetime` | YES | `NULL` |  |  |
