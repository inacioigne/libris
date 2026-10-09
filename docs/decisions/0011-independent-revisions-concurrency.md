# ADR 0011 — Revisões independentes, histórico e concorrência

Status: aceito para implementação técnica do Incremento 1; aprovação institucional pendente

Data: 2026-10-09

## Contexto

O CAS, histórico imutável, trigger e FK diferida existentes são adequados. ETag/If-Match não existem na API atual. Uma composição pode variar quando autoridade ou relacionamento filho muda.

## Decisão

Reutilizar BibliographicService e RevisionStore. O perfil exato é informado na criação e preservado em revisões; tipo da raiz também é preservado. UUID:revisão identifica o validador opaco de escrita. CAS continua decidindo a atualização no banco; falhas revertem avanço e snapshot. Uma atualização de Authority/Instance/Item não revisa Work.

## Alternativas consideradas

Versão global ou revisão em cascata acoplariam entidades. Sobrescrita sem histórico perde auditoria. Usar número de revisão sozinho como ETag forte de todos os formatos viola a distinção de representações e dependências.

## Consequências

O token de domínio não é ETag HTTP publicado. Na API futura, a representação de edição terá ETag forte apropriado e If-Match obrigatório (428 sem precondição, 412 obsoleta); aceitar apenas validador da representação e rejeitar W/, curingas e seleções incompatíveis conforme contrato. Exportações têm ETags próprios, incluindo formato, bytes e dependências. Histórico devolve afirmações proprietárias da revisão; composição histórica exige revisões escolhidas/corte temporal, sem alegar que a composição atual é snapshot histórico. Auditoria humana depende de autenticação posterior.

## Estado e evidências

As diretrizes foram revisadas e autorizadas pelo solicitante após o diagnóstico
(Momentos A/B). A homologação institucional dos perfis e das regras catalográficas
continua pendente. A aprovação técnica não define domínio público nem aprova
vocabulários institucionais. Ver [contrato](../architecture/catalogographic-contract.md),
[diagnóstico](../architecture/catalogographic-contract-diagnosis.md) e
[verificação](../architecture/catalogographic-contract-verification.md).
