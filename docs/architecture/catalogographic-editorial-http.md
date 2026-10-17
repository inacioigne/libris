# Ciclo editorial, histórico e auditoria por HTTP — M05.05 / #49

Complemento vigente de [HTTP v1](catalogographic-http.md) e do
[contrato catalográfico 1.0.0](catalogographic-contract.md).
[ADR 0038](../decisions/0038-catalog-editorial-http.md).
[Execução e matriz de testes](catalogographic-m0505-verification-2026-10-16.md).

Prefixo `B=/api/v1/catalog/{collection}/{id}`, com collection em
works/instances/items/agents/subjects e id UUID persistido. Todas as respostas JSON
usam `application/json`; erros usam Problem Details 1.0 e `X-Request-ID`.
Somente `/public` dispensa Bearer. As outras operações usam ator OIDC e guard no
backend. Nenhum body aceita actor_id, roles, permissions ou expectativas de versão.

## Operações disponíveis

| Método e caminho | Permissão necessária | Entrada | Resposta/sucesso |
| --- | --- | --- | --- |
| GET `B/editorial` | bibliographic:read + metadata_revision:read; para Agent/Subject, authority:read + metadata_revision:read | sem body | EditorialStateRead, 200 e ETag de edição |
| POST `B/editorial/submit` | editorial:submit | TransitionRequest e If-Match | EditorialStateRead, 200 e novo ETag |
| POST `B/editorial/approve` | editorial:approve | mesmo contrato | mesmo contrato |
| POST `B/editorial/publish` | editorial:publish | mesmo contrato | mesmo contrato |
| POST `B/editorial/return` | editorial:return | mesmo contrato, justification obrigatória | mesmo contrato |
| POST `B/editorial/withdraw` | editorial:withdraw | mesmo contrato, justification obrigatória | mesmo contrato |
| POST `B/editorial/republish` | editorial:republish | mesmo contrato | mesmo contrato |
| POST `B/editorial/archive` | editorial:archive | mesmo contrato, justification obrigatória | mesmo contrato |
| GET `B/revisions` | metadata_revision:read | limit=100 (1–200), after_number=0 (>=0) | RevisionPage, 200 |
| GET `B/revisions/{number}` | metadata_revision:read | número positivo | Revision, 200 |
| GET `B/revisions/{number}/snapshot` | metadata_revision:read | número positivo | grafo proprietário completo text/turtle, 200 |
| GET `B/revisions/compare` | metadata_revision:read | previous e current positivos obrigatórios | SemanticDiff, 200 |
| POST `B/revisions/restore` | metadata_revision:read + metadata_revision:create | RestoreRequest e If-Match | nova Revision, 201 |
| GET `B/audit` | metadata_audit:read | limit=100 (1–200), cursor opcional | EventPage, 200 |
| GET `B/audit/{event_id}` | metadata_audit:read | UUID de evento do mesmo recurso | AuditEvent, 200 |
| GET `B/history` | metadata_revision:read + metadata_audit:read | mesmos parâmetros de audit | EditorialHistory coerente, 200 |
| GET `B/public` | nenhuma; revisão pública visível | sem body | Read v1 da coleção, 200 |

As sete rotas de comando são literais; não existe `/editorial/{action}` arbitrário.
Nenhuma rota remove ou atualiza snapshots históricos. GET do recurso corrente
continua editorial autorizado; `/public` delega exclusivamente a read_public.

## Estado, CAS e exemplos de comandos

GET `/api/v1/catalog/works/00000000-0000-4000-8000-000000000001/editorial`
com `Authorization: Bearer <access-token>` retorna, por exemplo, após edição de R1:

```json
{"contract_version":"1.0","internal_id":"00000000-0000-4000-8000-000000000001","editorial_state":"published","current_revision":2,"candidate_state":"draft","candidate_revision":2,"approved_revision":null,"published_revision":1,"public_revision":1,"editorial_version":5}
```

Estado legado não inicializado: editorial_state/editorial_version e ponteiros são
null; current_revision continua real. Não é publicação presumida.

Para os POST abaixo, enviar `Authorization: Bearer <access-token>`,
`Content-Type: application/json` e `If-Match: "catalog-v1-<digest-observado>"`.
Obter ETag pelo GET corrente ou GET editorial e renovar após cada sucesso.
Os exemplos são corpos completos, aplicáveis aos estados indicados:

| Caminho relativo a B | Estado de origem | Body |
| --- | --- | --- |
| `/editorial/submit` | draft R1 | `{"selected_revision":1,"scope":"record"}` |
| `/editorial/approve` | in_review R1 | `{"selected_revision":1,"scope":"record"}` |
| `/editorial/publish` | approved R1 | `{"selected_revision":1,"scope":"record"}` |
| `/editorial/return` | in_review/approved R1 | `{"selected_revision":1,"scope":"record","justification":"Revisar descrição"}` |
| `/editorial/withdraw` | published R1 | `{"selected_revision":1,"justification":"Retirada justificada"}` |
| `/editorial/republish` | withdrawn R1 | `{"selected_revision":1}` |
| `/editorial/archive` | withdrawn R1 | `{"selected_revision":1,"justification":"Encerramento editorial"}` |
| `/editorial/submit` | published R1 com candidata draft R2 | `{"selected_revision":2,"scope":"candidate"}` |
| `/editorial/approve` | candidata in_review R2 | `{"selected_revision":2,"scope":"candidate"}` |
| `/editorial/publish` | candidata approved R2, registro published | `{"selected_revision":2,"scope":"candidate"}` |

TransitionRequest exige selected_revision inteiro positivo estrito; scope é record
(default) ou candidate. justification opcional até 2.000 caracteres, sem NUL e não
vazia quando fornecida. RETURN/WITHDRAW/ARCHIVE exigem justificativa no domínio.
As respostas possuem os campos do exemplo EditorialStateRead e novo ETag, com a
versão editorial incrementada uma vez. Comandos não criam revisões de conteúdo.
Apenas publish/republish revalidam SHACL, perfil, cobertura e integridade referencial
na transação protegida antes de gravar estado e auditoria. approve fixa a revisão
corrente exata. Conteúdo aprovado/em revisão exige return antes de edição.

O ETag existente vincula UUID/URI, perfil, conteúdo projetado, revisão e versão
editorial. Não há segundo modelo de CAS. A observação HTTP produz as expectativas
que o serviço compara sob lock e no UPDATE condicional. Só verificar o digest antes
da transação seria insuficiente. Um sucesso retorna somente após commit.

| Erro | Contrato |
| --- | --- |
| 400 | JSON/If-Match malformado, duplicado, fraco, lista ou wildcard; limites de body/profundidade existentes |
| 401 | Bearer ausente/inválido; WWW-Authenticate: Bearer |
| 403 | operação sem todas as permissões; system:admin isolado não concede acesso |
| 404 | recurso/coleção/revisão/evento não encontrado; `/public` também para ausência de publicação visível |
| 409 | aresta/comando/estado inválido, inclusive publish em withdrawn; conflito SQL classificado |
| 412 | If-Match obsoleto, CAS de conteúdo ou versão editorial derrotado |
| 422 | estrutura, escopo/precondição editorial, revisão selecionada diferente da aprovada, justificativa, SHACL ou integridade rejeitados; código específico existente |
| 428 | If-Match ausente nos sete comandos ou restore |
| 500/503 | falha técnica/interna ou dependência indisponível conforme classificador vigente; sem SQL/segredos |

Esses erros aplicam-se conforme os parâmetros da operação. GETs não exigem If-Match;
`/public` não exige autenticação. Schemas e respostas reais estão em `/openapi.json`.
Diagnósticos de publicação rejeitada preservam validation/ issues e request_id;
não expõem mensagens técnicas arbitrárias. Body não escolhe perfil, ator, SHACL,
mapa de referências externas ou estado de destino.

## Revisões, comparação, snapshots e restauração

Exemplos GET autorizados, sem body:

```http
GET B/revisions?limit=2&after_number=0
GET B/revisions/1
GET B/revisions/1/snapshot
GET B/revisions/compare?previous=1&current=2
```

`B` significa o prefixo concreto definido acima, não texto literal de uma URL.
Revision contém identity (internal_id/uri), number, created_at UTC, provenance
(source/process/reason), profile exato e actor_id nullable histórico. RevisionPage
contém contract_version=1.0, items de `{revision, content_event_recorded}` e
next_after_number. Ordenação numérica crescente, cursor exclusivo; página vazia
encerra navegação e retorna cursor null. Um cursor não nulo aponta para o último
item, podendo produzir uma página vazia seguinte. Não representa total ou has_more.
Legado sem evento observado não recebe autoria/eventos fabricados. Consultas
históricas conferem o tipo da raiz sem exigir um Read corrente válido ou aplicar
retroativamente ownership aos protótipos compostos; preservam o snapshot integral.
Isso não permite sua publicação implícita.

Snapshot é Turtle do grafo integral histórico, incluindo extensões não projetadas
no Read; serialização não altera o JSONB. SemanticDiff contém added/removed de
RdfStatement: subject/predicate/object com kind/value/language/datatype. Comparação
isomórfica devolve `{"added":[],"removed":[]}` apesar de nomes diferentes de blank
nodes ou serializações distintas. Alterações de componentes podem produzir delta
conservador; não usar rótulos de blank nodes como identificadores de edição.

```http
POST B/revisions/restore
Authorization: Bearer <access-token>
If-Match: "catalog-v1-<digest-atual>"
Content-Type: application/json

{"source_revision":1,"justification":"Recuperar descrição histórica"}
```

RestoreRequest exige source_revision inteiro positivo estrito e justification
opcional nas mesmas condições do comando. Retorna Revision nova com number=N+1,
proveniência source=catalog/process=http:restore e ator atual confiável. Cria um
único restored/content com source_revision na mesma transação. Preserva perfil,
identidade e todas as revisões anteriores; revalida conteúdo e CAS. Não publica:
registro published mantém R1 pública e nova candidata draft; draft continua draft.
Requer ciclo editável existente; não contorna aprovação, retirada ou arquivamento.
Consultar GET corrente/editorial para obter o ETag da nova geração antes de escrever.

## Histórico cronológico e auditoria

```http
GET B/audit?limit=2
GET B/audit?limit=2&after_time=2026-10-16T20%3A00%3A00Z&after_event_id=00000000-0000-4000-8000-000000000002
GET B/audit/00000000-0000-4000-8000-000000000002
GET B/history?limit=2
```

EventPage tem items de AuditEvent e next_cursor `{occurred_at,event_id}` ou null.
Passar os dois componentes em after_time/after_event_id; ambos devem estar presentes
ou ausentes, e after_time exige timezone. Eventos ordenam por occurred_at/UUID
ascendentes, com cursor exclusivo e precisão completa; ao terminar, página vazia.
É navegação viva: novas inserções podem aparecer, sem prometer fotografia global;
eventos que forem inseridos com chave anterior ao cursor só aparecem numa navegação
nova. Não há offset nem ordenação ambígua com instantes iguais.

AuditEvent conserva event_id/type, identity, revision_number, occurred_at,
source/process/profile, actor_id/type nullable, reason, previous_state/new_state,
scope, previous_version/new_version, source_revision/restoration_kind e sucessor
quando previsto pelo contrato. Não expõe JWT/claims/logs de segurança. Evento deve
pertencer ao UUID do caminho. EditorialHistory devolve state (EditorialRecord ou
null legado), current (Revision) e events; o estado/corrente/eventos são lidos sob
o protocolo coerente M03. Para próxima página, usar instante/UUID do último evento.
O campo state usa version do contrato interno, enquanto EditorialStateRead usa
editorial_version e explicita candidate_revision/public_revision.

## Leitura pública

```http
GET /api/v1/catalog/works/00000000-0000-4000-8000-000000000001/public
```

Sem Bearer ou body. Retorna WorkRead v1 (ou Read correspondente à coleção), sem
metadados editoriais/auditoria e sem ETag de edição. Draft/legado sem publicação,
withdrawn/archived, UUID inexistente ou coleção errada retornam 404 resource.unknown.
R1 continua visível durante R2 draft/in_review/approved, restauração e falha de
publicação. Publish autorizado da candidata exata passa a expor R2. Withdraw oculta,
conservando candidata e ponteiro histórico; republish revalida a publicação anterior;
archive é terminal e encerra candidata. Falhas não removem a publicação anterior.

Respostas de API usam no-store/private, incluindo a projeção pública. Endpoints
internos anônimos retornam 401, sem conteúdo/snapshots/diagnóstico privado. Cabeçalhos
actor_id/roles enviados pelo cliente não alteram auditoria nem autorização.

Limites: sem negociação Accept/listagem de catálogo (#50), UI editorial (#M07),
circulação ou administração de perfis. O mapa externo do serviço interno não é
exposto/configurado por esta API: publicação de referência não local sem evidência
continua bloqueada com reference.unverified. Não há busca remota. A observação para
conferir coleção/ETag carrega snapshot corrente; a comparação conserva o custo RDF
já documentado, sem promessa de quota de CPU ou capacidade de produção.
