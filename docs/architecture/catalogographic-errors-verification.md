# Verificação da #22 — diagnósticos catalográficos e Problem Details

Data: 2026-10-12. Implementação na branch `main`, inicialmente sem alterações.
Não houve nova branch, troca de branch, PR, push, merge/rebase ou fechamento de issue.
[Contrato completo](catalogographic-errors.md) e [ADR 0023](../decisions/0023-catalogographic-diagnostics.md).

## Diagnóstico e decisões

Lidos AGENTS, README, contrato/esquemas/perfis e ADRs de monólito, RDF, PostgreSQL,
persistência, revisões, identidade, perfis e SHACL. Inspecionados o módulo
bibliográfico, serviços/transações, fixtures e testes das entregas #15/#17/#19/#20/#21.
Lacunas reais: representação pública de diagnósticos, taxonomia independente de
mensagens/HTTP, erros estruturais seguros, handlers e correlação na aplicação.
Reutilizados relatórios/engine/correlação e Pydantic já existentes; nenhuma API de
catálogo foi criada para justificar o contrato.

Os contratos ficam na aplicação, neutros ao transporte, reexportados pela API.
CatalogError herda ValueError para compatibilidade; ausência persistente herda
LookupError explicitamente. Catálogo não captura ValueError/KeyError genéricos como
422/404. Report confiável não conforme e falha técnica têm estados distintos.
O adaptador HTTP normaliza ID de requisição em cópia do relatório, sem mutá-lo.
Blank nodes usam descrições redigidas/canonizadas, não identificadores persistentes.

## Arquivos criados/alterados

| Arquivo (relativo à raiz) | Finalidade |
| --- | --- |
| apps/api/src/libris/modules/bibliographic/domain/errors.py | Taxonomia e exceções tipadas sem HTTP |
| apps/api/src/libris/modules/bibliographic/application/diagnostics.py | Schemas canônicos, invariantes, ordenação e rejeição com relatório |
| apps/api/src/libris/modules/bibliographic/application/validation.py | Pré-validação interna usando motor e releases existentes |
| apps/api/src/libris/modules/bibliographic/infrastructure/diagnostics.py | SHACL/legado/resolvido, caminhos RDF, campos e política de exposição |
| apps/api/src/libris/modules/bibliographic/api/schemas/diagnostics.py | Reexportação pública dos contratos |
| apps/api/src/libris/api/problems.py | Problem Details, mapeamentos HTTP, If-Match, middleware e OpenAPI |
| apps/api/src/libris/core/correlation.py | ContextVar para um ID por requisição |
| apps/api/src/libris/main.py | Instalação real dos handlers e correlação; CORS expõe X-Request-ID |
| apps/api/src/libris/modules/bibliographic/application/service.py | Rejeição tipada SHACL e erros de identificação/perfil; transações preservadas |
| apps/api/src/libris/modules/bibliographic/application/relationships.py | Tipagem de rejeições de integridade/política existentes |
| apps/api/src/libris/modules/bibliographic/infrastructure/ownership.py | Tipagem de rejeições de identidade/ownership existentes |
| apps/api/src/libris/modules/bibliographic/infrastructure/persistence.py | Exceção explícita de recurso/revisão ausente |
| tests/api/test_catalog_diagnostics.py | Contrato, integração real SHACL/FastAPI, segurança e regressões |
| tests/api/test_shacl_validation.py | Adapta asserção de tipo exato para nova subclasse ValueError e verifica relatório/rollback |
| tests/integration/test_diagnostic_transactions_postgres.py | Rollback real em rejeição e falha técnica, revisão e snapshot preservados |
| scripts/generate_diagnostic_examples.py | Geração e --check reproduzíveis dos exemplos a partir de contratos/fixtures reais |
| docs/examples/validation/conformant.json | Validação conforme |
| docs/examples/validation/warnings.json | Conformidade com Warning do perfil legado |
| docs/examples/validation/violations.json | Violações SHACL com campos e componentes |
| docs/examples/validation/schema-error.json | Pydantic estrutural em Problem Details |
| docs/examples/validation/unknown-profile.json | Perfil desconhecido em Problem Details |
| docs/examples/validation/stale-revision.json | Revisão obsoleta em Problem Details |
| docs/examples/validation/operational-failure.json | Indisponibilidade técnica HTTP 503 |
| docs/examples/validation/failed-validation.json | Pré-validação técnica failed, sem conforms |
| docs/examples/validation/consume.ts | Distribuição de diagnósticos e tradução para integração Next.js futura |
| docs/architecture/catalogographic-errors.md | Estrutura, códigos, segurança, HTTP, evolução e limitações |
| docs/architecture/catalogographic-errors-verification.md | Este inventário, evidências e critérios |
| docs/decisions/0023-catalogographic-diagnostics.md | Decisão estrutural e compatibilidade |
| README.md | Entrada para a entrega e seus limites |

Perfis, shapes, release-lock, schema histórico, migrações, dependências e lockfiles
não foram modificados. Nenhuma tabela, serviço permanente ou abstração administrativa
foi acrescentada. PostgreSQL permanece autoritativo; Elasticsearch não participa.

## Critérios de aceitação

Todos os critérios abaixo são **Atendidos** no escopo da #22; APIs de catálogo e
editor futuros são limitações explícitas, não demonstrações de funcionalidades existentes.

| Critério solicitado | Estado | Evidência concreta |
| --- | --- | --- |
| Contrato público Pydantic tipado, estado/conformidade/lista | Atendido | CatalogValidationResult, Diagnostic; test_real_validation_and_immutable_release/test_result_invariants |
| Código, mensagem, categoria, severidade, IDs de campo | Atendido | Schemas e testes de motor real por severidade |
| Foco, caminho, valor seguro, constraint e shape | Atendido | adapt_report; test_complex_paths/test_component_codes_do_not_depend_on_messages/test_value_policy_preserves_only_safe_iris |
| Perfil e release real; snapshot/composed; correlação | Atendido | test_real_validation_and_immutable_release/test_context_and_profile_policy/test_request_correlation_in_service_and_rejection |
| Múltiplos campos/globais, ordenação/omissão determinísticas | Atendido | test_multiple_fields_and_global_diagnostics/test_stable_serialization_under_blank_node_renaming_and_engine_order |
| Sem RDFLib/pySHACL/Pydantic interno no payload | Atendido | PublicContract/public_dict, schemas OpenAPI e respostas reais |
| Taxonomia estrutural, SHACL, perfil, identificação e referências | Atendido | CatalogCode, adaptação por componente/tipo, CatalogError em ownership/relationships |
| Perfis desconhecidos/incompatíveis/indisponíveis | Atendido | test_unknown_and_incompatible_profiles_keep_typed_errors/test_http_mapping_and_security |
| Conflito de revisão/estado, falha interna e temporária | Atendido | Mapeamento de StaleRevisionError/DBAPIError; testes HTTP/SQLSTATE e PostgreSQL |
| Códigos independentes do idioma, sem comparação de mensagem | Atendido | Mapa de URIs SHACL e códigos existentes explícitos; teste de componentes desconhecidos/ausentes |
| Política de evolução/compatibilidade documentada | Atendido | ADR 0023 e seção Taxonomia/evolução do contrato |
| Reutilização de ValidationReport/FieldValidationIssue/correlação | Atendido | Adaptador chama correlate_validation_issues para ResolvedProfile; mantém classes anteriores |
| Violation/Warning/Info e múltiplas violações | Atendido | test_real_engine_severities e serialização com motor real |
| Constraint/shape ausentes e caminhos complexos preservados | Atendido | test_component_codes_do_not_depend_on_messages/test_complex_paths; globais sem classificação inventada |
| Preservação de IRIs BIBFRAME/outras ontologias; sem rede/inferência | Atendido | IRIs completas nos testes; registro/engine anteriores intactos; nenhum downloader novo |
| Violation bloqueia; Warning/Info não bloqueiam sozinhos | Atendido | Motor real com allow_warnings/infos; prepare_document rejeita não conformidade |
| Sucesso conforme, não conforme e falha técnica distintos | Atendido | test_real_validation_and_immutable_release/test_technical_failure_is_distinct |
| RFC 9457 / application/problem+json / status uniformes | Atendido | ProblemDetails e test_http_mapping_and_security cobrindo 400/404/409/412/422/428/500/503 |
| Preservar precondições obrigatórias/obsoletas e tokens de domínio | Atendido | test_http_preconditions; require_if_match não gera ETag nem extrai revisão; CAS anterior preservado |
| Integração FastAPI sem CRUD fictício | Atendido | install_problem_handlers em create_app; teste existente confirma apenas health/me |
| Falhas de programação continuam 500 e registradas | Atendido | Casos ValueError/KeyError/RuntimeError; handlers não convertidos em 422/404 |
| Pré-validação normal distinta de operação rejeitada | Atendido | validate_catalog vs CatalogValidationRejected/problem.validation; exemplos de ambos |
| OpenAPI com schemas e media types implementados | Atendido | test_real_http_schema_errors_openapi_and_authentication |
| Traduções, vários erros por campo, obrigatoriedade/cardinalidade/valores, globais | Atendido | code/parameters/severity/field_ids; consume.ts compilado strict; exemplos DTO/SHACL |
| Sem acoplamento a rótulos/React/editor | Atendido | IDs semânticos/JSON Pointer; funções TypeScript neutras; frontend não alterado |
| Segurança: sem trace/path/SQL/config/credenciais/texto de exceção | Atendido | test_http_mapping_and_security/test_schema_adapter_uses_pydantic_contract_and_omits_input |
| Política explícita de valores, truncamento/omissão | Atendido | Literais omitidos; IRIs suspeitas/longas omitidas; teste de digest sem lexical sensível |
| Um request ID por requisição e log técnico seguro | Atendido | Middleware/ContextVar, testes de rejeição e relatório pré-calculado, reset de contexto |
| Transações/rollback sem persistência parcial | Atendido | test_invalid_create_never_opens_transaction, regressão de transação e test_public_rejections_rollback_postgres |
| Compatibilidade monograph-v1, monograph-v1.1, authority-v1 | Atendido | Testes parametrizados/fixtures e suíte anterior; hashes de perfis históricos na suíte |
| Testes com contratos reais e PostgreSQL, sem SQLite | Atendido | TestClient/motor real; seis integrações reais; simulação somente para falhas e tradução SQLSTATE |
| Documentação portuguesa, exemplos JSON/FastAPI/Next.js e limites | Atendido | Contrato, ADR, oito exemplos JSON gerados e TypeScript strict |
| Tipagem, camadas, infraestrutura existente, locks/releases intactos | Atendido | mypy strict/ruff; diff; ausência de dependências/migrações/perfis alterados |
| Verificação, revisão de diff e estado Git respeitado | Atendido | Comandos/resultados abaixo; main preservada; commits funcionais sem push |
## Comandos e resultados

- `bash scripts/check.sh`: tentativa interrompida no uv do Snap por falha de confinamento
  snap-confine/AppArmor. As partes foram executadas pelos binários da `.venv` existente.
- Da raiz: `apps/api/.venv/bin/pytest -c apps/api/pyproject.toml tests/api -q`:
  **864 passed**, sem PostgreSQL/Elasticsearch (788 anteriores + 76 novos).
  A suíte específica `tests/api/test_catalog_diagnostics.py` também passou: **76 passed**.
- De apps/api: `.venv/bin/ruff check . ../../tests ../../scripts/generate_diagnostic_examples.py`:
  aprovado, configuração do projeto respeitada.
- De apps/api: `.venv/bin/mypy src`: aprovado, 60 arquivos.
- De apps/web, Node 24.16.0 no PATH: `npm run build` e `npm run typecheck`: aprovados.
- `tsc --noEmit --strict --target ES2022 --module ESNext --moduleResolution bundler --skipLibCheck docs/examples/validation/consume.ts`:
  aprovado pelo TypeScript já instalado no frontend.
- De apps/api: `.venv/bin/python ../../scripts/generate_diagnostic_examples.py` e `--check`:
  exemplos gerados e reprodução aprovada.
- `docker compose --env-file .env.example config --quiet`: aprovado.
- PostgreSQL 17-bookworm descartável, porta aleatória exclusivamente em 127.0.0.1,
  sem volume persistente. Alembic upgrade head aplicou migrações existentes somente
  nesse banco. `.venv/bin/python` com `Settings.model_config["env_file"] = None`
  e `pytest.main(["-c", "pyproject.toml", "../../tests/integration", "-q"])`,
  com TEST_DATABASE_URL do banco descartável: **6 passed**. Banco removido ao finalizar.
- `git diff --check`: aprovado; revisão confirma ausência de alterações nos recursos
  versionados e nos arquivos de dependências/migrações.

Limites observados: TestClient bloqueia comunicação entre threads no sandbox;
execução fora dele passou. Build do Next.js também exigiu comunicação permitida.
O `.env` local tem sintaxe inválida e valores inválidos; foi preservado integralmente.
Não usar Compose padrão nem ler esse arquivo para verificar o banco: migração/testes
usaram configurações isoladas por processo. Houve tentativas iniciais com falha por
esse arquivo, corrigidas pela execução isolada. DeprecationWarnings existentes de
RDFLib/Starlette continuam visíveis; não houve instalação de dependências para ocultá-los.

## Pendências e Git

Sem pendência funcional da #22. Homologação catalográfica, CRUD/pré-validação HTTP,
editor/traduções frontend, ETags fortes específicos das representações e adoção
persistente de perfis 2.0 dependem de entregas futuras. Não são afirmados como disponíveis.
Não há benchmark institucional de canonização; limites e identidade anônima local
estão documentados no contrato.

A branch permanece main. Implementação/testes registrados em `2f8f48b`;
documentação/exemplos em commit separado. Hash final e estado do workspace são
apresentados ao solicitante após confirmar a gravação dos commits.
Nenhum push/PR/fechamento automático de issue.
