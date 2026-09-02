<?php
declare(strict_types=1);

function rdDevicesLoadConfig(): array
{
    global $RD_DEVICES_WEB_CONFIG;
    static $loaded = false;
    if (!$loaded) {
        $external = '/etc/rd_devices/config.web.php';
        if (is_file($external)) {
            require_once $external;
        } else {
            require_once __DIR__ . DIRECTORY_SEPARATOR . 'config.web.php';
        }
        $loaded = true;
    }
    if (!function_exists('rdDevicesWebConfig')) {
        throw new RuntimeException('Configuracao web do RD Devices nao encontrada.');
    }
    return rdDevicesWebConfig();
}

function webControlConfig(): array
{
    $config = rdDevicesLoadConfig();
    if (empty($config['web_control']) || !is_array($config['web_control'])) {
        throw new RuntimeException('Configuracao web_control ausente em config.web.php.');
    }
    return $config['web_control'];
}

function webControlBasePath(): string
{
    $config = rdDevicesLoadConfig();
    return rtrim((string)($config['base_path'] ?? ''), '/');
}

function webControlUrl(string $path): string
{
    return webControlBasePath() . '/' . ltrim($path, '/');
}

function webControlRedirect(string $path): never
{
    header('Location: ' . webControlUrl($path));
    exit;
}

function webControlSystemSlug(): string
{
    $config = webControlConfig();
    return (string)($config['system_slug'] ?? 'rd_devices');
}

function webControlStartSession(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }
    $config = rdDevicesLoadConfig();
    $session = $config['session'] ?? [];
    session_name((string)($session['name'] ?? 'RD_DEVICES_SESSID'));
    session_set_cookie_params([
        'lifetime' => 0,
        'path' => webControlBasePath() !== '' ? webControlBasePath() : '/',
        'secure' => (bool)($session['secure'] ?? false),
        'httponly' => (bool)($session['httponly'] ?? true),
        'samesite' => (string)($session['samesite'] ?? 'Lax'),
    ]);
    session_start();
}

function webControlPdo(): PDO
{
    static $pdo = null;
    if ($pdo instanceof PDO) {
        return $pdo;
    }
    $config = webControlConfig();
    $db = $config['db'] ?? [];
    $dsn = sprintf(
        'mysql:host=%s;port=%d;dbname=%s;charset=%s',
        $db['host'] ?? '127.0.0.1',
        (int)($db['port'] ?? 3306),
        $db['database'] ?? 'web_control',
        $db['charset'] ?? 'utf8mb4'
    );
    $pdo = new PDO($dsn, (string)($db['user'] ?? ''), (string)($db['password'] ?? ''), [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ]);
    return $pdo;
}

function webControlCurrentUser(): ?array
{
    webControlStartSession();
    return isset($_SESSION['web_control_user']) && is_array($_SESSION['web_control_user'])
        ? $_SESSION['web_control_user']
        : null;
}

function webControlCsrfToken(): string
{
    webControlStartSession();
    if (empty($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return (string)$_SESSION['csrf_token'];
}

function webControlValidateCsrf(?string $token): bool
{
    webControlStartSession();
    return is_string($token) && isset($_SESSION['csrf_token']) && hash_equals((string)$_SESSION['csrf_token'], $token);
}

function webControlClientIp(): ?string
{
    return $_SERVER['REMOTE_ADDR'] ?? null;
}

function webControlUserAgent(): ?string
{
    return isset($_SERVER['HTTP_USER_AGENT']) ? substr((string)$_SERVER['HTTP_USER_AGENT'], 0, 500) : null;
}

function webControlFindSystem(PDO $pdo): ?array
{
    $stmt = $pdo->prepare('SELECT id, is_active FROM tb_web_sistema WHERE slug = ? LIMIT 1');
    $stmt->execute([webControlSystemSlug()]);
    $row = $stmt->fetch();
    return is_array($row) ? $row : null;
}

function webControlLog(?int $userId, ?int $systemId, string $eventType, ?string $pagePath, array $details = []): void
{
    try {
        $stmt = webControlPdo()->prepare('INSERT INTO tb_web_access_log (user_id, sistema_id, event_type, page_path, ip_address, user_agent, details) VALUES (?, ?, ?, ?, ?, ?, ?)');
        $stmt->execute([
            $userId,
            $systemId,
            $eventType,
            $pagePath,
            webControlClientIp(),
            webControlUserAgent(),
            $details ? json_encode($details, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) : null,
        ]);
    } catch (Throwable $e) {
        error_log('web_control log failure: ' . $e->getMessage());
    }
}

function webControlAttemptLogin(string $username, string $password): bool
{
    webControlStartSession();
    $pdo = webControlPdo();
    $system = webControlFindSystem($pdo);
    $systemId = isset($system['id']) ? (int)$system['id'] : null;

    $stmt = $pdo->prepare('SELECT id, username, full_name, email, password_hash, is_active, is_admin FROM tb_web_users WHERE username = ? LIMIT 1');
    $stmt->execute([trim($username)]);
    $user = $stmt->fetch();

    if (!is_array($user) || !(bool)$user['is_active'] || !password_verify($password, (string)$user['password_hash'])) {
        webControlLog(is_array($user) ? (int)$user['id'] : null, $systemId, 'login_failure', '/login.php', ['username' => $username]);
        return false;
    }

    session_regenerate_id(true);
    $_SESSION['web_control_user'] = [
        'id' => (int)$user['id'],
        'username' => (string)$user['username'],
        'full_name' => (string)$user['full_name'],
        'email' => $user['email'],
        'is_admin' => (bool)$user['is_admin'],
    ];
    $pdo->prepare('UPDATE tb_web_users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?')->execute([(int)$user['id']]);
    webControlLog((int)$user['id'], $systemId, 'login_success', '/login.php');
    return true;
}

function webControlLogout(): void
{
    $user = webControlCurrentUser();
    $systemId = null;
    try {
        $system = webControlFindSystem(webControlPdo());
        $systemId = isset($system['id']) ? (int)$system['id'] : null;
    } catch (Throwable $e) {
        error_log('web_control logout failure: ' . $e->getMessage());
    }
    if ($user) {
        webControlLog((int)$user['id'], $systemId, 'logout', '/logout.php');
    }
    $_SESSION = [];
    if (ini_get('session.use_cookies')) {
        $params = session_get_cookie_params();
        setcookie(session_name(), '', time() - 42000, $params['path'], $params['domain'] ?? '', (bool)$params['secure'], (bool)$params['httponly']);
    }
    session_destroy();
}

function webControlRequirePermission(string $pagePath, string $capability = 'can_access'): void
{
    $user = webControlCurrentUser();
    if (!$user) {
        $target = $_SERVER['REQUEST_URI'] ?? webControlUrl($pagePath);
        webControlRedirect('/login.php?redirect=' . rawurlencode($target));
    }

    $pdo = webControlPdo();
    $system = webControlFindSystem($pdo);
    $systemId = isset($system['id']) ? (int)$system['id'] : null;
    $allowed = false;
    $reason = null;

    if (!$system || !(bool)$system['is_active']) {
        $reason = 'system_inactive_or_missing';
    } elseif (!empty($user['is_admin'])) {
        $allowed = true;
    } else {
        $valid = ['can_access', 'can_create', 'can_update', 'can_delete'];
        if (!in_array($capability, $valid, true)) {
            throw new InvalidArgumentException('Capacidade invalida: ' . $capability);
        }
        $stmt = $pdo->prepare("SELECT {$capability} FROM tb_web_user_page_permissions WHERE user_id = ? AND sistema_id = ? AND page_path = ? LIMIT 1");
        $stmt->execute([(int)$user['id'], $systemId, $pagePath]);
        $permission = $stmt->fetch();
        $allowed = is_array($permission) && (bool)$permission[$capability];
        $reason = $allowed ? null : 'permission_missing_or_denied';
    }

    webControlLog((int)$user['id'], $systemId, $allowed ? 'access_allowed' : 'access_denied', $pagePath, $reason ? ['reason' => $reason] : []);

    if (!$allowed) {
        http_response_code(403);
        header('Content-Type: text/html; charset=utf-8');
        echo '<!doctype html><html lang="pt-br"><meta charset="utf-8"><title>Acesso negado</title><body style="font-family:Arial,sans-serif;margin:32px"><h1>Acesso negado</h1><p>Usuario sem permissao para acessar esta pagina.</p><p><a href="' . htmlspecialchars(webControlUrl('/logout.php'), ENT_QUOTES, 'UTF-8') . '">Sair</a></p></body></html>';
        exit;
    }
}

