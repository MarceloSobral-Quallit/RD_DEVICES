# Documentação RD Devices

## Estado Atual (2026-09-01)

- Fluxo principal operacional entregue: `COLETOR -> SQLite local -> INTEGRADOR -> MariaDB`.
- Versão do projeto: `1.25.09.26`, definida em `version_info.txt` (fonte única — `tools/build_release.py` lê dela e deriva os `version.py`). `COLETOR.exe` e `INTEGRADOR.exe` compilados e assinados (`Valid` / `CN=Quallit Local Code Signing`); ZIPs `RELEASE`/`BACKUP` `1.25.09.26` em `release/`, `release/backup/` e em `C:\DESENV\PROJECT_RELEASE`/`PROJECT_BACKUP`; `release/RD-COLETOR.zip` gerado.
- COLETOR ganhou a **Aba 7 — Autopilot**: pipeline automático `B12 -> Scan Loja -> Hardware` por loja, núcleo compartilhado em `COLETOR/src/common/scan_core.py`. Com validação pré-flight (botão "Validar"), cancelamento imediato, progresso no log em tempo real e, se a última execução foi interrompida, diálogo ao iniciar: **limpar banco e recomeçar** / **completar o que faltou** / **reescanear só os que falharam** (`tb_scan_runs` / `tb_scan_run_items`).
- Histórico append-only no MariaDB: `tb_devices_detail_history` e `tb_detected_devices_history` (migração em `docs/mariadb_history_tables_migration_2026-09-01.sql`), já reconhecidas pelo INTEGRADOR.
- Build: `tools/build_all.py` faz a compilação total (COLETOR + INTEGRADOR + assinatura + ZIPs em `release/` + publicação `RD-COLETOR.zip`). `tools/build_release.py` é o motor; publica automaticamente no `[download_server]` de `config/config.ini` quando `enabled = 1`, e limpa `__pycache__` no início/fim.
- `release/` contém os pacotes da versão corrente: `RD_DEVICES_RELEASE-...1.25...zip`, `RD_DEVICES_BACKUP-...1.25...zip` e `RD-COLETOR.zip` (ZIPs de versões intermediárias já removidos).

## Governança de Documentação

- Índice central: `docs/INDEX.md`
- Playbook técnico: `docs/DEV_PLAYBOOK.md`
- Protocolo cíclico: `docs/protocolo-ciclico-publicacao-exclusao.md`

## Componentes

| Componente | Papel | Banco |
| --- | --- | --- |
| `COLETOR` | GUI de coleta em ambiente restrito | SQLite local |
| `INTEGRADOR` | Integração administrativa do SQLite coletado | MariaDB |
| `PROJETO_ORIGINAL` | Referência histórica do projeto anterior | Conforme original |

## Fluxo de dados

1. O `COLETOR` roda no equipamento ou ambiente de loja.
2. As coletas gravam dados no SQLite local (`devices.db`).
3. O arquivo SQLite é copiado para uma máquina administrativa.
4. O `INTEGRADOR` valida o SQLite e integra os dados no MariaDB.

O `COLETOR` não deve importar bibliotecas de MariaDB, não deve abrir conexão MariaDB e não deve manter credenciais do banco central.

## Credenciais

As credenciais foram separadas por responsabilidade:

- Credenciais dos equipamentos de loja: configuradas no `COLETOR`, pela aba `Credenciais`.
- Credenciais do MariaDB: configuradas somente em `INTEGRADOR/config.ini`.

Senhas não devem ser documentadas nem versionadas em texto puro. A solução adotada é Fernet com chave local fora do Git. Quando `cryptography` não estiver disponível, o sistema usa fallback `b64:` apenas como ofuscação portátil.

## Documentação específica

- `COLETOR/docs/README.md`
- `INTEGRADOR/docs/README.md`

## Build e Versionamento

A compilação fica centralizada em `tools/build_release.py`.

```powershell
python tools\build_release.py --component all --bump patch --build-type onefile
```

O script atualiza `version.py` a partir de `tools/version_template.py.in`. Use `--bump none` para compilar sem alterar versão.

Para contexto histórico e decisões por rodada, consultar também `docs/RoadMap.md`.

