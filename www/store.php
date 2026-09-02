<?php
declare(strict_types=1);

ini_set('memory_limit', '512M');

require_once __DIR__ . DIRECTORY_SEPARATOR . 'web_control_auth.php';
webControlRequirePermission('/store.php');

function h($value): string {
    return htmlspecialchars((string)($value ?? ''), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function project_root(): string {
    return realpath(__DIR__ . DIRECTORY_SEPARATOR . '..') ?: dirname(__DIR__);
}

function resolve_db_path(): string {
    $root = project_root();
    $candidates = [];
    if (!empty($_GET['db'])) {
        $candidates[] = (string)$_GET['db'];
    }
    if (getenv('RD_DEVICES_DB')) {
        $candidates[] = (string)getenv('RD_DEVICES_DB');
    }
    $candidates[] = 'COLETOR/database/devices.db';
    $candidates[] = 'database/devices.db';
    $candidates[] = 'temp/Preventiva-coletor-3/database/devices.db';

    foreach ($candidates as $candidate) {
        $path = $candidate;
        if (!preg_match('/^[A-Za-z]:[\\\\\\/]/', $path) && !str_starts_with($path, DIRECTORY_SEPARATOR)) {
            $path = $root . DIRECTORY_SEPARATOR . $path;
        }
        $real = realpath($path);
        if ($real && is_file($real) && str_starts_with($real, $root)) {
            return $real;
        }
    }
    throw new RuntimeException('Banco SQLite nao encontrado. Use ?db=caminho/para/devices.db');
}

function table_exists(PDO $pdo, string $table): bool {
    if ($pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql') {
        $stmt = $pdo->prepare("SELECT 1 FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = ? LIMIT 1");
        $stmt->execute([$table]);
        return (bool)$stmt->fetchColumn();
    }

    $stmt = $pdo->prepare("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?");
    $stmt->execute([$table]);
    return (bool)$stmt->fetchColumn();
}

function fetch_rows_from_python(string $dbPath): array {
    $script = __DIR__ . DIRECTORY_SEPARATOR . 'store_export.py';
    $python = getenv('PYTHON') ?: 'python';
    $command = escapeshellcmd($python) . ' ' . escapeshellarg($script) . ' ' . escapeshellarg($dbPath);
    $output = shell_exec($command);
    if ($output === null || trim($output) === '') {
        throw new RuntimeException('PHP sem SQLite e fallback Python nao retornou dados.');
    }
    $rows = json_decode($output, true);
    if (!is_array($rows)) {
        throw new RuntimeException('Falha ao decodificar JSON do fallback Python.');
    }
    return $rows;
}

function bytes_to_gb($bytes): string {
    if ($bytes === null || $bytes === '' || !is_numeric($bytes) || (float)$bytes <= 0) {
        return '-';
    }
    return number_format(((float)$bytes) / 1073741824, 2, ',', '.') . ' GB';
}

function collection_date($value): string {
    $value = trim((string)$value);
    if ($value === '') {
        return '-';
    }
    $timestamp = strtotime($value);
    if ($timestamp === false) {
        return substr($value, 0, 10);
    }
    return date('Y-m-d', $timestamp);
}

function normalize_status(?string $status, ?string $hwScannedAt): string {
    $status = trim((string)$status);
    $lower = strtolower($status);
    if ($hwScannedAt) {
        return 'Coletado';
    }
    if ($status === '') {
        return 'Sem hardware';
    }
    if (str_contains($lower, 'access is denied') || str_contains($lower, '-2147024891')) {
        return 'Bloqueio WMI';
    }
    if (str_contains($lower, 'rpc server is unavailable') || str_contains($lower, '-2147023174')) {
        return 'Erro WMI';
    }
    if (str_starts_with($status, 'WINDOWS_WMI_BLOQUEADO_SSH_INATIVO')) {
        return 'Bloqueio WMI';
    }
    if (str_starts_with($status, 'SSH_') || str_starts_with($status, 'ERRO_SSH')) {
        return 'SSH indisponivel';
    }
    if (str_starts_with($status, 'SNMP_')) {
        return 'SNMP sem resposta';
    }
    return $status;
}

function fetch_rows(PDO $pdo): array {
    $rows = [];

    if (table_exists($pdo, 'tb_devices_detail')) {
        $sql = "
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
        ";
        foreach ($pdo->query($sql)->fetchAll(PDO::FETCH_ASSOC) as $row) {
            $rows[] = $row;
        }
    }

    if (table_exists($pdo, 'tb_detected_devices')) {
        $latestJoin = "";
        $statusExpr = "NULL AS last_status";
        if (table_exists($pdo, 'tb_scan_run_items')) {
            $latestJoin = "
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
            ";
            $statusExpr = "lsi.status AS last_status";
        }

        $sql = "
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
                $statusExpr
            FROM tb_detected_devices d
            $latestJoin
            WHERE NOT EXISTS (
                SELECT 1
                FROM tb_devices_detail dd
                WHERE dd.ip = d.ip COLLATE utf8mb4_general_ci
            )
        ";
        foreach ($pdo->query($sql)->fetchAll(PDO::FETCH_ASSOC) as $row) {
            $row['scan_status'] = normalize_status($row['last_status'] ?? '', $row['scanned_at'] ?? null);
            unset($row['last_status']);
            $rows[] = $row;
        }
    }

    usort($rows, function (array $a, array $b): int {
        $javaA = is_numeric($a['filial'] ?? '') ? (int)$a['filial'] : PHP_INT_MAX;
        $javaB = is_numeric($b['filial'] ?? '') ? (int)$b['filial'] : PHP_INT_MAX;
        if ($javaA !== $javaB) {
            return $javaA <=> $javaB;
        }
        return strnatcmp((string)($a['ip'] ?? ''), (string)($b['ip'] ?? ''));
    });

    return $rows;
}

function filters_active(): bool {
    return trim((string)($_GET['java'] ?? '')) !== ''
        || trim((string)($_GET['tipo'] ?? '')) !== ''
        || trim((string)($_GET['status'] ?? '')) !== ''
        || isset($_GET['consultar']);
}

function parse_java_filter(string $value): array {
    $value = trim($value);
    if ($value === '') {
        return [];
    }

    $parts = preg_split('/\s*,\s*/', $value, -1, PREG_SPLIT_NO_EMPTY) ?: [];
    $filters = [];

    foreach ($parts as $part) {
        $part = trim($part);
        if ($part === '') {
            continue;
        }
        if (preg_match('/^(\d+)\s*-\s*(\d+)$/', $part, $matches)) {
            $start = (int)$matches[1];
            $end = (int)$matches[2];
            if ($start > $end) {
                [$start, $end] = [$end, $start];
            }
            $filters[] = ['type' => 'range', 'start' => $start, 'end' => $end];
            continue;
        }
        if (preg_match('/^\d+$/', $part)) {
            $filters[] = ['type' => 'value', 'value' => $part];
            continue;
        }
        $filters[] = ['type' => 'value', 'value' => $part];
    }

    return $filters;
}

function java_matches_filter(string $java, string $filter): bool {
    $java = trim($java);
    if ($filter === '') {
        return true;
    }

    $parsed = parse_java_filter($filter);
    if ($parsed === []) {
        return $java === $filter;
    }

    foreach ($parsed as $item) {
        if (($item['type'] ?? '') === 'range') {
            if ($java !== '' && is_numeric($java)) {
                $num = (int)$java;
                if ($num >= (int)$item['start'] && $num <= (int)$item['end']) {
                    return true;
                }
            }
            continue;
        }
        if ($java === (string)($item['value'] ?? '')) {
            return true;
        }
    }

    return false;
}

function filtered_rows(array $rows): array {
    $java = trim((string)($_GET['java'] ?? ''));
    $type = trim((string)($_GET['tipo'] ?? ''));
    $status = trim((string)($_GET['status'] ?? ''));

    return array_values(array_filter($rows, function (array $row) use ($java, $type, $status): bool {
        if ($java !== '' && !java_matches_filter((string)($row['filial'] ?? ''), $java)) {
            return false;
        }
        if ($type !== '' && (string)($row['device_type'] ?? '') !== $type) {
            return false;
        }
        if ($status !== '' && normalize_status((string)($row['scan_status'] ?? ''), $row['scanned_at'] ?? null) !== $status) {
            return false;
        }
        return true;
    }));
}

function distinct_values(array $rows, string $field): array {
    $values = [];
    foreach ($rows as $row) {
        $value = (string)($row[$field] ?? '');
        if ($value !== '') {
            $values[$value] = true;
        }
    }
    $values = array_keys($values);
    sort($values, SORT_NATURAL | SORT_FLAG_CASE);
    return $values;
}
function mysql_distinct_values(PDO $pdo, string $field): array {
    if ($pdo->getAttribute(PDO::ATTR_DRIVER_NAME) !== 'mysql') {
        return [];
    }

    if ($field === 'device_type') {
        $sql = "
            SELECT DISTINCT device_type COLLATE utf8mb4_unicode_ci AS value FROM tb_detected_devices WHERE device_type IS NOT NULL AND device_type <> ''
            UNION
            SELECT DISTINCT tipo_equipamento COLLATE utf8mb4_unicode_ci AS value FROM tb_devices_detail WHERE tipo_equipamento IS NOT NULL AND tipo_equipamento <> ''
            ORDER BY value
        ";
    } else {
        return [];
    }

    return array_values(array_filter(array_map('strval', $pdo->query($sql)->fetchAll(PDO::FETCH_COLUMN))));
}

function status_options(): array {
    return ['Coletado', 'Sem hardware', 'Bloqueio WMI', 'Erro WMI', 'SSH indisponivel', 'SNMP sem resposta'];
}

function count_with_hardware(array $rows): int {
    return count(array_filter($rows, fn($r) => !empty($r['scanned_at'])));
}
function mysql_total_devices(PDO $pdo): ?int {
    if ($pdo->getAttribute(PDO::ATTR_DRIVER_NAME) !== 'mysql') {
        return null;
    }

    $total = 0;
    if (table_exists($pdo, 'tb_devices_detail')) {
        $total += (int)$pdo->query('SELECT COUNT(*) FROM tb_devices_detail')->fetchColumn();
    }
    if (table_exists($pdo, 'tb_detected_devices')) {
        if (table_exists($pdo, 'tb_devices_detail')) {
            $sql = "
                SELECT COUNT(*)
                FROM tb_detected_devices d
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM tb_devices_detail dd
                    WHERE dd.ip = d.ip COLLATE utf8mb4_general_ci
                )
            ";
            $total += (int)$pdo->query($sql)->fetchColumn();
        } else {
            $total += (int)$pdo->query('SELECT COUNT(*) FROM tb_detected_devices')->fetchColumn();
        }
    }
    return $total;
}

// ---------------------------------------------------------------------------
// Comparacao "antes x depois" por data de coleta (tabelas de historico).
// ---------------------------------------------------------------------------

const B12_COMPARE_COLS = [
    'hostname', 'sistema_operacional', 'kernel', 'cores_fisicos', 'memoria_total',
    'mac_address', 'mb_manufacturer', 'mb_product_name', 'mb_version',
    'hdd_media_type', 'hdd_model', 'hdd_size',
];

const DETECTED_COMPARE_COLS = [
    'device_type', 'expected_type', 'ssh', 'radmin', 'printer', 'logo',
    'hw_hostname', 'hw_cpu_model', 'hw_os', 'hw_os_version', 'hw_kernel', 'hw_cores_fisicos',
    'hw_memoria_total', 'hw_mac_address', 'hw_mb_manufacturer', 'hw_mb_product_name', 'hw_mb_version',
    'hw_hdd_media_type', 'hw_hdd_model', 'hw_hdd_size',
];

const COMPARE_COL_LABELS = [
    'hostname' => 'Hostname', 'sistema_operacional' => 'SO', 'kernel' => 'Kernel',
    'cores_fisicos' => 'Cores', 'memoria_total' => 'Memoria (bytes)', 'mac_address' => 'MAC',
    'mb_manufacturer' => 'Fabricante placa-mae', 'mb_product_name' => 'Modelo placa-mae',
    'mb_version' => 'Versao placa-mae', 'hdd_media_type' => 'Tipo disco', 'hdd_model' => 'Modelo disco',
    'hdd_size' => 'Tamanho disco (bytes)', 'device_type' => 'Tipo dispositivo',
    'expected_type' => 'Tipo esperado', 'ssh' => 'SSH', 'radmin' => 'Radmin', 'printer' => 'Impressora',
    'logo' => 'Bandeira', 'hw_hostname' => 'Hostname', 'hw_cpu_model' => 'CPU', 'hw_os' => 'SO',
    'hw_os_version' => 'Versao SO', 'hw_kernel' => 'Kernel', 'hw_cores_fisicos' => 'Cores',
    'hw_memoria_total' => 'Memoria (bytes)', 'hw_mac_address' => 'MAC',
    'hw_mb_manufacturer' => 'Fabricante placa-mae', 'hw_mb_product_name' => 'Modelo placa-mae',
    'hw_mb_version' => 'Versao placa-mae', 'hw_hdd_media_type' => 'Tipo disco',
    'hw_hdd_model' => 'Modelo disco', 'hw_hdd_size' => 'Tamanho disco (bytes)',
];

function compare_available(PDO $pdo): bool {
    return table_exists($pdo, 'tb_devices_detail_history') || table_exists($pdo, 'tb_detected_devices_history');
}

// Datas distintas (com coleta) para uma loja, mais recentes primeiro.
function snapshot_dates(PDO $pdo, string $java): array {
    $dates = [];
    if (table_exists($pdo, 'tb_devices_detail_history')) {
        $stmt = $pdo->prepare('SELECT DISTINCT DATE(data_coleta) AS d FROM tb_devices_detail_history WHERE java = ?');
        $stmt->execute([$java]);
        foreach ($stmt->fetchAll(PDO::FETCH_COLUMN) as $d) {
            $dates[$d] = true;
        }
    }
    if (table_exists($pdo, 'tb_detected_devices_history')) {
        $stmt = $pdo->prepare('SELECT DISTINCT DATE(snapshot_at) AS d FROM tb_detected_devices_history WHERE filial = ?');
        $stmt->execute([$java]);
        foreach ($stmt->fetchAll(PDO::FETCH_COLUMN) as $d) {
            $dates[$d] = true;
        }
    }
    $result = array_keys($dates);
    rsort($result);
    return $result;
}

// Ultima linha por IP dentro do dia informado, em tb_devices_detail_history.
function b12_snapshot(PDO $pdo, string $java, string $date): array {
    if (!table_exists($pdo, 'tb_devices_detail_history')) {
        return [];
    }
    $sql = "
        SELECT h.* FROM tb_devices_detail_history h
        INNER JOIN (
            SELECT ip, MAX(data_coleta) AS max_dc
            FROM tb_devices_detail_history
            WHERE java = :java1 AND DATE(data_coleta) = :date
            GROUP BY ip
        ) latest ON latest.ip = h.ip AND latest.max_dc = h.data_coleta
        WHERE h.java = :java2
    ";
    $stmt = $pdo->prepare($sql);
    $stmt->execute(['java1' => $java, 'date' => $date, 'java2' => $java]);
    $out = [];
    foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $row) {
        $out[$row['ip']] = $row;
    }
    return $out;
}

// Ultima linha por IP dentro do dia informado, em tb_detected_devices_history.
function detected_snapshot(PDO $pdo, string $java, string $date): array {
    if (!table_exists($pdo, 'tb_detected_devices_history')) {
        return [];
    }
    $sql = "
        SELECT h.* FROM tb_detected_devices_history h
        INNER JOIN (
            SELECT ip, MAX(snapshot_at) AS max_sa
            FROM tb_detected_devices_history
            WHERE filial = :java1 AND DATE(snapshot_at) = :date
            GROUP BY ip
        ) latest ON latest.ip = h.ip AND latest.max_sa = h.snapshot_at
        WHERE h.filial = :java2
    ";
    $stmt = $pdo->prepare($sql);
    $stmt->execute(['java1' => $java, 'date' => $date, 'java2' => $java]);
    $out = [];
    foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $row) {
        $out[$row['ip']] = $row;
    }
    return $out;
}

// Classifica cada ip em novo / removido / alterado, comparando as colunas informadas.
function diff_snapshots(array $before, array $after, array $compareCols): array {
    $novo = [];
    $removido = [];
    $alterado = [];

    foreach ($after as $ip => $row) {
        if (!isset($before[$ip])) {
            $novo[$ip] = $row;
            continue;
        }
        $changes = [];
        foreach ($compareCols as $col) {
            $old = (string)($before[$ip][$col] ?? '');
            $new = (string)($row[$col] ?? '');
            if ($old !== $new) {
                $changes[] = [$col, $old, $new];
            }
        }
        if ($changes) {
            $alterado[$ip] = ['row' => $row, 'changes' => $changes];
        }
    }
    foreach ($before as $ip => $row) {
        if (!isset($after[$ip])) {
            $removido[$ip] = $row;
        }
    }

    return ['novo' => $novo, 'removido' => $removido, 'alterado' => $alterado];
}

// Retorna o codigo JAVA quando o filtro e um valor unico (nao lista/intervalo);
// string vazia caso contrario. Usado para decidir se o seletor de data de
// coleta faz sentido (so se aplica a uma loja especifica).
function single_java_value(string $filter): string {
    $filter = trim($filter);
    if ($filter === '' || str_contains($filter, ',') || preg_match('/^\d+\s*-\s*\d+$/', $filter)) {
        return '';
    }
    return $filter;
}

// Monta as linhas da tabela principal a partir do historico, como estavam
// naquela data de coleta especifica (em vez do estado atual).
function fetch_rows_at_date(PDO $pdo, string $java, string $date): array {
    $rows = [];
    $b12 = b12_snapshot($pdo, $java, $date);
    foreach ($b12 as $ip => $r) {
        $rows[] = [
            'filial' => $r['java'] ?? $java,
            'ip' => $ip,
            'device_type' => $r['tipo_equipamento'] ?? '',
            'expected_type' => '',
            'logo' => '',
            'hostname' => $r['hostname'] ?? '',
            'os' => $r['sistema_operacional'] ?? '',
            'os_version' => $r['kernel'] ?? '',
            'cores' => $r['cores_fisicos'] ?? '',
            'mem_bytes' => $r['memoria_total'] ?? null,
            'mb_manufacturer' => $r['mb_manufacturer'] ?? '',
            'mb_product_name' => $r['mb_product_name'] ?? '',
            'mb_version' => $r['mb_version'] ?? '',
            'hdd_media_type' => $r['hdd_media_type'] ?? '',
            'hdd_model' => $r['hdd_model'] ?? '',
            'hdd_size' => $r['hdd_size'] ?? null,
            'scanned_at' => $r['data_coleta'] ?? null,
            'source' => 'tb_devices_detail_history',
            'scan_status' => 'Coletado',
        ];
    }

    $detected = detected_snapshot($pdo, $java, $date);
    foreach ($detected as $ip => $r) {
        if (isset($b12[$ip])) {
            continue;
        }
        $rows[] = [
            'filial' => $r['filial'] ?? $java,
            'ip' => $ip,
            'device_type' => $r['device_type'] ?? '',
            'expected_type' => $r['expected_type'] ?? '',
            'logo' => $r['logo'] ?? '',
            'hostname' => $r['hw_hostname'] ?? '',
            'os' => $r['hw_os'] ?? '',
            'os_version' => $r['hw_os_version'] ?? '',
            'cores' => $r['hw_cores_fisicos'] ?? '',
            'mem_bytes' => $r['hw_memoria_total'] ?? null,
            'mb_manufacturer' => $r['hw_mb_manufacturer'] ?? '',
            'mb_product_name' => $r['hw_mb_product_name'] ?? '',
            'mb_version' => $r['hw_mb_version'] ?? '',
            'hdd_media_type' => $r['hw_hdd_media_type'] ?? '',
            'hdd_model' => $r['hw_hdd_model'] ?? '',
            'hdd_size' => $r['hw_hdd_size'] ?? null,
            'scanned_at' => $r['hw_scanned_at'] ?? $r['detected_at'] ?? null,
            'source' => 'tb_detected_devices_history',
            'scan_status' => normalize_status('', $r['hw_scanned_at'] ?? null),
        ];
    }

    usort($rows, function (array $a, array $b): int {
        $javaA = is_numeric($a['filial'] ?? '') ? (int)$a['filial'] : PHP_INT_MAX;
        $javaB = is_numeric($b['filial'] ?? '') ? (int)$b['filial'] : PHP_INT_MAX;
        if ($javaA !== $javaB) {
            return $javaA <=> $javaB;
        }
        return strnatcmp((string)($a['ip'] ?? ''), (string)($b['ip'] ?? ''));
    });

    return $rows;
}

function connect_data_source(): array {
    if (function_exists('getDbConnection')) {
        try {
            $pdo = getDbConnection();
            $config = rdDevicesWebConfig();
            $db = $config['db'] ?? [];
            $label = sprintf('MySQL %s/%s', (string)($db['host'] ?? ''), (string)($db['database'] ?? ''));
            return [$pdo, $label, 'PDO MySQL'];
        } catch (Throwable $e) {
            error_log('Falha ao conectar MySQL rd_devices_dev: ' . $e->getMessage());
        }
    }

    $dbPath = resolve_db_path();
    $drivers = PDO::getAvailableDrivers();
    if (in_array('sqlite', $drivers, true)) {
        $pdo = new PDO('sqlite:' . $dbPath);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        return [$pdo, $dbPath, 'PDO SQLite'];
    }

    return [null, $dbPath, 'Python sqlite3'];
}

[$pdo, $dbPath, $backend] = connect_data_source();
$hasQuery = filters_active();
$rowsAll = [];
$rowsFiltered = [];
$rows = [];
$displayLimit = max(100, min(5000, (int)($_GET['limit'] ?? 1000)));

$isCompare = ($_GET['view'] ?? '') === 'compare';
$compareJava = trim((string)($_GET['java'] ?? ''));
$compareDates = [];
$compareDateBefore = null;
$compareDateAfter = null;
$b12Diff = null;
$detDiff = null;

if ($isCompare && $pdo instanceof PDO && $compareJava !== '') {
    $compareDates = snapshot_dates($pdo, $compareJava);
    $compareDateBefore = $_GET['date_before'] ?? ($compareDates[1] ?? null);
    $compareDateAfter = $_GET['date_after'] ?? ($compareDates[0] ?? null);
    if ($compareDateBefore && $compareDateAfter) {
        $b12Before = b12_snapshot($pdo, $compareJava, $compareDateBefore);
        $b12After = b12_snapshot($pdo, $compareJava, $compareDateAfter);
        $b12Diff = diff_snapshots($b12Before, $b12After, B12_COMPARE_COLS);

        $detBefore = detected_snapshot($pdo, $compareJava, $compareDateBefore);
        $detAfter = detected_snapshot($pdo, $compareJava, $compareDateAfter);
        $detDiff = diff_snapshots($detBefore, $detAfter, DETECTED_COMPARE_COLS);
    }
}

$singleJava = single_java_value((string)($_GET['java'] ?? ''));
$snapshotDates = [];
$snapshotDate = trim((string)($_GET['snapshot_date'] ?? ''));
if ($pdo instanceof PDO && $singleJava !== '' && compare_available($pdo)) {
    $snapshotDates = snapshot_dates($pdo, $singleJava);
    if ($snapshotDate !== '' && !in_array($snapshotDate, $snapshotDates, true)) {
        $snapshotDate = '';
    }
}

// "Atual" (nenhuma data escolhida) para uma loja especifica deve mostrar so a
// coleta mais recente daquela loja — nao o acumulado das tabelas de estado
// atual, que preservam registros de coletas antigas para IPs nao rechecados
// na coleta seguinte. Quando ha historico disponivel, resolve "Atual" para a
// data mais recente (snapshotDates[0], ja ordenado desc).
$effectiveSnapshotDate = $snapshotDate;
if ($effectiveSnapshotDate === '' && $singleJava !== '' && $snapshotDates) {
    $effectiveSnapshotDate = $snapshotDates[0];
}

if ($hasQuery && !$isCompare) {
    if ($pdo instanceof PDO && $singleJava !== '' && $effectiveSnapshotDate !== '') {
        $rowsAll = fetch_rows_at_date($pdo, $singleJava, $effectiveSnapshotDate);
    } elseif ($pdo instanceof PDO) {
        $rowsAll = fetch_rows($pdo);
    } else {
        $rowsAll = fetch_rows_from_python($dbPath);
    }
    $rowsFiltered = filtered_rows($rowsAll);
    $rows = array_slice($rowsFiltered, 0, $displayLimit);
}

$types = ($pdo instanceof PDO) ? mysql_distinct_values($pdo, 'device_type') : distinct_values($rowsAll, 'device_type');
$statuses = status_options();

$total = ($pdo instanceof PDO) ? (mysql_total_devices($pdo) ?? count($rowsAll)) : count($rowsAll);
$filtered = count($rowsFiltered);
$collected = count_with_hardware($rowsFiltered);
$pending = $filtered - $collected;
?>
<!doctype html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>RD Devices - Store</title>
    <style>
        :root { color-scheme: light; --line:#d7dde5; --muted:#667085; --bg:#f6f8fa; --ink:#17212f; }
        body { margin:0; font:14px/1.4 Arial, sans-serif; color:var(--ink); background:var(--bg); }
        header { padding:16px 20px; background:#1d2733; color:#fff; }
        h1 { margin:0 0 4px; font-size:20px; }
        main { padding:16px 20px 28px; }
        .meta, .filters, .summary { display:flex; gap:10px; flex-wrap:wrap; align-items:end; }
        .pill { background:#fff; border:1px solid var(--line); border-radius:6px; padding:8px 10px; }
        .muted { color:var(--muted); }
        label { display:block; color:var(--muted); font-size:12px; margin-bottom:3px; }
        input, select, button, .btn-clear { height:32px; border:1px solid var(--line); border-radius:4px; background:#fff; padding:0 8px; }
        button, .btn-clear { display:inline-flex; align-items:center; justify-content:center; text-decoration:none; }
        button { background:#1d2733; color:#fff; cursor:pointer; }
        .btn-clear { background:#eef2f6; color:#1d2733; cursor:pointer; }
        table { width:100%; border-collapse:collapse; background:#fff; margin-top:14px; }
        th, td { border:1px solid var(--line); padding:6px 8px; text-align:left; vertical-align:top; }
        th { background:#eef2f6; position:sticky; top:0; z-index:1; }
        tr.warn td { background:#fff8e5; }
        tr.fail td { background:#fff0f0; }
        tr.new td { background:#eaffea; }
        .nowrap { white-space:nowrap; }
        .compare-section { margin-top:22px; }
        .compare-section h2 { font-size:16px; margin:0 0 8px; }
        .compare-changes { margin:0; padding-left:18px; }
        .compare-changes li { margin-bottom:2px; }
        .badge { display:inline-block; border-radius:4px; padding:2px 6px; font-size:12px; color:#fff; }
        .badge-new { background:#2e9e44; }
        .badge-removed { background:#c0392b; }
        .badge-changed { background:#b8860b; }
    </style>
</head>
<body>
<header>
    <h1>RD Devices - Consulta de Equipamentos</h1>
    <div class="muted"><?= h($dbPath) ?> | Backend: <?= h($backend) ?></div>
</header>
<main>
    <section class="summary">
        <div class="pill">Total Dispositivos: <strong><?= h($total) ?></strong></div>
        <div class="pill">Filtrados: <strong><?= h($filtered) ?></strong></div>
        <div class="pill">Exibidos: <strong><?= h(count($rows)) ?></strong></div>
        <div class="pill">Com hardware: <strong><?= h($collected) ?></strong></div>
        <div class="pill">Sem hardware: <strong><?= h($pending) ?></strong></div>
        <div class="pill">
            Data coleta:
            <select name="snapshot_date" form="filtersForm" onchange="this.form.submit()" <?= $singleJava === '' ? 'disabled title="Informe um unico JAVA para escolher a data"' : '' ?>>
                <option value="">Atual</option>
                <?php foreach ($snapshotDates as $d): ?>
                    <option value="<?= h($d) ?>" <?= ($d === $snapshotDate) ? 'selected' : '' ?>><?= h($d) ?></option>
                <?php endforeach; ?>
            </select>
        </div>
    </section>

    <form class="filters" id="filtersForm" method="get">

        <div>
            <label>JAVA</label>
            <input name="java" size="18" value="<?= h($_GET['java'] ?? '') ?>" placeholder="1234, 1235 ou 1234-1238">
        </div>
        <div>
            <label>Tipo equipamento</label>
            <select name="tipo">
                <option value="">Todos</option>
                <?php foreach ($types as $type): ?>
                    <option value="<?= h($type) ?>" <?= (($_GET['tipo'] ?? '') === $type) ? 'selected' : '' ?>><?= h($type) ?></option>
                <?php endforeach; ?>
            </select>
        </div>
        <div>
            <label>Status coleta</label>
            <select name="status">
                <option value="">Todos</option>
                <?php foreach ($statuses as $st): ?>
                    <option value="<?= h($st) ?>" <?= (($_GET['status'] ?? '') === $st) ? 'selected' : '' ?>><?= h($st) ?></option>
                <?php endforeach; ?>
            </select>
        </div>

        <input type="hidden" name="consultar" value="1">
        <button type="submit">Filtrar</button>
        <a class="btn-clear" href="store.php">Limpar</a>
        <?php if ($pdo instanceof PDO && compare_available($pdo)): ?>
            <a class="btn-clear" href="?view=compare<?= $compareJava !== '' ? '&java=' . h($compareJava) : '' ?>">Comparar datas</a>
        <?php endif; ?>
    </form>

    <?php if ($isCompare): ?>
        <section class="compare-section">
            <h2>Comparar equipamentos por data — loja <?= h($compareJava ?: '?') ?></h2>
            <?php if (!($pdo instanceof PDO)): ?>
                <p class="muted">Comparacao por data requer conexao PDO (MySQL ou SQLite); backend atual: <?= h($backend) ?>.</p>
            <?php elseif ($compareJava === ''): ?>
                <p class="muted">Informe um codigo JAVA acima (um unico codigo, sem lista/intervalo) e clique em "Comparar datas".</p>
            <?php elseif (count($compareDates) < 2): ?>
                <p class="muted">Apenas <?= h(count($compareDates)) ?> data(s) de coleta disponivel(is) para a loja <?= h($compareJava) ?>; nada para comparar ainda.</p>
            <?php else: ?>
                <form class="filters" method="get">
                    <input type="hidden" name="view" value="compare">
                    <input type="hidden" name="java" value="<?= h($compareJava) ?>">
                    <div>
                        <label>Data anterior</label>
                        <select name="date_before">
                            <?php foreach ($compareDates as $d): ?>
                                <option value="<?= h($d) ?>" <?= ($d === $compareDateBefore) ? 'selected' : '' ?>><?= h($d) ?></option>
                            <?php endforeach; ?>
                        </select>
                    </div>
                    <div>
                        <label>Data posterior</label>
                        <select name="date_after">
                            <?php foreach ($compareDates as $d): ?>
                                <option value="<?= h($d) ?>" <?= ($d === $compareDateAfter) ? 'selected' : '' ?>><?= h($d) ?></option>
                            <?php endforeach; ?>
                        </select>
                    </div>
                    <button type="submit">Comparar</button>
                </form>

                <?php
                $renderCompareTable = function (string $title, array $diff, array $labels) {
                    $total = count($diff['novo']) + count($diff['removido']) + count($diff['alterado']);
                    echo '<h3>' . h($title) . ' (' . h($total) . ' diferenca(s))</h3>';
                    if ($total === 0) {
                        echo '<p class="muted">Nenhuma diferenca encontrada.</p>';
                        return;
                    }
                    echo '<table><thead><tr><th>Status</th><th>IP</th><th>Detalhe</th></tr></thead><tbody>';
                    foreach ($diff['novo'] as $ip => $row) {
                        echo '<tr class="new"><td><span class="badge badge-new">NOVO</span></td><td class="nowrap">' . h($ip) . '</td><td>'
                            . h($row['hostname'] ?? $row['hw_hostname'] ?? '-') . '</td></tr>';
                    }
                    foreach ($diff['removido'] as $ip => $row) {
                        echo '<tr class="fail"><td><span class="badge badge-removed">REMOVIDO</span></td><td class="nowrap">' . h($ip) . '</td><td>'
                            . h($row['hostname'] ?? $row['hw_hostname'] ?? '-') . '</td></tr>';
                    }
                    foreach ($diff['alterado'] as $ip => $info) {
                        echo '<tr class="warn"><td><span class="badge badge-changed">ALTERADO</span></td><td class="nowrap">' . h($ip) . '</td><td><ul class="compare-changes">';
                        foreach ($info['changes'] as [$col, $old, $new]) {
                            $label = $labels[$col] ?? $col;
                            echo '<li><strong>' . h($label) . ':</strong> ' . h($old ?: '-') . ' &rarr; ' . h($new ?: '-') . '</li>';
                        }
                        echo '</ul></td></tr>';
                    }
                    echo '</tbody></table>';
                };
                $renderCompareTable('B12 (SSH)', $b12Diff, COMPARE_COL_LABELS);
                $renderCompareTable('Dispositivos de rede / hardware', $detDiff, COMPARE_COL_LABELS);
                ?>
            <?php endif; ?>
        </section>
    <?php elseif (!$hasQuery): ?>
        <p class="muted">Informe um filtro e clique em Filtrar para consultar os dispositivos.</p>
    <?php else: ?>
    <table>
        <thead>
        <tr>
            <th>JAVA</th>
            <th>IP</th>
            <th>Tipo equipamento</th>
            <th>Hostname</th>
            <th>SO</th>
            <th>Kernel</th>
            <th>Cores</th>
            <th>RAM</th>
            <th>Placa-mae</th>
            <th>Disco</th>
            <th>Status coleta</th>
            <th>Data coleta</th>
        </tr>
        </thead>
        <tbody>
        <?php foreach ($rows as $row):
            $status = normalize_status((string)($row['scan_status'] ?? ''), $row['scanned_at'] ?? null);
            $class = ($status === 'Coletado') ? '' : ((str_contains($status, 'WMI') || str_contains($status, 'SSH')) ? 'fail' : 'warn');
        ?>
            <tr class="<?= h($class) ?>">
                <td class="nowrap"><?= h($row['filial'] ?? '') ?></td>
                <td class="nowrap"><?= h($row['ip'] ?? '') ?></td>
                <td><?= h($row['device_type'] ?? '') ?></td>
                <td><?= h($row['hostname'] ?: '-') ?></td>
                <td><?= h($row['os'] ?: '-') ?></td>
                <td><?= h($row['os_version'] ?: '-') ?></td>
                <td><?= h($row['cores'] ?: '-') ?></td>
                <td class="nowrap"><?= h(bytes_to_gb($row['mem_bytes'] ?? null)) ?></td>
                <td><?= h(trim(($row['mb_manufacturer'] ?? '') . ' ' . ($row['mb_product_name'] ?? '') . ' ' . ($row['mb_version'] ?? '')) ?: '-') ?></td>
                <td><?= h(trim(($row['hdd_media_type'] ?? '') . ' ' . ($row['hdd_model'] ?? '') . ' ' . bytes_to_gb($row['hdd_size'] ?? null)) ?: '-') ?></td>
                <td><?= h($status) ?></td>
                <td class="nowrap"><?= h(collection_date($row['scanned_at'] ?? '')) ?></td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table>
    <?php endif; ?>
</main>
</body>
</html>














