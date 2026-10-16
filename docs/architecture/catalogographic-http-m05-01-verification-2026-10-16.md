# Verificação M05.01 / #45 — 2026-10-16

Execução em 16/10/2026 (America/Manaus). Base local:
`236c355cd77447e6d9cb74b1eca28268c7a6955d`, branch `main`.
`git branch --show-current`, `git status --short` e `git log -5 --oneline` foram
executados antes de editar arquivos. Working tree inicial limpo, incluindo ausência
de arquivos não rastreados. Nenhum trabalho preexistente foi atribuído a esta entrega.
`git rev-list --left-right --count main...origin/main` retornou `0 0` contra a
referência local já existente; não houve fetch/pull nem sincronização remota.

## Diagnóstico e fontes

Foram lidos AGENTS.md, README, overview/domains, contrato v1, schemas, erros,
autorização por operação, matriz de acesso, identidade e roteiro M04.09; ADRs de
PostgreSQL/persistência, revisões independentes, consistência RDF, OIDC, DTOs,
diagnósticos, evolução e autorização. Inspecionados main, problemas/correlação,
segurança/CORS, Database, dependências/serviço/guard/políticas de identidade,
serviço bibliográfico, schemas, infraestrutura e testes relevantes, além do gate.

As issues [#45](https://github.com/inacioigne/libris/issues/45),
[#46](https://github.com/inacioigne/libris/issues/46),
[#47](https://github.com/inacioigne/libris/issues/47),
[#48](https://github.com/inacioigne/libris/issues/48),
[#49](https://github.com/inacioigne/libris/issues/49),
[#50](https://github.com/inacioigne/libris/issues/50) e
[#51](https://github.com/inacioigne/libris/issues/51) foram consultadas pelo conector
GitHub somente em leitura: todas abertas, associadas à milestone 5. A leitura direta
da milestone foi recusada pela allowlist do conector; a página web não foi recuperada
(cache miss) e `gh` não está instalado. O vínculo e o sequenciamento foram verificados
nos corpos/metadados das sete issues, sem alterar recursos remotos.

Os cinco commits recentes da main incluem alterações de frontend/admin/OPAC e
fluxos BFF; essas mudanças existentes não foram modificadas. O backend tinha somente
health/me, handlers RFC 9457, correlação, OIDC/RBAC/guard e engine no lifespan.
`BibliographicService` recebe async_sessionmaker e delimita as transações. Os DTOs
estão disponíveis, mas falta a ponte persistente genérica DTO ↔ RDF (#46).
Publicar CRUD antes dela arriscaria perda de extensões e projeções incorretas.

Lacunas relevantes: CORS só admite preflight health/me com GET; futuras operações
precisarão ampliação exata e testes. OpenAPI global já anuncia erros do mecanismo,
mas /me não declara explicitamente 401 no documento; seu comportamento continua
401 Bearer. Códigos editoriais genéricos mantêm fallback 422, sem inferir status
pelo nome; integração específica fica para #49. Nenhuma dessas lacunas foi ocultada
por endpoint placeholder ou alteração global sem necessidade.

## Decisões e arquivos

| Arquivo | Finalidade e estado Git esperado |
| --- | --- |
| `apps/api/src/libris/main.py` | modificado: inclui catalog_router mantendo health/me e lifespan |
| `apps/api/src/libris/modules/bibliographic/api/router.py` | novo: APIRouter `/api/v1/catalog`, tag catalog, sem operações artificiais |
| `apps/api/src/libris/modules/bibliographic/api/dependencies.py` | novo: acesso tipado à fábrica de sessões existente, sem abrir transação |
| `tests/api/test_catalogographic_http.py` | novo: 27 cenários de composição, compatibilidade, segurança e limites de cobertura |
| `docs/architecture/catalogographic-contract.md` | modificado: liga esta fundação e sua matriz ao contrato canônico |
| `docs/architecture/catalogographic-http.md` | novo: convenção de recursos/métodos, schemas, permissões, público/editorial, concorrência, paginação e sequenciamento |
| este relatório | novo: evidência separada, sem reescrever verificações históricas |

A única dependência nova retorna `Database.sessions` do lifespan. Identidade,
HumanContext, AuthorizationGuard/POLICIES, require_permissions e correlação são
reutilizados diretamente. Não há wrapper de autenticação, matriz executável nova,
sessão global, commit implícito ou transação HTTP externa. Os serviços existentes
preservam autoridade transacional, CAS, auditoria, fechamento e rollback.
Sem tabelas, migrações, create_all, dependências ou mudanças de locks/perfis/SHACL.
A composição aplica ADRs existentes; não muda a arquitetura nem o contrato DTO.

## Funcionalidade e cobertura efetivas

- Ponto de composição catalográfico registrado. Teste substitui somente esse ponto
  por um router com probe exclusivamente de teste e comprova sua inclusão; o router
  de produto continua vazio. Nenhum handler fictício entra no OpenAPI de produção.
- GET `/health`: público, HealthResponse; sem consulta de banco/provedor no startup.
- GET `/api/v1/identity/me`: Bearer validado, IdentityResponse; sem permissão funcional
  adicional, 401 para ausência/token malformado. Teste com override verifica o DTO,
  sem alegar validação criptográfica para esse caso positivo.
- OpenAPI HTTP real: somente os dois caminhos, operation IDs distintos, schemas
  reais e segurança Bearer; sem CRUD, transições ou relações anunciados.
- HTTP real: rejeição de contexto forjado, 401 com OIDC habilitado e JWT malformado,
  404 em caminhos futuros, 405/Allow em health, Problem Details, request ID e headers.
- Dependências/políticas **em isolamento**: 401, HumanContext, guard real para os
  cinco tipos, conjunção read + metadata_revision:read, system:admin sem bypass,
  negação mapeada para 403 e projeção pública da revisão exata. Não são testes de
  autorização HTTP de catálogo, pois não há endpoint protegido catalográfico.
- Pydantic + handler de validação **em isolamento**: cinco Create inválidos produzem
  422 seguro sem refletir sentinela de input. Não há cobertura HTTP de body
  catalográfico nesta entrega. A regressão existente cobre validadores/rotas de teste.
- Fábrica: mesma instância do lifespan, sessões distintas sem transação aberta,
  fechamento e chamada real de dispose observada no teardown. Nenhuma dependência
  geradora de sessão nova; nenhum ensaio transacional PostgreSQL foi feito aqui.
- Preflight permitido e negado mantém caminhos/métodos/origens/headers existentes;
  catálogo não é liberado prematuramente. BFF e políticas de segurança preservados.

## Execuções e resultados

Ambiente: Python 3.13.15, uv 0.12.21, Node 24.16.0 e npm 11.15.0 (PATH com
`/home/inacio/.nvm/versions/node/v24.16.0/bin`); Docker Compose v5.6.0.

| Comando / local | Resultado observado |
| --- | --- |
| `uv run pytest ../../tests/api -q`, `uv run ruff check . ../../tests`, `uv run mypy src` em apps/api, sandbox | bloqueados antes de executar: snap-confine/AppArmor |
| `bash scripts/check.sh` na raiz, sandbox | bloqueado no uv/Snap; não aprovado nessa tentativa |
| `.venv/bin/pytest ../../tests/api/test_catalogographic_http.py -q`, sandbox | sem progresso no TestClient; processo exclusivo desta tentativa encerrado (143) |
| mesmo pytest específico fora do sandbox, primeira execução | 24 passaram, 3 falharam por expectativa nova incorreta de código 404; corrigida para `resource.unknown`, sem mudar o handler existente |
| mesmo pytest específico fora do sandbox, após correção e após OIDC habilitado nos cenários negativos | 27 passaram; 1 aviso Starlette/httpx, sem skips |
| `.venv/bin/ruff check . ../../tests ../../scripts/verify-m04-integration.py` em apps/api | passou |
| `.venv/bin/mypy src` em apps/api | passou, 88 arquivos |
| `.venv/bin/pytest ../../tests/api -q` fora do sandbox | execução parcial substituída pelo gate oficial (processo desta tarefa encerrado); não contada como suíte aprovada |
| `npm test` em apps/web, sandbox | 3 arquivos passaram, auth.test.ts falhou sem diagnóstico específico; não atribuído a uma regressão de código |
| `npm test` em apps/web, fora do sandbox | 167 passaram, nenhum skip/falha |
| `npm run build` em apps/web, sandbox | falhou: Could not parse output from TypeScript's --showConfig |
| `npm run build` em apps/web, fora do sandbox | passou, rotas Next compiladas e geradas |
| `npm run typecheck` em apps/web | passou |
| `docker compose --env-file .env.example config --quiet` sem env administrativo | bloqueado por variáveis Keycloak obrigatórias ausentes |
| mesmo Compose com valores administrativos efêmeros aleatórios, como no gate | passou; somente validação estática, sem iniciar serviços |
| `uv --version` fora do sandbox | passou; viabilizou repetição oficial do gate sem adaptador ou alteração do script |

Repetição oficial na raiz, fora do sandbox, com Node 24 no PATH:
`bash scripts/check.sh` **passou, exit 0**. O script foi executado sem alterações,
sem wrappers de uv e sem reduzir sua suíte:

| Etapa oficial | Resultado final |
| --- | --- |
| `uv run pytest` | **1695 passaram**, 477 avisos, 135,13 s; nenhum skip/falha |
| `uv run ruff check . ../../tests ../../scripts/verify-m04-integration.py` | passou |
| `uv run mypy src` | passou, 88 arquivos |
| `npm test` | **167 passaram**, nenhum skip/falha |
| `npm run build` | passou |
| `npm run typecheck` | passou |
| Compose estático com credenciais aleatórias geradas pelo script | passou; nenhum serviço iniciado |

Os avisos são de depreciação Starlette/httpx e RDFLib/ConjunctiveGraph, sem
supressão. Os 27 testes novos estão incluídos nos 1695. Os dois imports que Next
regenerou em `apps/web/next-env.d.ts` foram repostos exatamente ao conteúdo inicial
depois do gate; o frontend não fica modificado por esta tarefa. Nenhum código mudou
após o gate, somente este relatório e a reposição do artefato gerado preexistente.
Logs locais em `/tmp/libris-m0501-*`; não foram anexados ambiente, credenciais ou
arquivos .env ao repositório. Os links locais dos documentos novos foram verificados.

Revisão final: `git diff --check` passou; `git diff --stat`, `git status --short`,
`git ls-files --others --exclude-standard`, `git diff --cached --quiet`, branch e
HEAD foram conferidos. Dois arquivos rastreados modificados e cinco novos não
rastreados, exatamente os sete da tabela. Staging vazio, branch main e HEAD inicial
preservados. Arquivos não rastreados foram revisados separadamente, pois não entram
em `git diff --stat`.

## Limites e próximas entregas

Nenhuma migração, integração PostgreSQL/Keycloak real, navegador ou implantação
foi executada nesta #45. Nenhum skip comprova integração. A evidência histórica
M04.09 permanece separada, sem reclassificá-la como execução atual ou homologação
institucional/produção. Avisos de bibliotecas existentes permanecem visíveis.

#46 entrega adaptadores sem perda; #47 CRUD/ETag e persistência HTTP; #48 relações,
pré-validação e perfis; #49 transições/histórico/auditoria e projeção pública;
#50 listagens/filtros/paginação/Accept; #51 homologação integrada. Schemas/envelopes
novos e políticas ainda incompletos na matriz documental precisam fechamento na
respectiva issue antes de qualquer handler ser disponibilizado.

As alterações ficam exclusivamente locais, sem staging. Nenhum commit, branch,
PR, push, alteração de issue/milestone ou outra mutação remota foi realizado.
