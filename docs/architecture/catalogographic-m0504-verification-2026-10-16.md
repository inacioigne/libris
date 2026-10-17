# Verificação M05.04 / issue #48 — 2026-10-16

## Contexto e escopo

Execução no checkout local, branch main, inicialmente sem alterações. A issue #48
foi consultada pelo conector GitHub em leitura, junto de #16/#20/#21/#22/#24/#25/
#45/#46/#47. A #47 estava aberta no GitHub, embora seu CRUD já existisse localmente;
o código foi a fonte de integração. Nenhuma issue foi modificada. Não houve pull,
branch, commit, PR, push, migração em banco de trabalho ou mudança de dependências.

Reutilizados CatalogService/BibliographicService, `_revise`, RevisionStore,
EditorialStore/AuditStore, gate transacional, DTOs v1, referências tipadas, operações
puras, resolução local, ownership, parser limitado, registry/SHACL e guard OIDC.
[ADR 0037](../decisions/0037-catalog-relationships-prevalidation.md) documenta as
escolhas adicionais. [Contrato HTTP](catalogographic-http.md#m0504--48--capacidades-implementadas)
contém os cinco handlers, entradas, respostas, exemplos, erros e permissões.

## Matriz de compatibilidade exigida

| Dependência | Contrato reutilizado / integração | Evidência executável | Limites preservados |
| --- | --- | --- | --- |
| #16 | RelationshipRead/Create/Update, add/remove/replace, DEFAULT_REGISTRY, resolved update, validate_cycles; aplicação à cópia integral do snapshot | test_relationship_lifecycle_integrity_history_and_extensions, test_inverses_cycles_and_target_types, test_relationship_writes_all_five_entities | Unreconciled sem política persistente é recusada; tipo externo ambíguo recebe reference.unverified |
| #20 | Registro local, release_ids/resolve, ResolvedProfile, campos/políticas/lineage; projeção pública legada sem arquivos | test_profiles_are_fixed_read_only_and_no_filesystem_leaks, test_profile_policy_draft_selection_and_jsonld_composed; suíte declarativa existente | Configured não significa approved; draft consultável mas não selecionável; 2.0 fora da persistência |
| #21 | validate_catalog, fontes SHACL locais e suplemento 2.0; mesmo motor da escrita | test_rdf_prevalidation_same_engine_and_no_sessions, test_prevalidation_observably_has_no_dml_and_matches_write, test_profile_policy_draft_selection_and_jsonld_composed | Sem downloads, inferência ou homologação institucional; limites não são deadline de CPU |
| #22 | CatalogValidationResult/Diagnostic 1.0, CatalogValidationRejected, handlers Problem Details/request ID | test_invalid_prevalidation, test_failed_engine_is_not_semantic_nonconformity, test_capabilities_deny_by_default; testes anteriores de diagnósticos | Nenhum código obrigatório novo; completed/failed distintos; sem dados internos nos erros |
| #24 | Referências/vocabulários permanecem nos DTOs e perfis existentes; nenhuma transformação de valor ou prova remota de pertença | Regressão test_controlled_vocabularies.py, políticas de perfil e testes de referências locais/externas | Não expõe endpoint de reconciliação nem alega verificar fonte externa |
| #25 | Graph integral e extensões da release, parser e serializadores existentes; relações alteram somente suas triplas | test_relation_graph_preserves_all_unaffected_terms, test_relationship_lifecycle_integrity_history_and_extensions, test_publication_changes_only_requested_agent_and_contribution_annotations_refuse_loss; regressão de extensões | Contribution anotada é preservada mediante recusa de remoção; metadados operacionais externos não são inventados no RDF |

## Testes novos e garantias observadas

`tests/api/test_catalog_capabilities.py` cobre HTTP real sem serviços externos,
401/403, resultados SHACL e falha técnica, release desconhecida/incompatível/draft,
JSON-LD remoto recusado, formatos/estrutura/spoofing, limites de bytes/profundidade,
perfis imutáveis/somente leitura, JSON-LD válido, contexto composto e políticas 2.0.
Testes puros verificam isomorfismo, preservação de extensões e publicação anotada.

`tests/integration/test_catalog_capabilities_postgres.py` usa PostgreSQL real,
com ator sintético injetado na dependência existente, sem alegar ensaio Keycloak.
Testa ciclo add/replace/remove, duplicação, inexistência, referências externas e
pendentes, tipos, inversas sem armazenamento, ciclos locais, cinco entidades,
falhas após snapshot/auditoria/CAS/commit, duas sessões concorrentes e candidata
isolada. Observação do SQL comprova ausência de INSERT/UPDATE/DELETE durante as
três formas exercitadas de pré-validação DTO/revisão; estado, histórico e eventos
são comparados antes/depois. Paridade inválida usa pré-validação RDF e revise real
sob a mesma release/contexto, comparando os diagnósticos; válida usa DTO e POST real.

Banco exclusivo: container `libris-issue48-20261016`, imagem local
`postgres:17-bookworm`, volume de dados tmpfs, porta loopback 55448,
banco `libris_issue48`, criado apenas para esta execução. Alembic head existente
foi aplicado explicitamente nesse banco. O container foi parado após os testes; não houve remoção de volumes de trabalho. Nenhum SQLite, dado de trabalho, volume
existente ou downgrade foi utilizado. Não foram criadas migrações novas.

## Resultados dos comandos

| Verificação | Estado | Evidência desta execução |
| --- | --- | --- |
| `uv run pytest`, ruff, mypy e Alembic | BLOCKED | uv instalado por Snap recusado por snap-confine neste ambiente; nenhuma reinstalação forçada |
| `.venv/bin/pytest -q` | PASS | 1.791 passed, 513 avisos de depreciação, 263,43 segundos; nenhuma falha ou skip |
| Testes HTTP/OpenAPI/perfis focados | PASS | 125 passed; inclui as expectativas atualizadas para os endpoints reais e a release draft |
| PostgreSQL: novos casos + CRUD #47 | PASS | 40 passed, 708 avisos RDFLib; comando abaixo |
| `.venv/bin/ruff check . ../../tests ../../scripts/verify-m04-integration.py` | PASS | Lint pela configuração de apps/api, sem supressões novas |
| `.venv/bin/mypy src` | PASS | 99 arquivos, strict |
| `.venv/bin/alembic heads` | PASS | 0005_web_auth (head) |
| `.venv/bin/alembic upgrade head --sql` | PASS | SQL offline gerado, 25.368 bytes; sem aplicar ao banco de trabalho |
| Upgrade explícito do PostgreSQL exclusivo | PASS | Head instalado apenas em libris_issue48 |
| `npm test` | PASS | 167 testes, nenhum skip/falha |
| `npm run build` | PASS | Node 24.16.0, Next build --webpack; exigiu execução fora do sandbox pelos subprocessos TypeScript |
| `npm run typecheck` | PASS | tsc --noEmit |
| `bash scripts/check.sh` | BLOCKED | Parou no uv/Snap; verificações equivalentes executadas separadamente |
| `docker compose --env-file .env.example config --quiet` | PASS | Variáveis obrigatórias com valores aleatórios efêmeros somente para validação estática; nenhum serviço iniciado pelo Compose |
| `git diff --check` | PASS | Sem erro de whitespace; repetido na revisão final |
| Keycloak real / navegador / produção | NOT RUN | Não são comprovados pela injeção de ator dos testes deste incremento |

Comando PostgreSQL, a partir de apps/api, usando TEST_DATABASE_URL do banco exclusivo:

```bash
.venv/bin/pytest -c pyproject.toml -q \
  ../../tests/integration/test_catalog_capabilities_postgres.py \
  ../../tests/integration/test_catalog_http_postgres.py
```

Falhas intermediárias foram corrigidas e repetidas: a extração relacional tentava
construir LocalReference para uma IRI externa URN; agora consulta a identidade
armazenada antes dessa classificação. Expectativas de OpenAPI/CORS foram ampliadas
somente para os handlers efetivos. O teste de perfis foi corrigido para os 14
artefatos reais e o estado draft de work-minimal, sem alterar releases nem hashes.
O primeiro build no sandbox falhou nos subprocessos TypeScript; a repetição fora
dele passou. O arquivo next-env.d.ts gerado pelo build foi devolvido ao seu conteúdo
original; não há alterações entregues no frontend.

A suíte final inclui 25 casos novos de API e 13 casos novos de integração PostgreSQL (38 casos novos ao todo). Os logs temporários da execução ficaram em `/tmp/libris-issue48-*.log`; este relatório preserva os resultados sem depender desses arquivos temporários.

## Critérios e limitações

Relações locais/externas de destino único e todas as cinco entidades possuem
caminhos funcionais testados. O caso externo ambíguo Agent dcterms:relation tem
tratamento seguro, porém não possui recuperação integral do discriminador a partir
do RDF. Portanto a aceitação irrestrita de todas as referências externas é
**PARCIAL**, sem declarar implantação integral desse caso. Referências não
reconciliadas são explicitamente recusadas pela política atual, sem entidade falsa.

Consulta de inversas percorre snapshots correntes; não é uma consulta paginada de
descoberta. Escala/custo de canonicalização/SHACL, Keycloak real neste incremento,
homologação institucional e produção não foram homologados por estes testes.
Não existe estado approved institucional de perfis no modelo; a API expõe o estado
real em vez de inferir aprovação. Nenhum release histórico foi alterado.


## Critérios de aceite da #48

| Critério | Estado | Evidência |
| --- | --- | --- |
| Consultar/alterar relações por HTTP | CONCLUÍDO | GET/PATCH e testes das cinco entidades |
| Todos os tipos de referência/integridade | PARCIAL | Local, externo de destino único e recusa de unreconciled testados; externo polimórfico não recuperável é recusado |
| Inválidas/duplicadas/inversas/inexistentes testadas | CONCLUÍDO | lifecycle_integrity e inverses_cycles_and_target_types |
| Autorização efetiva das relações | CONCLUÍDO | Guards humanos, testes 401/403, tipo persistido reautorizado |
| Mesma transação relacional | CONCLUÍDO | `_revise` dentro de session.begin único |
| CAS e rollback | CONCLUÍDO | Corrida entre sessões e falhas snapshot/audit/CAS/commit em PostgreSQL |
| Propriedades não alteradas intactas | CONCLUÍDO | Snapshot integral, extensão multilíngue e isomorfismo |
| Não publicar candidata automaticamente | CONCLUÍDO | Revisão pública comparada antes/depois e conflito editorial |
| Pré-validação HTTP funcional | CONCLUÍDO | DTO, Turtle, JSON-LD, revisão e release fixada |
| Ausência de persistência bibliográfica | CONCLUÍDO | Observação SQL, READ ONLY e comparação de estado/histórico/auditoria |
| Diagnósticos estáveis | CONCLUÍDO | Contract 1.0, paridade de issues e request ID |
| Mesmas regras de pré-validação/escrita | CONCLUÍDO | Preparação comum e mesmo validate_catalog/SHACL; comparação com revise real |
| Catálogo somente-leitura de perfis/releases | CONCLUÍDO | Listagem e consulta determinísticas das 14 releases |
| Sem administração de perfis por HTTP | CONCLUÍDO | Testes POST/PATCH/DELETE 405 |
| Problem Details/request ID existentes | CONCLUÍDO | Nenhum modelo/código concorrente de erro |
| Sem busca de contexto RDF remoto | CONCLUÍDO | Parser limitado existente, remoto recusado antes de parsing RDF |
| Testes HTTP e de regressão | CONCLUÍDO | Novos testes e regressão do CRUD #47 |
| Matriz #16/#20/#21/#22/#24/#25 | CONCLUÍDO | Tabela deste relatório |
| Documentação refletindo código | CONCLUÍDO | Contrato HTTP, seis referências, README e ADR 0037 |
| Nenhuma branch criada | CONCLUÍDO | main no início e ao fim, sem comandos de criação |
| Nenhum commit ou PR criado | CONCLUÍDO | Nenhum comando de commit/PR executado |
| Alterações na main local | CONCLUÍDO | Working tree preservado, sem push |

A entrega não é classificada como integralmente concluída enquanto a pendência de
referências externas polimórficas permanecer. Sua solução exige definir como
conservar a classificação operacional versionada que o RDF proprietário atual não
representa, sem adicionar tipos fictícios a entidades externas.


## Arquivos entregues

Criados:

- `bibliographic/api/capabilities.py`: cinco handlers, dependências e ETag relacional.
- `bibliographic/api/limits.py`: leitura limitada, profundidade e chaves JSON únicas.
- `bibliographic/api/schemas/validation.py`: DTOs de entrada discriminados.
- `bibliographic/application/catalog_profiles.py`: projeção pública sem caminhos de arquivos.
- `bibliographic/application/catalog_relationships.py`: consulta, integridade, fecho e transação.
- `bibliographic/application/catalog_validation.py`: coordenação de pré-validação autorizada.
- `bibliographic/infrastructure/relationship_graph.py`: diferenças relacionais no Graph integral.
- `tests/api/test_catalog_capabilities.py` e `tests/integration/test_catalog_capabilities_postgres.py`: testes novos.
- `docs/decisions/0037-catalog-relationships-prevalidation.md` e este relatório: decisão e evidências.

Os caminhos `bibliographic/` acima têm prefixo
`apps/api/src/libris/modules/`. Modificados:

- `apps/api/src/libris/api/security.py`: CORS dos endpoints reais.
- `bibliographic/api/router.py`: composição do novo router.
- `bibliographic/api/schemas/relationships.py`: erros conhecidos tipados, sem mudança de schema.
- `bibliographic/application/catalog.py` e `editorial_postgres.py`: resolução sem locks para leitura.
- `bibliographic/application/relationships.py`: URI alegada externa que existe localmente é conferida.
- `bibliographic/domain/profile_registry.py`: enumeração determinística das releases.
- `bibliographic/infrastructure/serialization/adapters.py`: preparação DTO compartilhada com a escrita.
- `tests/api/test_catalogographic_http.py`, `test_catalogographic_contract_specification.py` e `test_startup.py`: expectativas de rotas reais e CORS.
- `README.md` e os seis contratos em `docs/architecture/`: HTTP, contrato canônico, relacionamentos, perfis, SHACL e erros.

Não houve mudanças entregues em frontend, dependências/locks, Compose, migrações,
recursos JSON/TTL históricos ou schema bibliográfico definitivo.


## Estado do Git na revisão final

```text
$ git branch --show-current
main

$ git status --short
 M README.md
 M apps/api/src/libris/api/security.py
 M apps/api/src/libris/modules/bibliographic/api/router.py
 M apps/api/src/libris/modules/bibliographic/api/schemas/relationships.py
 M apps/api/src/libris/modules/bibliographic/application/catalog.py
 M apps/api/src/libris/modules/bibliographic/application/editorial_postgres.py
 M apps/api/src/libris/modules/bibliographic/application/relationships.py
 M apps/api/src/libris/modules/bibliographic/domain/profile_registry.py
 M apps/api/src/libris/modules/bibliographic/infrastructure/serialization/adapters.py
 M docs/architecture/catalog-profiles.md
 M docs/architecture/catalogographic-contract.md
 M docs/architecture/catalogographic-errors.md
 M docs/architecture/catalogographic-http.md
 M docs/architecture/relationships.md
 M docs/architecture/shacl-validation.md
 M tests/api/test_catalogographic_contract_specification.py
 M tests/api/test_catalogographic_http.py
 M tests/api/test_startup.py
?? apps/api/src/libris/modules/bibliographic/api/capabilities.py
?? apps/api/src/libris/modules/bibliographic/api/limits.py
?? apps/api/src/libris/modules/bibliographic/api/schemas/validation.py
?? apps/api/src/libris/modules/bibliographic/application/catalog_profiles.py
?? apps/api/src/libris/modules/bibliographic/application/catalog_relationships.py
?? apps/api/src/libris/modules/bibliographic/application/catalog_validation.py
?? apps/api/src/libris/modules/bibliographic/infrastructure/relationship_graph.py
?? docs/architecture/catalogographic-m0504-verification-2026-10-16.md
?? docs/decisions/0037-catalog-relationships-prevalidation.md
?? tests/api/test_catalog_capabilities.py
?? tests/integration/test_catalog_capabilities_postgres.py

$ git diff --check
(sem saída)

$ git diff --stat
 README.md                                          |   2 +
 apps/api/src/libris/api/security.py                |  12 ++
 .../src/libris/modules/bibliographic/api/router.py |   4 +
 .../bibliographic/api/schemas/relationships.py     |  17 ++-
 .../modules/bibliographic/application/catalog.py   |   4 +-
 .../application/editorial_postgres.py              |   7 +-
 .../bibliographic/application/relationships.py     |  15 +-
 .../bibliographic/domain/profile_registry.py       |   4 +
 .../infrastructure/serialization/adapters.py       |  15 +-
 docs/architecture/catalog-profiles.md              |   4 +
 docs/architecture/catalogographic-contract.md      |   8 +-
 docs/architecture/catalogographic-errors.md        |   4 +
 docs/architecture/catalogographic-http.md          | 157 +++++++++++++++++++--
 docs/architecture/relationships.md                 |   4 +
 docs/architecture/shacl-validation.md              |   4 +
 .../test_catalogographic_contract_specification.py |   5 +
 tests/api/test_catalogographic_http.py             |  13 +-
 tests/api/test_startup.py                          |   5 +
 18 files changed, 257 insertions(+), 27 deletions(-)
```

Branch: main. Novas branches: nenhuma. Commits criados: nenhum. Pull requests: nenhum. Push: não. Alterações mantidas no working tree local. O diff --stat convencional lista somente arquivos rastreados; os onze arquivos novos estão identificados por ?? no status.
