# ROADMAP VERSION

## Regra de versão

Formato: `X.Y.MM.YY`

- `X`: major do projeto (mantido em `1` no ciclo atual).
- `Y`: incremento sequencial por nova entrada no `docs/RoadMap.md`, **exceto** quando definido manualmente em `version_info.txt` (que é a fonte única da versão para os builds — ver `docs/DEV_PLAYBOOK.md` §Versionamento).
- `MM.YY`: mês e ano da rodada.

Fonte da versão para compilação: `version_info.txt` na raiz. `tools/build_release.py` lê essa linha; `--bump` incrementa e reescreve o arquivo; os `version.py` são derivados dela.

## Versão atual

- Versão: `1.25.09.26` (definida manualmente em `version_info.txt`; manual `1.14` → `1.20`; `build_all.py` (bump build) 5x nesta sessao → `1.25`).
- Data da última entrada no RoadMap: `01/09/2026`
- Arquivo de referência: `docs/RoadMap.md` (entrada `v1.25.09.26` consolida o trabalho da sessão antes registrado sob `v1.14.09.26`).
- Chat snapshot desta rodada: `docs/chat/` não encontrado; snapshot de chat mantido sem novo JSONL versionado.
