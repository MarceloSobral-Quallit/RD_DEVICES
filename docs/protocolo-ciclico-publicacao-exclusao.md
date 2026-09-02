# Protocolo Ciclico - Publicacao e Exclusao (RD Devices)

## Objetivo

Garantir alinhamento continuo entre documentacao, implementacao, compilacao, empacotamento e auditoria de consistencia.

## Ciclo Operacional (Rodada)

1. Contrato
- Confirmar que a documentacao descreve o comportamento real dos componentes COLETOR e INTEGRADOR.
- Declarar escopo da rodada e criterios de aprovacao.

2. Implementacao
- Ajustar codigo e scripts apenas quando houver divergencia com o contrato.
- Preservar seguranca operacional (sem apagar dados validos sem confirmacao explicita).

3. Execucao Tecnica
- Rodar validacoes tecnicas da rodada (build, sintaxe, integridade de artefatos, verificacoes de banco).
- Registrar evidencias (comandos executados e artefatos gerados).

4. Auditoria De Consistencia
- Verificar referencias cruzadas em docs, README raiz e scripts.
- Corrigir referencias orfas antes de encerrar a rodada.

## Criterio De Aprovacao Da Rodada

Uma rodada so e aprovada quando:

1. contrato sem contradicoes;
2. implementacao aderente ao contrato;
3. validacoes tecnicas aprovadas;
4. evidencias registradas na documentacao.

## Evidencias Minimas Por Rodada

Registrar em docs/DEV_PLAYBOOK.md e/ou docs/RoadMap.md:

1. comandos executados;
2. arquivos alterados/criados;
3. resultado da rodada (aprovada ou pendente);
4. riscos e pendencias remanescentes.

## Aplicacao No RD Devices

- COLETOR e INTEGRADOR devem manter versao alinhada quando a entrega for conjunta.
- Build de release deve evitar recursao de ZIP quando diretorios de saida estiverem dentro da raiz do projeto.
- Fluxo oficial de dados: COLETOR (SQLite) -> transporte controlado -> INTEGRADOR (MariaDB).
