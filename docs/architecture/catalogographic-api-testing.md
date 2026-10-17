# Integração e consumo da API catalográfica — M05.07 / #51

Referência operacional das M05.01–M05.06, preservando o
[contrato catalográfico v1, especificação 1.0.0](catalogographic-contract.md).
As [evidências desta entrega](catalogographic-m0507-verification-2026-10-16.md)
registram resultados separados dos relatórios históricos. Aprovação técnica não
substitui homologação biblioteconômica, de Keycloak, navegador ou produção.

## Preparar e executar

Requisitos: Python 3.13–3.14, uv, dependências de `apps/api/uv.lock`; Node 24/npm
e dependências web para o gate; Docker com imagem local `postgres:17-bookworm`
para integração. Nenhuma dependência nova. A partir da raiz:

```bash
bash scripts/check.sh
# Opt-in; cria e remove uma instância exclusiva, sem usar .env/DATABASE_URL de trabalho.
bash scripts/test-postgres.sh
# Seleção focada em outra instância nova:
bash scripts/test-postgres.sh -k 'catalog_acceptance or two_http_sessions'
```

`test-postgres.sh` publica uma porta dinâmica somente em loopback, usa dados em
tmpfs e autenticação trust exclusivamente nessa instância descartável. O script
não faz pull de imagem, não usa Compose nem volumes de trabalho. Instala Alembic
HEAD explicitamente em `libris_test` e cria três bancos inicialmente vazios,
separados, para migrações de auditoria, editorial e web. Só esses bancos recebem
os upgrades/downgrades previstos nos testes. Não há DDL no startup da aplicação.
O trap remove somente o ID do container criado pelo script, inclusive após falha.
O JUnit impresso em `/tmp` registra contagens; qualquer skip na seleção é erro.
Os testes rodam sequencialmente: paginação pressupõe ausência de outros escritores
fora das concorrências determinísticas de cada cenário. Não usar xdist nesta suíte.

Execução manual, apenas em bancos comprovadamente exclusivos e descartáveis:

```bash
cd apps/api
uv run pytest
uv run ruff check . ../../tests
uv run mypy src
# URLs configuradas fora do histórico/logs; quatro bancos distintos.
DATABASE_URL="$TEST_DATABASE_URL" uv run alembic upgrade head
TEST_WEB_ISOLATED=1 uv run pytest -c pyproject.toml ../../tests/integration -m 'not keycloak' -q -rs
```

| Variável manual | Banco / pré-condição |
| --- | --- |
| TEST_DATABASE_URL | PostgreSQL asyncpg dedicado, migrado até HEAD |
| TEST_MIGRATION_DATABASE_URL | Outro banco inicialmente vazio; migração de auditoria |
| TEST_EDITORIAL_MIGRATION_DATABASE_URL | Terceiro banco inicialmente vazio; migração editorial |
| TEST_WEB_MIGRATION_DATABASE_URL | Quarto banco inicialmente vazio; migração web; TEST_WEB_ISOLATED=1 |

Variáveis ausentes geram skips na execução manual e não comprovam persistência.
SQLite e bancos de trabalho não são alternativas. Não copiar credenciais para o
repositório. O executor isolado ignora essas URLs preexistentes e define as próprias.

## Níveis de evidência

| Nível | Mecanismo real e substituições | O que comprova |
| --- | --- | --- |
| Offline `tests/api` | FastAPI, contratos, JWT RS256 e validador OIDC; discovery/JWKS por MockTransport; alguns testes substituem ator/serviço explicitamente | Estrutura, permissões, autenticação inválida, parser/RDF/SHACL, OpenAPI e erros; sem persistência física |
| PostgreSQL HTTP das M05.03–06 | AsyncClient/ASGI, transações e banco reais; override de ator confiável | CAS, atomicidade, publicação, paginação e RDF; não valida emissão OIDC |
| `test_catalog_acceptance_postgres.py` | AsyncClient/ASGI, PostgreSQL, dependências de ator/guard/serviço reais; somente transporte OIDC e chave efêmera locais | JWT → permissões → operação HTTP → persistência → ator auditado, sem rede OIDC |
| Keycloak opt-in | Provedor externo isolado, harness e ativação próprios | Integração real somente quando executada; separada do runner PostgreSQL |

As verificações reais Keycloak existentes continuam em
`tests/integration/test_keycloak_oidc.py`, controladas por
`TEST_KEYCLOAK_ENABLED=1`/`TEST_KEYCLOAK_GOVERNANCE=1` e pelo
[roteiro isolado M04](identity-keycloak-local.md). O runner exclui os dois casos
com marker `keycloak`; os testes offline do harness permanecem executados.
Mocks/JWKS assinados não são homologação Keycloak.

## Criar, ler e editar os cinco tipos

Base `http://localhost:8000/api/v1/catalog`. Bearer é access token do provedor
configurado, passado em header; a API não oferece login/refresh/senhas. Create
gera UUIDv4/URI, retorna 201, `Location` relativo e `ETag` forte. GET de Location
retorna 200, Read v1 e o mesmo ETag enquanto conteúdo/geração editorial não mudam.
Create rejeita `internal_id`, `uri`, `actor_id`, permissões e revisão do cliente.

Payloads mínimos válidos (substituir referências pelos UUIDs realmente criados):

| POST da coleção | JSON |
| --- | --- |
| `/works` | `{"title":[{"main_title":[{"value":"Monografia sintética","language":"pt"}]}]}` |
| `/instances` | `{"instance_of":{"kind":"local","entity_type":"Work","internal_id":"<uuid-work>"}}` |
| `/items` | `{"item_of":{"kind":"local","entity_type":"Instance","internal_id":"<uuid-instance>"},"identified_by":[{"kind":"Local","value":"EX-SINTETICO-1"}]}` |
| `/agents` | `{"kind":"Person","authorized_name":[{"value":"Pessoa sintética","language":"pt"}]}` |
| `/subjects` | `{"preferred_label":[{"value":"Assunto sintético","language":"pt"}],"scheme":[{"uri":"urn:libris:test:subjects"}]}` |

As quinze [fixtures Create/Read/Update](../../tests/fixtures/bibliographic/contracts/)
continuam sendo exemplos completos versionados. Exemplo de fluxo Work:

```bash
API=http://localhost:8000/api/v1/catalog
# ACCESS_TOKEN é fornecido por sessão autorizada; não imprimir ou versionar seu valor.
curl -i "$API/works" -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"title":[{"main_title":[{"value":"Monografia sintética","language":"pt"}]}]}'
# RESOURCE_ID recebe internal_id; ETAG recebe o header ETag completo, com aspas.
curl -i "$API/works/$RESOURCE_ID" -H "Authorization: Bearer $ACCESS_TOKEN"
curl -i -X PATCH "$API/works/$RESOURCE_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" -H "If-Match: $ETAG" \
  -H 'Content-Type: application/json' \
  --data '{"note":[{"label":[{"value":"Nota revisada","language":"pt"}]}]}'
```

PATCH mantém UUID/URI/perfil, cria revisão independente e renova ETag. Omissão
preserva, null limpa propriedade opcional, lista substitui integralmente. Listas
vazias não removem propriedades obrigatórias. Auxiliares são estruturas completas.
Não reconstruir o snapshot a partir do Read: o serviço preserva as propriedades
RDF externas à projeção DTO ou rejeita uma edição que causaria perda silenciosa.

Sem If-Match → 428; validador obsoleto → 412; weak/wildcard/lista/duplicado → 400.
Não enviar o token de domínio UUID:revisão nem ETag de exportação RDF/pública.
O ETag de edição vincula conteúdo e versão editorial; após transição é necessário
renová-lo mesmo sem mudar a revisão de conteúdo. Um conflito exige recarregar e
reconciliar a edição; não repetir cegamente a escrita com o novo ETag.

## Relações, validação e ciclo editorial

Instance possui `instanceOf` Work; Item possui `itemOf` Instance. `hasInstance`
e `hasItem` são inversas derivadas, consultáveis com `include_inverses=true`,
sem escrita no snapshot do pai. Work→Agent usa Contribution com role por URI;
Work→Subject usa referência. Autoridades compartilhadas mantêm revisões próprias;
remover um vínculo não remove/revisa a autoridade ou outro proprietário.

GET `/{collection}/{id}/relationships` retorna vínculos e ETag próprio. PATCH
nessa rota usa **esse ETag**, operações ordenadas add/remove/replace e revalida
o resultado inteiro atomicamente. Exemplo Work→Subject, substituindo UUIDs:

```json
{"operations":[{"op":"add","links":[{"kind":"direct","source":{"kind":"local","entity_type":"Work","internal_id":"<uuid-work>"},"target":{"kind":"local","entity_type":"Subject","internal_id":"<uuid-subject>"},"predicate":"http://id.loc.gov/ontologies/bibframe/subject"}]}]}
```

Uma referência explicitamente local inexistente/incompatível é rejeitada. URI
externa não é consultada nem comprova existência/tipo; pode permanecer pendente
no rascunho e bloquear publicação. Não se promete verificação remota universal.

POST `/works/validation`, autorizado para criação, não persiste:

```json
{"kind":"dto","profile_release":"urn:libris:profile:monograph:v1:1","resource":{"title":[{"main_title":[{"value":"Pré-validação"}]}]}}
```

O resultado 200 indica execução concluída; verificar `conforms` e `issues`,
inclusive severidade/path/componente. Erro de envelope é 422. Propostas RDF usam
`kind=rdf`, `format=turtle` ou `json-ld`, `root`, `profile_release` e `document`;
somente parser limitado e contextos locais. GET `/profiles` e `/profiles/release`
é consulta autorizada, sem cadastrar/alterar releases. Perfis 2.0 podem ser
pré-validados; escritas seguem os perfis históricos fixados pelo contrato vigente.

Cada POST editorial usa ETag de edição atualizado, `selected_revision` positivo
e `scope=record` (ou `candidate`). Sequência: submit → approve → publish; retornar
com return permite correções. withdraw → republish ou archive preserva histórico;
return/withdraw/archive exigem justification. Ver a
[matriz completa de transições e exemplos](catalogographic-editorial-http.md).
Não existe DELETE físico: retorna 405 mesmo ao administrador com permissão delete.
Tombstones, fusão e resolvedor HTTP não estão implementados.

GET `/revisions`, `/revisions/{number}`, `/revisions/{number}/snapshot`,
`/revisions/compare?previous=1&current=2`, `/audit`, `/audit/{event_id}` e `/history`
é protegido. POST `/revisions/restore` recebe `source_revision`, If-Match e cria
nova revisão; não sobrescreve a histórica nem publica automaticamente.

## Permissões e confidencialidade

Fonte executável: `identity.domain.authorization.POLICIES` e
`infrastructure.role_mapper.ROLE_PERMISSIONS`; detalhes na
[matriz por operação](operation-authorization.md). Papéis podem ser combinados.

| Papel real | Capacidades relevantes / limite |
| --- | --- |
| libris-reader | leitura pública; não lê editorial sem metadata_revision:read |
| libris-cataloger | cria/edita bibliográficos, consulta editorial/revisões dos cinco tipos, submete; não gerencia autoridades/aprova/publica |
| libris-authority-manager | cria/edita autoridades; isolado não possui leitura editorial/revisões ou submissão |
| libris-reviewer | consulta editorial/revisões/auditoria; aprova/devolve; não edita/publica |
| libris-publisher | consulta editorial/revisões/auditoria; publica/retira/republica/arquiva; não submete/aprova/edita |
| libris-admin | conjunto explícito de permissões; system:admin isolado não é bypass |

Ausência/token inválido → 401 com Bearer challenge; token válido sem todas as
permissões → 403. Ator vem de issuer/sub assinados, nunca body, query, headers
de identidade ou roles do frontend. Campos bibliográficos Agent/Subject não
representam contas/permissões de identidade.

Somente GET `/{collection}/{id}/public` e `/public/{collection}` leem publicação
anônima. Draft/in_review/approved/withdrawn/archived/legado sem publicação são 404
no individual e ausentes na listagem. Nova edição de publicado abre candidata;
a revisão publicada anterior continua selecionada, em todos os formatos e listas,
até publicar a candidata aprovada. Referências por URI não expandem descrições
dos alvos. Erros e endpoints auxiliares não devem revelar conteúdo, ator,
diagnósticos ou ETag editorial a usuários sem acesso.

## Formatos, listagem e erros

GET individual editorial/público aceita application/json (Read operacional),
application/ld+json ou text/turtle (snapshot integral). Vary: Accept; MIME correto;
Accept incompatível/malformado → 406 Problem Details. Não há ingestão RDF CRUD
nem exportação RDF de coleções. Extensões, idioma, datatype e URI são preservados
em RDF; comparar grafos por isomorfismo, nunca bytes/labels de blank nodes.
Todas as rotas de API mantêm no-store/private, inclusive leitura pública.

Listagens JSON aceitam limit 1–100 (default 20), cursor devolvido, internal_id,
uri, profile; editorial também editorial_state. Ordem UUID ascendente; reenviar
mesmos filtros/limit. Paginação não promete snapshot global entre requisições;
inserções/retiradas podem alterar participação. Sem Elasticsearch, full-text,
facetas ou expansão de relações. Ver [contrato completo](catalogographic-listing.md).

| Status | Significado e ação |
| --- | --- |
| 400 | sintaxe/parser/If-Match/cursor malformado; corrigir entrada |
| 401 / 403 | autenticar ou obter as permissões efetivas necessárias |
| 404 | recurso/revisão/release ausente ou publicação indisponível |
| 405 | método indisponível, incluindo DELETE; consultar Allow |
| 406 | Accept sem formato suportado; solicitar JSON, JSON-LD ou Turtle |
| 409 | estado/transição ou integridade em conflito; consultar estado autorizado |
| 412 / 428 | revisão obsoleta / falta de If-Match; recarregar ETag de edição |
| 422 | DTO, referência, perfil ou SHACL inválido; consultar code/issues/validation |
| 500 / 503 | falha interna / infraestrutura indisponível; correlacionar X-Request-ID |

Erros usam `application/problem+json`, contrato 1.0, status/code/request_id e
diagnósticos seguros quando aplicáveis. OpenAPI real em `/openapi.json` descreve
somente operações existentes e declara ProblemDetails também no 406.
Não interpretar 200 de pré-validação como publicação ou aprovação institucional.
Deploy, editor, MARC21, circulação, inventário físico e busca M09 ficam fora da #51.

## Gate OpenAPI M06.01 / #53

Antes das suítes, `scripts/check.sh` verifica o JSON Schema documental e a
[baseline operacional OpenAPI](catalogographic-openapi.md), sem escrever arquivos.
O workflow `.github/workflows/catalogographic-contract.yml` executa esses checks,
a suíte offline API completa e análise estática com o lock. O
[inventário de operações](catalogographic-openapi-inventory.md) e
[relatório #53](catalogographic-openapi-m0601-verification-2026-10-16.md) distinguem
contrato declarado, comportamento exercitado e integração PostgreSQL.
