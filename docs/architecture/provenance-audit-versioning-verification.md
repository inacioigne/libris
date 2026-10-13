# Verificação — M03.04.02 / issue #28

Relatório em português da entrega de
[proveniência, auditoria e versionamento](provenance-audit-versioning.md).
Data de referência do cliente: 2026-10-12. Python executado: 3.13.15.
[ADR 0027](../decisions/0027-provenance-audit-versioning.md).

## Resumo executivo

Implementados eventos imutáveis e duráveis para criação/revisão/restauração de
conteúdo, na mesma transação do recurso/CAS/snapshot; contratos dos oito tipos,
atores conhecidos/desconhecidos, consultas internas autorizadas e comparação RDF.
Migração incremental preserva legado e não cria observações retrospectivas.
Nenhuma nova dependência, rota, API de editor, interface, branch ou commit.

A #27 já contém política editorial, mas não armazenamento concreto. Esta entrega
adapta seus eventos preparados; a gravação de estado editorial e auditoria no mesmo
CAS permanece dependente do adaptador futuro. RETURN/ARCHIVE exigem extensão
governada da taxonomia. Não se declara workflow editorial durável concluído.

## Arquivos e responsabilidades

| Arquivo (relativo à raiz) | Estado | Responsabilidade |
| --- | --- | --- |
| apps/api/src/libris/modules/bibliographic/domain/audit.py | Novo | Taxonomia fechada, envelope frozen, atores técnicos e validação |
| apps/api/src/libris/modules/bibliographic/domain/models.py | Alterado | Provenance.reason opcional, invariantes de Revision, limite de histórico |
| apps/api/src/libris/modules/bibliographic/application/audit.py | Novo | Seleção de ator confiável, envelope de conteúdo e adaptação da #27 |
| apps/api/src/libris/modules/bibliographic/application/service.py | Alterado | Eventos no commit, mesmo CAS e restauração de conteúdo |
| apps/api/src/libris/modules/bibliographic/application/history.py | Novo | Autorização e coordenação de consultas/comparação histórica |
| apps/api/src/libris/modules/bibliographic/application/comparison.py | Novo | Delta RDF puro, com termos estruturados e isomorfismo |
| apps/api/src/libris/modules/bibliographic/infrastructure/audit.py | Novo | ORM/store append-only, consultas e cobertura de revisões |
| apps/api/src/libris/modules/bibliographic/infrastructure/persistence.py | Alterado | Justificativa nullable e listagem de metadados de revisões |
| apps/api/migrations/versions/0003_semantic_audit.py | Novo | Tabela experimental, FKs, CHECKs, índices e triggers |
| apps/api/migrations/env.py | Alterado | Inclusão do ORM de auditoria no metadata Alembic |
| apps/api/src/libris/modules/identity/domain/permissions.py | Alterado | metadata_audit:read |
| apps/api/src/libris/modules/identity/infrastructure/role_mapper.py | Alterado | Concessão explícita a reviewer/publisher/admin |
| tests/api/test_audit_history.py | Novo | 100 casos unitários de contrato/RDF/permissões |
| tests/api/test_semantic_extensions.py | Alterado | Double do novo store e asserções de evento sem perder extensão RDF |
| tests/integration/test_audit_postgres.py | Novo | Transações, CAS real, restauração, paginação, integridade e triggers |
| tests/integration/test_audit_migrations_postgres.py | Novo | Upgrade legado e downgrade em outro banco descartável |
| docs/architecture/provenance-audit-versioning.md | Novo | Contrato, exemplos, compatibilidade e limites |
| docs/architecture/provenance-audit-versioning-verification.md | Novo | Evidências e matriz de aceite |
| docs/decisions/0027-provenance-audit-versioning.md | Novo | Decisão estrutural incremental |
| docs/architecture/identity.md | Alterado | Política de leitura administrativa e atores técnicos |
| docs/architecture/editorial-lifecycle.md | Alterado | Integração preparada e dependências explícitas |
| README.md | Alterado | Referências da entrega e migração atual |

Migrações 0001/0002, recursos de perfil/SHACL/contexto, DTOs HTTP, frontend e locks
permanecem sem alterações. A modificação de teste preexistente conserva as asserções
originais de perfil, conteúdo RDF e extensão DCTERMS.

## Contratos, persistência e compatibilidade

Provenance mantém source/process e acrescenta reason opcional. Revision conserva
UUID/URI, UTC, número, perfil e ator opcional; release é resolvida deterministicamente
pelo artefato local, sem duplicação. AuditEvent tem PK UUID, tipo fechado, recurso,
revisão, instante, origem/processo, ator/tipo opcionais e metadados aplicáveis.
Estados/versões somente aparecem em eventos editoriais; restored/content exige origem
histórica e nova revisão; restored/editorial não copia conteúdo.

0003_semantic_audit sucede 0002_revision_actor e cria uma cadeia única. FK de revisão
é obrigatória, FK de origem histórica e sucessor são condicionais. CHECKs rejeitam
combinações inválidas. Triggers impedem UPDATE/DELETE/TRUNCATE de eventos; PK impede
reutilização de ID. Stores não dão commit, e falha na inserção/validação reverte CAS,
revisão e evento. Downgrade perde toda a auditoria e justificativas; somente foi
executado no segundo banco descartável, inicialmente vazio.

Legado criado sob 0002 conserva exatamente JSONB, timestamp, source/process, perfil
e NULL de ator após upgrade, downgrade 0003→0002 e upgrade. Reason fica NULL e
lista de eventos vazia; listagem informa content_event_recorded=False. Não há backfill.
CAS concorrente, revisões sequenciais, UUID/URI estáveis e perfis são verificáveis.
Restauração não altera revisões anteriores nem publica conteúdo silenciosamente.

## Comandos e evidências

Todos os testes PostgreSQL usam container postgres:17-bookworm criado nesta sessão,
sem volumes, em 127.0.0.1:55448. Banco libris_test é de integração; outro banco,
libris_migration_test, começa vazio e recebe exclusivamente o teste destrutivo.
Não foi acessado banco de desenvolvimento/produção nem usado SQLite. O container
descartável foi removido após os testes; os bancos de trabalho não foram alterados.

| Comando | Resultado observado |
| --- | --- |
| uv sync --locked | Passou; 83 pacotes resolvidos, 82 verificados; locks inalterados |
| uv run pytest (execução final, via check.sh) | 1.170 passaram, nenhuma falha; 389 avisos |
| uv run pytest -q (primeira execução completa) | 1.159 passaram, 1 falhou no double preexistente sem audit store; corrigido |
| uv run pytest -q tests novos + regressão específica | 101 passaram (100 novos + 1 regressão), 9 avisos |
| uv run pytest -q tests/api/test_audit_history.py (após separação dos stores) | 100 passaram, 4 avisos |
| uv run ruff check . ../../tests | Passou |
| uv run mypy src | Passou, 74 arquivos de código |
| uv run alembic heads | Um HEAD: 0003_semantic_audit |
| uv run alembic upgrade head --sql | Passou; SQL gerado offline em arquivo temporário |
| DATABASE_URL do banco descartável: uv run alembic upgrade head | Passou, sem alteração dos bancos de trabalho |
| DATABASE_URL do banco descartável: uv run alembic check | Passou; nenhuma operação de upgrade nova detectada |
| Integração com -c pyproject.toml e dois bancos descartáveis | 27 passaram, 94 avisos; nenhum teste pulado |
| Integração sem TEST_DATABASE_URL/TEST_MIGRATION_DATABASE_URL | 27 pulados explicitamente |
| bash scripts/check.sh (execução final) | Passou completo: 1.170 testes, 389 avisos; Ruff, mypy, build Next.js, TypeScript e Compose |
| git diff --check | Passou |

A primeira chamada de uv via Snap e de Docker foi bloqueada no sandbox. Execuções
escalonadas autorizadas usaram as ferramentas já instaladas. Node 24.16.0 já existente
foi acrescentado ao PATH para o check completo. Não houve instalação de dependências
adicionais. A primeira integração sem `-c pyproject.toml` passou com avisos de marcador;
a execução correta com configuração explícita passou sem esses avisos.

O primeiro check completo havia carregado o teste antigo antes da correção e terminou
com a mesma falha de double (1.169 passaram, 1 falhou); essa execução não é declarada
aprovada. A regressão específica corrigida passou e o check final reexecutou
toda a suíte com sucesso: 1.170 testes e 389 avisos. Avisos de depreciação RDFLib/ConjunctiveGraph e Starlette/httpx são
preexistentes e não foram ocultados ou corrigidos com dependências fora do escopo.

## Reproduzir integração

Seguir o procedimento descartável de [semantic-foundation.md](semantic-foundation.md).
Para a migração destrutiva, criar **outro banco vazio** no mesmo container, por exemplo
`createdb -U postgres libris_migration_test`; configurar explicitamente
TEST_MIGRATION_DATABASE_URL com esse banco. Esse teste se recusa a iniciar em banco
com tabelas públicas ou com a mesma URL de TEST_DATABASE_URL. Para repeti-lo, recriar
somente esse banco descartável conhecido; nunca apontar para dados de trabalho.

```bash
cd apps/api
uv sync --locked
uv run pytest
uv run ruff check . ../../tests
uv run mypy src
uv run alembic heads
uv run alembic upgrade head --sql
# DATABASE_URL/TEST_DATABASE_URL: banco de integração descartável migrado.
# TEST_MIGRATION_DATABASE_URL: outro banco descartável inicialmente vazio.
uv run alembic upgrade head
uv run alembic check
uv run pytest -c pyproject.toml ../../tests/integration -m integration
# Na raiz:
bash scripts/check.sh
```

Sem as duas URLs, os testes respectivos são pulados; o teste de migração não recebe
a URL ordinária como fallback. Nenhum serviço externo é requerido pelos unitários.

## Matriz de critérios de aceite

“Implementado” significa código e evidência no escopo interno atual; a última linha
separa operações editoriais futuras das garantias já exercidas em conteúdo.

| Critério da solicitação | Estado | Evidência |
| --- | --- | --- |
| Contrato de proveniência documentado | Implementado | Provenance/Revision e contrato arquitetural |
| Taxonomia dos oito eventos | Implementado | StrEnum AuditEventType; oito variantes unitárias |
| Modelo tipado, validado e imutável | Implementado | AuditEvent frozen; casos inválidos e FrozenInstanceError |
| Persistência de auditoria | Implementado | SemanticAuditEvent/AuditStore/0003; PostgreSQL real |
| Criação/revisão emitem respectivos eventos | Implementado | BibliographicService + testes transacionais |
| Identidade, operação, instante, ator quando conhecido | Implementado | Envelopes e round-trip humano/desconhecido/service/automated |
| Revisões imutáveis e recuperáveis | Implementado | Trigger preexistente + suítes PostgreSQL histórica/atual |
| Leitura histórica não altera corrente | Implementado | HistoryService; leitura r1 mantém r3 |
| Semântica inequívoca de restauração | Implementado no escopo | content cria rN+1 com source_revision; editorial é envelope pendente |
| CAS continua funcional | Implementado | Disputa real de duas sessões: um vencedor e um conflito |
| Revisões/eventos na mesma transação | Implementado para conteúdo | session.begin único; repositórios fazem somente flush |
| Rollbacks sem eventos órfãos | Implementado | Falha após INSERT audit reverte recurso, revisão, evento e CAS |
| Legado válido sem backfill fictício | Implementado | Banco sob 0002, comparações exatas após migração, sem eventos/ator novo |
| Comparação RDF semântica | Implementado | rdflib.compare; idioma/datatype, isomorfismo, ciclos, blank nodes e JSON-LD/Turtle |
| Autorização histórica definida e testada | Implementado | HistoryService, nova permissão, papéis permitidos/negados |
| Testes de integridade/concurrency/proveniência/auditoria | Implementado | 100 casos unitários novos, 21 casos novos de integração, suítes existentes |
| Documentação e ADR atualizados | Implementado | Contrato, este relatório, ADR 0027, README, identidade/editorial |
| Sem dependências/funcionalidades indevidas | Implementado | Sem novos pacotes/locks, rotas, DTOs, frontend, filas ou triplestore |
| Integração editorial operacional da #27 | Pendente explícita | Falta adaptador de estado/CAS; envelopes suportados, sem workflow fictício |

Os doze critérios originais da issue #28 correspondem às linhas acima: proveniência,
taxonomia/estrutura/identificação, revisões/leitura/restauração/CAS, transações/legado,
testes e documentação. Não são usados para alegar persistência editorial inexistente.

## Dependências, riscos e limites

- Estado editorial: adaptador PostgreSQL de EditorialTransaction e coordenação
  atômica de prepare_content_revision + snapshots + auditoria ainda necessários.
- RETURN/ARCHIVE: extensão versionada da taxonomia, migração incremental dos CHECKs
  e testes, sem reinterpretar eventos existentes.
- Substituição: serviço de ciclo de identidade futuro; FK garante sucessor existente,
  mas estado ativo/ausência de ciclos ainda dependem de persistência própria.
- Banco: administradores privilegiados podem remover proteções; não há assinatura
  criptográfica, backup/DR ou imutabilidade física contra DBA.
- Segurança: AuthenticatedActor é contexto confiável do servidor; conferência de hash
  não substitui JWT validado. Textos source/process/reason não devem conter segredos.
- RDF: alteração de descrição de blank nodes pode ampliar o delta estrutural; sem
  garantia de edição mínima ou identidade persistente desses nós. Quotas futuras.
- Operação: aplicar 0003 antes de usar o serviço atualizado. Downgrade é destrutivo.
- Homologação: perfis, retenção, papéis OIDC provisionados e política institucional
  de acesso/visibilidade continuam decisões dos mantenedores.

## Git e pull request

A solicitação proíbe branches e commits e também pede preservar main. O HEAD foi
destacado no mesmo commit inicial, sem branch nova; todas as alterações ficam no
workspace. Main não recebeu commits. Não foi aberto PR: sem branch/commits de origem,
não existe diff publicado elegível para um PR contra main. A conexão GitHub foi usada
para ler as issues; não houve push, merge ou encerramento automático de issue.
