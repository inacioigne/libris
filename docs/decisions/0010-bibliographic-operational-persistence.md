# ADR 0010 — Persistência bibliográfica e operacional

Status: aceito para implementação técnica do Incremento 1; aprovação institucional pendente

Data: 2026-10-09

## Contexto

PostgreSQL já persiste JSON-LD expandido em JSONB e mantém identidade e revisão atual. Inventário e circulação são domínios futuros, distintos do Item semântico.

## Decisão

Manter JSONB como conteúdo RDF canônico, PostgreSQL como fonte transacional única e RDFLib Graph como representação em memória. Tipos são afirmações RDF do snapshot; criação e alteração são derivadas das revisões primeira e atual. Proveniência técnica está nas colunas existentes; proveniência semântica pode ser expressa no grafo. Não criar esquema bibliográfico definitivo neste incremento.

## Alternativas consideradas

Triplestore introduziria outra fonte gravável e sincronização distribuída. Colunas para todos os campos perderiam extensibilidade ou exigiriam migrações frequentes. Turtle em TEXT preserva RDF, mas abandona sem necessidade a infraestrutura JSONB funcional.

## Consequências

O esquema experimental existente acomoda novas raízes e releases sem alteração física, portanto não há nova migração. Ciclo de vida/tombstones são contrato futuro, não colunas nem operações já disponíveis. Barcode/inventário podem aparecer como identificação bibliográfica local, mas situação patrimonial, empréstimos, multas e reservas pertencem aos módulos administrativos; alterações operacionais não avançam a revisão de Item.

## Estado e evidências

As diretrizes foram revisadas e autorizadas pelo solicitante após o diagnóstico
(Momentos A/B). A homologação institucional dos perfis e das regras catalográficas
continua pendente. A aprovação técnica não define domínio público nem aprova
vocabulários institucionais. Ver [contrato](../architecture/catalogographic-contract.md),
[diagnóstico](../architecture/catalogographic-contract-diagnosis.md) e
[verificação](../architecture/catalogographic-contract-verification.md).
