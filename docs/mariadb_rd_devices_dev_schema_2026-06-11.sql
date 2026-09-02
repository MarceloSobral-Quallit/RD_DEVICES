-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: <mariadb-host>    Database: rd_devices_dev
-- ------------------------------------------------------
-- Server version	11.8.6-MariaDB-0+deb13u1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `rd_devices_dev`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `rd_devices_dev` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;

USE `rd_devices_dev`;

--
-- Temporary view structure for view `cs_devices`
--

DROP TABLE IF EXISTS `cs_devices`;
/*!50001 DROP VIEW IF EXISTS `cs_devices`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `cs_devices` AS SELECT 
 1 AS `java`,
 1 AS `ip`,
 1 AS `device_id`,
 1 AS `device_name`,
 1 AS `hostname`,
 1 AS `groupname`,
 1 AS `bandeira`,
 1 AS `cpu`,
 1 AS `cores`,
 1 AS `ram_gb`,
 1 AS `disk_gb`,
 1 AS `os`,
 1 AS `os_version`,
 1 AS `scan_date`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `cs_scan_control`
--

DROP TABLE IF EXISTS `cs_scan_control`;
/*!50001 DROP VIEW IF EXISTS `cs_scan_control`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `cs_scan_control` AS SELECT 
 1 AS `scan_id`,
 1 AS `java`,
 1 AS `bandeira`,
 1 AS `ip`,
 1 AS `start_time`,
 1 AS `end_time`,
 1 AS `status`,
 1 AS `attempts`,
 1 AS `last_attempt`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `cs_service`
--

DROP TABLE IF EXISTS `cs_service`;
/*!50001 DROP VIEW IF EXISTS `cs_service`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `cs_service` AS SELECT 
 1 AS `java`,
 1 AS `ip`,
 1 AS `device_id`,
 1 AS `device_name`,
 1 AS `hostname`,
 1 AS `groupname`,
 1 AS `bandeira`,
 1 AS `cpu`,
 1 AS `cores`,
 1 AS `ram_gb`,
 1 AS `disk_gb`,
 1 AS `os`,
 1 AS `os_version`,
 1 AS `scan_date`,
 1 AS `tcprinterservice`,
 1 AS `tcscannerservice`,
 1 AS `tcbiometriaservice`,
 1 AS `tccontroladosprinterservice`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `cs_service3`
--

DROP TABLE IF EXISTS `cs_service3`;
/*!50001 DROP VIEW IF EXISTS `cs_service3`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `cs_service3` AS SELECT 
 1 AS `java`,
 1 AS `ip`,
 1 AS `device_id`,
 1 AS `device_name`,
 1 AS `hostname`,
 1 AS `groupname`,
 1 AS `bandeira`,
 1 AS `tcprinterservice`,
 1 AS `tcscannerservice`,
 1 AS `tcbiometriaservice`,
 1 AS `tccontroladosprinterservice`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `cs_service4`
--

DROP TABLE IF EXISTS `cs_service4`;
/*!50001 DROP VIEW IF EXISTS `cs_service4`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `cs_service4` AS SELECT 
 1 AS `java`,
 1 AS `ip`,
 1 AS `device_id`,
 1 AS `device_name`,
 1 AS `hostname`,
 1 AS `groupname`,
 1 AS `bandeira`,
 1 AS `tcprinterservice`,
 1 AS `tcscannerservice`,
 1 AS `tcbiometriaservice`,
 1 AS `tccontroladosprinterservice`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `cs_service5`
--

DROP TABLE IF EXISTS `cs_service5`;
/*!50001 DROP VIEW IF EXISTS `cs_service5`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `cs_service5` AS SELECT 
 1 AS `java`,
 1 AS `ip`,
 1 AS `hostname`,
 1 AS `groupname`,
 1 AS `bandeira`,
 1 AS `tcprinterservice`,
 1 AS `tcscannerservice`,
 1 AS `tcbiometriaservice`,
 1 AS `tccontroladosprinterservice`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `tb_alerts`
--

DROP TABLE IF EXISTS `tb_alerts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_alerts` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `alert_type` enum('ERROR','WARNING','INFO','SUCCESS') NOT NULL,
  `severity` enum('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL DEFAULT 'MEDIUM',
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `script_name` varchar(100) DEFAULT NULL,
  `scan_id` varchar(100) DEFAULT NULL,
  `ip` varchar(15) DEFAULT NULL,
  `java` varchar(20) DEFAULT NULL,
  `status` enum('ACTIVE','ACKNOWLEDGED','RESOLVED','IGNORED') NOT NULL DEFAULT 'ACTIVE',
  `created_at` datetime DEFAULT current_timestamp(),
  `acknowledged_at` datetime DEFAULT NULL,
  `acknowledged_by` varchar(100) DEFAULT NULL,
  `resolved_at` datetime DEFAULT NULL,
  `resolved_by` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_alert_type` (`alert_type`),
  KEY `idx_severity` (`severity`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_alerts_type_status_created` (`alert_type`,`status`,`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_audit_config`
--

DROP TABLE IF EXISTS `tb_audit_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_audit_config` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `config_key` varchar(100) NOT NULL,
  `config_value` text NOT NULL,
  `description` text DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `config_key` (`config_key`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_audit_log`
--

DROP TABLE IF EXISTS `tb_audit_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_audit_log` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NOT NULL DEFAULT current_timestamp(),
  `script_name` varchar(100) NOT NULL,
  `script_version` varchar(20) DEFAULT NULL,
  `level` enum('INFO','WARNING','ERROR','CRITICAL') NOT NULL DEFAULT 'INFO',
  `action` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `ip` varchar(15) DEFAULT NULL,
  `java` varchar(20) DEFAULT NULL,
  `bandeira` varchar(50) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `duration_ms` int(11) DEFAULT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  `session_id` varchar(100) DEFAULT NULL,
  `metadata` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`metadata`)),
  PRIMARY KEY (`id`),
  KEY `idx_timestamp` (`timestamp`),
  KEY `idx_script` (`script_name`),
  KEY `idx_level` (`level`),
  KEY `idx_action` (`action`),
  KEY `idx_ip` (`ip`),
  KEY `idx_java` (`java`),
  KEY `idx_status` (`status`),
  KEY `idx_audit_script_timestamp` (`script_name`,`timestamp`),
  KEY `idx_audit_level_timestamp` (`level`,`timestamp`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_b12_data_collection_status`
--

DROP TABLE IF EXISTS `tb_b12_data_collection_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_b12_data_collection_status` (
  `java` varchar(50) NOT NULL,
  `ip_b12` varchar(15) NOT NULL,
  `nome_filial` varchar(100) DEFAULT NULL,
  `collection_status` varchar(20) DEFAULT NULL COMMENT 'IN_PROGRESS | SUCCESS | PARTIAL | FAILED',
  `collection_date` datetime DEFAULT NULL,
  `collection_duration_seconds` int(11) DEFAULT NULL,
  `hostname_collected` tinyint(1) DEFAULT 0,
  `hostname_value` varchar(100) DEFAULT NULL,
  `hostname_raw_collected` tinyint(1) DEFAULT 0,
  `hostname_raw_value` varchar(100) DEFAULT NULL,
  `os_collected` tinyint(1) DEFAULT 0,
  `os_value` varchar(100) DEFAULT NULL,
  `os_version_collected` tinyint(1) DEFAULT 0,
  `os_version_value` varchar(100) DEFAULT NULL,
  `kernel_collected` tinyint(1) DEFAULT 0,
  `kernel_value` varchar(100) DEFAULT NULL,
  `cidr_collected` tinyint(1) DEFAULT 0,
  `cidr_value` varchar(20) DEFAULT NULL,
  `cores_collected` tinyint(1) DEFAULT 0,
  `cores_value` varchar(50) DEFAULT NULL,
  `memory_collected` tinyint(1) DEFAULT 0,
  `memory_value_bytes` bigint(20) DEFAULT NULL,
  `mac_collected` tinyint(1) DEFAULT 0,
  `mac_value` varchar(17) DEFAULT NULL,
  `mb_manufacturer_collected` tinyint(1) DEFAULT 0,
  `mb_manufacturer_value` varchar(100) DEFAULT NULL,
  `mb_product_collected` tinyint(1) DEFAULT 0,
  `mb_product_value` varchar(100) DEFAULT NULL,
  `mb_version_collected` tinyint(1) DEFAULT 0,
  `mb_version_value` varchar(50) DEFAULT NULL,
  `disk_media_type_collected` tinyint(1) DEFAULT 0,
  `disk_media_type_value` varchar(20) DEFAULT NULL,
  `disk_model_collected` tinyint(1) DEFAULT 0,
  `disk_model_value` varchar(100) DEFAULT NULL,
  `disk_size_collected` tinyint(1) DEFAULT 0,
  `disk_size_value` bigint(20) DEFAULT NULL,
  `fields_collected_count` int(11) DEFAULT 0,
  `collection_percentage` float DEFAULT 0,
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`java`,`ip_b12`),
  KEY `idx_collection_status` (`collection_status`),
  KEY `idx_ip_b12` (`ip_b12`),
  KEY `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Rastreamento granular de coleta B12 por filial/IP';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_detected_devices`
--

DROP TABLE IF EXISTS `tb_detected_devices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_detected_devices` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `filial` varchar(10) DEFAULT NULL,
  `ip` varchar(15) NOT NULL,
  `expected_type` varchar(20) DEFAULT NULL,
  `device_type` varchar(50) DEFAULT NULL,
  `logo` varchar(20) DEFAULT NULL,
  `ssh` tinyint(1) DEFAULT 0,
  `radmin` tinyint(1) DEFAULT 0,
  `printer` tinyint(1) DEFAULT 0,
  `detected_at` datetime DEFAULT current_timestamp(),
  `hw_hostname` varchar(100) DEFAULT NULL,
  `hw_cpu_model` varchar(200) DEFAULT NULL,
  `hw_cores` int(11) DEFAULT NULL,
  `hw_ram_gb` float DEFAULT NULL,
  `hw_disk_gb` float DEFAULT NULL,
  `hw_os` varchar(100) DEFAULT NULL,
  `hw_os_version` varchar(100) DEFAULT NULL,
  `hw_kernel` varchar(100) DEFAULT NULL,
  `hw_cores_fisicos` varchar(50) DEFAULT NULL,
  `hw_memoria_total` bigint(20) DEFAULT NULL,
  `hw_mac_address` varchar(17) DEFAULT NULL,
  `hw_mb_manufacturer` varchar(100) DEFAULT NULL,
  `hw_mb_product_name` varchar(100) DEFAULT NULL,
  `hw_mb_version` varchar(50) DEFAULT NULL,
  `hw_hdd_media_type` varchar(20) DEFAULT NULL,
  `hw_hdd_model` varchar(100) DEFAULT NULL,
  `hw_hdd_size` bigint(20) DEFAULT NULL,
  `hw_scanned_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_ip_unique` (`ip`),
  KEY `idx_filial` (`filial`),
  KEY `idx_device_type` (`device_type`),
  KEY `idx_expected_type` (`expected_type`),
  KEY `idx_logo` (`logo`),
  KEY `idx_detected_at` (`detected_at`),
  KEY `idx_hw_scanned_at` (`hw_scanned_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Dispositivos detectados em scan de rede por filial';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_devices`
--

DROP TABLE IF EXISTS `tb_devices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_devices` (
  `job_id` int(11) NOT NULL AUTO_INCREMENT,
  `java` int(11) DEFAULT 0 CHECK (`java` between 1 and 9999),
  `ip` varchar(15) NOT NULL,
  `device_id` varchar(50) DEFAULT '',
  `device_name` varchar(255) DEFAULT '',
  `device_description` text DEFAULT '',
  `scan_date` datetime DEFAULT current_timestamp(),
  `hostname` varchar(255) DEFAULT '',
  `groupname` varchar(255) DEFAULT '',
  `bandeira` varchar(255) DEFAULT '',
  `cpu` varchar(255) DEFAULT '',
  `cores` int(11) DEFAULT 0,
  `ram_gb` float DEFAULT 0,
  `disk_gb` float DEFAULT 0,
  `os` varchar(255) DEFAULT '',
  `os_version` varchar(100) DEFAULT '',
  `tcprinterservice` text DEFAULT NULL,
  `tcscannerservice` text DEFAULT NULL,
  `tcbiometriaservice` text DEFAULT NULL,
  `tccontroladosprinterservice` text DEFAULT NULL,
  `detail_job_id` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`job_id`),
  KEY `idx_ip` (`ip`),
  KEY `idx_java` (`java`),
  KEY `idx_device_id` (`device_id`),
  KEY `idx_scan_date` (`scan_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_devices_catalog`
--

DROP TABLE IF EXISTS `tb_devices_catalog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_devices_catalog` (
  `device_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin NOT NULL,
  `device_name` varchar(255) NOT NULL,
  PRIMARY KEY (`device_id`,`device_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_devices_detail`
--

DROP TABLE IF EXISTS `tb_devices_detail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_devices_detail` (
  `detail_job_id` varchar(50) DEFAULT NULL,
  `java` varchar(50) NOT NULL,
  `ip` varchar(15) NOT NULL,
  `hostname` varchar(100) NOT NULL,
  `tipo_equipamento` varchar(20) NOT NULL,
  `sistema_operacional` varchar(100) NOT NULL,
  `kernel` varchar(100) NOT NULL DEFAULT '',
  `cores_fisicos` varchar(50) NOT NULL,
  `memoria_total` bigint(20) NOT NULL,
  `mac_address` varchar(17) DEFAULT NULL,
  `mb_manufacturer` varchar(100) DEFAULT NULL,
  `mb_product_name` varchar(100) DEFAULT NULL,
  `mb_version` varchar(50) DEFAULT NULL,
  `hdd_media_type` varchar(50) DEFAULT NULL,
  `hdd_model` varchar(100) DEFAULT NULL,
  `hdd_size` bigint(20) DEFAULT NULL,
  `data_coleta` datetime NOT NULL DEFAULT current_timestamp(),
  `data_atualizacao` datetime DEFAULT NULL,
  PRIMARY KEY (`ip`),
  UNIQUE KEY `ip` (`ip`),
  UNIQUE KEY `idx_ip_unique` (`ip`),
  KEY `idx_tipo_equipamento` (`tipo_equipamento`),
  KEY `idx_data_coleta` (`data_coleta`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_devices_detail_log`
--

DROP TABLE IF EXISTS `tb_devices_detail_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_devices_detail_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `data_scan` datetime NOT NULL,
  `detail_job_id` varchar(50) DEFAULT NULL,
  `java` varchar(10) DEFAULT NULL,
  `ip` varchar(15) NOT NULL,
  `hostname` varchar(100) DEFAULT NULL,
  `tipo_equipamento` varchar(50) DEFAULT NULL,
  `status` enum('success','auth_failed','auth_user_invalid','auth_password_invalid','connection_timeout','connection_refused','no_route','port_closed','ssh_auth_failed','ssh_timeout','ssh_command_failed','wmi_not_available','wmi_auth_failed','wmi_timeout','wmi_query_failed','snmp_no_response','snmp_timeout','snmp_community_invalid','snmp_oid_not_found','data_collection_failed','hardware_info_missing','database_insert_failed','unknown') NOT NULL DEFAULT 'unknown',
  `mensagem` text DEFAULT NULL,
  `error_type` enum('success','auth_failed','auth_user_invalid','auth_password_invalid','connection_timeout','connection_refused','no_route','port_closed','ssh_auth_failed','ssh_timeout','ssh_command_failed','wmi_not_available','wmi_auth_failed','wmi_timeout','wmi_query_failed','snmp_no_response','snmp_timeout','snmp_community_invalid','snmp_oid_not_found','data_collection_failed','hardware_info_missing','database_insert_failed','unknown') DEFAULT NULL COMMENT 'Tipo específico de erro',
  `error_code` varchar(50) DEFAULT NULL COMMENT 'Código de erro (se disponível)',
  `error_details` text DEFAULT NULL COMMENT 'Detalhes adicionais do erro',
  `protocol_used` enum('SSH','WMI','SNMP','MIXED') DEFAULT NULL COMMENT 'Protocolo usado na tentativa',
  `attempt_number` int(11) DEFAULT 1 COMMENT 'Número da tentativa (para retries)',
  `last_success_scan` datetime DEFAULT NULL COMMENT 'Última coleta bem-sucedida',
  PRIMARY KEY (`id`),
  KEY `idx_data_scan` (`data_scan`),
  KEY `idx_ip` (`ip`),
  KEY `idx_status` (`status`),
  KEY `idx_error_type` (`error_type`),
  KEY `idx_protocol_used` (`protocol_used`),
  KEY `idx_last_success_scan` (`last_success_scan`),
  KEY `idx_java_ip_error` (`java`,`ip`,`error_type`),
  KEY `idx_ip_data_scan` (`ip`,`data_scan` DESC) COMMENT 'Índice para buscar histórico de tentativas por IP',
  KEY `idx_status_error_type` (`status`,`error_type`) COMMENT 'Índice para análise de erros'
) ENGINE=InnoDB AUTO_INCREMENT=35869 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_filial`
--

DROP TABLE IF EXISTS `tb_filial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_filial` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID único auto-incremento',
  `filial` varchar(10) NOT NULL COMMENT 'Código da filial',
  `historico` varchar(10) NOT NULL COMMENT 'Histórico da filial',
  `nome_filial` varchar(100) NOT NULL COMMENT 'Nome da filial',
  `data_inauguracao` date DEFAULT NULL COMMENT 'Data de inauguração da filial',
  `inscricao_estadual` varchar(20) DEFAULT NULL COMMENT 'Inscrição Estadual',
  `cnpj` varchar(20) DEFAULT NULL COMMENT 'CNPJ da filial',
  `endereco` varchar(200) NOT NULL COMMENT 'Endereço completo com CEP',
  `bairro` varchar(100) NOT NULL COMMENT 'Bairro',
  `cidade` varchar(100) NOT NULL COMMENT 'Cidade',
  `uf` char(2) NOT NULL COMMENT 'Unidade Federativa (Estado)',
  `regiao` varchar(50) NOT NULL COMMENT 'Região da filial',
  `logomarca` varchar(20) NOT NULL COMMENT 'Logomarca/Bandeira da filial',
  `telefone` varchar(30) DEFAULT NULL COMMENT 'Telefone de contato',
  `ip_banco_12` varchar(15) DEFAULT NULL COMMENT 'IP do Banco 12 (B12)',
  `cidr` varchar(20) DEFAULT NULL COMMENT 'CIDR da rede da loja detectado via SSH no B12 (ex: /24, /25)',
  `data_criacao` timestamp NULL DEFAULT current_timestamp() COMMENT 'Data de criação do registro',
  `data_atualizacao` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT 'Data da última atualização',
  `ativo` tinyint(1) DEFAULT 1 COMMENT 'Indica se a filial está ativa (1=Sim, 0=Não)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_filial` (`filial`),
  KEY `idx_nome_filial` (`nome_filial`),
  KEY `idx_uf` (`uf`),
  KEY `idx_cidade` (`cidade`),
  KEY `idx_regiao` (`regiao`),
  KEY `idx_logomarca` (`logomarca`),
  KEY `idx_ip_banco_12` (`ip_banco_12`),
  KEY `idx_ativo` (`ativo`),
  KEY `idx_filial_cidr` (`cidr`)
) ENGINE=InnoDB AUTO_INCREMENT=3592 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tabela de filiais com informações cadastrais e operacionais';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_hardware_historico`
--

DROP TABLE IF EXISTS `tb_hardware_historico`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_hardware_historico` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `job_id` varchar(50) NOT NULL,
  `java` varchar(50) NOT NULL,
  `ip` varchar(15) NOT NULL,
  `hostname` varchar(100) NOT NULL,
  `tipo_equipamento` varchar(20) NOT NULL,
  `sistema_operacional` varchar(100) NOT NULL,
  `kernel` varchar(100) NOT NULL,
  `cores_fisicos` varchar(50) NOT NULL,
  `memoria_total` bigint(20) NOT NULL,
  `mac_address` varchar(17) NOT NULL,
  `mb_manufacturer` varchar(100) DEFAULT NULL COMMENT 'Fabricante da placa-mãe/sistema',
  `mb_product_name` varchar(100) DEFAULT NULL COMMENT 'Nome do produto/modelo',
  `mb_version` varchar(50) DEFAULT NULL COMMENT 'Versão do produto/BIOS',
  `hdd_media_type` varchar(50) DEFAULT NULL COMMENT 'Tipo de mídia (SSD, HDD, etc)',
  `hdd_model` varchar(100) DEFAULT NULL COMMENT 'Modelo do disco',
  `hdd_size` bigint(20) DEFAULT NULL COMMENT 'Tamanho em bytes',
  `data_coleta` datetime NOT NULL,
  `data_atualizacao` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_job_id` (`job_id`)
) ENGINE=InnoDB AUTO_INCREMENT=49859 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_log_execucao`
--

DROP TABLE IF EXISTS `tb_log_execucao`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_log_execucao` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `data_inicio` datetime DEFAULT NULL,
  `data_fim` datetime DEFAULT NULL,
  `tipo_scan` varchar(50) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `mensagem` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_data` (`data_inicio`),
  KEY `idx_tipo` (`tipo_scan`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_network_ips`
--

DROP TABLE IF EXISTS `tb_network_ips`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_network_ips` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) NOT NULL,
  `is_active` tinyint(1) DEFAULT 0,
  `last_seen` timestamp NULL DEFAULT NULL,
  `port_22` tinyint(1) DEFAULT NULL,
  `port_80` tinyint(1) DEFAULT NULL,
  `port_135` tinyint(1) DEFAULT NULL,
  `port_443` tinyint(1) DEFAULT NULL,
  `port_445` tinyint(1) DEFAULT NULL,
  `port_161` tinyint(1) DEFAULT NULL,
  `port_7856` tinyint(1) DEFAULT NULL,
  `hostname` varchar(255) DEFAULT NULL,
  `os_info` text DEFAULT NULL,
  `device_type` enum('router','switch','server','printer','workstation','unknown') DEFAULT 'unknown',
  `snmp_community` varchar(50) DEFAULT NULL COMMENT 'Comunidade SNMP (se descoberta)',
  `subnet_id` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_ip` (`ip`),
  KEY `subnet_id` (`subnet_id`),
  KEY `idx_device_type` (`device_type`),
  KEY `idx_last_seen` (`last_seen`),
  CONSTRAINT `tb_network_ips_ibfk_1` FOREIGN KEY (`subnet_id`) REFERENCES `tb_network_subnets` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Armazena informa├º├Áes sobre os dispositivos de rede descobertos, incluindo portas abertas e metadados';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_network_ports`
--

DROP TABLE IF EXISTS `tb_network_ports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_network_ports` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `network_id` int(11) NOT NULL,
  `ip` varchar(15) NOT NULL,
  `ssh_open` tinyint(1) DEFAULT 0,
  `radmin_open` tinyint(1) DEFAULT 0,
  `snmp_open` tinyint(1) DEFAULT 0 COMMENT 'Porta SNMP (161 UDP) aberta - indica impressora acessível via SNMP',
  `java` varchar(10) DEFAULT NULL,
  `last_scan` datetime DEFAULT current_timestamp(),
  `status_scan_hardware` enum('PENDING','PROCESSING','SUCCESS','ERROR','OFFLINE','FAILED','SKIPPED') NOT NULL DEFAULT 'PENDING' COMMENT 'Status: PENDING=aguardando, PROCESSING=em andamento, SUCCESS=sucesso, ERROR=erro, OFFLINE=host offline, FAILED=falha crítica, SKIPPED=pulado',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_ip` (`network_id`,`ip`),
  KEY `idx_status_scan_hardware` (`status_scan_hardware`),
  KEY `idx_status_scan_java` (`status_scan_hardware`,`java`) COMMENT 'Índice para buscar hosts pendentes por java'
) ENGINE=InnoDB AUTO_INCREMENT=246100 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_network_ports_backup_20251211`
--

DROP TABLE IF EXISTS `tb_network_ports_backup_20251211`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_network_ports_backup_20251211` (
  `id` int(11) NOT NULL DEFAULT 0,
  `network_id` int(11) NOT NULL,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `ssh_open` tinyint(1) DEFAULT 0,
  `radmin_open` tinyint(1) DEFAULT 0,
  `snmp_open` tinyint(1) DEFAULT 0 COMMENT 'Porta SNMP (161 UDP) aberta - indica impressora acessível via SNMP',
  `java` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `last_scan` datetime DEFAULT current_timestamp(),
  `status_scan_hardware` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'pending' COMMENT 'Status: pending, processing, success, offline, error, failed, skipped'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_network_subnets`
--

DROP TABLE IF EXISTS `tb_network_subnets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_network_subnets` (
  `id` int(11) NOT NULL DEFAULT 0,
  `subnet_ip` varchar(15) NOT NULL,
  `b12_ip` varchar(15) NOT NULL,
  `ultima_verificacao` datetime DEFAULT NULL,
  `scan_status` enum('PENDING','PROCESSING','SUCCESS','FAILED','SKIPPED') DEFAULT 'PENDING' COMMENT 'Status do escaneamento da subnet',
  `last_scan` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_b12_ip` (`b12_ip`),
  KEY `idx_scan_status` (`scan_status`) COMMENT 'Índice para buscar subnets pendentes'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_network_subnets_type`
--

DROP TABLE IF EXISTS `tb_network_subnets_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_network_subnets_type` (
  `id` int(11) NOT NULL DEFAULT 0,
  `subnet_ip` varchar(15) NOT NULL,
  `b12_ip` varchar(15) NOT NULL,
  `net_type` enum('nao_verificada','plana','segmentada','desconectada') NOT NULL DEFAULT 'nao_verificada',
  `hostname` varchar(255) DEFAULT NULL,
  `hostname_raw` varchar(255) DEFAULT NULL,
  `os_info` varchar(255) DEFAULT NULL,
  `java` varchar(10) DEFAULT NULL,
  `version_id` varchar(50) DEFAULT NULL,
  `ssh_status` varchar(255) DEFAULT NULL,
  `data_registro` datetime DEFAULT current_timestamp(),
  `cidr` varchar(20) DEFAULT NULL COMMENT 'CIDR da conexão (ex: /24, /25)',
  `bandeira` varchar(50) DEFAULT NULL COMMENT 'Bandeira da loja',
  `filial` varchar(10) DEFAULT NULL COMMENT 'Código da filial',
  `usuario` varchar(50) DEFAULT NULL COMMENT 'Usuário do sistema',
  `nome_maquina` varchar(100) DEFAULT NULL COMMENT 'Nome da máquina',
  `terminal` varchar(20) DEFAULT NULL COMMENT 'Tipo do terminal',
  `imagem_so` varchar(100) DEFAULT NULL COMMENT 'Imagem do sistema operacional',
  `tipo` varchar(20) DEFAULT NULL COMMENT 'Tipo do sistema',
  `script2_processado` datetime DEFAULT NULL COMMENT 'Data/hora que Script 2 processou',
  `script3_processado` datetime DEFAULT NULL COMMENT 'Data/hora que Script 3 processou',
  `ssh_error_type` enum('success','auth_failed','auth_user_invalid','auth_password_invalid','timeout','connection_refused','no_route','port_closed','unknown') DEFAULT NULL COMMENT 'Tipo de erro SSH identificado',
  `ssh_error_message` text DEFAULT NULL COMMENT 'Mensagem detalhada do erro SSH',
  `ssh_error_timestamp` datetime DEFAULT NULL COMMENT 'Timestamp do último erro SSH',
  `ssh_last_success` datetime DEFAULT NULL COMMENT 'Timestamp da última conexão SSH bem-sucedida',
  `script2_status` enum('PENDING','PROCESSING','SUCCESS','FAILED','SKIPPED') DEFAULT 'PENDING' COMMENT 'Status do processamento do Script 2',
  `script3_status` enum('PENDING','PROCESSING','SUCCESS','FAILED','SKIPPED') DEFAULT 'PENDING' COMMENT 'Status do processamento do Script 3',
  KEY `idx_b12_data` (`b12_ip`,`data_registro` DESC),
  KEY `idx_net_type` (`net_type`),
  KEY `idx_bandeira` (`bandeira`),
  KEY `idx_filial` (`filial`),
  KEY `idx_cidr` (`cidr`),
  KEY `idx_ssh_error_type` (`ssh_error_type`),
  KEY `idx_ssh_error_timestamp` (`ssh_error_timestamp`),
  KEY `idx_ssh_last_success` (`ssh_last_success`),
  KEY `idx_script2_status` (`script2_status`) COMMENT 'Índice para buscar itens pendentes do Script 2',
  KEY `idx_script3_status` (`script3_status`) COMMENT 'Índice para buscar itens pendentes do Script 3'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_performance_metrics`
--

DROP TABLE IF EXISTS `tb_performance_metrics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_performance_metrics` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `script_name` varchar(100) NOT NULL,
  `metric_name` varchar(100) NOT NULL,
  `metric_value` decimal(15,4) NOT NULL,
  `metric_unit` varchar(20) DEFAULT NULL,
  `timestamp` datetime NOT NULL DEFAULT current_timestamp(),
  `context` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`context`)),
  PRIMARY KEY (`id`),
  KEY `idx_script` (`script_name`),
  KEY `idx_metric` (`metric_name`),
  KEY `idx_timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_scan_control`
--

DROP TABLE IF EXISTS `tb_scan_control`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_scan_control` (
  `scan_id` int(11) NOT NULL AUTO_INCREMENT,
  `java` varchar(255) NOT NULL,
  `bandeira` varchar(255) DEFAULT '',
  `ip` varchar(15) DEFAULT '',
  `start_time` datetime NOT NULL,
  `end_time` datetime DEFAULT current_timestamp(),
  `status` enum('PENDING','PROCESSING','SUCCESS','FAILED') DEFAULT 'PENDING',
  `attempts` int(11) DEFAULT 0,
  `last_attempt` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`scan_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_scan_control_backup_20251211`
--

DROP TABLE IF EXISTS `tb_scan_control_backup_20251211`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_scan_control_backup_20251211` (
  `scan_id` int(11) NOT NULL DEFAULT 0,
  `java` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `bandeira` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT '',
  `ip` varchar(15) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT '',
  `start_time` datetime NOT NULL,
  `end_time` datetime DEFAULT current_timestamp(),
  `status` enum('Pendente','Em Andamento','Concluído','Falhou') CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT 'Pendente',
  `attempts` int(11) DEFAULT 0,
  `last_attempt` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_scan_details`
--

DROP TABLE IF EXISTS `tb_scan_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_scan_details` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `scan_id` varchar(100) NOT NULL,
  `item_type` enum('IP','NETWORK','DEVICE','PORT') NOT NULL,
  `item_identifier` varchar(255) NOT NULL,
  `status` enum('PENDING','PROCESSING','SUCCESS','FAILED','SKIPPED') NOT NULL DEFAULT 'PENDING',
  `start_time` datetime DEFAULT NULL,
  `end_time` datetime DEFAULT NULL,
  `duration_ms` int(11) DEFAULT NULL,
  `error_message` text DEFAULT NULL,
  `result_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`result_data`)),
  `attempts` int(11) DEFAULT 0,
  `max_attempts` int(11) DEFAULT 3,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `last_heartbeat` datetime DEFAULT NULL COMMENT 'Último heartbeat do processo - para detectar processos travados',
  `hostname` varchar(255) DEFAULT NULL COMMENT 'Hostname do host sendo processado',
  PRIMARY KEY (`id`),
  KEY `idx_scan_id` (`scan_id`),
  KEY `idx_item_type` (`item_type`),
  KEY `idx_status` (`status`),
  KEY `idx_identifier` (`item_identifier`),
  KEY `idx_scan_details_scan_status` (`scan_id`,`status`),
  KEY `idx_status_attempts` (`status`,`attempts`) COMMENT 'Índice para buscar itens pendentes ou com falha para retry',
  KEY `idx_scan_status_attempts` (`scan_id`,`status`,`attempts`) COMMENT 'Índice composto para queries de continuação de scan',
  KEY `idx_item_type_status` (`item_type`,`status`) COMMENT 'Índice para filtrar por tipo de item e status',
  KEY `idx_heartbeat` (`last_heartbeat`) COMMENT 'Índice para identificar processos sem heartbeat',
  CONSTRAINT `tb_scan_details_ibfk_1` FOREIGN KEY (`scan_id`) REFERENCES `tb_scan_status` (`scan_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_scan_java_log`
--

DROP TABLE IF EXISTS `tb_scan_java_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_scan_java_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) NOT NULL,
  `java` varchar(50) NOT NULL,
  `bandeira` varchar(50) NOT NULL,
  `status` enum('PENDING','PROCESSING','SUCCESS','FAILED','SKIPPED') DEFAULT 'PENDING' COMMENT 'Status do processamento',
  `attempts` int(11) DEFAULT 1,
  `start_time` timestamp NULL DEFAULT NULL,
  `end_time` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_ip_java` (`ip`,`java`),
  KEY `idx_status_java` (`status`,`java`) COMMENT 'Índice para buscar itens pendentes por java'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_scan_run_items`
--

DROP TABLE IF EXISTS `tb_scan_run_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_scan_run_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `run_id` int(11) NOT NULL,
  `item_key` varchar(255) NOT NULL,
  `filial` varchar(50) DEFAULT NULL,
  `ip` varchar(45) DEFAULT NULL,
  `device_type` varchar(100) DEFAULT NULL,
  `status` text NOT NULL,
  `action` varchar(100) DEFAULT NULL,
  `result_ref` varchar(255) DEFAULT NULL,
  `error_message` text DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_scan_run_item` (`run_id`,`item_key`),
  KEY `idx_scan_items_run` (`run_id`),
  KEY `idx_scan_items_filial` (`filial`),
  KEY `idx_scan_items_ip` (`ip`),
  CONSTRAINT `fk_scan_items_run` FOREIGN KEY (`run_id`) REFERENCES `tb_scan_runs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_scan_runs`
--

DROP TABLE IF EXISTS `tb_scan_runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_scan_runs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `scan_type` varchar(50) NOT NULL,
  `source_tab` varchar(100) DEFAULT NULL,
  `status` varchar(30) NOT NULL,
  `started_at` datetime NOT NULL DEFAULT current_timestamp(),
  `finished_at` datetime DEFAULT NULL,
  `total_items` int(11) DEFAULT 0,
  `processed_items` int(11) DEFAULT 0,
  `success_items` int(11) DEFAULT 0,
  `failed_items` int(11) DEFAULT 0,
  `cancelled_items` int(11) DEFAULT 0,
  `selected_count` int(11) DEFAULT 0,
  `notes` text DEFAULT NULL,
  `error_message` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_scan_runs_status` (`status`),
  KEY `idx_scan_runs_type` (`scan_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_scan_status`
--

DROP TABLE IF EXISTS `tb_scan_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_scan_status` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `scan_id` varchar(100) NOT NULL,
  `script_name` varchar(100) NOT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime DEFAULT NULL,
  `status` enum('STARTED','PROCESSING','SUCCESS','FAILED','CANCELLED') DEFAULT 'STARTED',
  `total_items` int(11) DEFAULT 0,
  `processed_items` int(11) DEFAULT 0,
  `failed_items` int(11) DEFAULT 0,
  `success_rate` decimal(5,2) DEFAULT 0.00,
  `error_message` text DEFAULT NULL,
  `parameters` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`parameters`)),
  `progress_percentage` decimal(5,2) DEFAULT 0.00,
  `estimated_completion` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `process_pid` int(11) DEFAULT NULL COMMENT 'PID do processo que está executando o scan',
  `server_hostname` varchar(255) DEFAULT NULL COMMENT 'Hostname do servidor que está executando o scan',
  PRIMARY KEY (`id`),
  UNIQUE KEY `scan_id` (`scan_id`),
  KEY `idx_scan_id` (`scan_id`),
  KEY `idx_script` (`script_name`),
  KEY `idx_start_time` (`start_time`),
  KEY `idx_scan_status_script_start` (`script_name`,`start_time`),
  KEY `idx_status_start` (`start_time`) COMMENT 'Índice para buscar scans ativos ordenados por início'
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_scan_status_backup_20251211`
--

DROP TABLE IF EXISTS `tb_scan_status_backup_20251211`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_scan_status_backup_20251211` (
  `id` bigint(20) NOT NULL DEFAULT 0,
  `scan_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `script_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime DEFAULT NULL,
  `status` enum('INICIADO','EM_ANDAMENTO','CONCLUIDO','FALHOU','CANCELADO') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'INICIADO',
  `total_items` int(11) DEFAULT 0,
  `processed_items` int(11) DEFAULT 0,
  `failed_items` int(11) DEFAULT 0,
  `success_rate` decimal(5,2) DEFAULT 0.00,
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `parameters` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`parameters`)),
  `progress_percentage` decimal(5,2) DEFAULT 0.00,
  `estimated_completion` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `process_pid` int(11) DEFAULT NULL COMMENT 'PID do processo que está executando o scan',
  `server_hostname` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Hostname do servidor que está executando o scan'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_usb_devices`
--

DROP TABLE IF EXISTS `tb_usb_devices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_usb_devices` (
  `vendor_id` varchar(10) NOT NULL,
  `product_id` varchar(10) NOT NULL,
  `manufacturer_name` varchar(255) DEFAULT NULL,
  `product_description` varchar(255) DEFAULT NULL,
  `device_id` varchar(21) GENERATED ALWAYS AS (concat(`vendor_id`,':',`product_id`)) STORED,
  PRIMARY KEY (`vendor_id`,`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_vpn_monitor`
--

DROP TABLE IF EXISTS `tb_vpn_monitor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_vpn_monitor` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ping_time` datetime DEFAULT NULL,
  `ping_status` varchar(10) DEFAULT NULL,
  `interface_status` varchar(10) DEFAULT NULL,
  `interface_name` varchar(50) DEFAULT NULL,
  `target_ip` varchar(15) NOT NULL DEFAULT '10.1.1.140',
  `monitor_active` tinyint(1) DEFAULT 0,
  `bytes_sent` bigint(20) DEFAULT NULL,
  `bytes_recv` bigint(20) DEFAULT NULL,
  `total_bytes` bigint(20) DEFAULT NULL,
  `bytes_sent_delta` bigint(20) DEFAULT 0,
  `bytes_recv_delta` bigint(20) DEFAULT 0,
  `total_bytes_delta` bigint(20) DEFAULT 0,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_ping_time` (`ping_time`),
  KEY `idx_ping_status` (`ping_status`),
  KEY `idx_interface_status` (`interface_status`),
  KEY `idx_monitor_active` (`monitor_active`),
  KEY `idx_target_ip` (`target_ip`)
) ENGINE=InnoDB AUTO_INCREMENT=579 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_vpn_status`
--

DROP TABLE IF EXISTS `tb_vpn_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_vpn_status` (
  `id` int(11) NOT NULL DEFAULT 1,
  `ping_status` enum('UP','DOWN') NOT NULL DEFAULT 'DOWN',
  `interface_status` enum('UP','DOWN','NOT_FOUND') NOT NULL DEFAULT 'DOWN',
  `last_ping_time` datetime DEFAULT NULL,
  `last_update` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `monitor_active` tinyint(1) DEFAULT 0,
  `error_count` int(11) DEFAULT 0,
  `last_error` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `chk_single_row` CHECK (`id` = 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_web_access_log`
--

DROP TABLE IF EXISTS `tb_web_access_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_web_access_log` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned DEFAULT NULL,
  `username` varchar(64) DEFAULT NULL,
  `ip` varchar(64) DEFAULT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  `action` varchar(64) NOT NULL,
  `success` tinyint(1) NOT NULL DEFAULT 0,
  `details` varchar(255) DEFAULT NULL,
  `path` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_access_user_id` (`user_id`),
  KEY `idx_access_username` (`username`),
  KEY `idx_access_created_at` (`created_at`),
  CONSTRAINT `fk_access_user` FOREIGN KEY (`user_id`) REFERENCES `tb_web_users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3453 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_web_user_page_permissions`
--

DROP TABLE IF EXISTS `tb_web_user_page_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_web_user_page_permissions` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned NOT NULL,
  `page` varchar(64) NOT NULL,
  `allowed` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_page` (`user_id`,`page`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `fk_perm_user` FOREIGN KEY (`user_id`) REFERENCES `tb_web_users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_web_users`
--

DROP TABLE IF EXISTS `tb_web_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tb_web_users` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(64) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` varchar(32) NOT NULL DEFAULT 'user',
  `active` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_web_users_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary view structure for view `v_active_alerts`
--

DROP TABLE IF EXISTS `v_active_alerts`;
/*!50001 DROP VIEW IF EXISTS `v_active_alerts`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_active_alerts` AS SELECT 
 1 AS `id`,
 1 AS `alert_type`,
 1 AS `severity`,
 1 AS `title`,
 1 AS `message`,
 1 AS `script_name`,
 1 AS `ip`,
 1 AS `java`,
 1 AS `created_at`,
 1 AS `age_minutes`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_b12_auth_errors`
--

DROP TABLE IF EXISTS `v_b12_auth_errors`;
/*!50001 DROP VIEW IF EXISTS `v_b12_auth_errors`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_b12_auth_errors` AS SELECT 
 1 AS `id`,
 1 AS `b12_ip`,
 1 AS `subnet_ip`,
 1 AS `ssh_status`,
 1 AS `ssh_error_type`,
 1 AS `ssh_error_message`,
 1 AS `ssh_error_timestamp`,
 1 AS `ssh_last_success`,
 1 AS `net_type`,
 1 AS `java`,
 1 AS `hostname`,
 1 AS `data_registro`,
 1 AS `hours_since_error`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_b12_never_connected`
--

DROP TABLE IF EXISTS `v_b12_never_connected`;
/*!50001 DROP VIEW IF EXISTS `v_b12_never_connected`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_b12_never_connected` AS SELECT 
 1 AS `id`,
 1 AS `b12_ip`,
 1 AS `subnet_ip`,
 1 AS `ssh_status`,
 1 AS `ssh_error_type`,
 1 AS `ssh_error_message`,
 1 AS `ssh_error_timestamp`,
 1 AS `net_type`,
 1 AS `data_registro`,
 1 AS `days_since_error`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_current_scan_status`
--

DROP TABLE IF EXISTS `v_current_scan_status`;
/*!50001 DROP VIEW IF EXISTS `v_current_scan_status`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_current_scan_status` AS SELECT 
 1 AS `scan_id`,
 1 AS `script_name`,
 1 AS `start_time`,
 1 AS `status`,
 1 AS `total_items`,
 1 AS `processed_items`,
 1 AS `failed_items`,
 1 AS `success_rate`,
 1 AS `progress_percentage`,
 1 AS `estimated_completion`,
 1 AS `duration_minutes`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_hardware_auth_errors`
--

DROP TABLE IF EXISTS `v_hardware_auth_errors`;
/*!50001 DROP VIEW IF EXISTS `v_hardware_auth_errors`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_hardware_auth_errors` AS SELECT 
 1 AS `java`,
 1 AS `ip`,
 1 AS `tipo_equipamento`,
 1 AS `error_type`,
 1 AS `error_message`,
 1 AS `protocol_used`,
 1 AS `attempt_number`,
 1 AS `scan_timestamp`,
 1 AS `last_success_scan`,
 1 AS `hours_since_error`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_hardware_errors_stats`
--

DROP TABLE IF EXISTS `v_hardware_errors_stats`;
/*!50001 DROP VIEW IF EXISTS `v_hardware_errors_stats`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_hardware_errors_stats` AS SELECT 
 1 AS `error_type`,
 1 AS `protocol_used`,
 1 AS `total_errors`,
 1 AS `dispositivos_afetados`,
 1 AS `primeiro_erro`,
 1 AS `ultimo_erro`,
 1 AS `media_tentativas`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_hardware_never_success`
--

DROP TABLE IF EXISTS `v_hardware_never_success`;
/*!50001 DROP VIEW IF EXISTS `v_hardware_never_success`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_hardware_never_success` AS SELECT 
 1 AS `java`,
 1 AS `ip`,
 1 AS `tipo_equipamento`,
 1 AS `ultima_tentativa`,
 1 AS `total_tentativas`,
 1 AS `tipos_erro`,
 1 AS `protocolos_tentados`,
 1 AS `days_since_last_attempt`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_hardware_recurring_errors`
--

DROP TABLE IF EXISTS `v_hardware_recurring_errors`;
/*!50001 DROP VIEW IF EXISTS `v_hardware_recurring_errors`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_hardware_recurring_errors` AS SELECT 
 1 AS `java`,
 1 AS `ip`,
 1 AS `tipo_equipamento`,
 1 AS `error_type`,
 1 AS `protocol_used`,
 1 AS `total_tentativas`,
 1 AS `ultima_tentativa`,
 1 AS `primeira_tentativa`,
 1 AS `duracao_horas`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_scan_items_for_retry`
--

DROP TABLE IF EXISTS `v_scan_items_for_retry`;
/*!50001 DROP VIEW IF EXISTS `v_scan_items_for_retry`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_scan_items_for_retry` AS SELECT 
 1 AS `scan_id`,
 1 AS `item_type`,
 1 AS `item_identifier`,
 1 AS `hostname`,
 1 AS `status`,
 1 AS `attempts`,
 1 AS `max_attempts`,
 1 AS `error_message`,
 1 AS `updated_at`,
 1 AS `minutes_since_last_attempt`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_scan_monitoring`
--

DROP TABLE IF EXISTS `v_scan_monitoring`;
/*!50001 DROP VIEW IF EXISTS `v_scan_monitoring`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_scan_monitoring` AS SELECT 
 1 AS `scan_id`,
 1 AS `script_name`,
 1 AS `status`,
 1 AS `start_time`,
 1 AS `end_time`,
 1 AS `total_items`,
 1 AS `processed_items`,
 1 AS `failed_items`,
 1 AS `progress_percentage`,
 1 AS `estimated_completion`,
 1 AS `process_pid`,
 1 AS `server_hostname`,
 1 AS `duration_minutes`,
 1 AS `pending_items`,
 1 AS `processing_items`,
 1 AS `success_items`,
 1 AS `failed_items_detail`,
 1 AS `skipped_items`,
 1 AS `stuck_items`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_scan_stuck_processes`
--

DROP TABLE IF EXISTS `v_scan_stuck_processes`;
/*!50001 DROP VIEW IF EXISTS `v_scan_stuck_processes`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_scan_stuck_processes` AS SELECT 
 1 AS `scan_id`,
 1 AS `item_type`,
 1 AS `item_identifier`,
 1 AS `hostname`,
 1 AS `start_time`,
 1 AS `last_heartbeat`,
 1 AS `minutes_without_heartbeat`,
 1 AS `total_processing_minutes`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_scan_summary`
--

DROP TABLE IF EXISTS `v_scan_summary`;
/*!50001 DROP VIEW IF EXISTS `v_scan_summary`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_scan_summary` AS SELECT 
 1 AS `script_name`,
 1 AS `scan_date`,
 1 AS `total_scans`,
 1 AS `successful_scans`,
 1 AS `failed_scans`,
 1 AS `avg_success_rate`,
 1 AS `avg_duration_seconds`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_ssh_errors_stats`
--

DROP TABLE IF EXISTS `v_ssh_errors_stats`;
/*!50001 DROP VIEW IF EXISTS `v_ssh_errors_stats`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_ssh_errors_stats` AS SELECT 
 1 AS `ssh_error_type`,
 1 AS `total_errors`,
 1 AS `b12s_afetados`,
 1 AS `primeiro_erro`,
 1 AS `ultimo_erro`*/;
SET character_set_client = @saved_cs_client;

--
-- Dumping events for database 'rd_devices_dev'
--

--
-- Dumping routines for database 'rd_devices_dev'
--

--
-- Current Database: `rd_devices_dev`
--

USE `rd_devices_dev`;

--
-- Final view structure for view `cs_devices`
--

/*!50001 DROP VIEW IF EXISTS `cs_devices`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `cs_devices` AS select `d`.`java` AS `java`,`d`.`ip` AS `ip`,`c`.`device_id` AS `device_id`,`d`.`device_name` AS `device_name`,`d`.`hostname` AS `hostname`,`d`.`groupname` AS `groupname`,`d`.`bandeira` AS `bandeira`,`d`.`cpu` AS `cpu`,`d`.`cores` AS `cores`,`d`.`ram_gb` AS `ram_gb`,`d`.`disk_gb` AS `disk_gb`,`d`.`os` AS `os`,`d`.`os_version` AS `os_version`,`d`.`scan_date` AS `scan_date` from ((`tb_devices` `d` join (select `tb_devices`.`device_id` AS `device_id`,`tb_devices`.`ip` AS `ip`,max(`tb_devices`.`job_id`) AS `max_job_id` from `tb_devices` group by `tb_devices`.`device_id`,`tb_devices`.`ip`) `latest_devices` on(lcase(`d`.`device_id`) = lcase(`latest_devices`.`device_id`) and `d`.`ip` = `latest_devices`.`ip` and `d`.`job_id` = `latest_devices`.`max_job_id`)) join `tb_devices_catalog` `c` on(lcase(`d`.`device_id`) = lcase(`c`.`device_id`))) group by `d`.`java`,`d`.`ip`,`c`.`device_id`,`d`.`device_name`,`d`.`hostname`,`d`.`groupname`,`d`.`bandeira`,`d`.`cpu`,`d`.`cores`,`d`.`ram_gb`,`d`.`disk_gb`,`d`.`os`,`d`.`os_version` order by `d`.`java`,inet_aton(`d`.`ip`),`c`.`device_id` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `cs_scan_control`
--

/*!50001 DROP VIEW IF EXISTS `cs_scan_control`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `cs_scan_control` AS select `t1`.`scan_id` AS `scan_id`,`t1`.`java` AS `java`,`t1`.`bandeira` AS `bandeira`,`t1`.`ip` AS `ip`,`t1`.`start_time` AS `start_time`,`t1`.`end_time` AS `end_time`,`t1`.`status` AS `status`,`t1`.`attempts` AS `attempts`,`t1`.`last_attempt` AS `last_attempt` from (`tb_scan_control` `t1` join (select `tb_scan_control`.`ip` AS `ip`,max(`tb_scan_control`.`scan_id`) AS `max_scan_id` from `tb_scan_control` group by `tb_scan_control`.`ip`) `t2` on(`t1`.`ip` = `t2`.`ip` and `t1`.`scan_id` = `t2`.`max_scan_id`)) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `cs_service`
--

/*!50001 DROP VIEW IF EXISTS `cs_service`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `cs_service` AS select `d`.`java` AS `java`,`d`.`ip` AS `ip`,`c`.`device_id` AS `device_id`,`d`.`device_name` AS `device_name`,`d`.`hostname` AS `hostname`,`d`.`groupname` AS `groupname`,`d`.`bandeira` AS `bandeira`,`d`.`cpu` AS `cpu`,`d`.`cores` AS `cores`,`d`.`ram_gb` AS `ram_gb`,`d`.`disk_gb` AS `disk_gb`,`d`.`os` AS `os`,`d`.`os_version` AS `os_version`,`d`.`scan_date` AS `scan_date`,`d`.`tcprinterservice` AS `tcprinterservice`,`d`.`tcscannerservice` AS `tcscannerservice`,`d`.`tcbiometriaservice` AS `tcbiometriaservice`,`d`.`tccontroladosprinterservice` AS `tccontroladosprinterservice` from ((`tb_devices` `d` join (select `tb_devices`.`device_id` AS `device_id`,`tb_devices`.`ip` AS `ip`,max(`tb_devices`.`job_id`) AS `max_job_id` from `tb_devices` group by `tb_devices`.`device_id`,`tb_devices`.`ip`) `latest_devices` on(lcase(`d`.`device_id`) = lcase(`latest_devices`.`device_id`) and `d`.`ip` = `latest_devices`.`ip` and `d`.`job_id` = `latest_devices`.`max_job_id`)) join `tb_devices_catalog` `c` on(lcase(`d`.`device_id`) = lcase(`c`.`device_id`))) group by `d`.`java`,`d`.`ip`,`c`.`device_id`,`d`.`device_name`,`d`.`hostname`,`d`.`groupname`,`d`.`bandeira`,`d`.`cpu`,`d`.`cores`,`d`.`ram_gb`,`d`.`disk_gb`,`d`.`os`,`d`.`os_version`,`d`.`tcprinterservice`,`d`.`tcscannerservice`,`d`.`tcbiometriaservice`,`d`.`tccontroladosprinterservice` order by `d`.`java`,inet_aton(`d`.`ip`),`c`.`device_id` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `cs_service3`
--

/*!50001 DROP VIEW IF EXISTS `cs_service3`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `cs_service3` AS select `d`.`java` AS `java`,`d`.`ip` AS `ip`,`c`.`device_id` AS `device_id`,`d`.`device_name` AS `device_name`,`d`.`hostname` AS `hostname`,`d`.`groupname` AS `groupname`,`d`.`bandeira` AS `bandeira`,`d`.`tcprinterservice` AS `tcprinterservice`,`d`.`tcscannerservice` AS `tcscannerservice`,`d`.`tcbiometriaservice` AS `tcbiometriaservice`,`d`.`tccontroladosprinterservice` AS `tccontroladosprinterservice` from ((`tb_devices` `d` join (select `tb_devices`.`device_id` AS `device_id`,`tb_devices`.`ip` AS `ip`,max(`tb_devices`.`job_id`) AS `max_job_id` from `tb_devices` group by `tb_devices`.`device_id`,`tb_devices`.`ip`) `latest_devices` on(lcase(`d`.`device_id`) = lcase(`latest_devices`.`device_id`) and `d`.`ip` = `latest_devices`.`ip` and `d`.`job_id` = `latest_devices`.`max_job_id`)) join `tb_devices_catalog` `c` on(lcase(`d`.`device_id`) = lcase(`c`.`device_id`))) group by `d`.`java`,`d`.`ip`,`c`.`device_id`,`d`.`device_name`,`d`.`hostname`,`d`.`groupname`,`d`.`bandeira`,`d`.`tcprinterservice`,`d`.`tcscannerservice`,`d`.`tcbiometriaservice`,`d`.`tccontroladosprinterservice` order by `d`.`java`,inet_aton(`d`.`ip`),`c`.`device_id` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `cs_service4`
--

/*!50001 DROP VIEW IF EXISTS `cs_service4`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `cs_service4` AS select `d`.`java` AS `java`,`d`.`ip` AS `ip`,`c`.`device_id` AS `device_id`,`d`.`device_name` AS `device_name`,`d`.`hostname` AS `hostname`,`d`.`groupname` AS `groupname`,`d`.`bandeira` AS `bandeira`,`d`.`tcprinterservice` AS `tcprinterservice`,`d`.`tcscannerservice` AS `tcscannerservice`,`d`.`tcbiometriaservice` AS `tcbiometriaservice`,`d`.`tccontroladosprinterservice` AS `tccontroladosprinterservice` from ((`tb_devices` `d` join (select `tb_devices`.`device_id` AS `device_id`,`tb_devices`.`ip` AS `ip`,max(`tb_devices`.`job_id`) AS `max_job_id` from `tb_devices` group by `tb_devices`.`device_id`,`tb_devices`.`ip`) `latest_devices` on(lcase(`d`.`device_id`) = lcase(`latest_devices`.`device_id`) and `d`.`ip` = `latest_devices`.`ip` and `d`.`job_id` = `latest_devices`.`max_job_id`)) join `tb_devices_catalog` `c` on(lcase(`d`.`device_id`) = lcase(`c`.`device_id`))) where `c`.`device_id` = 'Computer' group by `d`.`java`,`d`.`ip`,`c`.`device_id`,`d`.`device_name`,`d`.`hostname`,`d`.`groupname`,`d`.`bandeira`,`d`.`tcprinterservice`,`d`.`tcscannerservice`,`d`.`tcbiometriaservice`,`d`.`tccontroladosprinterservice` order by `d`.`java`,inet_aton(`d`.`ip`),`c`.`device_id` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `cs_service5`
--

/*!50001 DROP VIEW IF EXISTS `cs_service5`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `cs_service5` AS select `d`.`java` AS `java`,`d`.`ip` AS `ip`,`d`.`hostname` AS `hostname`,`d`.`groupname` AS `groupname`,`d`.`bandeira` AS `bandeira`,`d`.`tcprinterservice` AS `tcprinterservice`,`d`.`tcscannerservice` AS `tcscannerservice`,`d`.`tcbiometriaservice` AS `tcbiometriaservice`,`d`.`tccontroladosprinterservice` AS `tccontroladosprinterservice` from (`tb_devices` `d` join (select `tb_devices`.`device_id` AS `device_id`,`tb_devices`.`ip` AS `ip`,max(`tb_devices`.`job_id`) AS `max_job_id` from `tb_devices` group by `tb_devices`.`device_id`,`tb_devices`.`ip`) `latest_devices` on(lcase(`d`.`device_id`) = lcase(`latest_devices`.`device_id`) and `d`.`ip` = `latest_devices`.`ip` and `d`.`job_id` = `latest_devices`.`max_job_id`)) group by `d`.`java`,`d`.`ip`,`d`.`hostname`,`d`.`groupname`,`d`.`bandeira`,`d`.`tcprinterservice`,`d`.`tcscannerservice`,`d`.`tcbiometriaservice`,`d`.`tccontroladosprinterservice` order by `d`.`java`,inet_aton(`d`.`ip`) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_active_alerts`
--

/*!50001 DROP VIEW IF EXISTS `v_active_alerts`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `v_active_alerts` AS select `tb_alerts`.`id` AS `id`,`tb_alerts`.`alert_type` AS `alert_type`,`tb_alerts`.`severity` AS `severity`,`tb_alerts`.`title` AS `title`,`tb_alerts`.`message` AS `message`,`tb_alerts`.`script_name` AS `script_name`,`tb_alerts`.`ip` AS `ip`,`tb_alerts`.`java` AS `java`,`tb_alerts`.`created_at` AS `created_at`,timestampdiff(MINUTE,`tb_alerts`.`created_at`,current_timestamp()) AS `age_minutes` from `tb_alerts` where `tb_alerts`.`status` = 'ACTIVE' order by `tb_alerts`.`severity` desc,`tb_alerts`.`created_at` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_b12_auth_errors`
--

/*!50001 DROP VIEW IF EXISTS `v_b12_auth_errors`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_uca1400_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `v_b12_auth_errors` AS select `tb_network_subnets_type`.`id` AS `id`,`tb_network_subnets_type`.`b12_ip` AS `b12_ip`,`tb_network_subnets_type`.`subnet_ip` AS `subnet_ip`,`tb_network_subnets_type`.`ssh_status` AS `ssh_status`,`tb_network_subnets_type`.`ssh_error_type` AS `ssh_error_type`,`tb_network_subnets_type`.`ssh_error_message` AS `ssh_error_message`,`tb_network_subnets_type`.`ssh_error_timestamp` AS `ssh_error_timestamp`,`tb_network_subnets_type`.`ssh_last_success` AS `ssh_last_success`,`tb_network_subnets_type`.`net_type` AS `net_type`,`tb_network_subnets_type`.`java` AS `java`,`tb_network_subnets_type`.`hostname` AS `hostname`,`tb_network_subnets_type`.`data_registro` AS `data_registro`,timestampdiff(HOUR,`tb_network_subnets_type`.`ssh_error_timestamp`,current_timestamp()) AS `hours_since_error` from `tb_network_subnets_type` where `tb_network_subnets_type`.`ssh_error_type` in ('auth_failed','auth_user_invalid','auth_password_invalid') order by `tb_network_subnets_type`.`ssh_error_timestamp` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_b12_never_connected`
--

/*!50001 DROP VIEW IF EXISTS `v_b12_never_connected`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_uca1400_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `v_b12_never_connected` AS select `tb_network_subnets_type`.`id` AS `id`,`tb_network_subnets_type`.`b12_ip` AS `b12_ip`,`tb_network_subnets_type`.`subnet_ip` AS `subnet_ip`,`tb_network_subnets_type`.`ssh_status` AS `ssh_status`,`tb_network_subnets_type`.`ssh_error_type` AS `ssh_error_type`,`tb_network_subnets_type`.`ssh_error_message` AS `ssh_error_message`,`tb_network_subnets_type`.`ssh_error_timestamp` AS `ssh_error_timestamp`,`tb_network_subnets_type`.`net_type` AS `net_type`,`tb_network_subnets_type`.`data_registro` AS `data_registro`,timestampdiff(DAY,`tb_network_subnets_type`.`ssh_error_timestamp`,current_timestamp()) AS `days_since_error` from `tb_network_subnets_type` where `tb_network_subnets_type`.`ssh_last_success` is null and `tb_network_subnets_type`.`ssh_error_type` is not null and `tb_network_subnets_type`.`ssh_error_type` <> 'success' order by `tb_network_subnets_type`.`ssh_error_timestamp` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_current_scan_status`
--

/*!50001 DROP VIEW IF EXISTS `v_current_scan_status`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `v_current_scan_status` AS select `tb_scan_status`.`scan_id` AS `scan_id`,`tb_scan_status`.`script_name` AS `script_name`,`tb_scan_status`.`start_time` AS `start_time`,`tb_scan_status`.`status` AS `status`,`tb_scan_status`.`total_items` AS `total_items`,`tb_scan_status`.`processed_items` AS `processed_items`,`tb_scan_status`.`failed_items` AS `failed_items`,`tb_scan_status`.`success_rate` AS `success_rate`,`tb_scan_status`.`progress_percentage` AS `progress_percentage`,`tb_scan_status`.`estimated_completion` AS `estimated_completion`,timestampdiff(MINUTE,`tb_scan_status`.`start_time`,coalesce(`tb_scan_status`.`end_time`,current_timestamp())) AS `duration_minutes` from `tb_scan_status` where `tb_scan_status`.`status` in ('INICIADO','EM_ANDAMENTO') order by `tb_scan_status`.`start_time` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_hardware_auth_errors`
--

/*!50001 DROP VIEW IF EXISTS `v_hardware_auth_errors`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_uca1400_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `v_hardware_auth_errors` AS select `tb_devices_detail_log`.`java` AS `java`,`tb_devices_detail_log`.`ip` AS `ip`,`tb_devices_detail_log`.`tipo_equipamento` AS `tipo_equipamento`,`tb_devices_detail_log`.`error_type` AS `error_type`,`tb_devices_detail_log`.`mensagem` AS `error_message`,`tb_devices_detail_log`.`protocol_used` AS `protocol_used`,`tb_devices_detail_log`.`attempt_number` AS `attempt_number`,`tb_devices_detail_log`.`data_scan` AS `scan_timestamp`,`tb_devices_detail_log`.`last_success_scan` AS `last_success_scan`,timestampdiff(HOUR,`tb_devices_detail_log`.`data_scan`,current_timestamp()) AS `hours_since_error` from `tb_devices_detail_log` where `tb_devices_detail_log`.`error_type` in ('auth_failed','auth_user_invalid','auth_password_invalid','ssh_auth_failed','wmi_auth_failed') order by `tb_devices_detail_log`.`data_scan` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_hardware_errors_stats`
--

/*!50001 DROP VIEW IF EXISTS `v_hardware_errors_stats`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_uca1400_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `v_hardware_errors_stats` AS select `tb_devices_detail_log`.`error_type` AS `error_type`,`tb_devices_detail_log`.`protocol_used` AS `protocol_used`,count(0) AS `total_errors`,count(distinct concat(`tb_devices_detail_log`.`java`,'-',`tb_devices_detail_log`.`ip`)) AS `dispositivos_afetados`,min(`tb_devices_detail_log`.`data_scan`) AS `primeiro_erro`,max(`tb_devices_detail_log`.`data_scan`) AS `ultimo_erro`,avg(`tb_devices_detail_log`.`attempt_number`) AS `media_tentativas` from `tb_devices_detail_log` where `tb_devices_detail_log`.`error_type` is not null and `tb_devices_detail_log`.`error_type` <> 'success' group by `tb_devices_detail_log`.`error_type`,`tb_devices_detail_log`.`protocol_used` order by count(0) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_hardware_never_success`
--

/*!50001 DROP VIEW IF EXISTS `v_hardware_never_success`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_uca1400_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `v_hardware_never_success` AS select `tb_devices_detail_log`.`java` AS `java`,`tb_devices_detail_log`.`ip` AS `ip`,`tb_devices_detail_log`.`tipo_equipamento` AS `tipo_equipamento`,max(`tb_devices_detail_log`.`data_scan`) AS `ultima_tentativa`,count(0) AS `total_tentativas`,group_concat(distinct `tb_devices_detail_log`.`error_type` order by `tb_devices_detail_log`.`error_type` ASC separator ',') AS `tipos_erro`,group_concat(distinct `tb_devices_detail_log`.`protocol_used` order by `tb_devices_detail_log`.`protocol_used` ASC separator ',') AS `protocolos_tentados`,timestampdiff(DAY,max(`tb_devices_detail_log`.`data_scan`),current_timestamp()) AS `days_since_last_attempt` from `tb_devices_detail_log` where `tb_devices_detail_log`.`last_success_scan` is null and (`tb_devices_detail_log`.`error_type` is null or `tb_devices_detail_log`.`error_type` <> 'success') group by `tb_devices_detail_log`.`java`,`tb_devices_detail_log`.`ip`,`tb_devices_detail_log`.`tipo_equipamento` order by max(`tb_devices_detail_log`.`data_scan`) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_hardware_recurring_errors`
--

/*!50001 DROP VIEW IF EXISTS `v_hardware_recurring_errors`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_uca1400_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `v_hardware_recurring_errors` AS select `tb_devices_detail_log`.`java` AS `java`,`tb_devices_detail_log`.`ip` AS `ip`,`tb_devices_detail_log`.`tipo_equipamento` AS `tipo_equipamento`,`tb_devices_detail_log`.`error_type` AS `error_type`,`tb_devices_detail_log`.`protocol_used` AS `protocol_used`,count(0) AS `total_tentativas`,max(`tb_devices_detail_log`.`data_scan`) AS `ultima_tentativa`,min(`tb_devices_detail_log`.`data_scan`) AS `primeira_tentativa`,timestampdiff(HOUR,min(`tb_devices_detail_log`.`data_scan`),max(`tb_devices_detail_log`.`data_scan`)) AS `duracao_horas` from `tb_devices_detail_log` where `tb_devices_detail_log`.`error_type` is not null and `tb_devices_detail_log`.`error_type` <> 'success' group by `tb_devices_detail_log`.`java`,`tb_devices_detail_log`.`ip`,`tb_devices_detail_log`.`tipo_equipamento`,`tb_devices_detail_log`.`error_type`,`tb_devices_detail_log`.`protocol_used` having `total_tentativas` >= 3 order by count(0) desc,max(`tb_devices_detail_log`.`data_scan`) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_scan_items_for_retry`
--

/*!50001 DROP VIEW IF EXISTS `v_scan_items_for_retry`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_uca1400_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `v_scan_items_for_retry` AS select `sd`.`scan_id` AS `scan_id`,`sd`.`item_type` AS `item_type`,`sd`.`item_identifier` AS `item_identifier`,`sd`.`hostname` AS `hostname`,`sd`.`status` AS `status`,`sd`.`attempts` AS `attempts`,`sd`.`max_attempts` AS `max_attempts`,`sd`.`error_message` AS `error_message`,`sd`.`updated_at` AS `updated_at`,timestampdiff(MINUTE,`sd`.`updated_at`,current_timestamp()) AS `minutes_since_last_attempt` from `tb_scan_details` `sd` where `sd`.`status` in ('FAILED','PENDING') and `sd`.`attempts` < `sd`.`max_attempts` order by `sd`.`attempts`,`sd`.`updated_at` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_scan_monitoring`
--

/*!50001 DROP VIEW IF EXISTS `v_scan_monitoring`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_uca1400_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `v_scan_monitoring` AS select `ss`.`scan_id` AS `scan_id`,`ss`.`script_name` AS `script_name`,`ss`.`status` AS `status`,`ss`.`start_time` AS `start_time`,`ss`.`end_time` AS `end_time`,`ss`.`total_items` AS `total_items`,`ss`.`processed_items` AS `processed_items`,`ss`.`failed_items` AS `failed_items`,`ss`.`progress_percentage` AS `progress_percentage`,`ss`.`estimated_completion` AS `estimated_completion`,`ss`.`process_pid` AS `process_pid`,`ss`.`server_hostname` AS `server_hostname`,timestampdiff(MINUTE,`ss`.`start_time`,coalesce(`ss`.`end_time`,current_timestamp())) AS `duration_minutes`,(select count(0) from `tb_scan_details` where `tb_scan_details`.`scan_id` = `ss`.`scan_id` and `tb_scan_details`.`status` = 'PENDING') AS `pending_items`,(select count(0) from `tb_scan_details` where `tb_scan_details`.`scan_id` = `ss`.`scan_id` and `tb_scan_details`.`status` = 'PROCESSING') AS `processing_items`,(select count(0) from `tb_scan_details` where `tb_scan_details`.`scan_id` = `ss`.`scan_id` and `tb_scan_details`.`status` = 'SUCCESS') AS `success_items`,(select count(0) from `tb_scan_details` where `tb_scan_details`.`scan_id` = `ss`.`scan_id` and `tb_scan_details`.`status` = 'FAILED') AS `failed_items_detail`,(select count(0) from `tb_scan_details` where `tb_scan_details`.`scan_id` = `ss`.`scan_id` and `tb_scan_details`.`status` = 'SKIPPED') AS `skipped_items`,(select count(0) from `tb_scan_details` where `tb_scan_details`.`scan_id` = `ss`.`scan_id` and `tb_scan_details`.`status` = 'PROCESSING' and `tb_scan_details`.`last_heartbeat` is not null and timestampdiff(MINUTE,`tb_scan_details`.`last_heartbeat`,current_timestamp()) > 10) AS `stuck_items` from `tb_scan_status` `ss` where `ss`.`status` in ('INICIADO','EM_ANDAMENTO') order by `ss`.`start_time` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_scan_stuck_processes`
--

/*!50001 DROP VIEW IF EXISTS `v_scan_stuck_processes`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_uca1400_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `v_scan_stuck_processes` AS select `sd`.`scan_id` AS `scan_id`,`sd`.`item_type` AS `item_type`,`sd`.`item_identifier` AS `item_identifier`,`sd`.`hostname` AS `hostname`,`sd`.`start_time` AS `start_time`,`sd`.`last_heartbeat` AS `last_heartbeat`,timestampdiff(MINUTE,`sd`.`last_heartbeat`,current_timestamp()) AS `minutes_without_heartbeat`,timestampdiff(MINUTE,`sd`.`start_time`,current_timestamp()) AS `total_processing_minutes` from `tb_scan_details` `sd` where `sd`.`status` = 'PROCESSING' and (`sd`.`last_heartbeat` is not null and timestampdiff(MINUTE,`sd`.`last_heartbeat`,current_timestamp()) > 10 or `sd`.`last_heartbeat` is null and timestampdiff(MINUTE,`sd`.`start_time`,current_timestamp()) > 30) order by `sd`.`start_time` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_scan_summary`
--

/*!50001 DROP VIEW IF EXISTS `v_scan_summary`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `v_scan_summary` AS select `tb_scan_status`.`script_name` AS `script_name`,cast(`tb_scan_status`.`start_time` as date) AS `scan_date`,count(0) AS `total_scans`,sum(case when `tb_scan_status`.`status` = 'CONCLUIDO' then 1 else 0 end) AS `successful_scans`,sum(case when `tb_scan_status`.`status` = 'FALHOU' then 1 else 0 end) AS `failed_scans`,avg(`tb_scan_status`.`success_rate`) AS `avg_success_rate`,avg(timestampdiff(SECOND,`tb_scan_status`.`start_time`,`tb_scan_status`.`end_time`)) AS `avg_duration_seconds` from `tb_scan_status` group by `tb_scan_status`.`script_name`,cast(`tb_scan_status`.`start_time` as date) order by cast(`tb_scan_status`.`start_time` as date) desc,`tb_scan_status`.`script_name` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_ssh_errors_stats`
--

/*!50001 DROP VIEW IF EXISTS `v_ssh_errors_stats`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_uca1400_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`192.168.10.%` SQL SECURITY DEFINER */
/*!50001 VIEW `v_ssh_errors_stats` AS select `tb_network_subnets_type`.`ssh_error_type` AS `ssh_error_type`,count(0) AS `total_errors`,count(distinct `tb_network_subnets_type`.`b12_ip`) AS `b12s_afetados`,min(`tb_network_subnets_type`.`ssh_error_timestamp`) AS `primeiro_erro`,max(`tb_network_subnets_type`.`ssh_error_timestamp`) AS `ultimo_erro` from `tb_network_subnets_type` where `tb_network_subnets_type`.`ssh_error_type` is not null group by `tb_network_subnets_type`.`ssh_error_type` order by count(0) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-10 22:50:09
