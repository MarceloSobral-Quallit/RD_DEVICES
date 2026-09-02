# INTEGRADOR - Documentacao Tecnica

Guia operacional da aplicação administrativa de integração de dados do RD Devices.

## Objetivo

Integrar para MariaDB os dados coletados no SQLite local gerado pelo COLETOR.

## Escopo e Responsabilidade

- Receber o devices.db vindo da operação de campo.
- Executar validação e importação controlada.
- Registrar integração com segurança operacional.

Este componente roda em ambiente administrativo e pode depender de Python e bibliotecas de banco/criptografia.

## Configuração

1. Copiar config.ini.template para config.ini.
2. Ajustar host, porta, usuário, database e charset.
3. Salvar senha criptografada com o importador.

```powershell
python import_sqlite_to_mariadb.py --sqlite caminho\para\devices.db --save-config
```

## Execução

Dry-run (sem gravação no MariaDB):

```powershell
python import_sqlite_to_mariadb.py --sqlite caminho\para\devices.db
```

Importação real:

```powershell
python import_sqlite_to_mariadb.py --sqlite caminho\para\devices.db --mode upsert --execute
```

Modos suportados:

- append
- upsert
- replace

## Segurança

- config.ini.template não deve conter senha real.
- config.ini local pode conter password criptografado por Fernet.
- Sem cryptography, fallback b64: é apenas ofuscação.
- Arquivo .integrador_secret.key deve permanecer fora do Git.

## Fluxo Operacional

1. Receber SQLite do COLETOR.
2. Executar dry-run para validação.
3. Executar importação real com confirmação explícita.
4. Validar resultados no banco de destino.

## Referências

- [../README.md](../README.md)
- [../../README.md](../../README.md)
- [../../docs/mariadb_rd_devices_dev_schema_2026-06-11.md](../../docs/mariadb_rd_devices_dev_schema_2026-06-11.md)

