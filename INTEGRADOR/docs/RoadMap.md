# RoadMap — INTEGRADOR

Registro incremental de mudanças funcionais por versão. Ordem cronológica reversa.

---

## v1.25.09.26 — 01/09/2026
- **Tabelas de histórico append-only:** `import_sqlite_to_mariadb.py` e a Aba Comparar (`src/tabs/tab_5_view_compare.py`) passam a reconhecer `tb_devices_detail_history` e `tb_detected_devices_history`.
- **Semântica append-only:** as tabelas `*_history` nunca são reescritas na importação — inserção incremental com deduplicação por chave natural (`ip` + data da coleta/snapshot). As tabelas de estado atual (`tb_devices_detail`, `tb_detected_devices`) seguem inalteradas.
- **Migração de referência:** schema das novas tabelas em `docs/mariadb_history_tables_migration_2026-09-01.sql` (aplicar no `rd_devices_dev` antes de importar históricos).
- **Versão:** `version_info.txt` (raiz) vira a fonte única da versão; `version.py` do INTEGRADOR é derivado dela no build. `INTEGRADOR.exe` compilado e assinado em `1.25.09.26`; ZIPs `1.25.09.26` em `release/`, `release/backup/` e nas pastas externas. Pendente: limpar ZIPs de versões intermediárias.

## v1.07.06.26 — 10/06/2026
- Listas padrao das abas Importar, Contagem e Comparar passam a refletir o schema SQLite atual do COLETOR: `tb_filial`, `tb_devices_detail`, `tb_b12_data_collection_status`, `tb_detected_devices`, `tb_scan_runs` e `tb_scan_run_items`.
- Importador CLI `import_sqlite_to_mariadb.py` passa a usar a mesma lista padrao atualizada.
- Tabelas legadas nao geradas pelo COLETOR deixam de aparecer por padrao, eliminando avisos falsos de ausencia no SQLite.
- Build onefile recompilado com bump para `1.07.06.26`, assinatura e metadados Quallit/Preventiva Integrador.

## v1.06.06.26 — 10/06/2026
- Log geral `logs/integrador_gui.log` passa a registrar cabecalho de inicializacao com aplicativo, versao, data de build, modo de execucao e diretorio base.
- Logs de console em `logs/console/` passam a iniciar com cabecalho de identificacao do INTEGRADOR, versao e data de build.
- Build onefile recompilado com bump para `1.06.06.26`, assinatura e metadados Quallit/Preventiva Integrador.

## v1.05.06.26 — 10/06/2026
- Build onefile do INTEGRADOR recompilado no release conjunto com bump de versao e assinatura.
- Metadados do executavel mantidos no padrao Quallit/Preventiva Integrador, com `FileVersion` e `ProductVersion` em `1.05.06.26`.

## v1.01.06.26 — 09/06/2026
- Build onefile do INTEGRADOR recompilado com bump de versão e assinatura Authenticode válida.
- Metadados do executável padronizados para Quallit/Preventiva: `CompanyName=Quallit`, `ProductName=Preventiva Integrador`, `FileDescription=Preventiva Integrador`, `OriginalFilename=Integrador.exe` e copyright Quallit.
- Arquivo `tools/file_version_info_INTEGRADOR.txt` regenerado com `FileVersion` e `ProductVersion` em `1.01.06.26`.

## v1.00.06.26 — 09/06/2026
- Estrutura inicial do INTEGRADOR: sincronização SQLite (COLETOR) → MariaDB (rd_devices_dev).
- Mapeamento inicial definido para tabelas operacionais do COLETOR no SQLite e MariaDB.
- Módulo `secure_store.py` para gestão de credenciais de conexão ao MariaDB.
- Configuração de conexão em `config.ini.template`.
