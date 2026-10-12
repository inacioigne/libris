# Contratos públicos Pydantic — M03.01.02

Implementação técnica sobre `monograph-v1.1` e `authority-v1`, candidatos locais
já existentes da M03.01.01. A homologação institucional permanece pendente.
Os DTOs não substituem RDFLib Graph como modelo semântico canônico nem SHACL
como validador de conformidade. Não são modelos ORM, snapshots persistentes ou
JSON-LD. Decisões de representação estão no [ADR 0017](../decisions/0017-catalogographic-json-contracts.md).

## Diagnóstico e arquivos

A investigação leu README, convenções, arquitetura, ADRs, perfis JSON/SHACL,
serviço, identidade, exemplos Turtle e testes existentes. Na consulta às issues,
M03.01.01 (#14) estava concluída; M03.01.03 (#16), M03.01.04 (#17) e
M03.01.05 (#18) estavam abertas, sem descrição retornada pelo conector.
A implementação se limita às decisões técnicas já registradas nos ADRs 0009–0015.
Não presume encerramento das dependências.

Plano executado: acrescentar DTOs na camada API do módulo bibliográfico existente,
tipos compartilhados, contratos por recurso, testes isolados e exemplos JSON;
preservar domínio, aplicação, infraestrutura, perfis publicados e rotas reais.

Localização: `apps/api/src/libris/modules/bibliographic/api/schemas/`.
`common.py` contém identidade de leitura, referências e auxiliares reutilizados;
`work.py`, `instance.py`, `item.py`, `agent.py` e `subject.py` contêm os contratos
Create/Read/Update. `__init__.py` publica os quinze contratos. Não há dependência
SQLAlchemy/FastAPI nesses arquivos. Reutiliza-se a validação de identidade existente.

O teste `tests/api/test_catalogographic_schemas.py` confere campos e obrigatoriedade
contra os JSONs locais, round-trip, rejeições, PATCH e OpenAPI. As quinze fixtures
em `tests/fixtures/bibliographic/contracts/` derivam dos exemplos sintéticos
institucionais `single-author.ttl`, `local-item.ttl` e `controlled-subjects.ttl`.
Nenhum ISBN ou autoridade de exemplo afirma existência real.

Uma matriz textual preexistente menciona `bf:itemLocation`; os artefatos JSON,
SHACL e fixtures implementam `bf:shelfMark`. Este contrato usa `shelf_mark`, sem
alterar releases ou corrigir silenciosamente decisões da M03.01.01.

## Convenções e cardinalidades

Nomes públicos em inglês, `snake_case`, sem aliases novos. O campo singular mantém
o nome da propriedade mesmo quando seu valor é uma lista, como nos descritores de
perfil. `relatedTo` vira `related_to`, `editionStatement` vira `edition_statement`.
`provenance` representa `prov:wasDerivedFrom`, nunca proveniência técnica/ator.
`Subject` corresponde a `skos:Concept`; `kind` de Agent admite somente Agent,
Person e Organization, sem hierarquia artificial de subclasses.

| Recurso | Obrigatórios no Create e Read | Outros campos proprietários, todos 0..* |
| --- | --- | --- |
| Work | `title` 1..*, ao menos um Title não variante | language, content, contribution, subject, classification, related_to, translation_of, note |
| Instance | `instance_of` 1..1 | title, edition_statement, provision_activity, identified_by, extent, carrier, note |
| Item | `item_of` 1..1; `identified_by` 1..*, ao menos um Local | held_by, note, custodial_history, shelf_mark, provenance |
| Agent | `kind` 1..1; `authorized_name` 1..* | variant_name, identified_by, external_reference, provenance, related_authority |
| Subject | `preferred_label` 1..*; `scheme` 1..* | alternative_label, broader, related, external_reference, provenance |

Create contém somente conteúdo proprietário. Read acrescenta `internal_id` (UUID)
e `uri` materializada. UUID e URI são fornecidos pelo chamador confiável na leitura,
nunca derivados de ISBN/barcode/título. A leitura não recalcula a URI com a base do
ambiente, não expõe actor_id, source, process ou colunas técnicas. Não acrescenta
inversas compostas hasInstance/hasItem nem presume consulta de filhos.

Coleções opcionais omitidas no Create/Read viram listas vazias independentes;
`null` é rejeitado. Listas obrigatórias exigem ao menos um elemento. Valores escalares
não substituem listas, e listas não substituem referências unitárias. Campos
extras são rejeitados em todos os níveis. Literais preservam espaços e grafia;
string vazia não é um valor, números não são convertidos em texto.

## Auxiliares e referências

Textos usam `{"value":"Título","language":"pt-BR"}`. `language` pode ser omitido
ou null: texto sem tag, sem idioma presumido. Tags seguem a sintaxe estrutural
aceita por RDFLib (letras, seguidas de subtags alfanuméricas com hífen); não há
consulta ao registro IANA nem verificação de existência de um idioma. A tag e o
texto originais são preservados. No comparador de idiomas, maiúsculas/minúsculas
não distinguem tags. main_title, authorized_name e preferred_label aceitam uma
forma por idioma, incluindo uma forma sem idioma. preferred_label e alternative_label
não podem conter o mesmo termo RDF (valor e tag), quando ambos estão presentes.

Title tem `kind` Title/VariantTitle, `main_title` 1..* e `subtitle` 0..*.
Contribution tem `agent` 1..1 e `role` 1..*. Publication tem agent/place/date 0..*.
Identifier tem kind Identifier/Local/Isbn, `value` 1..1 e `source` 0..*; ISBN
transcrito não vazio é preservado sem checksum, conforme o perfil. Extent/Note têm
`label` 1..*; Note tem `note_type` 0..* de textos sem idioma. Classification tem
`classification_portion` 1..* e source 0..*. ShelfMark tem value 1..1 e source 0..*.
Auxiliares incorporam a revisão do proprietário, sem identidades/revisões próprias.

PublicationDate preserva `value` textual e `datatype` explícito xsd:string, xsd:gYear
ou xsd:date (URI completa). O default é xsd:string; transcrição incerta permanece
texto, nunca é interpretada automaticamente como ano/data. gYear/date verificam
forma lexical, calendário gregoriano, ano não zero e timezone opcional até ±14:00;
aceitam anos negativos/longos. Nenhuma normalização de valor ou timezone é feita.

ResourceReference contém somente `uri`. A IRI deve ser absoluta, sem espaços,
controles ou caracteres proibidos; HTTP(S) exige host. URN e outros esquemas são
permitidos para referências, fontes e vocabulários. A identidade própria Read usa
HTTP(S), sem credenciais/query/fragmento, conforme ResourceIdentity e ADR 0012.
As strings são preservadas, inclusive caixa, escapes e fragmentos de IRIs externas.

A classe esperada vem da propriedade e do perfil: instance_of → Work, item_of →
Instance, contribuição → Agent/Person/Organization, subject → Concept, held_by →
Organization. O DTO não afirma a classe de um alvo apenas a partir da URI e não
consulta banco/rede. Validar existência, classe real, ciclo de vida e concorrência
continua responsabilidade da aplicação/SHACL. Não há alternativa UUID-only ou
regra unilateral de exclusividade UUID/URI: depende da M03.01.04. Entidades completas
não são embutidas nas referências.

## Atualização parcial

Update permite `{}`. `model_fields_set` distingue presença e
`model_dump(mode="json", exclude_unset=True)` preserva a intenção. Não usar
`exclude_none=True`: apagaria remoções explícitas.

| Entrada | Intenção |
| --- | --- |
| Campo omitido | Preservar o valor atual |
| Campo opcional com null | Remover os valores dessa propriedade |
| Campo opcional com [] | Substituir a coleção por coleção vazia |
| Campo com valor/lista | Substituir integralmente a propriedade |
| Campo obrigatório com null ou [] | Rejeitar; referência unitária também rejeita lista |
| internal_id, uri, kind, revision, actor_id | Rejeitar: não são campos atualizáveis |

Null e [] permanecem distintos no DTO/JSON; ambos podem resultar na ausência de
triplas de uma propriedade opcional no futuro adaptador. Estruturas auxiliares
são substituídas completas, sem PATCH recursivo. O schema remove o ramo null apenas
nos atributos obrigatórios de Update, mantendo-os omissíveis no OpenAPI.

Antes de gravar, a futura aplicação precisa aplicar as remoções/substituições ao
snapshot vigente e validar o resultado completo. Um SubjectUpdate que fornece
somente alternative_label não pode conferir disjunção com preferred_label omitido.
O serviço também terá de aplicar a revisão esperada/CAS existente e as precondições
HTTP da entrega correspondente. Nenhuma gravação/PATCH HTTP foi implementada aqui.

## FastAPI, serialização e extensibilidade

Os contratos geram JSON Schema e podem ser usados como body e response_model.
O teste registra quinze rotas exclusivamente numa FastAPI isolada, valida referências
OpenAPI e respostas 422 padrão. A aplicação real mantém `/health` e
`/api/v1/identity/me`; não há endpoints catalográficos artificiais. Rotas futuras
seguirão `/api/v1` e a estratégia de validação existente. Se uma resposta devolver
um Update, usar `response_model_exclude_unset=True` para preservar omissões.

Create/Read fazem round-trip com model_dump(mode="json"), model_validate e
model_validate_json. UUID sai como string; URIs não são normalizadas. Update faz
round-trip com exclude_unset=True, inclusive null explícito. Não há dependências
novas ou alterações de locks. Os schemas permitem geração futura de clientes;
nenhum cliente TypeScript foi gerado nesta issue.

O contrato é uma superfície de edição tipada dos perfis locais, não um formato
RDF genérico nem uma exportação lossless de todo o grafo. Campos desconhecidos
falham, em vez de serem descartados. O núcleo RDF existente continua aberto a
outras ontologias. Uma representação pública de extensões, tipos RDF adicionais,
IRIs/blank nodes auxiliares e datatypes arbitrários depende da M03.01.05 e de
perfis explícitos futuros; não se adicionou metadata/dicionário arbitrário ou
conversor especulativo. Consumidores não devem substituir um grafo completo por
este DTO sem uma política de preservação de propriedades fora do perfil.

## Exemplos JSON

Exemplos mínimos de Create, Read e Update, respectivamente. As fixtures contêm
exemplos mais ricos e são validadas nos testes. Identidades são exclusivamente sintéticas.

### Work

```json
{"title":[{"main_title":[{"value":"Monografia sintética de teste","language":"pt"}]}]}
```

```json
{"internal_id":"00000000-0000-4000-8000-000000000001","uri":"https://catalog.example.invalid/resources/00000000-0000-4000-8000-000000000001","title":[{"main_title":[{"value":"Monografia sintética de teste","language":"pt"}]}]}
```

```json
{"subject":[]}
```

### Instance

```json
{"instance_of":{"uri":"https://catalog.example.invalid/resources/00000000-0000-4000-8000-000000000001"}}
```

```json
{"internal_id":"00000000-0000-4000-8000-000000000002","uri":"https://catalog.example.invalid/resources/00000000-0000-4000-8000-000000000002","instance_of":{"uri":"https://catalog.example.invalid/resources/00000000-0000-4000-8000-000000000001"}}
```

```json
{"edition_statement":null}
```

### Item

```json
{"item_of":{"uri":"https://catalog.example.invalid/resources/00000000-0000-4000-8000-000000000002"},"identified_by":[{"kind":"Local","value":"TEST-3"}]}
```

```json
{"internal_id":"00000000-0000-4000-8000-000000000003","uri":"https://catalog.example.invalid/resources/00000000-0000-4000-8000-000000000003","item_of":{"uri":"https://catalog.example.invalid/resources/00000000-0000-4000-8000-000000000002"},"identified_by":[{"kind":"Local","value":"TEST-3"}]}
```

```json
{"held_by":[]}
```

### Agent

```json
{"kind":"Person","authorized_name":[{"value":"Autoridade fictícia 10","language":"pt"}]}
```

```json
{"internal_id":"00000000-0000-4000-8000-000000000010","uri":"https://catalog.example.invalid/resources/00000000-0000-4000-8000-000000000010","kind":"Person","authorized_name":[{"value":"Autoridade fictícia 10","language":"pt"}]}
```

```json
{"variant_name":[]}
```

### Subject

```json
{"preferred_label":[{"value":"Assunto sintético","language":"pt"}],"scheme":[{"uri":"urn:libris:test:subjects"}]}
```

```json
{"internal_id":"00000000-0000-4000-8000-000000000030","uri":"https://catalog.example.invalid/resources/00000000-0000-4000-8000-000000000030","preferred_label":[{"value":"Assunto sintético","language":"pt"}],"scheme":[{"uri":"urn:libris:test:subjects"}]}
```

```json
{"alternative_label":[]}
```

## Verificação e critérios de aceitação

Comandos executados a partir de `apps/api`, usando as ferramentas do ambiente
virtual existente (Python 3.13.15):

- `.venv/bin/pytest`: suíte padrão sem PostgreSQL/Elasticsearch; resultado final
  **315 testes aprovados**, incluindo 171 novos, sem falhas. Foram emitidos
  273 avisos de depreciação preexistentes.
- `.venv/bin/ruff check . ../../tests`: lint de todo o backend e testes.
- `.venv/bin/mypy src`: tipagem strict, 41 arquivos.
- `.venv/bin/alembic heads`: `0002_revision_actor (head)`.
- `.venv/bin/alembic upgrade head --sql`: geração offline bem-sucedida, sem aplicar
  migrações; DDL temporário fora do repositório.

A partir de `apps/web`, Node 24.5.0 local com dependências já instaladas:
`node node_modules/next/dist/bin/next build --webpack` e
`node node_modules/typescript/bin/tsc --noEmit` passaram. Na raiz,
`docker compose --env-file .env.example config --quiet` e `git diff --check` passaram.
Não houve mudança de código/dependências do frontend.

`bash scripts/check.sh` foi tentado e parou no uv via Snap: snap-confine recusou
execução pelo confinamento do ambiente. Todas as partes do script foram executadas
separadamente com as ferramentas locais. TestClient precisou de execução fora do
sandbox por restrições de streams; não foi substituído por mock. Os avisos existentes
de Starlette/httpx e RDFLib/ConjunctiveGraph permanecem visíveis. Nenhum teste de
integração PostgreSQL foi executado para esta alteração de contratos; não há
persistência alterada ou validação referencial implementada para afirmar.

| Critério | Resultado |
| --- | --- |
| Cinco recursos com Create/Read/Update Pydantic v2 | Atendido |
| Tipos compartilhados, nulidade, cardinalidade, campos extras e imutabilidade | Atendido |
| JSON e PATCH preservando omissão/null/valor explícito | Atendido; usar exclude_unset em Update |
| Compatibilidade com campos e relações dos perfis existentes | Atendido para os artefatos locais candidatos; homologação pendente |
| Sem acoplamento ORM ou segunda fonte bibliográfica canônica | Atendido |
| JSON Schema/FastAPI/OpenAPI e testes sem serviços | Atendido na aplicação isolada |
| Documentação e quinze exemplos testados | Atendido |
| Integração em endpoints catalográficos reais | Pendente: não existem endpoints; nenhum foi simulado em produção |
| Referências UUID-only/alternativas e integridade dos alvos | Parcial: URI conforme ADRs; demais regras dependem das M03.01.03/.04 |
| Extensões semânticas públicas genéricas e transformação RDF/JSON-LD | Pendente: M03.01.05; núcleo Graph existente preservado |

Próximos passos: concluir regras de referências nas M03.01.03/.04; definir na
M03.01.05 a preservação de propriedades e identidades auxiliares; integrar os
DTOs na API real com validação do estado resultante, autorização e concorrência.
