# ADR 0012 — Política institucional de URIs

Status: aceito para implementação técnica do Incremento 1; aprovação institucional pendente

Data: 2026-10-09

## Contexto

A convenção existente é RESOURCE_BASE_URI/uuid, com URI materializada e persistida. Não há endpoint resolvível ou domínio público institucional escolhido.

## Decisão

Preservar /resources/{uuid} para todas as classes, sem título, ISBN ou tipo no caminho. URI armazenada prevalece sobre mudança da base. Identificadores jamais são reutilizados. URL de interface, URL de documento e URI da entidade são distintas. Recursos ativos usarão 303 para representação negociada; documentos retornam 200. Implementação HTTP fica para o Incremento 2.

## Alternativas consideradas

/id/works/{uuid} explicita tipo, mas muda a convenção e torna mudanças de classificação dependentes de URI. Resposta RDF direta 200 é mais simples; escolhemos 303 para distinguir identidade de documento.

## Consequências

A política detalhada de Accept, Vary, 404/406/410, tombstones e fusões está no contrato. Fusão comprovada terá 308 para a identidade sobrevivente; substituição sem equivalência terá relação explícita, sem assumir fusão. Domínio público, publicação e permissões de descontinuação/fusão exigem revisão institucional. Nada reescreve URIs existentes ou externas. A função de identidade e a persistência são testadas, sem criar infraestrutura de resolução.

## Estado e evidências

As diretrizes foram revisadas e autorizadas pelo solicitante após o diagnóstico
(Momentos A/B). A homologação institucional dos perfis e das regras catalográficas
continua pendente. A aprovação técnica não define domínio público nem aprova
vocabulários institucionais. Ver [contrato](../architecture/catalogographic-contract.md),
[diagnóstico](../architecture/catalogographic-contract-diagnosis.md) e
[verificação](../architecture/catalogographic-contract-verification.md).
