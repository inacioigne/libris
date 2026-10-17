# Persistência editorial PostgreSQL — issue #43

A [baseline M06.02](catalogographic-persistence.md) consolida o inventário físico,
a rastreabilidade e a política de evolução destes mecanismos. O
[ADR 0040](../decisions/0040-catalogographic-persistence-stabilization.md) preserva
os nomes históricos e os contratos transacionais abaixo, sem nova migração.
O head efetivo é `0005_web_auth`; a regressão ampliada verifica sua reversão para
0004 e re-upgrade com revisões, candidata/publicação, instituições e eventos.

Implementação interna da [issue #43](https://github.com/inacioigne/libris/issues/43),
com os contratos das #27/#28. Decisão: [ADR 0028](../decisions/0028-editorial-transactions.md).
Não acrescenta rotas, editor, indexação, circulação ou esquema bibliográfico definitivo.

## Modelo e instalação

Aplicar explicitamente `uv run alembic upgrade head`, antes de executar os serviços
atualizados. Nenhuma migração executa no startup. `0004_semantic_editorial` sucede
`0003_semantic_audit`; não modifica 0001–0003, JSON-LD, UUID/URI ou releases de perfil.

`experimental_semantic_editorial_states` contém uma linha por recurso, PK resource_id,
estado, versão editorial, revisão corrente, aprovada, publicada e estado candidato.
Cada ponteiro tem FK composta para a revisão do mesmo recurso. CHECKs rejeitam
estados, versões, candidatas e aprovações inconsistentes. A PK serve às leituras e
atualizações por recurso; os índices de auditoria permitem histórico cronológico,
por revisão e por versão editorial. Não há estado editorial dentro do RDF.

`candidate_revision` é derivada: current_revision quando candidate_state existe,
None caso contrário. Não existe um segundo número de candidata que possa divergir.
Transições incrementam version sem criar revisões; conteúdo incrementa ambos.

Legado permanece **sem estado editorial observado** após a migração. Leitura interna
retorna state=None e nunca inicializa registros. Uma primeira escrita válida bloqueia
a identidade e inicializa draft/version=1 sobre a revisão corrente, na mesma transação
da operação. Autorização, CAS ou validação negados revertem essa inicialização.
Nenhum evento created, aprovação ou publicação retrospectivos é fabricado.
Eventos antigos não são utilizados para reconstruir um estado que nunca foi persistido.

## Unidade transacional e CAS

BibliographicService conserva suas operações e RevisionStore/AuditStore. Stores fazem
flush; somente o context manager session.begin confirma/reverte. Criação salva
identidade, snapshot r1, draft e created. Revisão/restauração salva CAS de conteúdo,
novo snapshot, prepare_content_revision, CAS editorial e revised/restored no mesmo commit.

PostgresEditorialTransactions fornece o adaptador de EditorialTransaction.
EditorialService verifica versão e revisão, permissões, seleção e validação, prepara
a máquina existente, chama UPDATE condicional por resource_id/version/current_revision
e AuditStore.append. Falha de qualquer etapa, inserção ou commit reverte tudo.
UPDATE sem linha retornada gera editorial.version_stale. O CAS de RevisionStore
continua sendo UPDATE condicional; não há observação em memória como única proteção.
O adaptador reconsulta a revisão corrente persistida antes de gravar a decisão.

Ordem de bloqueios: **gate transacional PostgreSQL → recurso → dependências locais**.
Todas as escritas de conteúdo adquirem pg_advisory_xact_lock_shared com chave fixa
0x4C4942524953 antes do FOR UPDATE da identidade. Decisões editoriais adquirem o
mesmo gate em modo exclusivo antes de ler/inicializar estado e validar conteúdo.
Assim, decisões esperam os escritores existentes; nenhuma revisão, criação local
ou outra transição pelo serviço atravessa a janela de validação até o commit.
Não há upgrade de shared para exclusive. Publicações cruzadas não mantêm locks de
origens diferentes esperando dependências: apenas uma decisão possui o gate exclusivo.
Resolvedores também mantêm FOR KEY SHARE nas identidades locais consultadas.

O gate tem alcance bibliográfico no banco e é deliberadamente conservador nesta
fase experimental: transições serializam e bloqueiam temporariamente escritas de
outros registros. Escritores de conteúdo de registros diferentes podem concorrer.
Não é lock de processo nem depende de Elasticsearch. A garantia pressupõe que as
escritas operacionais usem esses serviços; SQL privilegiado/adaptadores que ignorem
o protocolo não recebem a garantia de validação transacional. Snapshots e eventos
continuam protegidos pelos triggers preexistentes, dentro de seus limites administrativos.

Novos consumidores de revise/restore_content podem passar expected_editorial_version
junto de expected_revision. A assinatura histórica continua funcionando: lê a versão
sob bloqueio, aplica a política atual e faz ambos os CAS na transação. Esse modo
conserva o contrato de conteúdo anterior; não detecta uma mudança editorial já
concluída antes da chamada quando ela não informa sua expectativa editorial.
Transições sempre exigem explicitamente as duas expectativas.

## Publicação, relações e visibilidade

Publicar usa a revisão **aprovada exata**, nunca max(number). Republicar usa a revisão
anteriormente publicada, revalidada, mesmo com candidata pendente. UUID/URI não mudam.
check_snapshot, perfil/release local, validate_catalog/SHACL e validate_references
continuam sendo os validadores existentes. Diagnósticos SHACL acompanham a rejeição.
Não há resolução de contextos/imports remotos nem mutação de shapes históricas.

O contexto concreto percorre os caminhos do registro de relacionamentos, inclusive
Contribution/Publication, papéis e auxiliares. Uma URI encontrada no PostgreSQL é
local pela identidade armazenada; seu tipo é resolvido pelo snapshot proprietário.
URI ausente **não vira externa por prefixo**: exige classificação explícita em
external_references, configuração confiável do servidor. Sem classificação, publicação
é rejeitada. UUID, URI, tipo, cobertura de vínculos RDF e regras como heldBy/Organization
são conferidos. Fechos locais de relações acíclicas são percorridos e validate_cycles
rejeita ciclos. As cabeças locais consultadas ficam estáveis pelo gate até o commit.

Classificação externa indica uma referência pendente, não verificação remota ou
existência comprovada. Não se oferece consistência transacional para mudanças nas
fontes externas nem ausência de ciclos que atravessem fontes externas. Propriedades
semânticas fora do registro não recebem afirmação de integridade de relacionamento;
a evolução governada desse registro continua necessária para novos contratos.

read_public é leitura interna confiável: sob bloqueio seleciona public_revision e
recupera exatamente esse snapshot. Draft, in_review, approved, withdrawn, archived e
legado sem estado retornam None. Edição de published cria/atualiza candidata draft,
conserva a revisão pública anterior e remove a aprovação da candidata. Submissão/
aprovação da candidata também não muda visibilidade. Edição em revisão/aprovação
exige RETURN; withdrawn/archived recusam revisão segundo a política da #27.
Os cinco tipos Work/Instance/Item/Agent/Subject usam os perfis já suportados pelo serviço.

## Auditoria, restauração e consulta

Cada transição efetiva grava um envelope existente AuditEvent. Provenance da decisão
vem da configuração interna source/process; ator humano é o AuthenticatedActor do
OIDC. O adaptador valida o identificador derivado de issuer/sub; nunca recebe actor_id
humano separado. A política editorial requer humanos; service/automated continuam
contextos explícitos para conteúdo, sem inventar humano para o legado desconhecido.
Não há bypass por system:admin nem JWT/claims persistidos.

| Operação | Evento | Semântica |
| --- | --- | --- |
| SUBMIT | record.submitted | draft → in_review, revisão específica |
| APPROVE | record.approved | in_review → approved, revisão corrente específica |
| PUBLISH | record.published | approved → published, candidata ou registro |
| WITHDRAW | record.withdrawn | published → withdrawn, justificativa |
| REPUBLISH | record.restored / editorial | withdrawn → published, nova validação |
| RETURN | record.returned | in_review/approved → draft; justificativa; remove aprovação |
| ARCHIVE | record.archived | withdrawn → archived; justificativa; encerra candidata |

Migração amplia ck_audit_type/ck_audit_states, preservando os oito tipos históricos.
Eventos RETURN/ARCHIVE não são revised/withdrawn/superseded. Uma tentativa repetida
com token antigo falha no CAS; com estado atual falha na matriz se a aresta não existe.
Não há deduplicação artificial: exatamente um append por transição confirmada,
protegido por CAS/commit. Envelopes históricos repetidos permitidos pela #28 permanecem
legíveis; o índice de versão não impõe unicidade retrospectiva.

restore_content copia um snapshot proprietário histórico como rN+1, aplica a mesma
política/CAS e grava restored/content com source_revision. Não publica. Restauração
editorial é a aresta autorizada REPUBLISH, restored/editorial, sem copiar conteúdo.
Retirada/arquivamento não apagam identidade ou revisões. O ciclo discontinued/replaced/
merged continua sendo o contrato independente da identidade; #43 não inventa seu
armazenamento, serviço de fusão, redirecionamentos ou exclusão física.

HistoryService.read_editorial exige metadata_audit:read e metadata_revision:read.
Retorna estado persistido (ou ausência explícita), revisão corrente/proveniência e
página de eventos no mesmo bloqueio de recurso. Eventos ordenam por occurred_at/event_id;
limit/after reutilizam a paginação existente. PreparedEditorialEvent não é histórico:
a consulta somente lê AuditStore. list_events/read_event/read_revision permanecem disponíveis.

Exemplo interno (actor é obtido previamente pela dependência autenticada):

```python
transactions = PostgresEditorialTransactions(
    sessions, actor=actor, provenance=Provenance("catalog", "editorial:decision")
)
editorial = EditorialService(transactions)
await editorial.transition(
    identifier, "in_review", actor=actor,
    expected_version=1, expected_current_revision=1, selected_revision=1,
)
view = await HistoryService(sessions).read_editorial(identifier, actor=actor)
```

## Migrações, testes e limites

Downgrade 0004→0003 remove o estado editorial e o índice novo; perde seus metadados.
Rejeita integralmente se houver record.returned/record.archived: não descarta evidência
nem a reinterpreta para caber na taxonomia antiga. Somente usar em banco descartável.

Suíte comum não exige bancos. Integração é separada, PostgreSQL real:

```bash
cd apps/api
uv run pytest
uv run ruff check . ../../tests
uv run mypy src
uv run alembic heads
uv run alembic upgrade head --sql
# DATABASE_URL: banco descartável; aplicar head antes de integrar.
uv run alembic upgrade head
uv run alembic check
# TEST_DATABASE_URL: banco de integração migrado.
# TEST_MIGRATION_DATABASE_URL: outro banco descartável inicialmente vazio (#28).
# TEST_EDITORIAL_MIGRATION_DATABASE_URL: terceiro banco inicialmente vazio (#43).
uv run pytest -c pyproject.toml ../../tests/integration -m integration
# Na raiz: bash scripts/check.sh
```

Não usar URLs de dados de trabalho para migrações destrutivas. Sem URLs, os testes
respectivos são pulados. Relatório: [evidências da #43](editorial-persistence-verification.md).
Sem homologação institucional, prontidão de produção, frontend ou APIs CRUD públicas.

## Integração HTTP M05.03 / #47

[POST/GET/PATCH catalográficos](catalogographic-http.md) reutilizam estes stores,
guard, política e passos transacionais por `CatalogService`, especialização de
BibliographicService. Não abrem transações em torno de serviços já transacionais.
A leitura corrente recupera snapshot e versão editorial coerentes, sem exigir
permissão de auditoria nem inicializar legado. O ETag vincula essa visão às duas
expectativas do PATCH. Histórico continua em HistoryService, sem endpoint novo.

Escritas DTO resolvem referências locais na mesma transação. Para evitar locks
cruzados de origens/dependências, adquirem o gate **exclusivo** já existente antes
do recurso; leituras correntes usam shared. Escritas internas Graph mantêm o
protocolo descrito acima. Decisão e custo de serialização no
[ADR 0036](../decisions/0036-catalog-http-concurrency.md). Nenhuma migração nova.
[Evidências próprias da #47](catalogographic-m0503-verification-2026-10-16.md).

## Adaptadores HTTP M05.05

A #49 expõe os serviços existentes por [rotas editoriais e histórico v1](catalogographic-editorial-http.md).
Comandos literais incluem republish e usam ETag de edição como ambas as expectativas
CAS, preservando estado/evento no mesmo commit. Leitura pública usa read_public;
restauração continua criando conteúdo candidato. Nenhum schema/migração foi alterado.
[Evidências desta execução](catalogographic-m0505-verification-2026-10-16.md).
