 Podemos programar de alguma maneira um novo botão para reescanear os B12 que estavam offline, filiais sem cidr e algum outro tipo de inconsistencia na aquisição de dados do B12. As lojas com IP inválido não entram na lista de lojas passíveis de escaneamento. Existiu uma desconexão eutomática pelo servidor da conexão do RDP o que MATOU a execução do coletor quando processava os hardwares. Algum tipo de proteção de fechamento da conexao RDP ou possibilidade de continuar o escaneamento efetuando retry no java/ip do equipamento imediatamente após o ultimo salvo com sucesso? vamos desenvolver um plano de ajuste do coletor e verificação de compatibilidade entre o banco gerado pelo coletor e o banco do mariadb que receberá os dados do coletor para exibir pelas páginas www deste projeto.

 #############

Sim. Eu dividiria o ajuste em 4 frentes, porque elas atacam problemas diferentes: reprocessamento B12, retomada de hardware, saneamento de dados e compatibilidade SQLite→MariaDB→www.

  Plano De Ajuste

  1. Novo botão: Reprocessar B12 pendentes/inconsistentes

  Adicionar na Aba 2 um botão tipo Reescanear Pendências B12.

  Critérios para entrar na fila:

  - tb_b12_data_collection_status.collection_status IN ('OFFLINE', 'FAILED', 'PARTIAL', 'AUTH_FAILED')
  - filiais ativas em tb_filial sem cidr
  - B12 com campos críticos ausentes, por exemplo:
      - hostname
      - os
      - kernel
      - cidr
      - memory
      - mac
      - disk_size

  - filiais ativas sem linha correspondente em tb_b12_data_collection_status

  Critérios para excluir:

  - ativo = 0
  - ip_banco_12 vazio
  - ip_banco_12 = '0.0.0.0'
  - IP inválido por parser real de IP, não regex solta
  - IP fora de range privado, caso essa regra seja desejada

  Resultado esperado:

  - Lista prévia na tela com quantidade por motivo: offline, failed, sem CIDR, parcial, IP inválido ignorado.
  - Botão executa só os elegíveis.
  - Cada item reprocessado grava em tb_scan_runs com scan_type = 'B12_RESCAN' ou B12.
  - Motivo do reprocessamento salvo em tb_scan_run_items.action ou notes.

  2. Retomada segura após queda de RDP ou fechamento do app

  O problema da queda RDP matou a execução porque a thread de hardware é daemon em COLETOR/src/tabs/tab_4_hardware.py:317. Se o processo fecha, ela não garante o finally que finaliza o run em COLETOR/src/tabs/tab_4_hardware.py:451.

  Ajustes:

  - Remover daemon=True ou criar fechamento controlado da janela.
  - Ao fechar o app:
      - se houver scan ativo, perguntar Cancelar e finalizar execução?
      - marcar run como CANCELLED
      - esperar workers encerrarem dentro de timeout curto

  - Ao iniciar o COLETOR:
      - procurar tb_scan_runs.status = 'RUNNING'
      - calcular itens já gravados em tb_scan_run_items
      - marcar execução antiga como ABANDONED ou CANCELLED
      - oferecer botão Continuar último scan

  Para retomar hardware:

  - A fila deve ser baseada no conjunto original menos os item_key já salvos com SUCCESS.
  - Como item_key = filial|ip, dá para continuar do “último salvo com sucesso”, mas melhor é continuar por “todos ainda não concluídos”, porque com threads paralelas a ordem real não é estritamente sequencial.
  - Adicionar opção:
      - Continuar pendentes
      - Reprocessar falhas
      - Reprocessar todos selecionados

  3. Corrigir métricas e inconsistências de registro

  Ajustes necessários:

  - Corrigir percentual B12 em COLETOR/src/tabs/tab_2_ssh.py:954: hoje divide por 18.0, mas há 15 campos rastreados.
  - Melhorar finish_scan_run em COLETOR/src/common/scan_runs.py:138, pois hoje falhas como SSH_INDISPONIVEL, SNMP_SEM_RESPOSTA e WINDOWS_WMI_BLOQUEADO_SSH_INATIVO não entram corretamente no resumo.
  - Reduzir ruído do Paramiko em COLETOR/main.py:61, colocando paramiko e paramiko.transport em WARNING ou CRITICAL.

  4. Compatibilidade SQLite → MariaDB → www

  O importador atual usa interseção de colunas entre SQLite e MariaDB em INTEGRADOR/import_sqlite_to_mariadb.py:206. Isso evita quebra, mas pode mascarar coluna faltante no MariaDB. Para produção, precisamos de validação mais
  rígida.

  Adicionar uma rotina de compatibilidade:

  - Comparar tabelas obrigatórias:
      - tb_filial
      - tb_devices_detail
      - tb_b12_data_collection_status
      - tb_detected_devices
      - tb_scan_runs
      - tb_scan_run_items

  - Comparar colunas SQLite vs MariaDB.
  - Classificar:
      - OK
      - FALTA NO MARIADB
      - TIPO DIFERENTE
      - COLUNA EXTRA

  - Bloquear importação real se faltar coluna crítica.
  - Gerar SQL sugerido de ALTER TABLE quando possível.

  Também precisamos alinhar o www: hoje store.php ainda consulta SQLite diretamente e usa fallback Python em www/store.php:32. Para produção, ele deve consultar MariaDB via config.web.php, como já previsto em www/
  INSTALL_APACHE_LINUX.md.

  Sequência Recomendada

  1. Implementar saneamento B12: seletor de pendências, exclusão de IP inválido e botão de reprocessamento.
  2. Implementar retomada de scan e proteção contra fechamento/RDP.
  3. Corrigir contadores, percentual B12 e ruído Paramiko.
  4. Criar verificador de compatibilidade SQLite/MariaDB no INTEGRADOR.

 #############
  
  Podemos programar de alguma maneira um novo botão para reescanear os B12 que estavam offline, filiais sem cidr e algum outro tipo de inconsistencia na aquisição de dados do B12. As lojas com IP inválido não entram na lista de
  lojas passíveis de escaneamento. Existiu uma desconexão eutomática pelo servidor da conexão do RDP o que MATOU a execução do coletor quando processava os hardwares. Algum tipo de proteção de fechamento da conexao RDP ou
  possibilidade de continuar o escaneamento efetuando retry no java/ip do equipamento imediatamente após o ultimo salvo comsucesso.
  
  Podemos programar de alguma maneira um novo botão para reescanear os B12 que estavam offline, filiais sem cidr e algum outro tipo de inconsistencia na aquisição de dados. As lojas com IP inválido não entram na lista de lojas passíveis de escaneamento.
  
  
	 Analisei o SQLite em temp\Preventiva-Coletor-4\database\devices.db sem alterar o arquivo.

  Resumo

  - Banco íntegro: PRAGMA integrity_check = ok
  - Tamanho: ~65,9 MB
  - Tabelas principais:
      - tb_filial: 3.724 filiais
      - tb_b12_data_collection_status: 3.711 coletas B12
      - tb_detected_devices: 46.476 dispositivos detectados
      - tb_devices_detail: 3.641 detalhes de hardware
      - tb_scan_runs: 8 execuções
      - tb_scan_run_items: 202.020 itens de execução

  Achados principais

  - Há 3.711 filiais ativas e exatamente 3.711 registros B12. As 13 filiais sem B12 são inativas.
  - A coleta B12 teve 3.641 sucessos, 65 offline e 5 falhas.
  - A execução HARDWARE id 7 está inconsistente: consta como RUNNING, processed_items = 0, mas tem 32.604 itens gravados, sendo 31.690 SUCCESS. Parece execução interrompida ou resumo não finalizado.
  - As execuções HARDWARE id 6 e 8 também têm diferença entre failed_items do resumo e quantidade real de itens não SUCCESS.
  - Em tb_b12_data_collection_status, o comentário diz “18 campos rastreáveis”, mas a tabela tem 15 pares reais de campos coletados. Por isso o melhor caso aparece como 83.33% em vez de 100%. Isso parece erro de denominador no
    cálculo de collection_percentage.

  - Em coletas B12 com SUCCESS, o campo mais ausente é mb_version: ausente em 2.156 registros.
  - tb_filial tem 84 filiais sem cidr: 71 ativas e 13 inativas.
  - Existem 13 filiais com ip_banco_12 = 0.0.0.0, todas duplicando esse IP.
  - Hardware detalhado:
      - 3.641 registros
      - 2.545 SSD
      - 1.096 HDD
      - 822 com Ubuntu 24.04

  - Dispositivos detectados:
      - 11.944 TC Linux
      - 7.787 IMPRESSORA

  Pontos que eu corrigiria/investigaria primeiro

  1. Finalizar ou marcar como falha/cancelada a execução tb_scan_runs.id = 7.
  2. Revisar o cálculo de collection_percentage, porque o banco parece usar denominador 18 enquanto só há 15 campos rastreados.
  3. Padronizar os contadores de tb_scan_runs com os itens reais de tb_scan_run_items.
  4. Validar as 84 filiais sem cidr e os 13 registros com ip_banco_12 = 0.0.0.0.
  5. Priorizar atualização/substituição das máquinas com Ubuntu 18.04 e os HDDs, se isso fizer parte da preventiva.

  #################
os logs reforçam bem os achados do banco.

  O ponto mais importante: a execução HARDWARE id 7 ficou RUNNING porque o log 20260610_092903_aba_4_hardware.log mostra uma segunda execução iniciando às 15:08:02, processando até 20:00:36, mas sem Concluido nem Exportado. No
  código, a thread do hardware é criada como daemon em COLETOR/src/tabs/tab_4_hardware.py:317. Se o app for fechado durante o scan, a thread pode morrer sem executar o finally que chama finish_scan_run em COLETOR/src/tabs/
  tab_4_hardware.py:451.

  Também encontrei estes pontos para ajuste:

  - coletor.log está muito ruidoso: 45.218 linhas de Authentication successful, 45.448 de Connected, 83 tracebacks do Paramiko. Não parecem falhas do coletor, são erros esperados de conexão SSH/log interno da biblioteca. A causa
    provável é o root logger em INFO em COLETOR/main.py:61. Vale colocar paramiko/paramiko.transport em WARNING ou CRITICAL.

  - A contagem de falhas em tb_scan_runs.failed_items não bate com os itens reais porque COLETOR/src/common/scan_runs.py:138 não considera status como SSH_INDISPONIVEL, SNMP_SEM_RESPOSTA e WINDOWS_WMI_BLOQUEADO_SSH_INATIVO como
    falha. Exemplo: run 8 teve 92 warnings, mas o resumo gravou 31 falhas.

  - O percentual B12 está errado por denominador fixo: COLETOR/src/tabs/tab_2_ssh.py:954 divide por 18.0, mas a tabela rastreia 15 campos. Por isso sucesso máximo aparece como 83.33%.
  - B12 está coerente nos logs: 3.646 online, 3.641 com SSH, 65 offline por ssh_port_closed e 5 falhas reais: 2 timeout, 2 kex incompatível, 1 sessão SSH inativa.

  Ajustes candidatos, em ordem:

  1. Remover daemon=True ou adicionar controle de fechamento para cancelar/finalizar scans antes de encerrar.
  2. Ao iniciar o app, marcar RUNNING antigo como CANCELLED/ABANDONED quando não houver processo ativo.
  3. Normalizar classificação de status em finish_scan_run.
  4. Corrigir o denominador B12 para 15 ou calcular dinamicamente.
  5. Reduzir ruído do Paramiko no coletor.log.

