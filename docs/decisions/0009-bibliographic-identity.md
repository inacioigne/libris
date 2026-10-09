# ADR 0009 — Identidade independente das entidades bibliográficas

Status: aceito para implementação técnica do Incremento 1; aprovação institucional pendente

Data: 2026-10-09

## Contexto

ADR 0008 mantém um grafo agregado experimental. URIs RDF distintas nesse grafo não proporcionam revisões independentes nem propriedade explícita de metadados.

## Decisão

Work, Instance, Item e autoridades controladas têm identidade, tipo e revisão próprios. O snapshot contém a descrição de uma entidade e seus nós auxiliares privados. Referências para outras entidades usam URIs. Agent/Person/Organization e skos:Concept são tipos de autoridade; Authority não é uma classe BIBFRAME inventada. Work pode existir sem Instance. Instance pode servir a vários Items.

## Alternativas consideradas

Um agregado para todo o registro simplifica gravação, mas acopla revisão de autoridades e manifestações. Tabelas específicas por classe antecipariam esquema definitivo. Escolhemos snapshots por entidade sobre o mecanismo existente.

## Consequências

Contribuições, títulos, publicações e identificadores continuam nós RDF estruturados. Auxiliares usam blank nodes locais ou IRIs sob URI-da-raiz#fragmento; identidades persistentes não usam fragmentos. Snapshot rejeita descrição alheia, nós órfãos e mudança de tipo. Referências locais precisam de integridade por contratos transacionais no Incremento 2. Não há migração automática de agregados legados.

## Estado e evidências

As diretrizes foram revisadas e autorizadas pelo solicitante após o diagnóstico
(Momentos A/B). A homologação institucional dos perfis e das regras catalográficas
continua pendente. A aprovação técnica não define domínio público nem aprova
vocabulários institucionais. Ver [contrato](../architecture/catalogographic-contract.md),
[diagnóstico](../architecture/catalogographic-contract-diagnosis.md) e
[verificação](../architecture/catalogographic-contract-verification.md).
