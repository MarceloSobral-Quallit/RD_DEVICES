<?php
declare(strict_types=1);

// Copiar este arquivo para /etc/rd_devices/config.web.php e preencher no servidor.
// Nao publicar senhas reais dentro do DocumentRoot.

$RD_DEVICES_WEB_CONFIG = [
    'system_name' => 'RD Devices',
    'base_path' => '/rd_devices',
    'web_control' => [
        'system_slug' => 'rd_devices',
        'db' => [
            'host' => '127.0.0.1',
            'port' => 3306,
            'database' => 'web_control',
            'user' => 'web_control_www',
            'password' => 'trocar_esta_senha',
            'charset' => 'utf8mb4',
        ],
    ],
    'db' => [
        'host' => '127.0.0.1',
        'port' => 3306,
        'database' => 'rd_devices_dev',
        'user' => 'rd_devices',
        'password' => 'trocar_esta_senha',
        'charset' => 'utf8mb4',
    ],
    'session' => [
        'name' => 'RD_DEVICES_SESSID',
        'secure' => false,
        'httponly' => true,
        'samesite' => 'Lax',
    ],
];

function rdDevicesWebConfig(): array
{
    global $RD_DEVICES_WEB_CONFIG;
    return $RD_DEVICES_WEB_CONFIG;
}

function getDbConnection(): PDO
{
    $config = rdDevicesWebConfig();
    $db = $config['db'];
    $dsn = sprintf(
        'mysql:host=%s;port=%d;dbname=%s;charset=%s',
        $db['host'],
        (int)$db['port'],
        $db['database'],
        $db['charset'] ?? 'utf8mb4'
    );
    return new PDO($dsn, $db['user'], $db['password'], [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ]);
}




