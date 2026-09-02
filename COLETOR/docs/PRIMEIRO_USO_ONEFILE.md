# Manual de Primeiro Uso - COLETOR onefile

Este guia cobre o cenário em que apenas o executável `COLETOR.exe` foi copiado para uma máquina nova.

## 1. Onde colocar o executável

Crie uma pasta própria para o coletor, por exemplo:

```text
C:\RD_DEVICES_COLETOR\
```

Copie o `COLETOR.exe` para essa pasta e execute a partir dela.

Evite executar direto da pasta `Downloads`, de compartilhamentos temporários ou de locais sem permissão de escrita. O coletor precisa criar arquivos ao lado do executável.

## 2. Arquivos criados ao lado do exe

No primeiro uso, o aplicativo usa a pasta do próprio `.exe` como diretório persistente.

Estrutura esperada:

```text
C:\RD_DEVICES_COLETOR\
  COLETOR.exe
  config\
    config.ini
    .coletor_secret.key
  database\
    devices.db
  logs\
    coletor.log
    console\
      AAAAMMDD_HHMMSS_aba_*.log
  backups\
```

Observações:

- `database/devices.db` é o banco SQLite local.
- `config/config.ini` guarda caminhos, usuários, portas, timeouts e senhas protegidas.
- `config/.coletor_secret.key` é a chave local usada para abrir senhas salvas com Fernet.
- `logs/console/` guarda a saída dos consoles por aba.
- O schema SQLite fica embutido no executável e é aplicado automaticamente ao abrir/criar o banco.

## 3. Primeiro ciclo recomendado

1. Abra o `COLETOR.exe`.
2. Entre na aba `SQLite`.
3. Confirme o caminho do banco:

```text
./database/devices.db
```

4. Se o banco ainda não existir, use `Criar Banco Novo...`.
5. Entre na aba `Credenciais`.
6. Informe as credenciais de Linux, Windows Drogasil e Windows Raia.
7. Clique em `Salvar Credenciais`.
8. Feche e abra o coletor novamente.
9. Na aba `SQLite`, clique em `Atualizar` e confira se o banco está `OK`.
10. Na aba `Import XLS`, importe o XLS de lojas.
11. Use as abas `B12`, `Scan Loja` e `Hardware` conforme a coleta desejada.

## 4. Atenção ao copiar config entre máquinas

Se as senhas foram salvas com Fernet, o arquivo abaixo faz parte da configuração:

```text
config\.coletor_secret.key
```

Se copiar apenas o `config.ini` para outra máquina sem essa chave, as senhas podem não ser lidas corretamente.

Para uma máquina nova, o mais seguro é:

1. copiar apenas o `COLETOR.exe`;
2. abrir o aplicativo;
3. preencher as credenciais novamente pela aba `Credenciais`;
4. salvar.

Se for necessário reaproveitar uma configuração já validada, copie junto:

```text
config\config.ini
config\.coletor_secret.key
```

## 5. Como validar credenciais

Na próxima execução de scan, os consoles registram linhas de diagnóstico sem expor a senha:

```text
Credencial Linux: usuario='pdv' | porta=22 | senha_lida=sim | tamanho=...
```

Interpretação:

- `senha_lida=não` ou `tamanho=0`: problema no `config.ini`, chave Fernet ou senha não salva.
- `senha_lida=sim` com tamanho esperado, mas `AUTH_FAILED`: a senha foi lida, porém o equipamento remoto recusou a autenticação.
- Porta SSH aberta não significa autenticação OK. A coleta só é considerada bem-sucedida após login SSH e comandos executados.

## 6. O que enviar para análise

Quando houver erro em máquina remota, envie preferencialmente:

- arquivo mais recente de `logs/console/` da aba usada;
- print da aba com o erro;
- trecho do log contendo início da operação e erro;
- informação se o `config.ini` foi criado nessa máquina ou copiado de outra;
- se possível, o `database/devices.db` após o teste.

Não envie senhas em texto puro. Se precisar enviar `config.ini`, remova ou mascare os valores de `password`.

## 7. Fluxo de coleta sugerido

1. `SQLite`: criar/validar banco local.
2. `Credenciais`: salvar credenciais.
3. `Import XLS`: importar lojas para `tb_filial`.
4. `B12`: consultar B12 e coletar dados Linux.
5. `Scan Loja`: detectar PDV, TC e impressoras.
6. `Hardware`: coletar detalhes dos dispositivos detectados.
7. `SQLite`: exportar `devices.db` para uso no integrador/admin.

## 8. Checklist rápido

Antes de iniciar coleta em campo:

- O executável está em uma pasta com permissão de escrita.
- A pasta `config/` existe.
- A pasta `database/` existe.
- A aba `SQLite` mostra banco `OK`.
- As credenciais foram salvas na própria máquina.
- O XLS foi importado sem erro.
- Os logs em `logs/console/` estão sendo gerados.

## 9. Build assinado

Antes de compilar, instale as dependências:

```powershell
pip install -r COLETOR\requirements.txt
```

Para compilar o COLETOR onefile com bump automático de build, metadados no executável e assinatura digital:

```powershell
python tools\build_release.py --component coletor --build-type onefile --sign
```

O certificado padrão fica em:

```text
tools\certs\quallit_codesign.pfx
```

A senha do PFX deve estar em uma destas variáveis de ambiente:

```text
QUALLIT_SIGN_PASSWORD
QUALLIT_CODESIGN_PASSWORD
RD_DEVICES_SIGN_PASSWORD
```

Se a senha não estiver disponível, o build tenta assinar usando um certificado instalado no store local do Windows.
