# COLETOR

Aplicação desktop de coleta offline do RD Devices para ambientes restritos.

## Objetivo

O COLETOR executa a coleta de dados em loja usando SQLite local, sem dependência de MariaDB durante a operação de campo.

## Responsabilidade

- Executar scans e coletas locais.
- Gravar resultados em database/devices.db.
- Preservar operação offline e rastreabilidade via logs.

Integração com MariaDB é responsabilidade do INTEGRADOR.

## Fluxo Operacional

COLETOR -> SQLite local (devices.db) -> transporte controlado -> INTEGRADOR -> MariaDB

## Configuração Inicial

```powershell
cd COLETOR
New-Item -ItemType Directory -Force config
Copy-Item config.ini.template config\config.ini
```

Depois, abrir a aba Credenciais para gravar as senhas dos equipamentos.

Perfis de credencial usados no COLETOR:

- CREDENTIALS_LINUX_STORE: B12, PDVs e terminais Linux.
- CREDENTIALS_TERMINAL_WINDOWS_DROGASIL: terminais Windows Drogasil.
- CREDENTIALS_TERMINAL_WINDOWS_RAIA: terminais Windows Raia.

## Execução em Desenvolvimento

```powershell
cd COLETOR
python main.py
```

## Estrutura de Runtime

No modo executável onefile, o COLETOR mantém ao lado do .exe:

- config/config.ini
- database/devices.db
- logs/

O schema SQLite é embutido e aplicado automaticamente quando necessário.

## Build e Versionamento

Política oficial do projeto:

- COLETOR e INTEGRADOR devem manter sempre a mesma versão.
- Bump de versão só é permitido em build conjunto.

Build conjunto com bump (na raiz do repositório):

```powershell
python tools\build_release.py --component all --bump build --build-type onefile --sign
```

Build isolado do COLETOR sem bump:

```powershell
python tools\build_release.py --component coletor --bump none --build-type onefile
```

## Documentação Relacionada

- ../README.md
- docs/README.md
- docs/PRIMEIRO_USO_ONEFILE.md

