# ADR 0002 — Modelo bibliográfico BIBFRAME e contratos canônicos

- **Status:** Proposto — pendente de aprovação
- **Data:** 2026-10-22
- **Escopo:** Catalogação, identificadores, RDF e interoperabilidade

## Contexto

O Libris adota BIBFRAME como modelo bibliográfico principal e deve admitir outras ontologias. O código atual implementa contratos restritos de **títulos** de Work e Instance em Pydantic, com conversão RDF/JSON-LD, shape SHACL e testes. Isso não constitui um modelo bibliográfico completo.

Há divergência a resolver: `WorkTitleRecord.id` e `InstanceTitleRecord.id` atualmente contêm IRIs HTTP(S), enquanto `docs/api/openapi.yaml` propõe `id` UUID, `uri` separada, `revision` e `title` como string. O contrato OpenAPI é uma proposta, não uma API implementada.

## Decisão proposta

1. **BIBFRAME como semântica canônica:** modelar `bf:Work` (obra), `bf:Instance` (materialização) e `bf:Item` (exemplar) como identidades distintas, com `bf:instanceOf` e `bf:itemOf`. Não confundir a entidade bibliográfica `bf:Item` com os estados operacionais de circulação.
2. **Identidade:** adotar UUID como chave interna proposta e IRI HTTP(S) persistente como identidade pública do recurso. A base, política de resolução e formato final das IRIs precisam ser aprovados antes de publicar dados. Identificadores externos (ISBN, ISSN, DOI, ORCID) não substituem a identidade interna.
3. **Títulos estruturados:** preservar `main_title`, `subtitle`, partes, idioma, títulos variantes e paralelos. Uma string de exibição pode ser derivada, mas não deve substituir a estrutura original.
4. **Representações:** definir um contrato de domínio independente do transporte HTTP; oferecer JSON de aplicação e JSON-LD/RDF sem perda silenciosa. Propriedades externas não suportadas devem ser preservadas por mecanismo explícito ou rejeitadas com erro informativo, nunca descartadas.
5. **Validação:** Pydantic para estruturas de entrada e invariantes locais; SHACL versionado para restrições de grafos. Validação deve anteceder persistência/publicação. Perfis publicados devem ser identificáveis por ID e versão.
6. **Relacionamentos e autoridades:** referenciar agentes, organizações e assuntos por identidades estáveis, evitando duplicação; implementar gradualmente. Não presumir integrações com VIAF, Wikidata ou MARC 21 existentes.
7. **Compatibilidade:** toda alteração em cardinalidades, mapeamentos, IRIs ou API requer atualização coordenada de modelos, serializadores, shapes, fixtures, testes e documentação.

## Alternativas consideradas

- **MARC 21 como modelo interno principal:** favorece migração tradicional, mas não realiza o objetivo BIBFRAME nativo; utilizar como formato de intercâmbio.
- **JSON simplificado como única fonte semântica:** reduz complexidade, mas pode perder relações e extensões RDF; rejeitado como modelo conceitual exclusivo.
- **BIBFRAME com contratos de aplicação tipados e mapeamento explícito:** recomendado.

## Consequências

Exige disciplina no mapeamento RDF, testes de equivalência de grafos, políticas de identificadores e evolução controlada de perfis. Em contrapartida, favorece Linked Open Data, interoperabilidade e navegação por entidades.

## Critérios de adoção

- Documentar mapeamento entre `id`/`uri`/`revision` da API proposta e `id` IRI dos modelos atuais, **antes** de mudar contratos.
- Testes de ida e volta modelo → RDF → modelo e JSON-LD → RDF com equivalência semântica.
- Rejeitar entradas inválidas e propriedades não suportadas sem perda silenciosa.
- Diferenciar Work, Instance e Item em fixtures e testes de relacionamento.
- Validar shapes SHACL com casos positivos e negativos.

## Questões pendentes

URI base e resolução HTTP, tratamento de blank nodes, suporte a extensões arbitrárias, regras de versionamento de perfis e escopo mínimo dos metadados por entidade. A aprovação desta ADR não implica que os contratos completos já estejam implementados.

## Relações

`docs/domain/bibliographic.md`, `docs/api/openapi.yaml`, `backend/app/catalog/shared/title/`, ADR 0003.
