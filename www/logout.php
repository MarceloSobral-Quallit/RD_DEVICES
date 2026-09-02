<?php
declare(strict_types=1);

require_once __DIR__ . DIRECTORY_SEPARATOR . 'web_control_auth.php';

webControlLogout();
webControlRedirect('/login.php');
