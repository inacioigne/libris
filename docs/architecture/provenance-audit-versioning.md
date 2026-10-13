# Proveniência, auditoria e versionamento — M03.04.02

A #43 integra a auditoria ao estado editorial persistido, incluindo a extensão
record.returned/record.archived. O [contrato atual de persistência](editorial-persistence.md)
e o [ADR 0028](../decisions/0028-editorial-transactions.md) sucedem as pendências
editoriais descritas nesta entrega original da #28.

Implementação interna da [issue #28](https://github.com/inacioigne/libris/issues/28),
com decisão em [ADR 0027](../decisions/0027-provenance-audit-versioning.md).
Fonte de verdade: PostgreSQL. Revisões e eventos são estruturas separadas;
não há novas rotas, interface, indexação, fila ou esquema bibliográfico definitivo.
[Evidências e critérios de aceite](provenance-audit-versioning-verification.md).

## Diagnóstico e compatibilidade

Issues #28 e #27 lidas integralmente pelo conector GitHub. Checkout inicial
`2f2bdb6`, workspace limpo. AGENTS.md, README, arquitetura, ADRs, migrações,
identidade, serviço bibliográfico, RDF/SHACL e testes existentes inspecionados.
A #27 está presente: domínio editorial e serviço com protocolo transacional,
mas sem adaptador PostgreSQL. Sua máquina não foi recriada.

Reutilizados ResourceIdentity, Provenance, Revision, RevisionStore, CAS, snapshots
JSONB, triggers de revisões, AuthenticatedActor, actor_identifier, authorize,
perfis locais e parsing limitado. Lacunas preenchidas: envelope durável, store,
consultas autorizadas, comparação RDF e restauração de conteúdo. Migração incremental
0003, sem modificar 0001/0002, sem backfill e sem reescrever JSON-LD histórico.

Plano executado: domínio e testes; persistência e migração; integração transacional;
histórico/comparação; permissões; PostgreSQL real e regressão; documentação.
A ausência de armazenamento editorial limita a integração da #27, explicitada abaixo.

## Proveniência

`Provenance(source, process, reason=None)` mantém os argumentos existentes e recebe
justificativa opcional não vazia. `Revision` agrega identidade UUID/URI persistida,
número positivo, created_at UTC, Provenance, perfil e actor_id opcional. Não duplicar
esses campos dentro de Provenance. Revisões novas conservam perfil e identidade;
instantes conscientes de timezone são normalizados para UTC. Não se aceita datetime
sem timezone nem número bool/zero/negativo no contrato de Revision.

| Informação | Local de recuperação |
| --- | --- |
| UUID/URI | Revision.identity, identidade armazenada do recurso |
| Origem/processo | Revision.provenance.source/process |
| Justificativa | Revision.provenance.reason, coluna nullable acrescentada por 0003 |
| Ator | Revision.actor_id; classificação de operações observadas no AuditEvent |
| Instante UTC/revisão | Revision.created_at/number |
| Perfil e release | Revision.profile, identificador exato da release local |

A release é resolvida deterministicamente por `load_legacy_profile(profile).release`:
`urn:libris:profile:monograph:v1` → 1.0 (adaptação local preservada);
`urn:libris:profile:monograph:v1:1` → 1.1;
`urn:libris:profile:authority:v1` → 1.0.
Perfis declarativos usam `load_profile_registry().resolve(release_id)` quando
adotados por seus serviços; BibliographicService continua com os três perfis anteriores.
Não interpretar sufixos arbitrariamente nem migrar perfis durante restauração.

Proveniência **técnica** descreve entrada e processamento. Proveniência **semântica**
é RDF fornecido pelo catalogador, como prov:wasDerivedFrom; segue no Graph/snapshot.
**Auditoria administrativa** registra operações observadas em tabela própria.
PROV-O não é automaticamente gerado a partir de eventos. A auditoria não acrescenta
triplas BIBFRAME nem metadados operacionais aos snapshots.

## Envelope de auditoria

`AuditEvent` é dataclass frozen, validada na construção; enums StrEnum fechados.
Identificadores de código permanecem em inglês; o contrato não aceita tipos de evento
arbitrários nem um dicionário genérico de claims/metadados.

| Campo | Obrigatoriedade e significado |
| --- | --- |
| event_id | UUID único da observação; PK impede sobrescrita |
| event_type | Um dos oito valores abaixo |
| identity | ResourceIdentity com UUID e URI persistida |
| revision_number | Inteiro positivo, FK à revisão relevante, inclusive em decisão editorial |
| occurred_at | Datetime com timezone, normalizado UTC |
| source/process | Origem e processo do evento, texto não vazio |
| profile | Release exata da revisão relevante; recuperada por FK, sem cópia redundante |
| actor_id/actor_type | Ambos ausentes quando desconhecidos, ou ambos presentes |
| reason | Opcional não vazia; obrigatória para retirada/substituição |
| previous_state/new_state | Par obrigatório para eventos editoriais; não aplicável a conteúdo/identidade |
| scope | record/candidate em transição editorial; ausente nas operações de conteúdo |
| previous_version/new_version | Versões editoriais positivas sequenciais em transição |
| related_resource_id | Sucessor UUID distinto, obrigatório somente em superseded, FK ao recurso |
| restoration_kind | content/editorial obrigatório somente em restored |
| source_revision | Revisão anterior do mesmo recurso, obrigatória somente em restored/content |

| Tipo | Significado e vínculo |
| --- | --- |
| record.created | Recurso e revisão inicial 1 criados |
| record.revised | Nova revisão de conteúdo, número >= 2 |
| record.submitted | draft → in_review; não cria snapshot |
| record.approved | in_review → approved; não cria snapshot |
| record.published | approved → published; não cria snapshot |
| record.withdrawn | published → withdrawn, justificativa; não cria snapshot |
| record.restored | content copia histórico como nova revisão; editorial republica withdrawn → published |
| record.superseded | Identidade substituída, sucessor distinto e justificativa; não presume equivalência RDF |

Eventos editoriais seguem os estados/escopos da #27, exigem humano autenticado e
versões sequenciais; retirada/republicação só têm scope=record. Eventos de conteúdo
não carregam estado editorial. Ator ausente não significa anonymous ou automated.
Validação rejeita datas ingênuas, revisão inválida, ator inconsistente, sucessor
igual ao recurso/ausente e combinações incompatíveis de restauração/estado.

## Persistência e transações

`experimental_semantic_audit_events` contém campos escalares tipados, timestamptz,
PK de evento, FK composta (resource_id, revision_number), FK composta opcional para
source_revision, FK do sucessor, CHECKs de taxonomia/atores/restauração/estados.
Não há FK a um usuário local fictício: o identificador OIDC é opaco e externo.
URI vem da identidade reservada e perfil vem da revisão imutável referenciada.
`AuditStore.append` confere também concordância exata de URI/perfil antes de inserir.

Índices (resource_id, occurred_at, event_id) e (resource_id, revision_number)
apoiam paginação e cobertura das revisões. Metadados são lidos com joins/projeções,
sem carregar documentos JSONB para listar eventos ou metadados das revisões.

`BibliographicService.create`: INSERT recurso, INSERT revisão 1, INSERT created,
commit único. `revise`: leitura, avanço CAS existente, validação/serialização,
INSERT revisão seguinte, INSERT revised, commit único. Falha em qualquer etapa
reverte tudo. Repositórios somente fazem flush; não controlam commit. CAS derrotado
não insere revisão ou evento. Actor/execution_actor são argumentos nomeados;
assinaturas e chamadas anteriores permanecem válidas.

Revisões mantêm a proteção preexistente contra UPDATE/DELETE. Eventos têm triggers
contra UPDATE/DELETE e TRUNCATE e não oferecem métodos de alteração/exclusão.
Inserção com event_id repetido falha, sem upsert. Essas garantias protegem DML normal;
proprietários/superusuários podem remover/desabilitar triggers, alterar esquema ou
restaurar backups. Não se promete prova criptográfica ou inviolabilidade diante de DBA.
A identidade não tem novo trigger de imutabilidade: reutiliza a garantia do serviço;
DML privilegiado fora dos serviços pode alterar a URI armazenada e afetar sua leitura.

A migração `0003_semantic_audit` sucede `0002_revision_actor`, acrescenta reason
nullable às revisões e cria a tabela vazia. Nenhum evento é fabricado para registros
antigos. Downgrade remove toda a auditoria e as justificativas, mantendo conteúdo,
atores e snapshots anteriores; é destrutivo e deve ser testado somente em banco
separado, vazio inicialmente e descartável. Aplicar upgrade explicitamente antes
de executar os serviços novos; não há migração automática no startup.

## Restauração e histórico

`restore_content(id, source_revision, expected_revision, provenance, actor=...)`
exige humano autenticado e metadata_revision:read/create. Recupera o snapshot
histórico pelo adaptador limitado, verifica perfil/identidade contra o corrente,
revalida seu conteúdo, usa o mesmo caminho CAS de revise e cria rN+1. A revisão
histórica é intocada. Proveniência/ator/instante são os da operação atual; não copia
autoria histórica. Registra **um** restored/content, source_revision explícita;
não registra revised adicional. Inclusive copiar rN corrente produz rN+1.

Restauração editorial não é cópia: a #27 revalida a revisão anteriormente publicada
e altera somente estado/versão editorial. O envelope suporta restored/editorial,
sem source_revision. A operação durável de republicação continua pendente do adaptador
editorial; restore_content não muda visibilidade nem aplica workflow inexistente.

`HistoryService` fornece read_revision(id, number=None), list_revisions,
list_events, read_event e compare_revisions. read_revision sem número identifica a
corrente; com número recupera o snapshot histórico proprietário. Leituras não mudam
current_revision. Proveniência vem de Revision; cada item da lista de revisões
inclui content_event_recorded. False significa ausência de observação durável,
compatível com legado, sem afirmar origem/ator desconhecidos como fatos positivos.

Revisões são ordenadas por número ascendente, cursor after_number exclusivo.
Eventos por occurred_at ascendente e event_id como desempate, cursor (datetime,UUID)
exclusivo. Limite default 100, máximo 200, mínimo 1. Recurso ausente é erro;
recurso legado existente pode ter lista de eventos vazia. read_event exige também
UUID do recurso, impedindo confusão entre históricos. Paginação não oferece um
snapshot global entre páginas; novos eventos podem aparecer durante a navegação.

## Comparação RDF

`compare_graphs(previous, current)` é puro e usa `rdflib.compare.to_isomorphic` e
`graph_diff`. Retorna SemanticDiff com tuplas imutáveis added/removed de RdfStatement,
com sujeito/predicado/objeto RdfTerm, kind iri/blank_node/literal, lexical, idioma
e datatype. Isomorfismo produz diff vazio, independentemente de ordem, serialização
ou nomes de blank nodes. Nenhum contexto/autoridade/ontologia é consultado na rede.

A canonicalização estrutural de cada grafo corresponde componentes isomórficos
por sua descrição, inclusive estruturas simétricas/cíclicas. Blank nodes não possuem
identidade persistente: alterar sua descrição pode mudar os rótulos canônicos de
todo o componente e incluir triplas de ligação no delta. O resultado é um delta
estrutural conservador, não necessariamente o conjunto mínimo de edições, nem uma
prova de que um nó interno continuou sendo o mesmo. Não usar rótulos para atualizar
snapshots. Custo de canonicalização em grafos simétricos pode ser alto; quotas e
benchmark de ingestão pública ficam para uma futura API.

A comparação histórica recebe revisões específicas do mesmo recurso, com snapshots
integrais. Não compõe autoridades/entidades usando suas revisões correntes nem chama
difflib. Normalizações de literal feitas pelo parser RDFLib mantêm os limites já
documentados de fidelidade semântica em vez de fidelidade textual de serialização.

## Autorização e privacidade

Humano vem exclusivamente de IdentityService/dependência OIDC validada.
`audit_actor` aceita AuthenticatedActor do servidor e confere seu identificador
contra actor_identifier(issuer, subject); não aceita dict de cliente. Isso detecta
inconsistências, mas não substitui autenticação: um objeto construído por código
confiável continua sendo uma fronteira de confiança. Rotas futuras devem usar a
dependência autenticada, nunca deserializar AuthenticatedActor de payload.

ExecutionActor é contexto interno configurado no servidor: ActorType service ou
automated, identificador `<tipo>:<nome>` com nome ASCII [a-z][a-z0-9_.-]{0,63}.
Human não é permitido nesse contexto; atores humano/técnico não podem coexistir
na mesma operação. Nenhuma identificação técnica é inferida de source/process.
Actor None conserva desconhecimento. Apenas identificador opaco/tipo persistem;
JWT, issuer, subject, claims, e-mail e senha não têm campos no envelope/tabela.
Source/process/reason são metadados autorais: não inserir segredos ou dados pessoais
nesses textos. Não se promete detectar automaticamente PII em texto livre.

| Consulta | Permissão | Papéis concedidos |
| --- | --- | --- |
| Revisões/comparação | metadata_revision:read | cataloger, reviewer, publisher, admin |
| Auditoria | metadata_audit:read (nova) | reviewer, publisher, admin |
| Restaurar conteúdo | metadata_revision:read e metadata_revision:create | cataloger, admin |

Leitor público e authority-manager isolado não recebem histórico. Catalogador não
recebe automaticamente auditoria administrativa. Papéis desconhecidos não concedem
nada; system:admin sozinho não é bypass. Autorizar antes de abrir sessão/consultar.
`BibliographicService.read` preserva o contrato de baixo nível para chamadores internos
confiáveis; não conectar esse método diretamente a rotas de histórico. Rotas futuras
usam HistoryService e a dependência OIDC. Não há exposição pública adicional.

## Integração editorial pendente

`editorial_event(prepared, revision, provenance, actor=...)` adapta o contrato existente
PreparedEditorialEvent, conservando instante, estados, escopo, versões, justificativa
e revisão selecionada. Confere identidade/ator/perfil e mapeia submit, approve,
publish, withdraw e republish. Prepara envelope; não escreve estado nem confirma evento.

O futuro adaptador EditorialTransaction deve obter a revisão relevante, usar esse
adaptador e chamar AuditStore.append **na mesma sessão/transação do CAS editorial**.
Não gravar envelopes preparados como se uma transição ainda não confirmada tivesse
ocorrido. BibliographicService continuará precisando da integração atômica de
prepare_content_revision quando a persistência editorial for adotada.

RETURN/ARCHIVE da #27 não têm correspondência correta nos oito eventos da #28:
revised implica revisão nova, withdrawn implica published → withdrawn, superseded
implica sucessor. O adaptador rejeita essas operações explicitamente. A integração
editorial completa requer extensão versionada/governada da taxonomia, migração
incremental de seus CHECKs e testes; não reinterpretar os oito tipos para escondê-las.
Substituição também exige futuro serviço de ciclo de identidade para validar sucessor
ativo/ausência de ciclos e atualizar metadados atomicamente. A FK atual garante
existência do sucessor, não seu estado ainda não persistido.

## Exemplos sintéticos

A representação abaixo ilustra recuperação do contrato, não um novo DTO HTTP.

```json
{
  "identity": {"internal_id":"00000000-0000-4000-8000-000000000001",
    "uri":"https://catalog.example.invalid/resources/00000000-0000-4000-8000-000000000001"},
  "number": 3,
  "created_at":"2026-10-12T20:00:00Z",
  "profile":"urn:libris:profile:monograph:v1:1",
  "provenance":{"source":"history:r1","process":"catalog:restore","reason":"Reverter teste"},
  "actor_id":"oidc:sha256:0000000000000000000000000000000000000000000000000000000000000000"
}
```

```json
{
  "event_id":"00000000-0000-4000-8000-000000000002",
  "event_type":"record.restored",
  "identity":{"internal_id":"00000000-0000-4000-8000-000000000001",
    "uri":"https://catalog.example.invalid/resources/00000000-0000-4000-8000-000000000001"},
  "revision_number":3,"source_revision":1,"restoration_kind":"content",
  "occurred_at":"2026-10-12T20:00:00Z","profile":"urn:libris:profile:monograph:v1:1",
  "source":"history:r1","process":"catalog:restore","reason":"Reverter teste",
  "actor_id":"oidc:sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "actor_type":"human"
}
```

Os exemplos representam a mesma restauração com hash sintético ilustrativo. Em execução, restore_content exige ator OIDC real do contexto;
a revisão nova e seu evento possuem o mesmo actor_id. Não usar esses exemplos para
fabricar autoria histórica ou enviar identidade humana por payload.
