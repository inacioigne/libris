# ADR 0024 — Valores controlados e evidência de resolução separada

Status: implementado tecnicamente para #24; homologação institucional pendente

Data: 2026-10-12

## Contexto

Os DTOs URI-only e EntityReference, rótulos LocalizedText e perfis 2.0 existem,
assim como Graph canônico, SHACL e Diagnostic. ReferenceValue.vocabulary declara
a fonte, mas não há valor rico de conceito, estados ou contrato de provedores.
Editar esses DTOs/releases mudaria contratos históricos. Consultar a rede durante
validação acoplaria aceitação de registros à disponibilidade de terceiros.

## Decisão

Contrato operacional aditivo libris.catalog-value 1.0, Pydantic discriminado:
literal, controlled_concept, local_concept, entity_reference. Reutilizar os tipos
comuns e os contratos EntityReference, sem mover ou relaxar os DTOs anteriores.
Application contém os valores/protocolo e diagnósticos; domínio contém somente
registro confiável de evidência de pertença e códigos. Nenhuma dependência HTTP no
domínio; nenhuma consulta nos validadores. A API reexporta o contrato.

Literais usam lexicais string/datatype compatíveis com perfis 2.0, sem coerção de
número/data JSON. Conceitos usam URI, vocabulary IRI e lista LocalizedText de
preferenciais únicos por idioma. Label não é identidade; ausência é permitida.
Conceitos locais conservam UUID/URI persistidos segundo ADR 0019.

Estados conhecidos da referência separados de outcome da consulta: resolved,
unverified, invalid, deprecated, unavailable; success, temporary_failure,
permanent_failure. Fonte obrigatória para estado definitivo; trusted provider e
proveniência explicitam evidência, sem afirmar que uma string source prova confiança.
EnrichedConcept conserva cataloged, attempt e última evidência. Sucessor não
substitui URI. Atualização de rótulo/estado exige decisão e nova revisão esperada.

VocabularyRegistry fixa evidência/release selecionada por URI exata e distingue
conjuntos completos/parciais. Ausência em parcial é desconhecida. Não confundir
registro de instâncias com SemanticRegistry de classes/propriedades. Verificação
suplementar usa campos já resolvidos e Diagnostic; SHACL histórico permanece
nodeKind/enums/classes/cardinalidades e não passa a alegar pertença remota.

Cache é política tipada documentada, sem infraestrutura persistente. Falhas
transitórias preservam evidência e registro aceito. Falhas definitivas da consulta,
inclusive not_found escopado, não invalidam identidade global automaticamente.

RDF do link bibliográfico contém URIRef, sem metadados de enriquecimento ou tipo
inventado sobre alvo externo. Descrição local própria mapeia explicitamente SKOS.
Ambos reutilizam Graph/serializadores/parser restrito e isomorfismo do ADR 0020.
Não criar owl:sameAs ou outros matches. Projeção as_reference para DTO histórico
é explícita e reduzida; metadados permanecem no contrato operacional separado.

## Alternativas e consequências

- Estender ResourceReference em todos os DTOs: mudaria schemas públicos sem caso
  de adoção/armazenamento autorizado. Evolução aditiva mantém compatibilidade.
- URI com prefixo/label igual como pertença: prova insuficiente; exigir evidência.
- Copiar todo vocabulário ou criar cache/tabelas: não necessário nesta etapa.
- Metadados externos no snapshot local: viola ownership e mistura afirmações de
  terceiros com transcrição catalogada. Enriquecimento separado evita sobrescrita.
- Gerar shapes ou atualizar releases antigas: mudaria interpretação histórica;
  futuras políticas RDF precisarão de novos artefatos/releases explícitos.

Sem novos endpoints/dependências, bibliotecas, filas, tabelas ou migrações.
O contrato é base reutilizável de #23/#25, não implementação de extensibilidade
irrestrita. Trust, domínio público, TTLs e vocabulários institucionais aguardam
homologação. [Especificação](../architecture/controlled-vocabularies.md).
