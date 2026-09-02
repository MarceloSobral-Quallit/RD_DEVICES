# RoadMap — COLETOR

Registro incremental de mudanças funcionais por versão. Ordem cronológica reversa.

---

## v1.25.09.26 — 01/09/2026
- **Nova Aba 7 — Autopilot:** pipeline automático `B12 → Scan Loja → Hardware` por loja. Cada loja avança de etapa assim que a anterior termina (sucesso, ou falha no caso do B12), sem esperar o lote inteiro. Pools de workers independentes por etapa (padrão B12=16, Scan=16, Hardware=8) e timeouts próprios (B12=5s, Scan=2s).
- **Aba 7 — seleção e entrada:** filtro por logomarca (`TODAS/DROGASIL/RAIA`) e faixa de JAVA; marcar/desmarcar/inverter; opção de importar um XLS de lojas antes de rodar (`Atualizar` = upsert, `Limpar e importar` = truncate) ou usar as lojas já importadas na Aba 1.
- **Aba 7 — opções do pipeline:** `Coletar detalhe B12`, seletores `SSH` / `Radmin` / `Impressora` para o scan de loja, painel "Progresso por Loja" (B12 / Scan / Hardware) e log em tempo real por aba (`logs/console/aba_7_autopilot`).
- **Retomada após interrupção — diálogo de modo:** se a última execução do Autopilot não terminou (`tb_scan_runs.status IN RUNNING/FAILED/CANCELLED`, `source_tab='autopilot'`), ao clicar "Iniciar Autopilot" abre um diálogo com 3 opções: **Limpar banco e recomeçar** (`DELETE` em `tb_scan_run_items`/`tb_scan_runs`/`tb_devices_detail`/`tb_detected_devices`/`tb_b12_data_collection_status`, com confirmação extra); **Completar o que faltou** (pula itens já `SUCCESS`); **Reescanear apenas os que falharam** (processa só os `item_key` marcados como falha, restringindo a lista de lojas às que têm falha). Substitui a antiga checkbox "Retomar". Seleção de pendências via `src/common/scan_runs.get_pending_items` (`done` = concluídos, `pending` = falhas).
- **Núcleo compartilhado `src/common/scan_core.py`:** extraídos das Abas 2/3/4 os blocos de teste TCP/SSH, coleta completa de B12, scan de loja por tipo esperado, coleta de hardware Linux/Windows (WMI + fallback SSH/PowerShell)/Impressora SNMP e a persistência no SQLite (`save_b12_result`, `save_store_scan_results`, `save_hardware_result`, `ensure_hw_columns`), agora com parâmetro `run_id` para rastreio. Abas 2, 3 e 4 passam a consumir esse núcleo.
- **Fix Aba 7 — "Nenhuma loja selecionada para o pipeline":** quando o campo XLS estava preenchido, o worker reimportava o XLS e recriava o Treeview (`_load_stores`), apagando a seleção antes de lê-la. Agora a seleção é capturada no clique (main thread) em `_pipeline_selection`, e o worker resolve a lista de lojas direto do SQLite via novo `_query_pipeline_stores()` (seguro fora da main thread; sem marcação + XLS ⇒ usa todas as lojas ativas importadas). Erro na importação do XLS passa a abortar o pipeline.
- **Aba 7 — cancelamento imediato:** "Cancelar" agora para na hora — silencia o log dos workers ainda em rede (`_mute_logs`), derruba a fila dos pools (`shutdown(wait=False, cancel_futures=True)`) sem esperar as tarefas em voo (threads daemon, resultados descartados) e devolve o botão "Iniciar" no mesmo instante. O `while pending` do worker sai ao ver `stop_event`. `_worker_running` impede iniciar uma nova execução antes do encerramento da anterior. `main_window.on_close` fecha de primeira quando o cancelamento já concluiu.
- **Aba 7 — validação pré-flight (`_validate_preflight`):** botão "Validar" e checagem automática antes de "Iniciar Autopilot". Verifica: seleção de lojas ou XLS informado; XLS existe, é `.xls` e tem cabeçalho compatível (`validate_header_mapping`); banco SQLite abre e tem `tb_filial`/`tb_detected_devices`/`tb_scan_runs`/`tb_scan_run_items`; lojas marcadas (ou lojas ativas) com IP no banco; credencial Linux (usuário+senha) presente e decodificável; credenciais Windows Drogasil/Raia e SNMP community (aviso se faltarem); Workers/Timeouts ≥ 1. Erros bloqueiam o início; avisos pedem confirmação. O relatório vai para o log em tempo real.
- **Aba 7 — progresso no log em tempo real:** o console antes só mostrava falhas (o `scan_core` não loga sucesso) — em uma execução saudável ficava mudo, com o andamento só no rótulo inferior e na tabela "Progresso por Loja". Agora o worker loga: início da etapa B12 (nº de lojas, workers, timeout), linha agregada `Progresso — B12 x/y | Scan x/y | Hardware n` a cada ~20 conclusões, `Etapa B12/Scan Loja concluida`, `[JAVA <n>] Scan Loja concluido: N dispositivo(s)` por loja, e um `Resumo —` final. `ConsoleLogger` ganhou `max_lines` (padrão 4000) para não crescer sem limite em execuções longas — o arquivo `.log` continua guardando tudo.
- **Versão:** `version_info.txt` (raiz) passa a ser a fonte única da versão; `version.py` do COLETOR é derivado dela no build. `COLETOR.exe` compilado e assinado em `1.25.09.26`; ZIPs `1.25.09.26` em `release/`, `release/backup/` e nas pastas externas; `release/RD-COLETOR.zip` gerado. Pendente: confirmar publicação no download server e limpar ZIPs de versões intermediárias.

## v1.09.06.26 — 10/06/2026
- Log geral `logs/coletor.log` passa a registrar cabecalho de inicializacao com aplicativo, versao, data de build, modo de execucao e diretorio base.
- Logs de console em `logs/console/` passam a iniciar com cabecalho de identificacao do COLETOR, versao e data de build.
- Build onefile recompilado com bump para `1.09.06.26`, assinatura e metadados Quallit/Preventiva Coletor.

## v1.08.06.26 — 10/06/2026
- Aba B12 ganha filtro por faixa de JAVA (`de`/`ate`), filtro `Somente offline` e botoes de selecao rapida para `OFFLINE`, `NAO ESCANEADO` e `ESCANEADO`.
- Aba B12 passa a registrar status `OFFLINE` em `tb_b12_data_collection_status`, permitindo recarregar a lista e tentar novo scan somente nesses B12.
- Campo `Workers` da Aba B12 passa a controlar paralelismo real com `ThreadPoolExecutor`.
- Aba Scan Loja ganha configuracao de `Workers` e paraleliza a varredura dos IPs de loja.
- Aba Scan Loja passa a salvar automaticamente os dispositivos online em `tb_detected_devices` ao concluir o scan, mantendo o botao manual `Salvar`.
- Aba Hardware ganha configuracao de `Workers`, paraleliza a coleta e adiciona opcao `Gerar JSON ao concluir`, marcada por padrao.
- Abas B12, Scan Loja e Hardware ganham botoes de limpeza/reprocessamento para remover dados do banco e reiniciar fluxos sem manipular logs em arquivo.
- Coletas B12 e Linux da Aba Hardware passam a compartilhar helpers de hardware Linux para memoria, disco raiz, sistema operacional, CPU, MAC e placa-mae.
- Coleta Windows via WMI passa a inicializar/finalizar COM por chamada (`pythoncom.CoInitialize`/`CoUninitialize`) e ganha fallback via SSH/PowerShell para hosts Windows com WMI bloqueado.
- Quando WMI e SSH falham, o equipamento permanece listado com status de falha e hostname `Inacessivel WMI/SSH`, preservando visibilidade da loja no relatorio.
- Schema SQLite ganha `tb_scan_runs` e `tb_scan_run_items` para registrar inicio/fim de processamento, itens inseridos e falhas por IP/JAVA.
- Coleta de disco passa a priorizar o device da particao raiz/sistema e normalizar HDD/NVMe/SSD e tamanhos em GB.
- Nova visualizacao web em `www/store.php`, com exportador Python `www/store_export.py`, permite auditar bancos SQLite locais combinando `tb_devices_detail`, `tb_detected_devices` e `tb_scan_run_items`.
- Build onefile recompilado com bump para `1.08.06.26`, assinatura e metadados Quallit/Preventiva Coletor.

## v1.05.06.26 — 09/06/2026
- Build onefile do COLETOR recompilado com bump de versão e assinatura Authenticode válida.
- Metadados do executável padronizados para Quallit/Preventiva: `CompanyName=Quallit`, `ProductName=Preventiva Coletor`, `FileDescription=Preventiva Coletor`, `OriginalFilename=Coletor.exe` e copyright Quallit.
- Arquivo `tools/file_version_info_COLETOR.txt` regenerado com `FileVersion` e `ProductVersion` em `1.05.06.26`.

## v1.04.06.26 — 09/06/2026
- Aba B12 corrigida para gravar `tb_devices_detail.java` e `tb_b12_data_collection_status.java` com o valor de `filial`/JAVA atual; `historico` permanece apenas como referência/log.
- Aba Hardware ganha seleção e filtros alinhados à Aba Scan Loja: busca, logomarca, somente não escaneado, marcar/desmarcar todos, inverter, selecionar escaneados e não escaneados.
- Aba Scan Loja ganha botões de seleção rápida para lojas `ESCANEADO` e `NAO ESCANEADO`.
- Abas Scan Loja e Hardware ganham filtro por faixa de JAVA (`de`/`até`), aplicado em conjunto com busca, logomarca e status de escaneamento.
- Logs de console passam a ser persistidos por aba em `logs/console/`.
- Build do COLETOR passa a gerar metadados `VSVersionInfo` no executável, com `CompanyName`, `ProductName`, `FileDescription`, `FileVersion`, `ProductVersion`, copyright, data de build e componente.
- `tools/build_release.py` passa a aceitar `--sign`, usando `tools/certs/quallit_codesign.pfx` quando a senha estiver disponível por variável de ambiente, com fallback para certificado instalado no store local.
- Dependências/hidden imports do build ajustados para coleta de hardware Windows (`wmi`) e impressoras SNMP (`pysnmp.hlapi.asyncio`), com fallback no código para API clássica.
- Ambiente de compilação consolidado na `.venv` da raiz do projeto; `COLETOR/.venv` removido para evitar uso acidental de dependências incompletas.
- Build onefile assinado validado em `COLETOR/dist/COLETOR.exe`, com metadados de versão `1.04.06.26`, assinatura Authenticode válida e pastas runtime preservadas em `config/`, `database/` e `logs/`.

## v1.03.06.26 — 09/06/2026
- Verificação de consistência SQLite × MariaDB: `historico` declarado `NOT NULL` no schema SQLite alinhando com constraint do MariaDB.
- `tb_b12_data_collection_status` e `tb_detected_devices` criadas no MariaDB `rd_devices_dev`; `cidr` adicionado a `tb_filial` via ALTER TABLE.
- Scripts DDL de referência criados em `PROJETO_ORIGINAL/devices_linux/config/` para as duas novas tabelas e para o ALTER.
- Aba 2 corrigida: `collection_status` alterado de `'COMPLETE'` para `'SUCCESS'`; `collection_date` passa a ser populado com o timestamp final da coleta.
- `tb_devices_detail`: INSERT OR REPLACE passa a gravar `data_atualizacao = CURRENT_TIMESTAMP` junto com `data_coleta`.

## v1.02.06.26 — 09/06/2026
- Schema SQLite inicial criado em `config/schema_sqlite_init.sql` com as 4 tabelas do COLETOR: `tb_filial`, `tb_devices_detail`, `tb_b12_data_collection_status` e `tb_detected_devices` (incluída para schema completo; auto-criada pela Aba 3).
- Aba 0 ganha botão "Criar Banco Novo..." que inicializa um `.db` vazio a partir do schema, atualiza o `config.ini` e orienta o próximo passo (importar XLS na Aba 1).
- `tb_filial` no SQLite inclui `historico` (lido do XLS coluna "Hist.") para compatibilidade com o MariaDB via INTEGRADOR.
- Importação XLS (Aba 1): `ativo` passa a ser derivado automaticamente do `ip_banco_12` — `1` se IP válido, `0` caso contrário; strip aplicado em todos os campos texto (fix: espaços em `telefone`).

## v1.01.06.26 — 09/06/2026
- Tab 3 passa a rotear testes por tipo esperado: IMPRESSORA testa somente porta 9100; PDV testa somente SSH (sempre Linux); TC testa Radmin e, se necessário, SSH com autenticação por credencial.
- Tab 4 ampliado para coletar hardware de todos os tipos de dispositivo: Linux via SSH, Windows via WMI (credencial dependente de logomarca), Impressoras via SNMP (pysnmp).
- Coleta completa de hardware Linux via SSH: hostname, modelo de CPU, núcleos físicos, RAM (GB e bytes), disco (GB e bytes), SO, kernel, MAC address, fabricante/modelo/versão da placa-mãe, modelo e tipo de mídia do disco (SSD/HDD).
- Coleta Windows via WMI usando Win32_Processor, Win32_ComputerSystem, Win32_OperatingSystem, Win32_DiskDrive e Win32_NetworkAdapter; credencial selecionada por logomarca (Drogasil/Raia).
- Coleta de impressoras via SNMP (pysnmp): fabricante, modelo (tratamento especial Epson), número de série e MAC address por OIDs padrão; configuração em `[CREDENTIALS_SNMP]` do config.ini.
- Todos os campos persistidos em colunas `hw_*` de `tb_detected_devices` (SQLite local), adicionadas automaticamente via ALTER TABLE.
- `_save_results` (Tab 3) usa `INSERT OR IGNORE` por padrão e `INSERT OR REPLACE` com Full Refresh; filtra dispositivos Offline antes de salvar; `UNIQUE(ip)` elimina duplicatas em re-scans.
- `_save_hw_result` (Tab 4) sempre sobrescreve quando chamado; guardado apenas após `_is_hw_success`, protegendo dados de coletas anteriores contra sobrescrita por falhas de conexão.

## v1.00.06.26 — 09/06/2026
- Estrutura inicial do COLETOR: GUI offline com tkinter + SQLite local.
- Abas implementadas: importação XLS (tb_filial), consulta B12 via SSH, scan de dispositivos por loja, coleta de hardware, comparação de scans, gestão de credenciais.
- Detecção de OS dos TCs via porta 7856 (Radmin = Windows) ou autenticação SSH (credencial `pdv` = Linux; credencial por logomarca = Windows).
- Credenciais armazenadas com Fernet (chave local) com fallback `b64:` quando `cryptography` não está disponível.
- Matriz de IPs por CIDR (/24 e /25) define alvos esperados por tipo: B12, PDV, TC, IMPRESSORA.
