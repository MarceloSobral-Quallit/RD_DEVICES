# RoadMap - WWW

Registro incremental da solucao web do RD Devices. Ordem cronologica reversa.

---

## Proxima versao - 10/06/2026
- Documentacao inicial de instalacao em servidor Linux/Apache criada em `INSTALL_APACHE_LINUX.md`.
- Exemplo de configuracao Apache criado em `apache-rd_devices.conf`, usando publicacao por `Alias /rd_devices /var/www/rd_devices`.
- Template de configuracao `config.web.example.php` criado para conexao PDO MariaDB, mantendo senhas reais fora do DocumentRoot em `/etc/rd_devices/config.web.php`.
- Definida estrategia de autenticacao baseada no modelo do projeto original: `tb_web_users`, `tb_web_user_page_permissions` e `tb_web_access_log`.
- Definida estrategia de evolucao do `store.php`: manter a consolidacao visual atual, trocar SQLite por MariaDB e proteger a pagina com autenticacao/permissao.
- Registrado checklist de dados necessarios do servidor antes da implementacao final: distribuicao, versoes Apache/PHP, publicacao, host MariaDB, schema de usuarios, modelo de senha e politica HTTPS/rede.

## Prototipo SQLite - 10/06/2026
- `store.php` criado como consulta consolidada local para auditar bancos SQLite do COLETOR durante desenvolvimento.
- `store_export.py` criado como fallback quando PHP nao possui extensao SQLite disponivel.
- Tela combina dados de `tb_devices_detail`, `tb_detected_devices` e `tb_scan_run_items`, normalizando status de hardware, WMI, SSH e SNMP.
