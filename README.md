# RD Devices

Coleta e integração de dados de equipamentos de loja, com operação offline no campo e sincronização administrativa controlada.

## Visão Geral

O projeto é dividido em dois componentes principais:

- COLETOR: aplicação desktop para execução em ambiente restrito, com banco SQLite local.
- INTEGRADOR: aplicação administrativa para importar o SQLite coletado para MariaDB.

Objetivo operacional:

1. Coletar dados em loja sem depender de MariaDB.
2. Transportar o arquivo SQLite para a máquina administrativa.
3. Integrar os dados no MariaDB com rastreabilidade.

## Arquitetura de Fluxo

COLETOR -> SQLite local (devices.db) -> transporte controlado -> INTEGRADOR -> MariaDB

## Componentes

### COLETOR

- Execução offline.
- Persistência local em SQLite.
- Coletas por abas operacionais (B12, Scan Loja, Hardware, ReScan, Credenciais).
- Geração de logs e histórico de execução.

Documentação do componente:

- [COLETOR/README.md](COLETOR/README.md)
- [COLETOR/docs/README.md](COLETOR/docs/README.md)

### INTEGRADOR

- Execução administrativa.
- Importação SQLite -> MariaDB.
- Suporte a validação e integração com segurança operacional.

Documentação do componente:

- [INTEGRADOR/README.md](INTEGRADOR/README.md)
- [INTEGRADOR/docs/README.md](INTEGRADOR/docs/README.md)

## Requisitos

- Windows (ambiente principal de build e operação local).
- Python 3.x para execução em desenvolvimento.
- Dependências listadas em:
	- COLETOR/requirements.txt
	- INTEGRADOR/requirements.txt

## Execução em Desenvolvimento

COLETOR:

- python COLETOR/main.py

INTEGRADOR:

- python INTEGRADOR/main.py

## Build, Versionamento e Release

Scripts de build:

- [tools/build_all.py](tools/build_all.py) — compilação total num comando (recomendado)
- [tools/build_release.py](tools/build_release.py) — motor de build (usado pelo `build_all.py`)

### Recompilação completa

`tools/build_all.py` é um pipeline **fixo, sem flags para desligar etapas** — sempre executa tudo:

```powershell
python tools/build_all.py
```

1. limpa `__pycache__`/bytecode do repositório (início);
2. **incrementa a versão** em `version_info.txt` (`--bump build`) e sincroniza os `version.py`;
3. PyInstaller **onefile** de COLETOR e INTEGRADOR;
4. **assinatura** Authenticode (PFX Quallit);
5. ZIPs `RD_DEVICES_RELEASE-*` e `RD_DEVICES_BACKUP-*` em `release/` e `release/backup/`;
6. **publica** `RD-COLETOR.zip` (apenas `COLETOR.exe` — o app gera `config/config.ini` na 1ª execução) no download server de `config/config.ini` `[download_server]`;
7. limpa `__pycache__`/bytecode (fim).

Únicos parâmetros aceitos: `--release-dir` / `--backup-dir` (só redirecionam os ZIPs).

Para builds parciais (sem bump, sem assinatura, sem publicação, um único componente, etc.),
use diretamente `tools/build_release.py` com as flags correspondentes — ele é o motor e continua
com todas as opções:

```powershell
$env:PROJECT_RELEASE = "C:\DESENV\PROJECT_GITHUB\RD_DEVICES\release"
$env:PROJECT_BACKUP  = "C:\DESENV\PROJECT_GITHUB\RD_DEVICES\release\backup"
python tools/build_release.py --component all --bump none --build-type onefile --no-publish
```

Publicação do COLETOR no download server: automática ao fim do build sempre que `config/config.ini`
(raiz; não versionada — ver `config/config.ini.template`) tem `[download_server] enabled = 1`. Monta
sempre `RD-COLETOR.zip` (nome fixo, **apenas `COLETOR.exe`**) e envia via `scp`/`sftp`/`local`
para o servidor de `active_profile`. O COLETOR embute `config.ini.template` (sem senhas — o
operador configura pela aba Credenciais) e cria `config/config.ini` na 1ª execução — por isso o
ZIP não leva `config.ini`. Pré-requisito: rota para o host do perfil e credenciais preenchidas no
perfil (`[servidor1]`/…).

Política de versão (release conjunta):

1. COLETOR e INTEGRADOR devem manter sempre a mesma versão V.vv.MM.AA.
2. Qualquer bump de versão exige --component all.
3. Build isolado de componente deve usar --bump none.
4. Se houver divergência de versão entre componentes, o build conjunto alinha automaticamente antes do bump.

## Estrutura Principal do Repositório

- COLETOR/: aplicação de coleta offline.
- INTEGRADOR/: aplicação de integração administrativa.
- config/: configuração de build/publicação (`config.ini` local, fora do versionamento; `config.ini.template` versionado).
- docs/: documentação de projeto e governança técnica.
- tools/: automação de build, release e suporte operacional (`build_all.py`, `build_release.py`).
- www/: artefatos e evolução do front web do projeto.
- release/: pacotes RELEASE/BACKUP por versão + `RD-COLETOR.zip` (não versionado).
- PROJETO_ORIGINAL/: base histórica de referência.

## Documentação do Projeto

Base documental da raiz:

- [docs/INDEX.md](docs/INDEX.md)
- [docs/README.md](docs/README.md)
- [docs/DEV_PLAYBOOK.md](docs/DEV_PLAYBOOK.md)
- [docs/protocolo-ciclico-publicacao-exclusao.md](docs/protocolo-ciclico-publicacao-exclusao.md)
- [docs/RoadMap.md](docs/RoadMap.md)

## Segurança e Boas Práticas

- Não versionar credenciais reais, chaves e segredos.
- Tratar config.ini local como arquivo operacional de ambiente.
- Validar integridade e consistência antes de importar dados em MariaDB.

## Licenciamento e Uso

Projeto proprietario de uso interno.

