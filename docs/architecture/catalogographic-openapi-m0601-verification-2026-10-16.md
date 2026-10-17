# Verificação M06.01 — baseline catalográfica/OpenAPI — 2026-10-16

## Identificação e ambiente

Issue [#53](https://github.com/inacioigne/libris/issues/53), acompanhamento
[#52](https://github.com/inacioigne/libris/issues/52). Data local America/Manaus.
Branch inicial `main`; HEAD de referência `5e8a00569dbe9f20a783e00f35dba4fddae81240`
(`5e8a005 M05.07`). Consultadas as issues #31/#51/#52/#53 e milestone indicada
na #52 (M06), somente leitura; nenhuma alteração remota.

Estado inicial: exclusões preexistentes `docs/M06-milestone-fase1.md` e
`scripts/create-m06-issues.sh`. Preservadas, sem atribuir à #53. Nenhuma branch,
commit, staging, stash, sincronização, push ou PR faz parte desta execução.
O documento histórico excluído não foi usado para definir escopo.

Ambiente Linux; Python 3.13.15, uv 0.12.21, FastAPI 0.143.0, Pydantic 2.14.0,
SQLAlchemy 2.0.54, RDFLib 7.6.0, pySHACL 0.40.1, pytest 9.1.1. Dependências
existentes de `apps/api/uv.lock`, sem atualizações. Node 24.16.0 disponível em
`/home/inacio/.nvm/versions/node/v24.16.0/bin` (acrescentado ao PATH dos gates web).
O uv via Snap e o socket Docker são restritos no sandbox; execução autorizada
fora dele permitiu usar as ferramentas reais, sem emulação ou bancos de trabalho.

## Diagnóstico inicial

`create_app` já incluía 49 operações efetivas (47 catálogo, identity/me e health),
38 paths e os quinze DTOs. Já existiam ProblemDetails, HTTPBearer, media types de
exportação e respostas globais; faltava artefato OpenAPI de referência e CI.
O JSON Schema documental 1.0.0/inventário não representavam inventário HTTP.

Divergências comprovadas: headers ETag/Location/Vary/WWW-Authenticate/X-Request-ID
não eram descritos, e If-Match aparecia opcional/nullable embora a dependência real
rejeitasse ausência com 428. Corrigida somente a documentação OpenAPI no hook
existente; nenhum handler, parser de precondição, DTO, permissão, transação ou
status runtime foi alterado. Vary foi descrito como string incluindo Accept:
CORS pode acrescentar Origin, portanto const=Accept seria incorreto.

FastAPI exclui None ao serializar OpenAPI, inclusive defaults null dos schemas
Pydantic. Isso foi constatado por diff de schemas, sem alterar o artefato documental.
O teste usa o serializador real FastAPI para confrontar os quinze schemas, mais
fixtures e validação runtime. Invariantes cruzadas/SHACL continuam comportamentais.

Respostas globais não comprovam alcance de todos os status em toda operação.
401/403 herdados também constam das rotas públicas, que continuam sem security
obrigatório. HTTPValidationError/ValidationError continuam componentes automáticos
inalcançáveis após substituição do 422 por ProblemDetails; preservados como emitidos
pela aplicação. Nenhum componente é apagado para obter igualdade.

O [inventário por operação](catalogographic-openapi-inventory.md) relaciona método,
path, operationId, tags, implementação com localização, body/modelos, parâmetros,
sucesso, mídia, headers, security, políticas e famílias de testes. O artefato JSON
contém os detalhes de restrições e todos os erros por operação.

## Implementação e governança

| Arquivo | Responsabilidade |
| --- | --- |
| `scripts/generate_catalogographic_openapi.py` (novo) | Fábrica real, isolamento ambiente/.env, refs locais, JSON determinístico, geração exclusiva, check byte a byte e unified diff |
| `docs/architecture/catalogographic-openapi-v1.json` (novo) | Baseline integral real: 38 paths, 49 operações, 98 schemas |
| `tests/api/test_catalogographic_openapi.py` (novo) | Rotas/modelos/fixtures, determinismo offline, derivações de drift, CLI sem escrita, integridade, alcançabilidade e erros HTTP |
| `.github/workflows/catalogographic-contract.yml` (novo) | Ambiente Python 3.13/uv fixado, lock, duas baselines, suíte API, Ruff/mypy; sem serviços externos |
| `apps/api/src/libris/api/problems.py` | Metadados de headers e precondições no OpenAPI existente |
| `scripts/check.sh` | Executa os checks antes do gate global e inclui lint do gerador |
| `docs/decisions/0029-catalogographic-contract-versioning.md` | Política adotada tecnicamente, processo de revisão e limites de aprovação |
| `docs/architecture/catalogographic-openapi.md` (novo) | Operação do gerador, compatibilidade direcional e consumo Work |
| `docs/architecture/catalogographic-openapi-inventory.md` (novo) | Matriz auditável das 49 operações reais e testes |
| `README.md`, `catalogographic-contract.md`, `catalogographic-api-testing.md` | Referências ao novo gate complementar |
| Este relatório (novo) | Evidências desta execução, sem sobrescrever relatórios históricos |

Sem dependências novas, migrações, frontend, cliente TypeScript ou novos endpoints.
A baseline documental 1.0.0, fixtures, UUID/URI, perfis, releases SHACL e revisões
não foram modificados. O novo artefato tem 550081 bytes, SHA-256
`c988855a0199eca0088b97343c43661c2456b72932e516441162f8d9283646c8`.
Comparação SHA-256 com `git show HEAD:<arquivo>` confirmou a preservação do schema
1.0.0 (`ddb123af54a353b9a95507e904c2ea251c2db9e30b8932edea6bbe8652a14feb`)
e inventário (`d8f185050b7427ed7c05fb658e4ca8b022eac88a7bd7095c9be0076761844493`).

O gerador importa a fábrica real, inclusive isolando a construção global de main,
sem iniciar lifespan ou consultar serviços. Não filtra paths/componentes nem ordena
listas significativas. Check usa bytes UTF-8 (CRLF também é drift); geração usa
abertura exclusiva e não tem force/update. O candidato inicial recebeu revisão
explícita dos headers antes de ser validado; o gerador não sobrescreveu artefatos.

ADR 0029: gates e revisão direcional adotados tecnicamente no escopo autorizado da
#53. Mantidas URN v1, especificação 1.0.0, FastAPI 0.1.0, paths /api/v1 e dimensões
independentes de perfis/SHACL/diagnósticos/valores/revisões/estado editorial.
SemVer orienta classificação técnica; publicação, suporte, depreciação e homologação
institucional continuam decisões humanas. Seleção/coexistência HTTP futura requer
ADR próprio. Drift documental também falha; nenhuma ferramenta declara compatível
um acréscimo de campo/enum sem testar produtores e consumidores nas duas direções.

## Execuções

Comandos Python a partir de `apps/api`; scripts bash a partir da raiz. Logs e
JUnit temporários em `/tmp/libris53-*`, distintos dos relatórios históricos.
Contagens e duração abaixo são as reportadas pelo pytest, não estimativas.

| Comando / ambiente | Exit | Total / passed / failed / skipped / deselected | Duração / evidência |
| --- | --- | --- | --- |
| `.venv/bin/python ../../scripts/generate_catalogographic_openapi.py --generate` | 0 | Artefato inicial criado sem serviços | Baseline local nova, não publicada |
| `uv run python ../../scripts/generate_catalogographic_contract.py --check` | 0 | 2 artefatos verificados | Schema/inventário preservados |
| `uv run python ../../scripts/generate_catalogographic_openapi.py --check` (duas execuções consecutivas) | 0 / 0 | Bytes idênticos à baseline | Sem escrita; SHA-256 permaneceu igual |
| `uv run pytest ../../tests/api -q --junitxml=/tmp/libris53-api-final.xml` | 0 | 2084 / 2084 / 0 / 0 / 0 | 455,96 s; `libris53-api-final.log` e JUnit |
| `uv run pytest ../../tests/api/test_catalogographic_openapi.py -q --junitxml=/tmp/libris53-final-contract.xml` | 0 | 47 / 47 / 0 / 0 / 0 | 106,06 s; `libris53-final-contract.log` e JUnit |
| `bash scripts/test-postgres.sh` | 0 | 169 coletados / 167 / 0 / 0 / 2 | 358,32 s; `libris53-postgres.log`, JUnit `libris-postgres-junit.VsuPIS.xml` |
| `PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH bash scripts/check.sh` | 0 | API: 2084 / 2084 / 0 / 0 / 0; web: 167 / 167 / 0 / 0 / 0 | API 453,12 s; web 1776,02 ms; `libris53-check-final.log` |
| `.venv/bin/ruff check . ../../tests ../../scripts/generate_catalogographic_openapi.py` | 0 | Sem violações | Análise real do backend/testes/gerador |
| `.venv/bin/mypy src` | 0 | 106 arquivos | Strict conforme pyproject |
| `MYPYPATH=src .venv/bin/mypy ../../scripts/generate_catalogographic_openapi.py` | 0 | 1 arquivo | Verificação adicional do gerador |
| `git diff --check` e `bash -n scripts/check.sh` | 0 | Sem erros | Inspeção local |

A integração usou PostgreSQL **17-bookworm** real novo, tmpfs, porta dinâmica em
loopback e quatro bancos novos. O runner foi lido antes da execução, limpa URLs de
trabalho, migra explicitamente e remove somente seu próprio container. Nenhum
volume/base preexistente recebeu DDL ou dados. Dois casos Keycloak são deselected
por `-m 'not keycloak'`; não são skips. O runner confirmou zero skips em JUnit e
encerrou com 0 após limpeza. Não se afirma execução Keycloak real nesta entrega.

Avisos: suíte focada emitiu 1 StarletteDeprecationWarning existente (httpx/TestClient).
PostgreSQL emitiu 2908 avisos existentes, principalmente RDFLib/ConjunctiveGraph.
Nenhuma dependência/asserção foi relaxada para eliminá-los.

Execuções intermediárias também foram preservadas: a primeira seleção nova teve
26 passed/16 failed (42 casos, 75,73 s, exit 1), por acesso incorreto à API interna
ModelField do FastAPI e comparação com defaults None que o serializador OpenAPI
omite. Corrigidos os testes usando field_info e jsonable_encoder reais; não foi
alterado o DTO para fazê-los passar. A seleção seguinte teve 44 passed (110,39 s,
exit 0); a seleção final ampliada acima teve 47 passed. Duas sondagens `-xq`
registraram os acessos a `required`/`type_` antes da correção.

Uma suíte API intermediária, iniciada antes da correção revisada de Vary no candidato,
carregou metadados antigos e teve 1003 passed/2 failed em checks de igualdade antes
de ser interrompida (318,89 s, exit 2); o gate intermediário foi interrompido com
662 passed (186,95 s, exit 2). Foram encerrados somente os dois processos de teste
próprios. As execuções finais usam arquivos estabilizados, sem edição de código
durante os testes. As falhas intermediárias não são apresentadas como aprovação.

O mypy adicional invocado sem MYPYPATH inicialmente reportou dois import-untyped
(exit 1, resolução do pacote instalado); com `MYPYPATH=src` analisou o código real
e passou. O gate oficial `mypy src` passou. Restrições iniciais de uv Snap/Docker
do sandbox foram resolvidas executando os comandos reais fora dele; não se usou
shim de uv, SQLite ou serviço simulado para declarar integração.


O gate global final também executou `uv run pytest`, `uv run ruff check . ../../tests
../../scripts/verify-m04-integration.py ../../scripts/generate_catalogographic_openapi.py`,
`uv run mypy src`, `npm test`, `npm run build`, `npm run typecheck` e
`docker compose --env-file .env.example config --quiet`, todos com sucesso. Build
Next.js 16.4.0/webpack: compilação 5,1 s, TypeScript 3,1 s, geração de dez páginas
1,236 s, finalização/traces concluídos. Duração total de parede do script não foi
instrumentada; os tempos registrados são os efetivamente reportados pelas etapas.
O frontend não teve código alterado. O build gerou somente troca de referências
`.next/dev/types` para `.next/types` em next-env.d.ts; após conferir que essa era
exatamente a alteração automática e que o arquivo não estava modificado no estado
inicial, seu conteúdo original foi preservado novamente. O typecheck foi repetido
sobre esse estado final. Caches/builds e configurações locais não foram versionados.

O workflow foi preparado localmente; nenhuma execução hospedada GitHub foi acionada,
pois não houve publicação remota. Os comandos equivalentes de check, suíte API,
Ruff e mypy foram executados aqui. Isso não é homologação operacional do GitHub,
Keycloak, navegador ou produção.

## Matriz de conformidade final

| Critério | Resultado | Evidência |
| --- | --- | --- |
| OpenAPI derivado de rotas reais | PASS | `test_baseline_matches_real_routes_models_and_parameters`: igualdade entre conjuntos completos, endpoints libris e baseline |
| Baseline determinística | PASS | Duas verificações consecutivas, teste offline com ambiente inválido, bytes/SHA iguais |
| Detecção de drift | PASS | Quinze mutações incluindo parâmetros/body/status/mídia/tipo/required/null/default/enum/validação/ref/security/texto; CRLF também falha |
| Diff legível no CI | PASS local | Unified diff exercitado nos testes; workflow usa --check e falha sem geração; execução hospedada não acionada |
| Pydantic Create/Read/Update | PASS | Quinze casos de schemas reais/fixtures, extras proibidos e null obrigatório rejeitado; regressão completa de schemas/adaptadores |
| Problem Details | PASS | Testes reais de rota com falhas de serviço explicitamente injetadas, autenticação real da dependência e 406/428 sem armazenamento; regressão PostgreSQL/HTTP |
| ETag/If-Match | PASS | 400/428 sem acesso ao serviço; testes `test_persistent_http_lifecycle`, `test_http_rejections_leave_persistence_unchanged`, `test_two_http_sessions_race_through_persistent_cas` e comandos editoriais |
| Autorização | PASS | 2084 API + matriz JWT/permissões/publicação/histórico em PostgreSQL, sem promoção por payload; nenhum teste Keycloak real alegado |
| Compatibilidade M03/M05 | PASS | 2084 API e 167 PostgreSQL: fixtures, perfis/SHACL, RDF por isomorfismo, URI/UUID, auditoria/snapshots e transações preservados |
| PostgreSQL isolado | PASS | Runner real exit 0, 167 passed, zero skips, dois Keycloak deselected |
| scripts/check.sh | PASS | Exit 0: checks de baseline, 2084 API, Ruff/mypy, 167 web, build/typecheck e Compose |

Problem Details: status 400/403/404/409/412/422/428/500/503 foram exercitados na
rota real de leitura com injeção explícita de erro do serviço; isso comprova o
handler/transporte, não ocorrência natural de todo erro nessa operação. 401 foi
exercitado nas dependências reais das rotas protegidas; 406 na negociação real;
400/428 também no parser real If-Match antes do armazenamento. Testes PostgreSQL
exercitam conflitos, ausência, rejeição semântica, publicação e CAS de operações
pertinentes. Todos preservam status/code/request_id e application/problem+json,
com X-Request-ID correspondente e sem refletir a sentinela sensível dos testes.
Não se afirma cobertura de todo status em toda rota.

## Lacunas, requisitos Work e encaminhamentos

| Constatação / evidência | Impacto e severidade | Correção concreta / classificação | Bloqueia #55? |
| --- | --- | --- | --- |
| If-Match opcional e headers ausentes no OpenAPI inicial | Médio: cliente gerado podia omitir precondição ou ignorar ETag | Correção compatível necessária nesta issue, implementada no hook e testada; 428 runtime preservado | Resolvido |
| `DtoValidation.resource` e GET público usam uniões sem discriminador universal de entidade; schema real e teste de refs | Baixo: geração TypeScript não deve presumir Work para toda coleção | Adaptação mínima #55: tipos concretos de Work nas rotas CRUD; selecionar união pela coleção e validar runtime; não acrescentar kind a Work | Não |
| Read v1 não contém revisão/perfil/estado; GET editorial e perfis existem | Baixo: consulta adicional quando a UI precisa de estado | #55/#58: usar estado separado e comparar ETags entre consultas; divergência exige releitura de conteúdo | Não |
| Perfis 2.0 consultáveis/pré-validáveis não implicam escrita habilitada | Médio se o formulário selecionar release arbitrária | #58: respeitar persistable/releases históricas suportadas; homologação institucional continua humana | Não para Work no perfil atual |
| Retenção, janela de depreciação e publicação de novas releases sem aprovação institucional | Governança: testes não decidem política pública | Mantenedores aprovam prazos/responsáveis antes de releases/depreciação; ADR próprio para coexistência/migração | Não para a baseline existente |

Não foi detectada incompatibilidade estrutural que exija migração nesta issue.
Persistência experimental segue a #54. Cliente #55, BFF #56, listagem/detalhe #57,
formulário #58 e E2E #59 continuam entregas próprias; não foram antecipados.
Não há bloqueador técnico conhecido para o início da #55 com os limites descritos.

## Critérios de aceite e conclusão

**Concluída tecnicamente no working tree local para revisão manual.** A baseline
complementar foi produzida pela fábrica real; integridade, determinismo byte a byte,
check sem escrita, geração exclusiva, drift/diff, CI local, quinze DTOs, erros,
precondições, ações/perfis e regressões foram comprovados pelas execuções acima.
Política técnica consolidada no ADR 0029, dimensões/históricos preservados e
necessidades do primeiro Work documentadas. O gate global e PostgreSQL real isolado
passaram, sem skips confundidos com integração. Aprovação institucional, publicação
e execução hospedada CI não foram alegadas nem efetuadas.

## Estado final do Git

Verificações: `git branch --show-current`, `git status --short`, `git diff --check`,
`git diff --stat`, `git log -1 --oneline` e `git diff --cached --stat`.
Branch `main`; HEAD permanece `5e8a00569dbe9f20a783e00f35dba4fddae81240`.
Nenhum commit, branch nova, git add, push, PR ou alteração de issue/remoto foi criado.
Os treze arquivos da entrega permanecem no working tree sem staging, incluindo os
novos artefatos preparados para versionamento pelo mantenedor. As duas exclusões
preexistentes permanecem intactas e separadas do escopo. Diff sem erros de whitespace;
nenhuma alteração funcional de frontend ou migração foi mantida.
