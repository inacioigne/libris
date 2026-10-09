# ADR 0015 — Consistência transacional e RDF

Status: aceito para implementação técnica do Incremento 1; aprovação institucional pendente

Data: 2026-10-09

## Contexto

RDF já é persistido dentro do mesmo PostgreSQL. Não existem consumidores de eventos ou store RDF externo. Inversas graváveis em dois snapshots criariam duas fontes para o mesmo relacionamento.

## Decisão

Afirmações canônicas ficam no proprietário: Instance instanceOf Work e Item itemOf Instance. hasInstance/hasItem são derivadas na composição; não são armazenadas no novo snapshot. Avanço CAS e inserção JSONB usam o mesmo commit e rollback. Composição renomeia blank nodes de grafos independentes e rejeita raízes duplicadas. Não introduzir Dataset, fila ou outbox neste incremento.

## Alternativas consideradas

Materializar ambas as direções exige coordenação e possível revisão de dois agregados. Dois bancos graváveis exigiriam protocolo de consistência. Named graphs físicos identificariam contexto, mas exigiriam mudar o adaptador e não acrescentam atomicidade ao modelo existente.

## Consequências

Representações compostas podem mudar sem alteração da revisão do pai. Relações inversas são validadas no modo composed; snapshots aceitam referências por URI sem requerer descrições alheias. Leitura histórica deve informar quais revisões/dependências foram compostas. Ao implementar a primeira projeção Elasticsearch, adicionar outbox no commit, evento identificável, consumidores idempotentes por entidade/revisão, tentativas, reconciliação e reconstrução; não publicar antes do commit. Não há escrita dupla, transação distribuída ou promessa de entrega nesta fase.

## Estado e evidências

As diretrizes foram revisadas e autorizadas pelo solicitante após o diagnóstico
(Momentos A/B). A homologação institucional dos perfis e das regras catalográficas
continua pendente. A aprovação técnica não define domínio público nem aprova
vocabulários institucionais. Ver [contrato](../architecture/catalogographic-contract.md),
[diagnóstico](../architecture/catalogographic-contract-diagnosis.md) e
[verificação](../architecture/catalogographic-contract-verification.md).
