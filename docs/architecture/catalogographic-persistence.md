# Persistência catalográfica — baseline operacional M06.02

Decisão: [ADR 0040](../decisions/0040-catalogographic-persistence-stabilization.md).
Os quatro nomes `experimental_semantic_*` são nomes físicos históricos suportados
para M03–M05. Sua origem experimental não exige substituição para novos consumidores
dos contratos atuais. A baseline é operacional no escopo testado; não define o
esquema bibliográfico definitivo nem homologa perfis, produção ou escala institucional.
[Execução e critérios da #54](catalogographic-persistence-m0602-verification-2026-10-17.md).

## Inventário físico e rastreabilidade

Todos os objetos catalográficos ficam em public. Caminhos de código abaixo relativos
a apps/api/src/libris/modules/bibliographic. Testes relativos a tests/integration;
nomes abreviados na matriz sempre designam test_*.py. Repositórios não fazem commit.

| Tabela | Modelo / arquivo infrastructure | Store e serviços application | Revisões Alembic | Testes / funcionalidade M05 |
| --- | --- | --- | --- | --- |
| experimental_semantic_resources | SemanticResource / persistence.py | RevisionStore; BibliographicService, CatalogService, RelationshipService; PostgresReferenceResolver; catalog_query | 0001 | persistent_identifiers_postgres, entity_revisions_postgres, catalog_http_postgres, catalog_listing_postgres; identidade, CRUD, relações e filtros |
| experimental_semantic_revisions | SemanticRevision / persistence.py | RevisionStore; BibliographicService, CatalogService, HistoryService, CatalogEditorialService; catalog_query | 0001; actor_id 0002; reason 0003 | semantic_postgres, revision_actor_postgres, catalog_acceptance_postgres, editorial_http_postgres; snapshots, PATCH, exportação e histórico |
| experimental_semantic_audit_events | SemanticAuditEvent / audit.py | AuditStore; BibliographicService, PostgresEditorialTransaction, HistoryService | 0003; taxonomia/CHECKs e índice parcial 0004 | audit_postgres, audit_migrations_postgres, editorial_http_postgres; eventos e atomicidade |
| experimental_semantic_editorial_states | SemanticEditorialState / editorial.py | EditorialStore; BibliographicService, PostgresEditorialTransactions, EditorialService, HistoryService; catalog_query | 0004 | editorial_postgres, editorial_migrations_postgres, catalog_listing_postgres; estados, candidata/publicação e CAS |

CatalogService especializa BibliographicService, sem duplicar o protocolo de
persistência. CatalogEditorialService adapta serviços de editorial/histórico à
superfície HTTP; list_catalog e infrastructure/catalog_query.py projetam uma página
num statement MVCC. Os serviços reutilizam os validadores, perfis e autorização.

### Colunas, chaves e referências

`uuid`, `integer`, `varchar`, `jsonb` e `timestamptz` abaixo são tipos PostgreSQL;
SQLAlchemy Uuid/DateTime(timezone=True) recebem esses tipos no dialeto real.
Nulabilidade explicitada: todas obrigatórias salvo as marcadas `NULL`. Não há
default de servidor, identidade automática ou sequence nesses quatro modelos.

| Tabela (sufixo) | Colunas e tipos | PK / unicidade / FKs |
| --- | --- | --- |
| resources | id uuid; uri varchar; current_revision integer | PK(id); UNIQUE(uri); fk_semantic_current (id,current_revision) → revisions(resource_id,number), DEFERRABLE INITIALLY DEFERRED |
| revisions | resource_id uuid; number integer; document jsonb; created_at timestamptz; source/process/profile varchar; actor_id/reason varchar NULL | PK(resource_id,number); FK(resource_id) → resources(id) |
| editorial_states | resource_id uuid; editorial_state varchar; version/current_revision integer; approved_revision/published_revision integer NULL; candidate_state varchar NULL | PK(resource_id); três FKs (resource_id,ponteiro) → revisions(resource_id,number): fk_editorial_current_revision, fk_editorial_approved_revision, fk_editorial_published_revision |
| audit_events | event_id/resource_id uuid; event_type varchar; revision_number integer; occurred_at timestamptz; source/process varchar; actor_id/actor_type/reason/previous_state/new_state/restoration_kind/scope varchar NULL; related_resource_id uuid NULL; source_revision/previous_version/new_version integer NULL | PK(event_id); fk_audit_revision (resource_id,revision_number) → revisions; fk_audit_source_revision (resource_id,source_revision) → revisions; fk_audit_successor (related_resource_id) → resources(id) |

As FKs não possuem cascata de exclusão. O ciclo resources ↔ revisions é resolvido
pela FK corrente diferida: o snapshot precisa existir no commit, não no primeiro
flush. FKs editoriais garantem que os ponteiros pertencem ao mesmo recurso; o
protocolo transacional mantém current_revision do estado e do recurso concordantes.
Não há relationship ORM com cascade nem tabelas independentes de Work/Instance/Item.

### Constraints, índices e objetos auxiliares

| Objeto | Regra / finalidade |
| --- | --- |
| ck_semantic_current_positive / ck_semantic_revision_positive | Revisões positivas |
| ck_semantic_document_array | JSONB expandido deve ser array; não prova validade semântica |
| ck_semantic_source / ck_semantic_process | Fonte/processo não vazios |
| ck_editorial_positive / ck_editorial_state | Versão/revisão positivas; seis estados fechados |
| ck_editorial_pointers / ck_editorial_public | Ponteiros entre 1 e corrente; publicação exigida para published/withdrawn/archived e ausente nos estados iniciais |
| ck_editorial_candidate / ck_editorial_approval | Candidata draft/in_review/approved apenas em published/withdrawn e distinta da publicada; aprovação ligada à revisão selecionada, removida para rascunho/revisão |
| ck_audit_type / ck_audit_revision | Dez eventos governados; created r1, revised r>1 |
| ck_audit_source / ck_audit_reason | Fonte/processo não vazios; razão ausente ou não vazia |
| ck_audit_actor | Identificador/tipo ambos nulos ou par válido human/service/automated |
| ck_audit_successor | Sucessor distinto e razão somente em superseded |
| ck_audit_restore | Restauração content aponta revisão anterior; editorial não copia snapshot |
| ck_audit_states | Conteúdo sem estados/versões; transições com estados, escopo e versões sequenciais e ator humano, conforme a máquina |
| PKs e UNIQUE(uri) | Cinco índices B-tree implícitos: quatro PKs e unicidade URI |
| ix_audit_resource_time | (resource_id,occurred_at,event_id), B-tree; histórico ordenado e cursor |
| ix_audit_resource_revision | (resource_id,revision_number), B-tree; eventos por revisão |
| ix_audit_editorial_version | (resource_id,new_version), B-tree parcial WHERE new_version IS NOT NULL; não UNIQUE |
| libris_reject_revision_mutation / immutable_semantic_revision | Função PL/pgSQL e trigger BEFORE UPDATE OR DELETE por linha, 0001 |
| libris_reject_audit_mutation / immutable_semantic_audit | Função PL/pgSQL e trigger BEFORE UPDATE OR DELETE por linha, 0003 |
| immutable_semantic_audit_truncate | BEFORE TRUNCATE por statement, mesma função de rejeição, 0003 |

São oito índices catalográficos no total. Não há enum PostgreSQL (estados/eventos
são varchar + CHECK; domínio usa StrEnum), view, sequence, alias, índice GIN ou
tabela de triplas. Revisões não têm trigger de TRUNCATE; auditoria tem. Triggers
não garantem inviolabilidade perante donos/superusuários. Não há trigger para
imutabilidade de URI; esta garantia é do serviço, sem API de reassociação.

### Ownership, instituições e identificadores

Propriedade é semântica: snapshot com raiz da entidade e auxiliares privados
(blank nodes ou URI-raiz#fragmento), validado por infrastructure/ownership.py.
Não existe tabela/coluna tenant, organization_id ou ownership institucional.
`bf:heldBy` é referência RDF a bf:Organization, validada no serviço; não é concessão
de acesso nem localização física. UUID/URI residem em resources e são reutilizados
nas leituras/revisões, independentemente de RESOURCE_BASE_URI atual.

ISBN, identificadores locais e fontes permanecem nós bf:Identifier/Local/Isbn no
JSONB do proprietário. Não são PK, sequência ou unicidade global de ISBN/barcode.
Tipo bibliográfico reside no RDF da raiz; relacionamentos entre entidades são
URIs nos snapshots, sem FK automática dentro do JSONB. A revisão guarda perfil
exato, instante, fonte/processo, reason e ator opcional; auditoria recupera URI e
perfil por joins, sem duplicá-los em colunas de evento.

## Migrações e limites de reversão

| Revision → down_revision | Alteração | Downgrade histórico |
| --- | --- | --- |
| 0001_semantic → None | Recursos/revisões, FK corrente diferida e trigger | Apaga recursos/snapshots; somente descartável |
| 0002_revision_actor → 0001_semantic | actor_id nullable, sem autoria retroativa | Remove actor_id |
| 0003_semantic_audit → 0002_revision_actor | reason nullable, auditoria/índices/triggers | Apaga auditoria e reason |
| 0004_semantic_editorial → 0003_semantic_audit | Estado/FKs/CHECKs, RETURN/ARCHIVE e índice parcial | Remove metadados editoriais; recusa novos eventos incompatíveis atomicamente |
| 0005_web_auth → 0004_semantic_editorial | Cria/adota libris_web.auth_transactions/sessions/auth_quotas; valida drift | Mantém schema/dados web; não altera catálogo |

0005 tem PK/CHECKs e índices de expiração próprios do BFF, sem FKs ao catálogo e
sem modelo ORM bibliográfico. As tabelas temporárias libris_expected_* da validação
são ON COMMIT DROP. Não são estruturas catalográficas permanentes.

A regressão em editorial_migrations_postgres usa seu banco exclusivo inicialmente
vazio: legado 0003 com actor_id nulo/eventos repetidos, upgrade head, downgrade
0003 compatível, re-upgrade e recusa de downgrade após RETURN; depois acrescenta
cinco entidades relacionadas e compara todas as colunas das quatro tabelas em
head idempotente e 0005 → 0004 → head. Lê snapshots por isomorfismo, publicação r1,
candidata r2 aprovada, referências, proveniência e eventos ordenados. O teste web
existente cobre adoção e reversão dos dados BFF. Esses testes não autorizam executar
downgrades em bases de trabalho nem tornam reversíveis as perdas históricas.

## Dependências físicas versus contratos públicos

| Consumidor | Dependência real / risco de renomeação |
| --- | --- |
| ORM | Nomes em infrastructure/persistence.py, editorial.py, audit.py e FKs literais; renomear exige alinhamento de versões |
| Migrações | SQL bruto e DDL congelado 0001–0004; preservar histórico; nova revisão se mudança comprovada |
| Serviços e consultas M05 | Importam modelos em catalog, catalog_relationships, editorial_postgres e catalog_query; não expõem tablename; query JSONB depende da estrutura do snapshot |
| Integração/fixtures | SQL bruto em audit_migrations, audit, catalog_capabilities, catalog_http, editorial_migrations, editorial e semantic_postgres; fixtures RDF/DTO não usam nomes físicos |
| Scripts | Runner usa Alembic e URLs exclusivas; geradores usam contratos, sem consumidor de nomes físicos |
| Documentos | ADRs 0008/0028, contrato, identificadores, auditoria, persistência editorial, security-audit e plano/evidências M05.06 registram os nomes; evidências históricas não se reescrevem |
| Público | DTOs, OpenAPI v1, RDF/JSON-LD, Problem Details e diagnósticos usam identidades/revisões sem nomes SQL; nenhuma camada de compatibilidade necessária |

Busca reproduzível: `rg -n 'experimental_semantic_' apps scripts tests docs` e
`rg -n 'SemanticResource|SemanticRevision|SemanticEditorialState|SemanticAuditEvent' apps tests`.
Uma alteração de nomes exigiria atualizar dependências ativas, coordenar runtime
antigo/novo e verificar constraints/índices/triggers/rollback; o prefixo não produz
problema funcional comprovado que compense esse custo agora.

## Classificação de estabilidade e evolução

| Componente | Classificação / ressalva |
| --- | --- |
| Identidade, revisões, snapshots, CAS, estados e auditoria M03–M05 pelos serviços | Operacionalmente estáveis no escopo das regressões reais; política incremental do ADR 0040 |
| Gate transacional, consultas JSONB e índices | Estáveis com ressalvas de paralelismo e volume; medir antes de evoluir |
| Ownership e referências locais | Estáveis com ressalvas: protocolo dos serviços, registro de relações e publicação validada; SQL arbitrário e fontes externas fora da garantia |
| Perfil experimental legado e grafos agregados | Experimentais semanticamente; históricos preservados, sem publicação/conversão automática |
| Perfis institucionais, URI pública, retenção, tombstones/fusão | Dependentes de decisões futuras; releases históricas não mudam |
| Inventário/circulação/aquisições, tenancy, busca e outbox | Domínios/decisões futuros, sem tabelas antecipadas |

A política exige necessidade demonstrada, ADR estrutural, revisão Alembic incremental,
compatibilidade de deploy, dados representativos e teste real upgrade/downgrade ou
limite explícito com recuperação progressiva. Não alterar histórico nem executar
DDL no startup. Contratos v1 seguem ADR 0029; dados continuam no PostgreSQL.

`bf:Item` descreve bibliograficamente uma cópia; inventário físico, localização
operacional, empréstimos, reservas, multas, aquisições e disponibilidade terão
identidades e contratos próprios. Não atualizar revisão bibliográfica para cada
transação operacional nem acessar diretamente tabelas de outro módulo.

## Verificação reproduzível

Na raiz: `bash scripts/test-postgres.sh` prepara PostgreSQL real em tmpfs, porta
loopback dinâmica e quatro bancos exclusivos. O runner aplica head explicitamente,
executa integração sem Keycloak e recusa skips; remove somente seu container.
`bash scripts/check.sh` verifica contratos/OpenAPI, API, lint, mypy, web e Compose.
Resultados desta execução no [relatório datado](catalogographic-persistence-m0602-verification-2026-10-17.md).
