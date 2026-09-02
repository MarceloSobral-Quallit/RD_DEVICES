# COLETOR - Documentacao Tecnica

Guia operacional da aplicação de coleta offline do RD Devices.

## Objetivo

Executar coleta em ambiente restrito de loja com persistência local em SQLite, sem dependência de MariaDB durante a execução de campo.

## Escopo e Responsabilidade

- Operar com banco local em database/devices.db.
- Executar scans e coletas por abas operacionais.
- Registrar logs e manter rastreabilidade de execução.
- Exportar base SQLite para processamento administrativo posterior.

## Persistência Local

Configuração padrão:

```ini
[DATABASE]
path = ./database/devices.db
backup_dir = ./backups
```

No executável onefile, ficam ao lado do .exe:

- config/config.ini
- database/devices.db
- logs/coletor.log

O schema SQLite é embutido e aplicado automaticamente quando necessário.

## Credenciais de Equipamentos

As credenciais são geridas na aba Credenciais e gravadas com proteção local.

- Método principal: Fernet com chave .coletor_secret.key.
- Fallback sem cryptography: prefixo b64: (apenas ofuscação).

Perfis utilizados:

| Perfil | Uso |
| --- | --- |
| CREDENTIALS_LINUX_STORE | B12, PDVs e terminais Linux |
| CREDENTIALS_TERMINAL_WINDOWS_DROGASIL | Terminais Windows de lojas Drogasil |
| CREDENTIALS_TERMINAL_WINDOWS_RAIA | Terminais Windows de lojas Raia |

## Fluxo Operacional Recomendado

1. Validar/criar config/config.ini nas abas SQLite e Credenciais.
2. Configurar credenciais de acesso aos equipamentos.
3. Importar base de lojas (XLS).
4. Executar coleta B12, Scan Loja e Hardware.
5. Validar logs e resultados no SQLite.
6. Transportar devices.db para o INTEGRADOR.

## Limite de Responsabilidade

O COLETOR não deve abrir conexão com MariaDB. Toda integração com banco central é feita no INTEGRADOR.

## Referências

- [PRIMEIRO_USO_ONEFILE.md](PRIMEIRO_USO_ONEFILE.md)
- [../README.md](../README.md)
- [../../README.md](../../README.md)

