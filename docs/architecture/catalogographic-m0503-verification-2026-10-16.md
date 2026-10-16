# Verificação M05.03 / #47 — 2026-10-16

Execução local na branch `main`, base `c936b88a484dac4dff05f43649ab07a4aaa8368a`.
Working tree e índice inicialmente limpos. Sem branch nova, staging, commit, push,
PR ou escrita em issues/milestones. Relatório novo; evidências históricas preservadas.

## Diagnóstico e entrega

Issue [#47](https://github.com/inacioigne/libris/issues/47) e dependências
[#45](https://github.com/inacioigne/libris/issues/45),
[#46](https://github.com/inacioigne/libris/issues/46),
[#28](https://github.com/inacioigne/libris/issues/28),
[#43](https://github.com/inacioigne/libris/issues/43),
[#38](https://github.com/inacioigne/libris/issues/38) e
[#42](https://github.com/inacioigne/libris/issues/42) consultadas somente em leitura.
A #47 estava aberta, milestone M05 (id 5); #28/#43/#38/#42 estavam fechadas.
O diagnóstico usou implementações e testes, sem inferir operacionalidade pelo
encerramento dessas issues: #45 já compunha router/dependências; #46 fornecia
adaptadores dos cinco DTOs; M03 fornecia stores, CAS, auditoria e publicação interna;
M04 fornecia OIDC/guard e políticas por operação. Não foi homologado OIDC novamente.

Entregues quinze operações: POST nas coleções works/instances/items/agents/subjects,
GET e PATCH por UUID em `/api/v1/catalog`. POST 201 com Location e ETag; GET/PATCH
200 com ETag. Read é editorial autenticado. PATCH exige If-Match forte único,
com 428/400/412 conforme ausência/sintaxe/precondição obsoleta.

`CatalogService` especializa `BibliographicService`; `_create` extraído sem alterar
o contrato histórico; `_revise`, RevisionStore, EditorialStore, AuditStore, guard e
adaptadores #46 são reutilizados. Cada escrita possui um único commit. HTTP não
abre transação externa sobre um serviço transacional. Fábrica vem do lifespan por
get_session_factory. HistoryService e PostgresEditorialTransactions são utilizados
nas verificações de estado/auditoria e publicação interna, sem endpoints extras.

Decisão de precondição e gate exclusivo nas escritas DTO documentada no
[ADR 0036](../decisions/0036-catalog-http-concurrency.md). Leitura corrente sob lock
obtém conteúdo e versão editorial coerentes, sem inicializar legado nem exigir
metadata_audit:read. UUID/URI, perfil persistido e autoria histórica são preservados.
Novas revisões candidatas conservam a revisão pública selecionada.

## Arquivos principais

| Arquivo / grupo | Responsabilidade |
| --- | --- |
| bibliographic/api/router.py | Quinze handlers tipados, DTOs existentes, status e headers |
| bibliographic/api/dependencies.py | Composição de serviço/guard e fábrica do lifespan |
| bibliographic/api/representations.py (novo) | ETag de edição e parsing de If-Match único |
| bibliographic/application/catalog.py (novo) | Casos de uso DTO, leitura coerente, resolução transacional e CAS |
| bibliographic/application/service.py | Extração de `_create` para reutilizar persistência M03 |
| api/problems.py | Parsing compartilhado, códigos HTTP e erros estruturais/indisponibilidade |
| api/security.py e main.py | CORS dos métodos/caminhos reais e exposição de ETag/Location |
| tests/api/test_catalogographic_http.py | Contrato operacional, OIDC isolado, autorização, CORS e ETag |
| tests/api/test_catalogographic_contract_specification.py e test_startup.py | OpenAPI/status atualizados, sem rotas futuras |
| tests/integration/test_catalog_http_postgres.py (novo) | 27 casos HTTP com PostgreSQL real |
| catalogographic-http.md e ADR 0036 (novo) | Contrato operacional e decisão transacional/ETag |
| READMEs e documentos arquiteturais relacionados | Estado implementado e distinção das próximas entregas |
| Este relatório (novo) | Evidência datada sem substituir histórico |

Os caminhos de código acima são relativos a apps/api/src/libris/modules quando
iniciados por bibliographic; api/problems.py, api/security.py e main.py são
relativos a apps/api/src/libris.

## Ambiente e isolamento

Python 3.13.15, PostgreSQL 17.11 (imagem `postgres:17-bookworm` já disponível), Node.js
24.16.0 existente via NVM. Sem instalação/alteração de dependências ou locks.
O uv por Snap e Docker não executavam no sandbox inicial; as execuções necessárias
foram autorizadas pelo mecanismo de revisão automática. Não houve rejeição final.

Criado contêiner exclusivo `libris-issue47-test`, porta loopback 55447, armazenamento
PostgreSQL em tmpfs, banco `libris_issue47_test`. Nenhum volume de trabalho montado.
Os serviços Compose existentes foram apenas listados; nenhuma migração, downgrade,
limpeza ou escrita de teste os utilizou. Autenticação trust restrita ao contêiner
descartável e porta loopback, sem credenciais versionadas.

Head aplicado explicitamente somente ao banco descartável. Criados três outros
bancos inicialmente vazios no mesmo contêiner para as suites de migração:
`issue47_audit_migrations`, `issue47_editorial_migrations`, `issue47_web_migrations`.
Respectivas variáveis TEST_MIGRATION_DATABASE_URL,
TEST_EDITORIAL_MIGRATION_DATABASE_URL e TEST_WEB_MIGRATION_DATABASE_URL, com
TEST_WEB_ISOLATED=1. TEST_DATABASE_URL apontou exclusivamente ao banco principal
de teste. Não houve uso de SQLite ou create_all. Não foi necessária migração nova.
Após as verificações, o contêiner exclusivo foi removido; tmpfs e bancos de teste
foram descartados. Nenhum contêiner/volume Compose preexistente foi removido.

## Cobertura e garantias observadas

`tests/integration/test_catalog_http_postgres.py` contém 27 casos com PostgreSQL
real e transporte HTTP ASGI, substituindo **somente a autenticação** por ator
sintético confiável via dependência; não são testes de integração Keycloak real.
O serviço persistente, sessões SQLAlchemy, stores, validação e commits são reais.

- Cinco fluxos POST → GET → PATCH → GET, UUID/URI/perfil estáveis, Location/ETag,
  revisão/estado/auditoria, rejeição de coleção errada e UUID inexistente.
- Omissão preserva, null remove, lista substitui; DTOs extras/imutáveis recusados;
  estado Subject completo revalidado, com Problem Details 422.
- If-Match ausente, fraco, lista, curinga, duplicado e obsoleto; correlação em erro.
- Duas requisições sincronizadas depois da leitura inicial, cada uma com sessões
  próprias: exatamente uma 200 e outra 412; somente r2, versão 2 e um evento de
  revisão adicionais. GET retorna apenas a alteração vencedora.
- Falha CAS SQL de zero linhas provocada em RevisionStore.advance; rejeição após
  avanço por SHACL real; em ambos, nova sessão observa revisão/estado/auditoria
  anteriores e ETag inalterado.
- Falhas após INSERT de snapshot ou evento, FK de auditoria, CAS tardio e FK
  diferida no COMMIT, tanto POST quanto PATCH: contagem das quatro tabelas antes/
  depois idêntica e estado/histórico recuperados em sessão nova idênticos.
- Predicado RDF fora do DTO conservado; edição publicada gera candidata sem
  mudar revisão/snapshot públicos; transição editorial interna invalida ETag sem
  alterar conteúdo, e estado não editável retorna 409.
- Referência local UUID-only resolve URI persistida; UUID/URI divergentes,
  inexistência e tipos/subtipo heldBy incompatíveis recusados.
- Leitura de legado não inicializa estado, não fabrica evento/ator/publicação;
  primeira edição inicializa estado apenas no commit e mantém autoria antiga nula.
- Escritas cruzadas com referências locais terminam sem deadlock sob gate exclusivo.

A suíte padrão acrescenta verificações de 401 (ausente/inválido/spoof), 403 antes
 de SQL, conjunção de permissões editoriais, system:admin sem bypass, ETag vinculado
à representação/versões, CORS por método/caminho, OpenAPI somente das operações reais
e indisponibilidade 503 sem detalhes sensíveis. Os testes #46 preexistentes cobrem
campo a campo, auxiliares, preservação RDF, listas, null e validação completa.

## Comandos e resultados

- `DATABASE_URL=<banco descartável> uv run alembic upgrade head`: passou.
- `uv run alembic heads`: `0005_web_auth (head)`.
- `uv run alembic upgrade head --sql`: passou, SQL offline em arquivo temporário.
- `uv run ruff check . ../../tests`: passou.
- `uv run mypy src`: passou, 92 arquivos.
- `uv run pytest -q ../../tests/api/test_catalogographic_http.py ../../tests/api/test_http_security.py ../../tests/api/test_catalogographic_contract_specification.py ../../tests/api/test_startup.py`:
  **145 aprovados**, sem skips/falhas.
- `uv run pytest -c pyproject.toml ../../tests/integration -m integration -q`, com
  as quatro URLs descartáveis e TEST_WEB_ISOLATED=1: **86 aprovados**, **14 desmarcados**,
  zero falhas/skips, 483 avisos, 146,23 s. Desmarcados não equivalem a aprovados:
  os testes Keycloak opt-in não foram selecionados pelo marcador integration.
- Reexecução final da suíte HTTP PostgreSQL: **27 aprovados**, zero falhas/skips,
  222 avisos, 37,81 s. Teste público reforçado reexecutado isoladamente:
  **1 aprovado, 26 desmarcados**, 27 avisos, 8,42 s.
- `PATH=<Node.js 24 instalado>:$PATH bash scripts/check.sh`: API **1.766 aprovados**,
  zero falhas/skips, 512 avisos, 259,28 s; Ruff passou; mypy strict passou em 92
  arquivos. `npm test`: **167 aprovados**, zero falhas/skips. `npm run build`,
  `npm run typecheck` e validação Compose passaram; script completo **exit 0**.

As primeiras execuções revelaram expectativas antigas de router vazio, OpenAPI
health/me e fallback 422 dos códigos editoriais. Foram atualizadas para o contrato
implementado, preservando verificações de exclusão das rotas futuras. Um override
de teste com assinatura variádica foi corrigido para dependência sem parâmetros.
Execuções amplas anteriores foram interrompidas após identificar essas falhas,
sem serem contabilizadas como aprovadas. A execução uv dentro do sandbox falhou
pela configuração Snap; execução pytest sem escalonamento foi interrompida.
Mypy invocado da raiz sem a configuração da API exibiu erro em código preexistente;
a execução canônica `cd apps/api && uv run mypy src` passou.
Avisos são depreciações existentes Starlette/httpx e RDFLib ConjunctiveGraph.

## Critérios e limites

| Critério #47 | Evidência / estado |
| --- | --- |
| POST/GET/PATCH dos cinco tipos | Atendido: cinco ciclos reais PostgreSQL |
| DTOs e serviços corretos | Atendido: schemas v1 e adaptadores existentes, passos M03 compartilhados |
| UUID/URI estáveis | Atendido: respostas e revisões posteriores comparadas |
| Perfil preservado | Atendido: perfil anterior/posterior conferido e extras imutáveis recusados |
| ETag/If-Match | Atendido: testes positivos/negativos e [contrato HTTP](catalogographic-http.md) |
| Concorrência sem lost updates | Atendido: duas sessões/requisições e CAS SQL |
| Rollback integral | Atendido: estado/histórico/contagens em novas sessões após falhas |
| PostgreSQL real isolado | Atendido: quatro bancos exclusivos, tmpfs |
| Autorização editorial | Atendido: guard/políticas e testes isolados 401/403/conjunções |
| Candidata não pública | Atendido: read_public interno mantém revisão/snapshot publicados |
| OpenAPI operacional | Atendido: somente quinze operações novas; sem superfícies #48–#50 |
| Migrações explícitas | Atendido: upgrade offline/real e regressão de migrações; nenhum startup DDL |
| Testes/verificações relevantes | Atendido: 1.766 API, 167 web, 86 integração; check.sh completo exit 0 |
| Documentação operacional | Atendido: HTTP, README, documentos relacionados e ADR atualizados |
| Restrições Git | Atendido: main local; nenhum comando de staging/histórico/remoto executado |

Gate exclusivo serializa escritas DTO; não foi medida capacidade de produção.
Referências externas/URI-only ausentes localmente continuam pendências compatíveis,
sem verificação remota. Fechos/ciclos e política de publicação permanecem sob a
validação mais restrita da #43. Não foram implementados os endpoints das #48/#49/#50,
frontend, exclusão física, inventário ou circulação. Perfis/schema continuam
experimentais e sem homologação institucional. OIDC e segurança ponta a ponta
novos não foram homologados nesta execução; integração M05 com provedor real e
produção continuam escopo separado da #51.

## Estado final do Git

Branch `main`; HEAD permanece `c936b88a484dac4dff05f43649ab07a4aaa8368a`.
`git diff --cached --stat` vazio: nenhum staging. Nenhum commit, push, PR, troca/criação
de branch ou mutação remota. `git diff --check` passou, sem saída.
Os 18 arquivos modificados e cinco novos estão no working tree para revisão:

```text
 M README.md
 M apps/api/README.md
 M apps/api/src/libris/api/problems.py
 M apps/api/src/libris/api/security.py
 M apps/api/src/libris/main.py
 M apps/api/src/libris/modules/bibliographic/api/dependencies.py
 M apps/api/src/libris/modules/bibliographic/api/router.py
 M apps/api/src/libris/modules/bibliographic/application/service.py
 M docs/architecture/catalogographic-contract.md
 M docs/architecture/catalogographic-errors.md
 M docs/architecture/catalogographic-http.md
 M docs/architecture/catalogographic-schemas.md
 M docs/architecture/editorial-persistence.md
 M docs/architecture/http-security.md
 M docs/architecture/overview.md
 M tests/api/test_catalogographic_contract_specification.py
 M tests/api/test_catalogographic_http.py
 M tests/api/test_startup.py
?? apps/api/src/libris/modules/bibliographic/api/representations.py
?? apps/api/src/libris/modules/bibliographic/application/catalog.py
?? docs/architecture/catalogographic-m0503-verification-2026-10-16.md
?? docs/decisions/0036-catalog-http-concurrency.md
?? tests/integration/test_catalog_http_postgres.py
```

O build regenerou automaticamente os imports de next-env.d.ts; somente essa
alteração gerada foi desfeita para preservar o arquivo frontend original.
`npm run typecheck` foi reexecutado depois dessa preservação e passou (exit 0).

Resultado técnico dos critérios #47: atendidos pelas evidências acima. A aprovação
institucional e a homologação M05 com OIDC real/produção permanecem separadas;
não foram inferidas dos testes com dependência de ator substituída.
