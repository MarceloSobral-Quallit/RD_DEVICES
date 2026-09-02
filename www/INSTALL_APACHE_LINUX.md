# RD Devices WWW - Instalacao em Linux/Apache

Este documento descreve a instalacao planejada da solucao web `rd_devices`
em servidor Linux com Apache, PHP e MariaDB.

O `www/store.php` atual ja serve como prototipo de consulta consolidada:
ele combina dados de B12 (`tb_devices_detail`), Scan Loja/Hardware
(`tb_detected_devices`) e execucoes (`tb_scan_run_items`). Para producao,
o mesmo conceito deve ser mantido, mas consultando MariaDB via PDO MySQL e
protegido por autenticacao.

## Arquitetura Recomendada

Fluxo de dados:

1. `COLETOR` gera `devices.db` SQLite nas lojas/ambiente de coleta.
2. `INTEGRADOR` importa o SQLite para MariaDB central.
3. `www` consulta o MariaDB central.
4. Usuarios acessam `https://servidor/rd_devices/` com login.

Componentes web recomendados:

- `config.web.php`: configuracao local do MariaDB e parametros da aplicacao.
- `auth.php`: autenticacao, sessao, permissao por pagina e log de acesso.
- `login.php` / `logout.php`: entrada e saida de usuario.
- `index.php`: tela inicial/dashboard.
- `store.php`: consulta consolidada de equipamentos.
- `db_count.php`: contagem/auditoria das tabelas importadas.
- `users.php`: gestao de usuarios e permissoes.
- `assets/`: CSS/JS/imagens, se houver.

## Banco MariaDB

Sim, o MariaDB precisa estar alinhado ao schema SQLite atual para receber os
dados importados pelo INTEGRADOR sem avisos falsos ou perda de colunas.

Tabelas operacionais atuais esperadas:

- `tb_filial`
- `tb_devices_detail`
- `tb_b12_data_collection_status`
- `tb_detected_devices`
- `tb_scan_runs`
- `tb_scan_run_items`

Tabelas legadas que nao devem ser exigidas pelo novo fluxo:

- `tb_devices`
- `tb_devices_detail_log`
- `tb_hardware_historico`
- `tb_scan_control`

Tabelas web de autenticacao recomendadas, reaproveitando o modelo do projeto
original:

- `tb_web_users`
- `tb_web_user_page_permissions`
- `tb_web_access_log`

Antes da primeira publicacao, validar no MariaDB:

```sql
SHOW TABLES;
DESCRIBE tb_filial;
DESCRIBE tb_devices_detail;
DESCRIBE tb_b12_data_collection_status;
DESCRIBE tb_detected_devices;
DESCRIBE tb_scan_runs;
DESCRIBE tb_scan_run_items;
DESCRIBE tb_web_users;
```

Pontos de ajuste provaveis:

- Criar `tb_scan_runs` e `tb_scan_run_items`, caso ainda nao existam.
- Garantir as colunas `hw_*` em `tb_detected_devices`.
- Garantir `cidr` em `tb_filial`.
- Garantir que `tb_web_users.password_hash` use hash compativel com
  `password_hash()` / `password_verify()` do PHP.

## Dependencias do Servidor

Exemplo para Debian/Ubuntu:

```bash
sudo apt update
sudo apt install apache2 php php-cli php-mysql php-mbstring php-json mariadb-client
sudo a2enmod rewrite headers ssl
sudo systemctl enable --now apache2
```

Versoes recomendadas:

- PHP 8.1 ou superior.
- Apache 2.4.
- MariaDB 10.5 ou superior.

## Arquivos a Copiar

Destino recomendado:

```text
/var/www/rd_devices/
```

Copiar:

```text
www/*.php
www/assets/              se existir
www/config.web.example.php
www/INSTALL_APACHE_LINUX.md
www/apache-rd_devices.conf
```

No servidor, criar o arquivo real de configuracao:

```bash
sudo cp /var/www/rd_devices/config.web.example.php /etc/rd_devices/config.web.php
sudo chown root:www-data /etc/rd_devices/config.web.php
sudo chmod 640 /etc/rd_devices/config.web.php
```

O arquivo real `/etc/rd_devices/config.web.php` deve conter as credenciais do
MariaDB e nao deve ficar dentro do diretorio publico do Apache.

## Configuracao Apache

Copiar o arquivo exemplo:

```bash
sudo cp /var/www/rd_devices/apache-rd_devices.conf /etc/apache2/sites-available/rd_devices.conf
sudo a2ensite rd_devices.conf
sudo apachectl configtest
sudo systemctl reload apache2
```

Se a aplicacao for publicada como subdiretorio em um site ja existente, usar o
bloco `Alias /rd_devices /var/www/rd_devices` do arquivo exemplo.

Se for publicada como virtual host dedicado, ajustar `ServerName` e apontar o
`DocumentRoot` para `/var/www/rd_devices`.

## Permissoes

```bash
sudo mkdir -p /var/www/rd_devices /etc/rd_devices
sudo chown -R root:www-data /var/www/rd_devices
sudo find /var/www/rd_devices -type d -exec chmod 755 {} \;
sudo find /var/www/rd_devices -type f -exec chmod 644 {} \;
sudo chmod 750 /etc/rd_devices
sudo chmod 640 /etc/rd_devices/config.web.php
```

## Configuracao do MariaDB para o WWW

Criar um usuario de leitura para o site. Exemplo:

```sql
CREATE USER 'rd_devices_www'@'localhost' IDENTIFIED BY 'trocar_esta_senha';
GRANT SELECT, INSERT, UPDATE, DELETE ON rd_devices_dev.tb_web_users TO 'rd_devices_www'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON rd_devices_dev.tb_web_user_page_permissions TO 'rd_devices_www'@'localhost';
GRANT SELECT, INSERT ON rd_devices_dev.tb_web_access_log TO 'rd_devices_www'@'localhost';
GRANT SELECT ON rd_devices_dev.* TO 'rd_devices_www'@'localhost';
FLUSH PRIVILEGES;
```

Se a gestao de usuarios for feita pela propria tela `users.php`, o usuario web
precisa gravar nas tabelas `tb_web_*`. Para as tabelas operacionais do coletor,
o acesso web deve ser somente leitura.

## Autenticacao

Modelo recomendado:

- `tb_web_users.username`
- `tb_web_users.password_hash`
- `tb_web_users.role`: `admin` ou `user`
- `tb_web_users.active`: `1` ou `0`
- `tb_web_user_page_permissions`: permissoes por pagina para usuarios comuns
- `tb_web_access_log`: auditoria de login, logout, acesso e negacao

Este modelo e compativel com o projeto original e pode ser reaproveitado na
nova solucao.

## Uso do store.php Atual

O `store.php` atual foi feito para auditar SQLite local durante o
desenvolvimento. Ele e util como modelo de tela e regra de consolidacao, mas
para producao deve evoluir para:

- usar `getDbConnection()` com PDO MySQL;
- exigir `requirePageAccess('store.php')`;
- remover a dependencia de `?db=...`;
- consultar MariaDB diretamente;
- manter os filtros por loja, tipo, status e busca;
- manter a normalizacao de status de WMI/SSH/SNMP.

## Checklist de Publicacao

1. Confirmar que MariaDB possui as tabelas operacionais atuais.
2. Confirmar que MariaDB possui tabelas `tb_web_*`.
3. Criar usuario MariaDB especifico para o site.
4. Criar `/etc/rd_devices/config.web.php`.
5. Copiar arquivos de `www/` para `/var/www/rd_devices`.
6. Ativar `apache-rd_devices.conf`.
7. Rodar `apachectl configtest`.
8. Acessar `/rd_devices/login.php`.
9. Validar login de admin.
10. Validar consulta `store.php`.
11. Validar logs de acesso em `tb_web_access_log`.

## Dados Necessarios Sobre o Servidor

Para finalizar a implementacao e gerar uma instalacao precisa, informar:

- Distribuicao Linux e versao.
- Apache ja instalado? Qual versao?
- Versao do PHP disponivel.
- O site sera publicado como `/rd_devices` ou dominio/subdominio dedicado?
- Caminho desejado no servidor, por exemplo `/var/www/rd_devices`.
- Host, porta e nome do database MariaDB.
- Se o MariaDB esta no mesmo servidor ou remoto.
- Nome das tabelas atuais de usuario, caso ja existam.
- Estrutura das tabelas de usuario existentes (`DESCRIBE ...`).
- Se as senhas atuais usam `password_hash`, MD5, SHA1, LDAP/AD ou outro modelo.
- Se precisa HTTPS ja no Apache ou se existe proxy/reverso terminando TLS.
- Usuario/grupo do Apache (`www-data`, `apache`, outro).
- Politica de acesso por rede: liberado geral, VPN, IPs especificos.
- Nome final do sistema no Apache: `rd_devices`, `devices_linux`, outro.

