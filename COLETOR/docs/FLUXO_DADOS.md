# Fluxo de Dados do COLETOR

```text
Equipamentos da loja
        |
        v
COLETOR
        |
        v
SQLite local (devices.db)
        |
        v
Cópia manual/controlada para máquina administrativa
        |
        v
INTEGRADOR
        |
        v
MariaDB rd_devices_dev
```

## Regras

- O `COLETOR` grava e lê somente SQLite.
- O `COLETOR` não contém credenciais MariaDB.
- O importador não deve ser empacotado junto do coletor.
- O SQLite coletado é o contrato entre os dois componentes.

---

## Aba 2 — Consulta B12

- Conecta via SSH ao IP do B12 (`tb_filial.ip_banco_12`).
- Coleta: hostname, SO, kernel, CIDR, CPU, memória, MAC, placa-mãe, disco.
- Grava em `tb_devices_detail` e `tb_b12_data_collection_status`.
- Atualiza `tb_filial.cidr` com o prefixo detectado (ex: `/24` ou `/25`).

## Aba 3 — Scan Loja (matriz de IPs por CIDR)

O scan usa o CIDR coletado na Aba 2 para gerar a lista completa de IPs da loja:

### CIDR /24

| Tipo       | Últimos octetos               |
|------------|-------------------------------|
| B12        | .12 (ignorado — coletado Aba 2) |
| PDV        | .1–.10, .110–.120             |
| TC         | .11, .13–.19, .30, .60, .70   |
| IMPRESSORA | .61, .62, .63                 |

### CIDR /25

| Tipo       | Últimos octetos               |
|------------|-------------------------------|
| B12        | .12 (ignorado — coletado Aba 2) |
| PDV        | .1–.10, .110–.120             |
| TC         | .129–.146                     |
| IMPRESSORA | .161–.165                     |

### Classificação por portas e autenticação SSH

A detecção segue uma hierarquia com dois estágios:

**Estágio 1 — Porta 7856 (Radmin)**

| Resultado        | Tipo detectado   |
|------------------|------------------|
| 7856 aberta      | TC Win           |

O Radmin é instalado em praticamente todos os TCs Windows da rede. Quando esta porta responde, o equipamento é classificado como Windows sem etapa adicional.

**Estágio 2 — Porta 22 (SSH) + autenticação**

Quando apenas a porta 22 está aberta, o sistema tenta autenticar com as credenciais de cada perfil:

| Credencial testada                          | Sucesso → Tipo detectado |
|---------------------------------------------|--------------------------|
| `CREDENTIALS_LINUX_STORE` (usuário `pdv`)   | TC Linux                 |
| `CREDENTIALS_TERMINAL_WINDOWS_*` (por logomarca: `drogasil` ou `drogaraia`) | TC Win |
| Nenhuma autentica                           | SSH/Desconhecido         |

A logomarca da loja (`tb_filial.logomarca`) determina qual credencial Windows é usada: `CREDENTIALS_TERMINAL_WINDOWS_DROGASIL` para lojas Drogasil e `CREDENTIALS_TERMINAL_WINDOWS_RAIA` para lojas Raia.

**Demais casos**

| Portas abertas      | Tipo detectado |
|---------------------|----------------|
| JetDirect (9100)    | IMPRESSORA     |
| Nenhuma             | Offline        |

- Resultado salvo em `tb_detected_devices` com os campos `expected_type` e `device_type`.
- `expected_type`: tipo esperado pela matriz (PDV, TC, IMPRESSORA).
- `device_type`: tipo detectado pelas portas e/ou autenticação SSH.

