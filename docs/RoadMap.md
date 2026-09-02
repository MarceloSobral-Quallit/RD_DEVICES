# RoadMap — RD Devices (Projeto)

Registro incremental de mudanças por versão do projeto como um todo.
Detalhes por componente em `COLETOR/docs/RoadMap.md` e `INTEGRADOR/docs/RoadMap.md`.

Ordem cronológica reversa.

---

## v1.25.09.26 — 01/09/2026
- **Versionamento — `version_info.txt` como fonte única:** `tools/build_release.py` passa a ler a versão de `version_info.txt` (raiz) via `read_project_version()`. `--bump none` compila exatamente essa versão; `--bump build/patch/minor/major` incrementa e reescreve o arquivo. `COLETOR/version.py` e `INTEGRADOR/version.py` são derivados/alinhados a `version_info.txt` no início de cada build. Versão do projeto: `1.25.09.26` (`version_info.txt` ajustado manualmente para `1.20`; `tools/build_all.py`, que faz `--bump build` fixo, executado 5× na sessão → `1.25`).
- **COLETOR — Aba 7 Autopilot (nova):** pipeline automático `B12 → Scan Loja → Hardware` executado por loja. Cada loja avança de etapa assim que a anterior termina, sem esperar o lote inteiro; cada etapa tem pool de workers e timeout próprios. Seleção de lojas por logomarca e faixa de JAVA, com opção de importar XLS antes de rodar (modos `Atualizar` / `Limpar e importar`).
- **COLETOR — retomada de pipeline:** se a última execução do Autopilot foi interrompida, ao iniciar abre um diálogo com 3 opções — **limpar banco e recomeçar**, **completar o que faltou** (pula os `SUCCESS`), **reescanear só os que falharam**. Lógica de pendências em `src/common/scan_runs.get_pending_items` (`done`/`pending`), generalizada da Aba 4.
- **COLETOR — fix Autopilot:** (1) corrigido "Nenhuma loja selecionada para o pipeline" quando havia XLS informado — a reimportação recriava o Treeview e apagava a seleção antes de lê-la; seleção agora é capturada no clique e a lista resolvida a partir do SQLite (`_query_pipeline_stores`). (2) **Cancelar** virou imediato: silencia o log dos workers em rede, derruba a fila dos pools sem esperar as tarefas em voo e libera o botão "Iniciar" na hora; `on_close` fecha de primeira. (3) **Validação pré-flight** (botão "Validar" + checagem automática ao iniciar): XLS, banco/schema, lojas com IP, credenciais e parâmetros — erros bloqueiam, avisos pedem confirmação.
- **COLETOR — progresso no log em tempo real do Autopilot:** o console só logava falhas; agora o worker loga início de etapa, linha agregada `Progresso — B12 x/y | Scan x/y | Hardware n` a cada ~20 conclusões, `Etapa B12/Scan Loja concluida`, `[JAVA n] Scan Loja concluido: N dispositivo(s)` e `Resumo —` final. `ConsoleLogger` ganhou `max_lines` (padrão 4000) — o arquivo `.log` continua completo.
- **COLETOR — núcleo compartilhado:** criado `src/common/scan_core.py` extraindo de Abas 2/3/4 a lógica de teste TCP/SSH, coleta B12, scan de loja, coleta de hardware (Linux/Windows/Impressora) e persistência (`save_b12_result`, `save_store_scan_results`, `save_hardware_result`), agora reutilizada pelo Autopilot. Abas 2, 3 e 4 ajustadas para consumir esse núcleo.
- **Projeto — histórico append-only no MariaDB:** criada migração `docs/mariadb_history_tables_migration_2026-09-01.sql` com `tb_devices_detail_history` (uma linha por IP por coleta B12) e `tb_detected_devices_history` (snapshot completo rede + hardware por scan). Não altera `tb_devices_detail` / `tb_detected_devices` (estado atual).
- **INTEGRADOR:** `import_sqlite_to_mariadb.py` e Aba Comparar (`tab_5_view_compare.py`) passam a conhecer as tabelas `*_history`, tratadas como append-only (nunca reescritas; deduplicação por chave natural).
- **WWW:** `store.php` passa a exigir autenticação via `web_control_auth.php` (`webControlRequirePermission`); `config.web.php` passa a ser configuração local (PDO MariaDB + web_control), fora do versionamento — template continua em `config.web.example.php`.
- **Higiene de repositório:** `.gitignore` cobre `config.web.php`, `*.OK_*`, `*.bak`, `*.orig`; removido `www/store.php.OK_20260611_004113`. `tools/build_release.py` ganha `is_local_secret_file()` (espelha os segredos do `.gitignore`), aplicada nos ZIPs RELEASE e BACKUP; RELEASE também exclui `logs/` e `*.log`. ZIPs regenerados sem `.key`, `*.db`, `config.ini` nem `config.web.php`.
- **Build — publicação no download server (automática):** `tools/build_release.py` monta sempre `RD-COLETOR.zip` (nome fixo = `[download_server].file_name`, URL estável) com **apenas `COLETOR.exe`** — o executável embute o `config.ini.template` (credenciais padrão) e cria `config/config.ini` na 1ª execução via `ensure_default_config()`. Envia por `scp`/`sftp` (paramiko) ou `local` (cópia/UNC). Config em `config/config.ini` da raiz (fora do versionamento; `config/config.ini.template` versionado), modelo papel + perfil: `[download_server]` tem `enabled`/`active_profile`/`protocol`/`remote_dir`/`file_name`/`public_base_url` e `active_profile` aponta para um servidor físico (`[dell]`/`[vmware1]`/…) com host/user/senha/`key_file`. **Publica automaticamente sempre que `enabled = 1`** (não precisa mais de `--publish`, que virou no-op); `--no-publish` desliga.
- **Build — limpeza de `__pycache__`:** `tools/build_release.py` varre todo o repositório (exceto `.venv`/`.git`) removendo `__pycache__` e bytecode no **início e no fim** de cada execução.
- **Config do COLETOR — só o template versionado:** removidos `COLETOR/config/config.ini` e `COLETOR/config.ini` (legado) do repo — eram cópias antigas do template **sem as linhas `password`** e são gerados em runtime (`ensure_default_config()` copia de `config.ini.template`, que tem as credenciais padrão `b64:` de `pdv`/`drogasil`/`drogaraia`). Fonte única de config do COLETOR = `COLETOR/config.ini.template`.
- **Build — `tools/build_all.py`:** compilação total num comando, **pipeline fixo sem flags para desligar etapas** — sempre limpa `__pycache__`, faz bump (`--bump build`), compila os 2 onefile, assina, gera ZIPs RELEASE/BACKUP em `release/` do repo e publica `RD-COLETOR.zip`. Únicos parâmetros: `--release-dir`/`--backup-dir`. Builds parciais → usar `tools/build_release.py` direto.
- **Build/Release:** versão unificada `1.25.09.26` (`__build__ = 25`) em COLETOR e INTEGRADOR (`version.py` sincronizados). Partiu de `1.20` (ajuste manual) e `tools/build_all.py` — que faz `--bump build` fixo (mantido por decisão) — foi executado 5× na sessão, chegando a `1.25`. Exes compilados e assinados (`CN=Quallit Local Code Signing`, FileVersion `1.25.09.26`). `release/` limpo: só `RD_DEVICES_RELEASE-...1.25...zip`, `RD_DEVICES_BACKUP-...1.25...zip` e `RD-COLETOR.zip` (apagados os ZIPs `1.14.*`/`1.22.*`/`1.23.*`/`1.24.*` de `release/`, `release/backup/` e das pastas externas). **Pendente:** confirmar que a publicação do `RD-COLETOR.zip` chegou ao download server; `C:\DESENV\PROJECT_RELEASE`/`PROJECT_BACKUP` ainda têm `1.13.*`/`1.21.*`.
- **GitHub — projeto sob versionamento:** `git init` + push inicial (`3b07a8b`, 96 arquivos) para o repo **privado** `github.com/MarceloSobral-Quallit/RD_DEVICES` (branch `main`). `.gitignore` reforçado (`*.pfx`/`*.p12`/`*.pem`, `tools/certs/`, `*.db-shm`/`-wal`, `release/`, `.specstory/`, `PROJETO_ORIGINAL/`). Auditoria confirmou que nenhum segredo (`.integrador_secret.key`, `config/config.ini`, `www/config.web.php`, `.pfx`, `*.db`) foi para o repositório. Templates seguros (`*.template`, `config.web.example.php`) versionados.

## v1.13.08.26 — 20/08/2026
- **Projeto:** compilação validada dos dois componentes em onefile sem bump, mantendo versão unificada `1.12.08.26` em COLETOR e INTEGRADOR.
- **Build/Release:** corrigido `tools/build_release.py` para evitar recursão/loop na geração de ZIP de backup quando `release/` e `release/backup/` estão dentro da raiz do repositório.
- **Release:** geração automática de ZIP validada após correção (`RELEASE` e `BACKUP`) sem travamento em loop.
- **Documentação raiz:** criados `docs/INDEX.md`, `docs/DEV_PLAYBOOK.md` e `docs/protocolo-ciclico-publicacao-exclusao.md`; atualizado `docs/README.md` e `README.md` com referências de governança.
- **Diretórios operacionais (auditoria desta rodada):** sem ajustes aplicados/versionados em `RPI-Monitor/`, `samba/`, `mariadb/`, `storage/` e `templates_remotos/<snapshot>` (não encontrados no workspace atual).
- **Apache:** sem ajuste novo nesta rodada; apenas referência histórica preservada em `PROJETO_ORIGINAL/devices_linux/apache/devices_linux.conf`.
- **Snapshot de chat:** `docs/chat/` ausente nesta rodada; nenhum JSONL novo disponível no repositório e sem `docs/CHAT_LOG.md` para indexação.

## Proxima versao — 10/06/2026
- **WWW:** criada documentacao de instalacao Linux/Apache em `www/INSTALL_APACHE_LINUX.md`, cobrindo dependencias, arquivos a copiar, permissoes, MariaDB, autenticacao e checklist de publicacao.
- **WWW:** criado exemplo de virtual host/Alias Apache em `www/apache-rd_devices.conf` para publicar a aplicacao como `/rd_devices`.
- **WWW:** criado template `www/config.web.example.php` para configurar PDO MariaDB fora do diretorio publico, usando `/etc/rd_devices/config.web.php` como arquivo real no servidor.
- **WWW:** definida abordagem para evoluir `store.php` do prototipo SQLite para consulta MariaDB autenticada, reaproveitando o modelo `tb_web_users`, `tb_web_user_page_permissions` e `tb_web_access_log` do projeto original.

## v1.07.06.26 — 10/06/2026
- **INTEGRADOR v1.07.06.26:** listas padrao de importacao, contagem, comparacao e CLI alinhadas ao schema SQLite atual do COLETOR.
- **INTEGRADOR:** tabelas legadas nao geradas pelo COLETOR (`tb_devices`, `tb_devices_detail_log`, `tb_hardware_historico`, `tb_scan_control`) deixam de ser selecionadas por padrao.
- **INTEGRADOR:** tabelas `tb_scan_runs` e `tb_scan_run_items` passam a fazer parte do fluxo padrao de auditoria/importacao.

## v1.09.06.26 — 10/06/2026
- **COLETOR v1.09.06.26 / INTEGRADOR v1.06.06.26:** logs gerais passam a registrar cabecalho de inicializacao com aplicativo, versao, data de build, modo de execucao e diretorio base.
- **COLETOR/INTEGRADOR:** logs de console por aba passam a iniciar com cabecalho contendo aplicativo, versao e data de build, facilitando auditoria de coletas antigas.
- **Projeto:** build onefile recompilado com bump e assinatura, gerando novo pacote `RELEASE` e `BACKUP`.

## v1.08.06.26 — 10/06/2026
- **COLETOR v1.08.06.26:** abas B12, Scan Loja e Hardware ganham controles de limpeza/reprocessamento, filtros por faixa de JAVA e paralelismo por Workers.
- **COLETOR:** coleta de hardware revisada com inicializacao COM para WMI, fallback Windows via SSH/PowerShell, status canonico para `WMI bloqueado / SSH inativo` e melhorias para memoria/disco/placa-mae em Linux.
- **COLETOR:** schema SQLite passa a registrar execucoes em `tb_scan_runs` e itens em `tb_scan_run_items`, permitindo identificar scans interrompidos e apoiar reprocessamento limpo.
- **Projeto:** criada tela web `www/store.php` com leitura SQLite e fallback Python `www/store_export.py`, consolidando B12, Scan Loja e Hardware para auditoria do banco local.
- **Projeto:** `tools/build.bat` usado como referencia para build dos dois componentes com bump `build`, onefile e assinatura.
- **Projeto:** build gerou ZIPs `RELEASE` e `BACKUP` em `C:\DESENV\PROJECT_RELEASE` e `C:\DESENV\PROJECT_BACKUP`.
- **INTEGRADOR v1.05.06.26:** build recompilado no mesmo pacote de release, mantendo metadados Quallit/Preventiva Integrador.

## v1.05.06.26 — 09/06/2026
- **COLETOR v1.05.06.26:** build onefile recompilado com bump e assinatura Authenticode válida; metadados do executável padronizados como Quallit/Preventiva Coletor.
- **INTEGRADOR v1.01.06.26:** build onefile recompilado com bump e assinatura Authenticode válida; metadados do executável padronizados como Quallit/Preventiva Integrador.
- `tools/build_release.py` centraliza os metadados dos executáveis em `EXE_METADATA` e regenera os arquivos `tools/file_version_info_*.txt` também em modo `--skip-build`.
- Ambiente de compilação consolidado na `.venv` da raiz do projeto para ambos os componentes.

## v1.03.06.26 — 09/06/2026
- **COLETOR v1.03.06.26:** consistência SQLite × MariaDB revisada e corrigida; `tb_b12_data_collection_status` e `tb_detected_devices` criadas no MariaDB; `cidr` adicionado a `tb_filial`; bugs de `collection_status` e `collection_date` na Aba 2 corrigidos; `data_atualizacao` populada na gravação de `tb_devices_detail`.

## v1.02.06.26 — 09/06/2026
- **COLETOR v1.02.06.26:** schema SQLite inicial (`config/schema_sqlite_init.sql`) com as 4 tabelas do COLETOR; botão "Criar Banco Novo..." na Aba 0 inicializa banco vazio a partir do schema; campo `historico` no SQLite mantém compatibilidade com MariaDB via INTEGRADOR; `ativo` derivado automaticamente da validade do `ip_banco_12` na importação XLS; strip aplicado em todos os campos texto.

## v1.01.06.26 — 09/06/2026
- **COLETOR v1.01.06.26:** coleta de hardware completa (SSH/WMI/SNMP) para Linux, Windows e Impressoras; lógica de persistência com proteção de dados válidos.
- **INTEGRADOR v1.00.06.26:** versão inicial; sincronização SQLite → MariaDB pendente de implementação.

## v1.00.06.26 — 09/06/2026
- Estrutura inicial do projeto com dois componentes independentes: COLETOR (GUI offline + SQLite) e INTEGRADOR (integração com MariaDB).
- Credenciais armazenadas com Fernet; matriz de IPs por CIDR define alvos por tipo de dispositivo.
