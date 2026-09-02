<?php
declare(strict_types=1);

require_once __DIR__ . DIRECTORY_SEPARATOR . 'web_control_auth.php';

function h($value): string {
    return htmlspecialchars((string)($value ?? ''), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

webControlStartSession();

if (webControlCurrentUser()) {
    webControlRedirect('/store.php');
}

$error = '';
$redirect = (string)($_GET['redirect'] ?? $_POST['redirect'] ?? webControlUrl('/store.php'));
if ($redirect === '') {
    $redirect = webControlUrl('/store.php');
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!webControlValidateCsrf($_POST['csrf_token'] ?? null)) {
        $error = 'Sessao expirada. Recarregue a pagina e tente novamente.';
    } else {
        $username = trim((string)($_POST['username'] ?? ''));
        $password = (string)($_POST['password'] ?? '');
        if ($username !== '' && $password !== '' && webControlAttemptLogin($username, $password)) {
            header('Location: ' . $redirect);
            exit;
        }
        $error = 'Usuario ou senha invalidos.';
    }
}
?>
<!doctype html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>RD Devices - Login</title>
    <style>
        :root { color-scheme: light; --line:#d7dde5; --muted:#667085; --bg:#f6f8fa; --ink:#17212f; }
        body { margin:0; min-height:100vh; display:grid; place-items:center; font:14px/1.4 Arial, sans-serif; color:var(--ink); background:var(--bg); }
        main { width:min(360px, calc(100vw - 32px)); background:#fff; border:1px solid var(--line); border-radius:8px; padding:22px; }
        h1 { margin:0 0 4px; font-size:20px; }
        p { margin:0 0 18px; color:var(--muted); }
        label { display:block; color:var(--muted); font-size:12px; margin:12px 0 4px; }
        input, button { box-sizing:border-box; width:100%; height:36px; border:1px solid var(--line); border-radius:4px; padding:0 9px; }
        button { margin-top:16px; background:#1d2733; color:#fff; cursor:pointer; }
        .error { margin-top:12px; color:#9b1c1c; background:#fff0f0; border:1px solid #ffd0d0; border-radius:4px; padding:8px; }
    </style>
</head>
<body>
<main>
    <h1>RD Devices</h1>
    <p>Entre com seu usuario central.</p>
    <form method="post">
        <input type="hidden" name="csrf_token" value="<?= h(webControlCsrfToken()) ?>">
        <input type="hidden" name="redirect" value="<?= h($redirect) ?>">
        <label>Usuario</label>
        <input name="username" autocomplete="username" autofocus required>
        <label>Senha</label>
        <input name="password" type="password" autocomplete="current-password" required>
        <button type="submit">Entrar</button>
        <?php if ($error !== ''): ?>
            <div class="error"><?= h($error) ?></div>
        <?php endif; ?>
    </form>
</main>
</body>
</html>
