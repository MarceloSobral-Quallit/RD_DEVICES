# INDEX - Documentacao RD Devices

Catalogo de documentos do projeto na pasta docs/ (raiz do repositorio).

## Basicos Obrigatorios

| Documento | Resumo |
| --- | --- |
| [README.md](README.md) | Escopo funcional atual e estado entregue do projeto. |
| [DEV_PLAYBOOK.md](DEV_PLAYBOOK.md) | Decisoes tecnicas, padroes operacionais e roadmap vigente. |
| [protocolo-ciclico-publicacao-exclusao.md](protocolo-ciclico-publicacao-exclusao.md) | Protocolo de rodada: contrato, implementacao, execucao tecnica e auditoria. |
| [RoadMap.md](RoadMap.md) | Historico incremental por versao e marcos do projeto. |
| [ROADMAP_VERSION.md](ROADMAP_VERSION.md) | Regra de versionamento `X.Y.MM.YY` e versao corrente da base documental. |

## Analises E Planejamento

| Documento | Resumo |
| --- | --- |
| [Planos desenvolvimento.md](Planos%20desenvolvimento.md) | Registro de propostas tecnicas e plano de ajuste de coleta/reprocessamento. |
| _(análise*.md)_ | Transcricoes de analise de sessao — fora do versionamento (contem IPs/credenciais internos); mantidas localmente. |

## Banco E Compatibilidade

| Documento | Resumo |
| --- | --- |
| [mariadb_rd_devices_dev_schema_2026-06-11.md](mariadb_rd_devices_dev_schema_2026-06-11.md) | Inventario do schema MariaDB e compatibilidade com SQLite do COLETOR. |
| [mariadb_rd_devices_dev_schema_2026-06-11.sql](mariadb_rd_devices_dev_schema_2026-06-11.sql) | Dump SQL de referencia do schema MariaDB da data de corte. |
| [mariadb_history_tables_migration_2026-09-01.sql](mariadb_history_tables_migration_2026-09-01.sql) | Migracao que cria as tabelas de historico append-only `tb_devices_detail_history` e `tb_detected_devices_history` (comparacao antes x depois por coleta). |

## Referencias De Componente

| Documento | Resumo |
| --- | --- |
| [COLETOR docs](../COLETOR/docs/README.md) | Operacao do coletor offline, credenciais e fluxo de campo. |
| [INTEGRADOR docs](../INTEGRADOR/docs/README.md) | Integracao administrativa SQLite -> MariaDB e modo de execucao. |
