# INTEGRADOR

Aplicação administrativa do RD Devices para integração de dados coletados em SQLite para MariaDB.

## Objetivo

Receber uma cópia do devices.db gerado pelo COLETOR e aplicar importação controlada no banco central.

## Responsabilidade

- Validar e processar o SQLite coletado.
- Executar importação em modo seguro (dry-run por padrão).
- Integrar dados no MariaDB com estratégia de carga definida.

## Fluxo de Uso

1. Receber o devices.db da operação de campo.
2. Executar validação e dry-run.
3. Executar importação real com confirmação explícita.

## Configuração

```powershell
cd INTEGRADOR
pip install -r requirements.txt
Copy-Item config.ini.template config.ini
```

Editar config.ini com host, porta, usuário e database.

Para salvar a senha de forma criptografada:

```powershell
python import_sqlite_to_mariadb.py --sqlite caminho\para\devices.db --save-config
```

Observações de segurança:

- Não versionar senhas em texto plano.
- Segredo local em .integrador_secret.key.
- Sem cryptography, fallback b64: é apenas ofuscação.

## Execução

Dry-run (não grava no MariaDB):

```powershell
python import_sqlite_to_mariadb.py --sqlite caminho\para\devices.db
```

Importação real:

```powershell
python import_sqlite_to_mariadb.py --sqlite caminho\para\devices.db --mode upsert --execute
```

Modos de importação:

- append
- upsert
- replace

## Build e Versionamento

Política oficial do projeto:

- INTEGRADOR e COLETOR devem manter sempre a mesma versão.
- Bump de versão só é permitido em build conjunto.

Build conjunto com bump (na raiz do repositório):

```powershell
python tools\build_release.py --component all --bump build --build-type onefile --sign
```

Build isolado do INTEGRADOR sem bump:

```powershell
python tools\build_release.py --component integrador --bump none --build-type onefile
```

## Documentação Relacionada

- ../README.md
- docs/README.md
- ../docs/mariadb_rd_devices_dev_schema_2026-06-11.md

