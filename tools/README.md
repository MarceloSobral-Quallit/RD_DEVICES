# Tools

Ferramentas de automação da raiz do projeto.

## Build centralizado

```powershell
python tools\build_release.py --component all --bump patch --build-type onefile
```

Atalho por duplo clique:

```powershell
tools\build.bat
```

Opções principais:

- `--component coletor`: compila somente o `COLETOR`.
- `--component integrador`: compila somente o `INTEGRADOR`.
- `--component all`: compila ambos.
- `--bump major|minor|patch|build|none`: atualiza versão antes do build.
- `--build-type onefile|onedir`: repassa o modo ao PyInstaller.
- `--skip-build`: apenas atualiza a versão.
- `--sign`: assina o executável gerado.
- `--sync-deps`: força sincronização dos requirements antes do build.
- `--no-venv`: não cria/reusa `.venv` automaticamente.
- `--skip-zip`: não cria os ZIPs de release e backup.

Política oficial de versão conjunta:

- Os executáveis `COLETOR` e `INTEGRADOR` devem manter sempre a mesma versão `V.vv.MM.AA`.
- Qualquer bump (`major|minor|patch|build`) exige `--component all`.
- Build isolado por componente só é permitido com `--bump none`.
- Em `--component all`, se houver divergência prévia entre versões, o build alinha automaticamente ambos para a mesma base antes de aplicar bump.

O template de versionamento é `tools/version_template.py.in`.

Durante o build, as pastas operacionais `config`, `database` e `logs` existentes em `dist` são preservadas e restauradas ao lado do executável.
O build cria/reusa `.venv` por padrão, verifica dependências antes de compilar, limpa artefatos temporários no início e no fim, gera ZIPs em `C:\DESENV\PROJECT_RELEASE` e `C:\DESENV\PROJECT_BACKUP`, e exibe um resumo final com metadados e status de assinatura dos executáveis.
