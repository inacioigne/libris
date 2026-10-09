# ADR 0013 — Agentes, assuntos e contribuições

Status: aceito para implementação técnica do Incremento 1; aprovação institucional pendente

Data: 2026-10-09

## Contexto

A fixture legada contém pessoas/editoras anônimas. O catálogo institucional precisa de autoridades reutilizadas e papéis explícitos, preservando estruturas BIBFRAME.

## Decisão

Usar perfil complementar authority-v1, com bf:Agent/bf:Person/bf:Organization e skos:Concept. Cada Contribution tem um agente por URI e um ou mais papéis por URI. Publication referencia publicadores sem converter a atividade em string. Rótulos autorizados/variantes e referências externas são metadados próprios da autoridade. Assuntos controlados usam bf:subject e conceitos SKOS.

## Alternativas consideradas

Copiar nomes em cada registro duplica identidade. Usar owl:sameAs automaticamente confunde identificação externa e equivalência. Exigir downloads para validar vocabulários introduz dependência de rede e risco de parsing remoto.

## Consequências

Não há reconciliação automática. rdfs:seeAlso registra referências VIAF/ORCID/ISNI/Wikidata sem afirmar equivalência; identificadores estruturados registram valor e fonte. Afirmações de owl:sameAs exigem evidência/proveniência e revisão institucional. Tradução é Work com idioma e contribuição trl, ligada por bf:translationOf à Work de origem; publicação/ISBN ficam na Instance. Essa regra e os vocabulários institucionais ainda precisam de avaliação catalográfica. Formas não controladas podem exigir perfil complementar futuro, sem relaxar silenciosamente o candidato.

## Estado e evidências

As diretrizes foram revisadas e autorizadas pelo solicitante após o diagnóstico
(Momentos A/B). A homologação institucional dos perfis e das regras catalográficas
continua pendente. A aprovação técnica não define domínio público nem aprova
vocabulários institucionais. Ver [contrato](../architecture/catalogographic-contract.md),
[diagnóstico](../architecture/catalogographic-contract-diagnosis.md) e
[verificação](../architecture/catalogographic-contract-verification.md).
