# Verificação M04.06 / #39 — governança de acesso

Data da execução: 2026-10-13 (America/Manaus).
HEAD inicial: `75c3759b950befb6032acb0df637bcdca4337557`.
Branch inicial: main; working tree inicialmente vazio.

## Diagnóstico anterior à implementação

Issues #39 (aberta), #35 e #38 (fechadas), milestone 4, consultadas via GitHub
somente para leitura. Inspecionados os seis commits 75c3759, 3f03eeb, ad6dbec,
cd30b0d, c325930 e 61d014d e as fontes obrigatórias do pedido.

| Controle/requisito #39 | Estado inicial e lacuna | Tratamento mínimo |
| --- | --- | --- |
| Assinatura, issuer, audience, JWKS, expiração, access token | OIDCValidator/TokenValidator implementados; testes RSA e integração histórica #35 | Preservar; testar validade residual |
| Identidade estável | AuthenticatedActor e actor_identifier por issuer/sub, sem email/nome | Preservar; demonstrar estabilidade entre emissões |
| Papéis mínimos | ROLE_PERMISSIONS central, seis papéis/17 permissões, unknown sem concessão | Preservar integralmente |
| Autorização interna | HumanContext, TechnicalContext, AuthorizationGuard, Operation/POLICIES e serviços M03 implementados | Reutilizar; não criar máquina paralela |
| Fronteira humana externa | IdentityService aceita qualquer client com JWT válido e roles humanas | Exige código/testes: vincular cliente humano por azp assinado, negar demais |
| Contexto HTTP | get_current_actor/get_execution_context e /me protegidos; 401/403 existentes | Preservar contrato; testar cliente indevido com headers falsos |
| BFF | Sessão servidor, PKCE, guard administrativo por resposta da API | Sem alteração frontend; regressão no gate |
| Concessão/revogação | Provedor responsável; procedimentos de ciclo de vida incompletos | Documentar responsabilidades, aprovações, revisão e revogação residual |
| Auditoria administrativa | Realm não habilita eventos administrativos explicitamente | Configuração não secreta e procedimento, sem representação sensível |
| Serviço externo | Nenhum consumidor M2M; TechnicalContext é interno | Contrato futuro fechado; nenhuma emissão/aceitação M2M operacional nesta issue |
| Instituições/unidades/bibliotecas | Sem escopo contextual/isolamento implementado | Contrato futuro M10/M11, sem tabelas/filtros/multi-tenancy |
| Autoria/proveniência | Revisão e auditoria M03, CAS, identidade técnica interna e NULL histórico | Preservar, sem backfill e sem auditoria administrativa bibliográfica |

Divergência histórica: AGENTS e o contexto original das issues descrevem Keycloak/
BFF como não validados/implementados; commits #35/#36 e relatórios posteriores
contêm implementação e ensaios isolados. Isso não é homologação de navegador,
institucional ou produção, nem prova de execução nesta sessão.

Decisão de escopo: #39 pede **projetar** identidade técnica; habilitar client_credentials
sem consumidor/endpoint M05 ampliaria a superfície sem uso demonstrado. Entregar
contrato M2M e fechar aceitação inadvertida como humano agora (ADR 0032).

## Ambiente e execução

Inspeção inicial: uv via snap; Node/npm fora do PATH (Node 24.16.0 encontrado em NVM).
Docker sem permissão no sandbox. Resultados finais registrados abaixo após execução.

## Mudanças realizadas e decisão

- IdentityService exige azp assinado do cliente interativo após TokenValidator;
  clientes desconhecidos/serviços não entram como humanos, mesmo com papel admin.
- OIDC_HUMAN_CLIENT_ID é validado em Settings e propagado pelo lifespan/Compose;
  .env.example documenta o padrão libris-web. Outro cliente web precisa alinhamento
  explícito. Tokens sem azp deixam de ser aceitos, intencionalmente.
- Realm demonstrativo habilita adminEventsEnabled e desabilita detalhes sensíveis.
  Preservados clients, papéis, usuários ausentes e prazos. Instâncias persistidas
  requerem atualização administrativa, sem reimportação destrutiva.
- Testes novos cobrem o boundary de cliente, configuração efetiva, identidade
  estável, revogação entre emissões e validade residual; RSA e JWT assinados locais.
- Harness novo verifica governança real, reutilizando PKCE existente; issuer de
  teste pode usar porta isolada via TEST_KEYCLOAK_ISSUER. Suíte opcional em subprocesso
  não revela stderr/traceback/segredos; sem credenciais, fica explicitamente skipped.
- Contrato de governança, responsabilidades, concessão/revogação, auditoria, futuro
  M2M e vínculos institucionais; ADR 0032. Referências cruzadas atualizadas.
- Nenhuma mudança em domínio/persistência/DTOs M03, mapas de roles/permissões,
  frontend, dependências, locks, tabelas ou migrações. Nenhum cadastro local de senha.

## Comandos efetivamente executados

| Comando | Resultado |
| --- | --- |
| git branch --show-current; git status --short; git rev-parse HEAD; git log -12 --oneline | main, limpo, HEAD inicial registrado; somente leitura |
| git show --stat dos seis commits solicitados | inspecionados; sem alteração de histórico |
| cd apps/api; uv run pytest ../../tests/api/identity (baseline) | 333 passed, 12 warnings, 7,06 s |
| cd apps/api; uv run pytest ../../tests/api/identity (com novos casos) | 342 passed, 12 warnings, 7,68 s |
| cd apps/api; uv run ruff check . ../../tests | final passou |
| cd apps/api; uv run mypy src | passou, 78 arquivos |
| PATH com Node 24.16.0; bash scripts/check.sh | exit 0: uv run pytest, Ruff, mypy, npm test/build/typecheck e Compose estático |
| uv run pytest, pelo gate | 1533 passed; sem skips/falhas |
| npm test, pelo gate | 91 passed; sem skips/falhas |
| npm run build, pelo gate | Next.js 16.4.0 compilou; rotas existentes |
| npm run typecheck, pelo gate e após restaurar arquivo gerado | passou nas duas execuções |
| python -m pytest -c pyproject.toml ../../tests/integration/test_keycloak_oidc.py -k governance -s, com ambiente privado isolado | 1 passed, 8 deselected, 1 warning, 6,12 s; provedor real |
| uv run pytest -c pyproject.toml ../../tests/integration/test_keycloak_oidc.py, sem flags | 7 passed, 2 skipped, 1 warning, 0,46 s |
| git diff --check | passou |

Os sete testes puros do harness não provam Keycloak. Os dois skips sem flags são
os ensaios opcionais M04.02 e governança M04.06; governança foi executada separadamente
com Keycloak real. M04.02 completo/rotação de chave não foi reexecutado nesta sessão.
Nenhuma integração PostgreSQL, migração, browser E2E ou M2M foi executada nesta
entrega; não são inferidas do gate. A suíte padrão confirma regressão interna
M03, incluindo CAS, publicação/visibilidade, autoria e NULL histórico via doubles.
Não houve alteração de persistência que exigisse nova homologação física.

Falhas e correções da execução, preservadas como evidência:

1. uv via snap não iniciou no sandbox (snap-confine/AppArmor); Docker também teve
   permission denied. Execuções necessárias escalonadas foram autorizadas pela
   revisão automática; nenhuma rejeição ou operação contra serviço de trabalho.
2. Primeiro Ruff após novos testes encontrou três linhas >100 caracteres; quebras
   corrigidas. Nova execução e gate completo passaram. mypy da cadeia inicialmente
   interrompida só foi considerado aprovado após execução efetiva no gate/final.
3. Node/npm não estavam no PATH; usado Node existente em NVM v24.16.0, sem instalação.
4. Build Next gerou next-env.d.ts apontando a .next/types; restaurado exclusivamente
   esse arquivo gerado desta execução ao conteúdo HEAD, via git show. Não havia
   alteração preexistente. Typecheck sobre o conteúdo final passou.

Avisos preexistentes Starlette/httpx e RDFLib ConjunctiveGraph não foram suprimidos.

## Evidência Keycloak real e isolamento

Criado container novo `libris-m0406-keycloak-isolated`, imagem
`quay.io/keycloak/keycloak:26.8.0`, ID inicial
`d46b14cf8bebe5503bab3fa698650eb6bfa44c377b21a4115561cc672a49d318`.
Porta publicada somente 127.0.0.1:18081 → 8080; issuer
http://keycloak.localhost:18081/realms/libris. Dados em tmpfs uid=1000,
sem volume persistente. JSON do working tree montado somente leitura para import.
Credenciais bootstrap aleatórias em arquivo /tmp criado O_EXCL, modo 0600;
runner privado modo 0700 carregou segredos no ambiente do subprocesso, sem saída.
Não foram lidos segredos do Compose/realm de trabalho.

Comando de inicialização efetivamente usado (arquivo privado, sem seu conteúdo):

```bash
docker run --detach --rm --name libris-m0406-keycloak-isolated \
  --env-file /tmp/libris-m0406-keycloak.env \
  -e KC_HOSTNAME=http://keycloak.localhost:18081 \
  -p 127.0.0.1:18081:8080 \
  --tmpfs /opt/keycloak/data:rw,uid=1000,gid=0 \
  -v /home/inacio/dev/libris/infrastructure/keycloak/libris-realm.json:/opt/keycloak/data/import/libris-realm.json:ro \
  quay.io/keycloak/keycloak:26.8.0 start-dev --import-realm
```

O ensaio usou Code + PKCE S256 e tokens reais emitidos por esse Keycloak. FastAPI
foi instanciado localmente via TestClient com OIDC habilitado e issuer isolado;
HTTPX real buscou discovery/JWKS. Não é mock de provedor, mas também não é um
ensaio de deployment da API por HTTP externo, navegador ou BFF.

Saída sanitizada do subprocesso:

```text
PASS: real PKCE grant/revoke; stable /me; old token 200; new token 403
PASS: provider session logout prevents refresh; existing JWT still offline
PASS: disable/reactivate and expired real token 401 Bearer
PASS: provider admin trail has actor/time/resource/operation; no representation
PASS: owned temporary user removed
```

Foi removido papel cataloger do usuário sintético desta execução; novas emissões
mantiveram actor_id e perderam permissões; JWT anterior continuou autorizado.
Logout administrativo recusou refresh; desativação recusou refresh, seguida de
reativação do mesmo usuário de teste. Lifespan reduzido a dois segundos apenas no
realm descartável; token emitido depois e expirado foi recusado 401 Bearer com skew
zero no teste. Esse ajuste não mudou JSON versionado nem prazos de trabalho.
Admin events continham CREATE/UPDATE/DELETE do usuário, time e authDetails.userId,
sem representation. O registro institucional de aprovação é procedimento externo;
o ensaio não o automatiza nem testa delegação administrativa refinada.

Limpeza efetiva: usuário removido por finally, container exato encerrado por
`docker stop libris-m0406-keycloak-isolated` (auto-removido por --rm), arquivos
privados /tmp de credenciais/runner removidos. Nenhum down/prune/volume removido.
Inventários antes/depois confirmaram os cinco containers de trabalho ativos:
libris-web-1, libris-api-1, libris-postgres-1, libris-keycloak-1,
libris-elasticsearch-1. Nenhuma conexão administrativa ao realm de trabalho.

## Matriz de critérios da #39

“Atendido” abaixo significa entrega local no nível pedido pela issue, não
homologação institucional/produção ou M2M operacional.

| Critério | Estado | Evidência |
| --- | --- | --- |
| Governança externa/ciclo de vida sem senha local | atendido documentalmente | identity-governance: responsabilidades, ciclo, aprovação por papel e revisão |
| Concessão/revogação reproduzível | atendido no ambiente demonstrativo | roteiro Admin Console + harness PKCE real executado |
| Revogação não instantânea | atendido | teste RSA entre emissões e teste real old 200/new 403; exp 401 |
| Acesso administrativo auditável | atendido no nível desta issue | eventos ON/representação OFF; teste real ator/time/recurso/operação; procedimento de evidência complementar restrita |
| Seis papéis/17 permissões/menor privilégio | atendido | mapa intacto; regressão 342 identidade e gate geral |
| Cliente externo técnico não vira humano | atendido | azp validado após assinatura; clientes ausentes/desconhecidos/serviços com admin negados |
| Identidade técnica estável e concessões mínimas | atendido como contrato; contexto interno existente preservado | ADR 0032, vinculação issuer/azp/sub futura; guard e allowlist existentes testados |
| Client_credentials operacional/rotação real de secret | fora do escopo implementado, pendente de consumidor | #39 exige projetar; nenhum client/role técnico novo habilitado, sem alegação de M2M |
| Contrato institucional/unidades/bibliotecas | atendido documentalmente | vínculos múltiplos/vigência/fonte/revogação sem apagar histórico; M10/M11 |
| Isolamento institucional operacional | futuro, não implementado | sem filtros/tabelas/schema tenant; limite explícito no contrato |
| Contratos M03/BFF/Problem Details preservados | atendido em regressão padrão | 1533 API, 91 web, build/tipos; sem diff em modelos/serviços bibliográficos/BFF |
| Documentação/ADR/relatório e Git local | atendido | arquivos abaixo, HEAD idêntico, main e estado final |

Pendências reais: #40 revisa HTTP/proteção de dados; #41 amplia eventos de segurança
API/BFF e correlação/retencão operacional; #42 homologa E2E, browser, ambiente e
produção. M05 implementará consumidores/endpoints com contexto e guard existentes;
M2M requer consumidor definido, credenciais por integração e ensaio real próprio.
M10/M11 devem definir/validar vínculos e autorização contextual antes de expor
coleções multiinstitucionais. Aprovação e adoção da política institucional, retenção
e delegação refinada pertencem à implantação; não foram automatizadas/homologadas.

## Arquivos e finalidade

Criados:

- docs/architecture/identity-governance.md: contrato, responsabilidades e roteiro.
- docs/decisions/0032-identity-governance.md: decisão de fronteira humana e escopo M2M.
- docs/architecture/identity-m04-06-verification.md: esta evidência independente.
- tests/integration/keycloak_governance_harness.py: fluxo administrativo real isolado.

Modificados:

- apps/api/src/libris/modules/identity/application/service.py: vinculação azp humana.
- apps/api/src/libris/core/config.py e main.py: configuração validada e propagação.
- .env.example e docker-compose.yml: configuração reproduzível, sem segredo.
- infrastructure/keycloak/libris-realm.json: eventos administrativos sem representação.
- tests/api/identity/test_identity.py: regressões novas de governança/cliente/realm.
- tests/integration/keycloak_harness.py: issuer isolado configurável (padrão preservado).
- tests/integration/test_keycloak_oidc.py: entrada opcional do ensaio de governança.
- README.md, identity.md, operation-authorization.md, security-access-matrix.md e
  security-m04-exit-criteria.md: links e estado vigente, preservando evidências datadas.

## Inspeção Git final

Branch main. HEAD final idêntico ao inicial:
`75c3759b950befb6032acb0df637bcdca4337557`.
Nenhuma branch criada/trocada, commit, staging, tag, merge, rebase, cherry-pick,
reset, stash, clean, pull, push, PR ou alteração remota de issue. Todas as mudanças
permanecem no working tree local. Relatórios anteriores não foram modificados.
O diff --stat abaixo cobre rastreados; os quatro novos arquivos aparecem no status.

```text
$ git status --short
 M .env.example
 M README.md
 M apps/api/src/libris/core/config.py
 M apps/api/src/libris/main.py
 M apps/api/src/libris/modules/identity/application/service.py
 M docker-compose.yml
 M docs/architecture/identity.md
 M docs/architecture/operation-authorization.md
 M docs/architecture/security-access-matrix.md
 M docs/architecture/security-m04-exit-criteria.md
 M infrastructure/keycloak/libris-realm.json
 M tests/api/identity/test_identity.py
 M tests/integration/keycloak_harness.py
 M tests/integration/test_keycloak_oidc.py
?? docs/architecture/identity-governance.md
?? docs/architecture/identity-m04-06-verification.md
?? docs/decisions/0032-identity-governance.md
?? tests/integration/keycloak_governance_harness.py
```

```text
$ git diff --stat
 .env.example                                       |  2 +
 README.md                                          |  5 ++
 apps/api/src/libris/core/config.py                 |  2 +
 apps/api/src/libris/main.py                        |  5 +-
 .../libris/modules/identity/application/service.py | 16 +++-
 docker-compose.yml                                 |  1 +
 docs/architecture/identity.md                      |  8 +-
 docs/architecture/operation-authorization.md       |  7 +-
 docs/architecture/security-access-matrix.md        |  5 ++
 docs/architecture/security-m04-exit-criteria.md    |  6 ++
 infrastructure/keycloak/libris-realm.json          |  2 +
 tests/api/identity/test_identity.py                | 88 ++++++++++++++++++++++
 tests/integration/keycloak_harness.py              |  2 +-
 tests/integration/test_keycloak_oidc.py            | 15 ++++
 14 files changed, 157 insertions(+), 7 deletions(-)
```

```text
$ git rev-parse HEAD
75c3759b950befb6032acb0df637bcdca4337557
```

```text
$ git branch --show-current
main
```

```text
$ git diff --check
```

```text
$ git diff --cached --name-only
```
