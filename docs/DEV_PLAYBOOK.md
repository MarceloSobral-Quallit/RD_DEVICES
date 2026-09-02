# DEV PLAYBOOK - RD Devices

Guia tecnico-operacional para evolucao e manutencao do projeto.

## Estado Tecnico Atual

- Projeto dividido em dois componentes:
  - COLETOR: execucao offline em ambiente restrito com SQLite local.
  - INTEGRADOR: importacao administrativa SQLite -> MariaDB.
- Build centralizado em tools/build_release.py (motor) + tools/build_all.py (compilacao total num comando).
- Versao do projeto: 1.25.09.26, definida em version_info.txt (fonte unica; version.py derivados). COLETOR.exe/INTEGRADOR.exe 1.25.09.26 compilados+assinados; ZIPs RELEASE/BACKUP 1.25.09.26 em release/, release/backup/ e nas pastas externas; release/RD-COLETOR.zip gerado. Pendente: limpar ZIPs de versoes intermediarias (1.14/1.22/1.23/1.24) e confirmar publicacao do RD-COLETOR.zip.
- Correcao aplicada no build para evitar loop/recursao em ZIP quando saidas de release/backup ficam dentro da raiz do repositorio.
- COLETOR: logica de coleta (B12 / Scan Loja / Hardware) e persistencia centralizada em src/common/scan_core.py; retomada de execucao via src/common/scan_runs.get_pending_items.
- COLETOR: Aba 7 (Autopilot) orquestra o pipeline por loja reutilizando scan_core + scan_runs.
- MariaDB: tabelas de historico append-only (tb_devices_detail_history, tb_detected_devices_history) definidas em docs/mariadb_history_tables_migration_2026-09-01.sql; INTEGRADOR ja as reconhece na importacao e na comparacao.

## Decisoes Tecnicas Ativas

1. Separacao de responsabilidade:
- COLETOR nao deve acessar MariaDB.
- INTEGRADOR concentra conectividade com MariaDB e importacao.

2. Persistencia local no COLETOR:
- Banco em database/devices.db ao lado do executavel.
- Configuracao em config/config.ini ao lado do executavel.
- Logs em logs/ ao lado do executavel.

3. Build e empacotamento:
- Compilacao via .venv da raiz do projeto.
- Preservacao de pastas de runtime no dist durante rebuild.
- ZIP release e ZIP backup gerados pelo script de build.

4. Versionamento:
- Fonte unica da versao: `version_info.txt` na raiz (linha `Versao: X.Y.MM.AA`). TODA compilacao parte dela.
- `--bump none` compila exatamente a versao de `version_info.txt`; `--bump {build|patch|minor|major}` incrementa a partir dela e reescreve o arquivo.
- `COLETOR/version.py` e `INTEGRADOR/version.py` sao derivados/alinhados a `version_info.txt` no inicio de cada build (nao editar a mao).
- Politica formal: os dois executaveis mantem sempre a mesma versao `V.vv.MM.AA`.
- Bump de versao so e permitido com `--component all`; build isolado por componente usa `--bump none` (stampa a versao de `version_info.txt`).

## Padroes De Execucao

- Compilacao total: `python tools/build_all.py`. Pipeline FIXO, sem flags para desligar etapas —
  sempre: limpa __pycache__, bump (--bump build), build onefile dos 2, assinatura, ZIPs RELEASE/BACKUP
  em release/, publicacao do RD-COLETOR.zip, limpa __pycache__. Unicos parametros: --release-dir/--backup-dir.
  Para builds parciais use tools/build_release.py diretamente (--bump none, --no-sign, --no-publish, --skip-build, --component ...).

- Build completo com bump e assinatura (baixo nivel):
  python tools/build_release.py --component all --bump build --build-type onefile --sign

- Build de validacao sem bump:
  python tools/build_release.py --component all --bump none --build-type onefile

- Publicacao do COLETOR no download server: AUTOMATICA ao fim de todo build quando config/config.ini (raiz) tem [download_server] enabled=1. Le [download_server] -> active_profile -> perfil [servidor1]/[servidor2]/... (protocol scp|sftp|local; senha texto puro ou b64:). Envia sempre com o nome fixo [download_server].file_name (RD-COLETOR.zip), conteudo APENAS COLETOR.exe (o app cria config/config.ini na 1a execucao a partir do config.ini.template embutido; sem senhas — configurar pela aba Credenciais). URL = public_base_url + file_name. Desligar com --no-publish.

- Operacao de campo:
  COLETOR -> devices.db (SQLite) -> transporte manual -> INTEGRADOR -> MariaDB

## Roadmap Vigente (Rodada 2026-09-01, revisado)

### Feito nesta rodada
- **Versionamento:** `version_info.txt` (raiz) vira fonte unica (`read_project_version` em `build_release.py`); `--bump` incrementa e reescreve; `version.py` derivados. Chegou a `1.25.09.26` (manual `1.14`->`1.20`, depois `build_all.py --bump build` 5x).
- **Build:** `tools/build_all.py` — pipeline fixo (limpa `__pycache__` -> bump -> build onefile x2 -> assinatura -> ZIPs RELEASE/BACKUP em `release/` -> publica `RD-COLETOR.zip` -> limpa `__pycache__`). Publicacao automatica quando `config/config.ini [download_server] enabled=1`; `--no-publish` desliga. `RD-COLETOR.zip` = so `COLETOR.exe` (o app cria `config/config.ini` do template embutido).
- **Config COLETOR:** removidos `COLETOR/config/config.ini` e `COLETOR/config.ini` (legado); fonte unica = `COLETOR/config.ini.template` (SEM senhas — sanitizado; configurar pela aba Credenciais). Novo `config/config.ini.template` (raiz) documenta `[download_server]`+perfis.
- **Autopilot:** fix da selecao perdida; **Cancelar imediato**; **validacao pre-flight** (`_validate_preflight` + botao "Validar"); **progresso no log em tempo real** (linhas agregadas + por etapa + `Resumo`); `ConsoleLogger.max_lines=4000`; **dialogo de retomada** ao iniciar quando a ultima execucao foi interrompida (limpar/completar/reescanear falhas), substituindo a checkbox "Retomar".
- **Higiene:** `is_local_secret_file()` nos ZIPs; `.gitignore` cobre `config.web.php`/`*.OK_*`/`*.bak`/`*.orig`; removido `www/store.php.OK_*`.

### Fase 1 - Limpeza de artefatos e confirmacao da release
Objetivo: `release/` e pastas externas so com a `1.25.09.26`; publicacao confirmada.

Feito:
- Politica de versao: mantido `--bump build` fixo no `build_all.py` (decisao do usuario).
- Apagados TODOS os ZIPs de versoes anteriores (`1.13.*`, `1.14.*`, `1.21.*`, `1.22.*`, `1.23.*`, `1.24.*`) de `release/`, `release/backup/`, `C:\DESENV\PROJECT_RELEASE` e `PROJECT_BACKUP`. `C:\DESENV\PROJECT_RELEASE` e `PROJECT_BACKUP` ficaram vazios; `release/` ficou com `RD_DEVICES_RELEASE-...1.25...zip`, `RD_DEVICES_BACKUP-...1.25...zip` e `RD-COLETOR.zip`.

Pendente:
- Confirmar que a publicacao chegou: baixar `<public_base_url>/RD-COLETOR.zip` e conferir tamanho/data.

Validacao:
- `ls release/` lista somente `1.25.*` (+ `RD-COLETOR.zip`); pastas externas vazias. (ok)

### Fase 2 - Migracao MariaDB (historico)
Objetivo: criar as tabelas `*_history` no `rd_devices_dev`.

Tarefas:
- Aplicar `docs/mariadb_history_tables_migration_2026-09-01.sql` (`mysql -h <host> -u <admin> -p rd_devices_dev < ...`). (depende de acesso ao MariaDB)
- Rodar uma importacao pelo INTEGRADOR e confirmar que as `*_history` sao reconhecidas sem erro.

Validacao:
- `SHOW TABLES LIKE '%_history'` retorna `tb_devices_detail_history` e `tb_detected_devices_history`.

### Fase 3 - Validacao do Autopilot em campo (v1.25.09.26)
Objetivo: exercitar os novos controles com dados reais.

Tarefas:
- **Pre-flight:** rodar com XLS inexistente, sem senha Linux e banco vazio — confirmar bloqueio; rodar com credencial Windows/SNMP faltando — confirmar aviso (nao bloqueio).
- **Cancelar:** com scan em andamento, clicar Cancelar — parada instantanea, log silencia, botao "Iniciar" volta, `on_close` fecha de primeira.
- **Dialogo de retomada:** apos Cancelar, reabrir e testar os 3 modos — `fresh` apaga `tb_devices_detail`/`tb_detected_devices`/`tb_b12_data_collection_status`/`tb_scan_run*`; `resume` pula `SUCCESS`; `retry_failed` refaz so as falhas e restringe as lojas.
- **Progresso:** confirmar `Progresso —`, `Etapa X concluida`, `[JAVA n] Scan Loja concluido`, `Resumo —` no log; `console_logger` cortando em 4000 linhas.

Validacao:
- `tb_scan_run_items` sem duplicatas apos `resume`/`retry_failed`.
- Comparacao "antes x depois" por data nas `*_history` (apos Fase 2).

### Fase 4 - Versionamento GitHub (concluida)
Objetivo: colocar o projeto sob git com o repositorio privado `github.com/MarceloSobral-Quallit/RD_DEVICES`.

Feito:
- `git init` + branch `main` + `origin` = `https://github.com/MarceloSobral-Quallit/RD_DEVICES.git` (repo **privado**, estava vazio).
- `.gitignore` reforcado: `*.pfx`/`*.p12`/`*.pem`, `tools/certs/`, `*.db-shm`/`-wal`/`-journal`, `release/`, `.specstory/`, `PROJETO_ORIGINAL/`.
- Commit inicial `3b07a8b` (96 arquivos, ~2,2 MB) e `git push -u origin main`. Auditado: nenhum segredo no tree (`tools/certs/`, `.integrador_secret.key`, `config/config.ini`, `www/config.web.php`, `*.db` confirmados ausentes via `git cat-file -e`).
- `DEFAULT_SIGN_PASSWORD` mantido hardcoded em `build_release.py` por decisao (repo privado; o `.pfx` nao esta no repo, cert e self-signed).

Pendente:
- Ajuste local: `git config --global credential.helper manager` (config aponta para `credential-manager-core`, nome antigo — push funcionou, mas gera warning).
- Se o repo um dia virar publico: mover a senha de assinatura para env var e rotacionar os segredos.

---

## Roadmap - Rodada 2026-08-20 (historico)

### Fase 1 - Confiabilidade de Coleta
Objetivo: reduzir perdas de coleta por interrupcao e inconsistencias de status.

Tarefas:
- Consolidar reprocessamento de B12 pendentes (offline/falha/sem CIDR) com criterios claros.
- Garantir finalizacao de run interrompido (CANCELLED/ABANDONED) e retomada segura.
- Revisar consolidacao de status de itens em tb_scan_runs e tb_scan_run_items.

Validacao:
- Simular interrupcao de scan e confirmar fechamento de status no SQLite.
- Confirmar reprocessamento parcial sem duplicacao indevida.

### Fase 2 - Qualidade de Dados E Compatibilidade
Objetivo: elevar consistencia SQLite x MariaDB para publicacao web.

Tarefas:
- Criar verificador de compatibilidade de schema com classificacao por severidade.
- Bloquear importacao executavel quando faltar coluna critica no destino.
- Emitir SQL sugerido para ajuste de schema quando aplicavel.

Validacao:
- Rodar verificador em base de homologacao e exigir 100% dos campos criticos.

### Fase 3 - Operacao De Release
Objetivo: padronizar releases reproduziveis sem recursao de artefatos.

Tarefas:
- Manter regra de exclusao de diretorios de saida no backup ZIP.
- Padronizar publicacao de pacote de executaveis por versao.
- Registrar evidencia de build, hash e metadados de executavel por rodada.

Validacao:
- Executar build completo com ZIP automatico e confirmar termino sem loop.

## Riscos Tecnicos

- Divergencia de versao entre componentes ao compilar separadamente.
- Falhas de conectividade remota gerando run sem fechamento semantico.
- Evolucao de schema no MariaDB sem espelhamento no integrador.

## Pendencias Em Aberto

- Definir conjunto minimo de testes de regressao antes de release assinado.
- Definir criterio de promocao do fluxo web para uso produtivo.
