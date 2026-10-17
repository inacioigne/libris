# Verificação M06.02 / issue #54 — 2026-10-17

Data local: 2026-10-17, America/Manaus. Relatório novo; evidências históricas
permanecem intactas. Implementação local da [issue #54](https://github.com/inacioigne/libris/issues/54),
acompanhamento [M06 #52](https://github.com/inacioigne/libris/issues/52).

## Contexto e diagnóstico

Checkout inicial: `main`, HEAD `c0be04b50d55d10c96c273b172204f984616b4c2`.
`git branch --show-current`, `git status --short` e `git diff --stat` executados
antes de editar: branch main, diretório de trabalho e índice limpos. Nenhuma
sincronização com origin/main. Issues #54 e seus comentários, #52, #47–#51,
#53 e #55 consultadas somente em leitura pelo conector GitHub. #54 aberta;
dependências M05 e #53 fechadas; #55 aberta. O estado foi confrontado com código
e testes, sem inferir aceite pela situação das issues.

Lidos AGENTS.md, READMEs, contratos/arquitetura solicitados, ADRs pertinentes
0008–0012/0015/0026–0029/0034/0036/0039, migrações 0001–0005, modelos/stores,
serviços e testes relevantes. Consultadas evidências históricas M05 de outubro,
inclusive regressões, EXPLAIN de listagens e consolidação M05.07. Esses resultados
anteriores não são contados como execução desta entrega.

Head inicial e final: **0005_web_auth**. Quatro tabelas catalográficas em public,
oito índices (incluindo PKs/UNIQUE), FKs/CHECKs, duas funções e três triggers de
imutabilidade. Sem enum SQL, sequences ou views catalográficas. Colunas, tipos,
nulabilidade, chaves, dependências, migrações, testes e funções M05 estão no
[inventário rastreável](catalogographic-persistence.md). A migração 0005 administra
somente libris_web e mantém dados no downgrade; tabelas temporárias de validação
não pertencem ao esquema catalográfico permanente.

Nomes físicos aparecem no ORM, migrações/SQL bruto de testes e documentação;
serviços/consultas M05 importam modelos. Não são campos de DTO, OpenAPI,
Problem Details ou identificadores RDF. Não foi encontrado problema funcional
que exigisse renomeação. A lacuna comprovada era a ausência de política explícita
de estabilização e de regressão conjunta 0004 ↔ 0005 com dados editoriais completos.

Riscos existentes: serialização conservadora pelo gate, custo JSONB sem benchmark
institucional, relações RDF sem FK SQL universal, identidade protegida pelo serviço,
triggers removíveis por administradores e downgrades históricos com perdas.
Ownership é propriedade de snapshot; heldBy é vínculo bibliográfico institucional,
sem coluna tenant/instituição administrativa ou concessão implícita de acesso.

## Decisão e implementação

**Alternativa A**: manter estrutura física como baseline operacional suportada,
com [ADR 0040](../decisions/0040-catalogographic-persistence-stabilization.md).
B (renomeação incremental) não resolve problema demonstrado e introduziria locks
DDL/coordenação de deploy; C (compatibilidade) adicionaria objetos sem consumidor
concreto. Nenhuma migração vazia, view, alias ou camada nova foi criada.

A política exige necessidade demonstrada, ADR para mudança estrutural, revisão
incremental a partir do head real, compatibilidade de deploy/contratos e evidência
PostgreSQL de preservação/reversão ou limite explícito. Mantém UUID/URI, JSONB,
perfis, snapshots, candidatos/publicação, CAS, histórico, eventos e autoria nula.
Não usa create_all, DDL no startup ou conversão/backfill retroativo.

A regressão ampliada reutiliza o banco exclusivo de test_editorial_migrations_postgres,
sem infraestrutura duplicada. Depois dos casos históricos 0003 ↔ head e recusa de
0004 → 0003 após RETURN, cria Organization, Subject, Work, Instance e Item por
BibliographicService e aplica transições pelos serviços existentes. Inclui vínculos
Work → Subject, Instance → Work, Item → Instance/heldBy → Organization,
identificador bf:Local, proveniência e auxiliares privados. Coexistem rascunho,
aprovado e publicado com candidata aprovada r2; r1 permanece pública.

Captura todas as colunas das quatro tabelas em ordem determinística, além de
constraints, índices e triggers pelos catálogos PostgreSQL. Compara antes/depois de
head idempotente, downgrade 0005 → 0004 e re-upgrade para head. Reabre engines e
sessões, lê identidades/perfis/proveniência, verifica eventos ordenados, ownership,
referências e isomorfismo dos grafos publicados/históricos. O legado criado em
0003 conserva ator nulo e eventos históricos repetidos, sem identidades fabricadas.
A contagem de testes não aumenta: um teste de migração existente foi ampliado.

Corrigida também uma corrida real do runner: pg_isready via socket podia observar
o servidor temporário da inicialização da imagem, que reinicia antes de createdb.
A espera passa a usar TCP em 127.0.0.1 dentro do container; somente o servidor
definitivo escuta nesse endereço. Mantidos isolamento, tmpfs, cleanup e recusa de skips.

Não há alteração de código de produção, contratos, autorização, frontend,
dependências ou migrações históricas. Correções ficam limitadas ao teste novo e
ao runner de integração e às referências técnicas que ainda tratavam todo o armazenamento como provisório.

## Ambiente, comandos e resultados

Python 3.13.15; uv 0.12.21; Node 24.16.0 já instalado via NVM; Docker Engine 29.8.2.
O sandbox impediu uv/Snap e acesso ao daemon inicialmente. Execuções fora dele
foram autorizadas pela revisão automática; não houve rejeição de aprovação.
Nenhuma ferramenta/dependência foi instalada ou lock alterado.

O runner scripts/test-postgres.sh foi lido antes da execução. Usa imagem local
postgres:17-bookworm, tmpfs em /var/lib/postgresql/data, porta dinâmica restrita a
127.0.0.1 e bancos novos libris_test, libris_audit_migration,
libris_editorial_migration e libris_web_migration. Limpa variáveis de URLs herdadas,
aplica head explicitamente no banco principal, exige bancos inicialmente vazios
nas migrações e remove somente seu container por ID no trap. Não usa volumes de
trabalho, SQLite ou docker compose down -v. JUnit rejeita qualquer skip da seleção.
Keycloak real permanece fora da seleção por marcador, sem ser apresentado como
integração comprovada nesta tarefa.

RESULTADOS_EM_CONSOLIDACAO

Os testes CAS/rollback são reutilizados, sem duplicar política ou enfraquecer asserts:

| Garantia | Evidência executável em tests/integration |
| --- | --- |
| Atualização correta, obsoleta e corrida sem atualização perdida | test_semantic_postgres; test_catalog_http_postgres::test_two_http_sessions_race_through_persistent_cas (cinco tipos) |
| Estado/conteúdo/auditoria revertidos em falha | test_catalog_http_postgres::test_http_transaction_failures_roll_back; test_editorial_postgres::test_transition_failures_roll_back_in_fresh_session; test_editorial_http_postgres::test_http_late_audit_failure_rolls_back_state_snapshot_and_event |
| Aprovação/publicação exatas e candidata isolada | test_editorial_http_postgres; test_catalog_listing_postgres::test_list_and_export_exact_published_revision; regressão ampliada editorial_migrations |
| UUID/URI, revisão independente e ator nulo | test_persistent_identifiers_postgres; test_entity_revisions_postgres; test_revision_actor_postgres; legado da regressão de migração |
| Auditoria imutável, FK e ordem de eventos | test_audit_postgres; test_audit_migrations_postgres; comparação de dados/catálogos na regressão ampliada |
| HTTP v1, RDF, RBAC e confidencialidade | test_catalog_acceptance_postgres; test_catalog_capabilities_postgres; test_catalog_http_postgres; test_catalog_listing_postgres |

## Matriz de critérios de aceite

MATRIZ_EM_CONSOLIDACAO

## Arquivos da entrega

| Arquivo | Estado / função |
| --- | --- |
| docs/decisions/0040-catalogographic-persistence-stabilization.md | Criado: alternativas, decisão, compatibilidade, riscos e evolução/reversão |
| docs/architecture/catalogographic-persistence.md | Criado: inventário físico, rastreabilidade, dependências, classificação e política |
| docs/architecture/catalogographic-persistence-m0602-verification-2026-10-17.md | Criado: este relatório datado |
| tests/integration/test_editorial_migrations_postgres.py | Modificado: dataset e comparação de dados/constraints/índices/triggers em 0004 ↔ 0005 |
| scripts/test-postgres.sh | Modificado: aguardar PostgreSQL definitivo por TCP, evitando a corrida de inicialização |
| README.md | Modificado: referência à baseline operacional |
| apps/api/README.md | Modificado: head e procedimento de regressão |
| docs/architecture/overview.md | Modificado: escopo da estabilização e cadeia Alembic |
| docs/architecture/catalogographic-contract.md | Modificado: status atual da persistência, sem mudar contrato v1 |
| docs/architecture/bibliographic-model.md | Modificado: distinguir origem experimental de estabilidade operacional |
| docs/architecture/editorial-persistence.md | Modificado: referência da baseline e da regressão |

Nenhum arquivo removido. Os três arquivos novos foram revisados separadamente,
pois não aparecem em git diff --stat sem staging. Relatórios históricos preservados.

## Conclusão e limites

CONCLUSAO_EM_CONSOLIDACAO

Inventário físico, localização operacional, circulação/empréstimos, reservas,
multas, aquisições e disponibilidade continuam futuros, separados de bf:Item.
Não são modeladas tabelas antecipadas. Permanecem decisões sobre perfis/domínio
público institucionais, fusão/tombstones, retenção/grants/backup, tenancy, carga e
consistência/outbox antes da primeira integração Elasticsearch.

Downgrade 0005 → 0004 preserva catálogo e BFF; isso não autoriza downgrade de
trabalho: 0004 → 0003 perde estado e recusa RETURN/ARCHIVE; 0003 perde auditoria/
reason; 0002 perde ator; 0001 remove conteúdo. Nenhuma promessa de recuperação
integral ou segurança de produção deriva da cadeia histórica.

GIT_EM_CONSOLIDACAO
