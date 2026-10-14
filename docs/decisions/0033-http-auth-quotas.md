# ADR 0033 — Quotas HTTP compartilhadas do BFF

Data: 2026-10-14. Estado: aceito para implementação local M04.07 / #40;
homologação de capacidade/produção separada.

## Contexto

O BFF usa sessões e transações compartilhadas no schema libris_web (ADR 0030).
Login/callback podem ocupar conexões e consultar o provedor. Não há contrato de
proxy/IP confiável: X-Forwarded-For arbitrário não identifica um cliente. Um Map
por processo não limitaria réplicas; adicionar Redis não se justifica.

## Decisão

Adicionar somente auth_quotas no schema web, com migração incremental 0002 própria,
explicitamente executada pelo operador. Nenhuma migração histórica é modificada;
nenhum DDL executa no startup. Runtime recebe DML somente no schema web.

Quota global independente para login, callback e logout, janela fixa iniciada na
primeira admissão. Padrões: 120, 240 e 240 requisições por 60 segundos respectivamente.
Todas as réplicas devem usar o mesmo banco e valores. Configuração privada validada:
janela 1–3600 segundos; limites 1–10000. Não há identificação de usuário por IP,
cookie ou header, nem criação de chaves controladas pelo atacante. Cardinalidade
máxima três linhas, sem expurgo ou armazenamento de dados pessoais.

INSERT ON CONFLICT DO UPDATE serializa a decisão em uma instrução PostgreSQL.
O relógio do banco inicia/renova a janela; o contador satura em limite+1. A admissão
ocorre antes de descoberta, consumo de transação, troca de código ou revogação.
Origin e limites baratos são verificados antes da quota. Recusa retorna 429 vazio,
no-store/private e Retry-After em segundos, entre 1 e o tamanho da janela.
O cálculo considera a espera por lock e arredonda para cima. Não há retry automático.
Tabela ausente/banco indisponível/timeouts recusam com 503 genérico; nenhum fallback
em memória ou acesso ao provedor. Pool/conexão/query/statement/lock têm timeouts.

## Consequências e limites

A proteção vale entre workers/réplicas que compartilhem banco/configuração; testes
usam dois pools reais e chamadas concorrentes. Não é quota individual nem promessa
de disponibilidade/fairness: um atacante pode consumir a quota global e prejudicar
usuários. NAT/múltiplas abas não são contabilizados como um único usuário; cada
requisição custa uma unidade. Ajustar capacidade somente após ensaios de carga.
Janela fixa permite rajadas na fronteira entre janelas, até duas quotas próximas.

O banco ainda é consultado para retornar 429; proteção volumétrica, limitação de
conexões/cabeçalhos/leitura lenta e identificação de origem dependem de proxy
confiável e isolamento de rede. Quotas por cliente exigirão contrato de confiança
específico antes de interpretar headers. Login e callback não repetem operações
OIDC não idempotentes; preservados PKCE, consumo único e rotação de refresh.
Backoff de descoberta é adicional e local ao processo; backoff de refresh continua
compartilhado pela sessão. Quotas não substituem autenticação, CSRF ou autorização.

Não há serviço novo, fila, Redis, usuário local ou alteração M03. Falha da migração
bloqueia autenticação até sua aplicação explícita; páginas públicas continuam
renderizando feedback genérico quando a configuração HTTP é válida.
