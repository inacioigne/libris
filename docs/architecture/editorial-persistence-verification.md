# Verificação — M03.04.03 / issue #43

Data de referência: 2026-10-12. Branch inicial: main; working tree inicialmente limpo.
Escopo: [issue #43](https://github.com/inacioigne/libris/issues/43), dependências #27/#28
consultadas pelo conector GitHub, juntamente com a issue principal #26. Somente leitura
remota: nenhum comentário, fechamento, PR ou publicação. Documentação:
[contrato de persistência](editorial-persistence.md), [ADR 0028](../decisions/0028-editorial-transactions.md).

## A. Entregas e diagnóstico

A branch tinha máquina editorial completa/protocolo sem adaptador, revisões/CAS e
AuditStore com flush, criação/revisão/restauração transacionais e HistoryService.
Não existiam metadados editoriais PostgreSQL, composição da escrita de conteúdo,
seleção pública persistida ou taxonomia fiel para RETURN/ARCHIVE. Não foi necessário
reescrever infraestrutura transacional, identidade, perfis ou migrações anteriores.

Implementados estado durável independente, adaptador concreto, CAS e transação única,
integração no BibliographicService, candidata isolada, validação/referências locais
protegidas até commit, auditoria de todas as arestas, consulta autorizada e migração
incremental 0004. O contrato vigente representa candidata com current_revision e
candidate_state; candidate_revision é propriedade derivada, não coluna divergente.

## B. Arquivos e finalidade

| Caminho relativo à raiz | Alteração |
| --- | --- |
| apps/api/migrations/versions/0004_semantic_editorial.py | Nova tabela experimental, FKs/CHECKs, índice e extensão da taxonomia; downgrade protegido |
| apps/api/migrations/env.py | Inclui metadata ORM editorial na inspeção Alembic |
| apps/api/src/libris/modules/bibliographic/infrastructure/editorial.py | ORM, inicialização legada, gate transacional, locks e UPDATE CAS |
| apps/api/src/libris/modules/bibliographic/application/editorial_postgres.py | Adaptador EditorialTransaction, unidade de trabalho, resolvedor local e fechos de relações |
| apps/api/src/libris/modules/bibliographic/application/service.py | Integra criação/revisão/restauração e read_public à política persistida |
| apps/api/src/libris/modules/bibliographic/application/editorial.py | Valida contexto humano e coordena adaptador concreto pelo protocolo existente |
| apps/api/src/libris/modules/bibliographic/application/history.py | EditorialHistory/read_editorial autorizado e coerente |
| apps/api/src/libris/modules/bibliographic/application/audit.py | Mapeia RETURN/ARCHIVE aos eventos governados |
| apps/api/src/libris/modules/bibliographic/domain/audit.py | record.returned/record.archived com invariantes e justificativa |
| apps/api/src/libris/modules/bibliographic/domain/editorial.py | Propriedade candidate_revision derivada; matriz preservada |
| apps/api/src/libris/modules/bibliographic/infrastructure/audit.py | CHECKs dos novos eventos e índice não exclusivo por versão |
| tests/integration/test_editorial_postgres.py | Transações reais, falhas, disputa de sessões, visibilidade, tipos e relações |
| tests/integration/test_editorial_migrations_postgres.py | Upgrade 0003→0004 com snapshots/eventos reais; downgrade aceito/rejeitado |
| tests/api/test_audit_history.py | Ampliou fixtures/assertions para dez eventos e RETURN/ARCHIVE |
| tests/api/test_editorial.py | Double humano usa actor_identifier OIDC; assertions de política preservadas |
| tests/api/test_semantic_extensions.py | Double editorial adicional; assertions de RDF/perfil preservadas |
| tests/api/test_shacl_validation.py | Double assíncrono da unidade editorial; mantém assertions de diagnóstico/rollback e acrescenta ausência de save editorial |
| README.md | Estado real, migração e referências da entrega |
| docs/architecture/editorial-lifecycle.md | Integração atual e distinção das evidências históricas da #27 |
| docs/architecture/provenance-audit-versioning.md | Indica evolução operacional/taxonômica da #43 |
| docs/architecture/editorial-persistence.md | Transação, CAS, legado, visibilidade, autorização, referências e reprodução |
| docs/decisions/0028-editorial-transactions.md | Decisão incremental e alternativas |
| docs/architecture/editorial-persistence-verification.md | Este relatório |

Sem dependências adicionais, locks alterados, migrações anteriores reescritas, frontend,
endpoints, dados pessoais, licença ou configuração dos serviços em uso modificados.

## C. Arquitetura e garantias

Uma session.begin por operação; stores fazem flush. Conteúdo grava CAS de identidade,
snapshot imutável, estado editorial/CAS e evento existente. Transição grava CAS de
estado e AuditStore.append na mesma sessão. Qualquer erro reverte também a inicialização
legada. Receber PreparedEditorialEvent não é evidência persistida; histórico só lê banco.

Gate PostgreSQL shared para conteúdo e exclusive para decisões, sempre antes da
identidade, impede TOCTOU e deadlocks entre publicações cruzadas. UPDATE editorial
condiciona versão e revisão corrente; zero linhas gera conflito explícito. Aprovação
seleciona corrente esperada; publicação seleciona aprovação exata. A candidata nunca
substitui public_revision automaticamente. Dependências locais e fechos acíclicos são
resolvidos sob o gate, com locks de identidade adicionais. Ver ADR para custo de concorrência.

Legado conserva ausência de estado/eventos observados, ator/proveniência e JSONB;
inicialização draft é observada apenas numa escrita efetiva. RETURN/ARCHIVE ampliam
constraints sem reinterpretar os oito eventos históricos. Envelopes históricos
repetidos permitidos pela #28 permanecem válidos. Exatamente uma vez vem do CAS e
commit, sem unicidade retroativa ou deduplicação artificial.

## D. Execuções, resultados e evidências

PostgreSQL 17-bookworm descartável, container libris-issue43-postgres, sem volumes,
porta exclusiva 127.0.0.1:55449. Removido ao término, após a integração final.
Banco libris_test para integração; bancos separados
inicialmente vazios para cada execução dos dois testes de migração. Nenhum banco dos
containers libris existentes foi acessado para escrita. Não foi usado SQLite,
create_all ou docker compose down -v. Credenciais descartáveis não foram versionadas.

| Comando/verificação | Resultado | Evidência e observações |
| --- | --- | --- |
| uv run pytest das suites #27/#28 | PASSOU | 193 testes; quatro avisos RDFLib |
| Integração PostgreSQL completa inicial | FALHOU | 46 passaram/1 falhou: índice exclusivo era incompatível com envelopes repetidos aceitos pela #28; corrigido para índice não exclusivo |
| Nova suíte editorial PostgreSQL, primeira execução | FALHOU | 19 passaram/1 falhou: fixture Agent usava propriedade de label incorreta para a release; corrigida para rdfs:label |
| uv run pytest -c pyproject.toml ../../tests/integration (rodada intermediária) | PASSOU | 52 testes, nenhum pulado; 218 avisos; inclui duas suítes de migração |
| Suíte editorial após revisão dos caminhos auxiliares | PASSOU | 27 testes, 161 avisos; Contribution, Publication e heldBy reais |
| Integração PostgreSQL final completa | PASSOU | 55 testes, nenhum pulado; 256 avisos; /tmp/libris-issue43-integration-final.log |
| PATH do Node instalado: bash scripts/check.sh (final) | PASSOU | Exit code 0; 1.172 testes, 389 avisos, Ruff, mypy (76 arquivos), build Next.js, TypeScript e Compose |
| scripts/check.sh, primeira rodada completa | FALHOU | 1.171 passaram/1 falhou: double SHACL não contemplava nova unidade transacional; corrigido sem enfraquecer assertions |
| Regressão SHACL específica corrigida | PASSOU | Um teste; diagnóstico estruturado e rollback preservados |
| uv run ruff check . ../../tests | PASSOU | All checks passed, configuração de apps/api |
| uv run mypy src | PASSOU | 76 arquivos verificados |
| uv run alembic heads | PASSOU | Head único 0004_semantic_editorial |
| uv run alembic upgrade head --sql | PASSOU | SQL offline gerado em /tmp/libris-issue43-migrations.sql |
| DATABASE_URL descartável: uv run alembic upgrade head | PASSOU | Banco instalado até 0004, sem tocar dados de trabalho |
| DATABASE_URL descartável: uv run alembic check | PASSOU | No new upgrade operations detected |
| Migrações automatizadas #28 e #43 | PASSOU | Upgrade/downgrade em bancos exclusivos vazios; JSONB, UTC, UUID/URI e eventos anteriores comparados exatamente |
| Downgrade com record.returned | PASSOU (rejeição esperada) | Falha transacional protege evidência; esquema/head e eventos preservados |
| git diff --check | PASSOU | Sem erros de whitespace |

A tentativa inicial de uv pelo Snap foi bloqueada pelo sandbox; execuções autorizadas
usaram as ferramentas já instaladas. Uma execução inicial de pytest dentro do sandbox
ficou bloqueada e foi encerrada; não é declarada aprovada. A execução real utiliza
uv e Python 3.13.15 fora desse bloqueio. Node 24.16.0 já instalado é usado no check.
Avisos RDFLib/ConjunctiveGraph e Starlette/httpx são preexistentes e não foram ocultados.

Evidências transitórias: /tmp/libris-issue43-integration-final.log e
/tmp/libris-issue43-check-final.log. Ambas as execuções finais terminaram com exit code 0.
Nenhum teste pulado na integração final; check.sh concluiu também frontend e Compose.

## E. Matriz de aceite da issue

| Critério da #43 | Estado | Evidência implementada |
| --- | --- | --- |
| Adaptador PostgreSQL real implementado/testado | COMPROVADO | PostgresEditorialTransaction/Transactions e round-trip entre sessões |
| Estado persistente independente de conteúdo | COMPROVADO | ORM/0004; version=4 com r1 após publicação |
| Transição/auditoria no mesmo commit | COMPROVADO | Rollback pós-INSERT, erro de inserção real e comparação em sessão nova |
| CAS e decisões obsoletas rejeitadas | COMPROVADO | UPDATE condicional; duas publicações; aprovação/edição; candidata/edição; retirada/republicação; restauração/edição |
| BibliographicService integrado e publicação isolada | COMPROVADO | Ciclo r1 pública/r2 candidata/r3 restaurada; read_public seleciona ponteiro |
| Publicação autorizada, perfil/SHACL/referências | COMPROVADO | Suíte #27 de permissões; PostgreSQL negado, SHACL legado inválido com diagnósticos, referência obrigatória não classificada e ciclo local |
| Auditoria das sete operações | COMPROVADO | Treze transições efetivas no fluxo completo; RETURN/ARCHIVE próprios; versões únicas das transições confirmadas |
| Restauração de conteúdo/editorial distinguida | COMPROVADO | rN+1 restored/content versus REPUBLISH restored/editorial |
| UUID/URI/snapshots legados preservados | COMPROVADO | Comparação exata de migração, histórico RDF isomórfico e identidade estável |
| PostgreSQL de atomicidade/rollback/concorrência/negações | COMPROVADO | Sessões independentes, consultas posteriores a cada falha; dependência bloqueada até commit |
| Documentação/ADR/evidências | COMPROVADO | Contrato, ADR 0028, README e este relatório |
| Regressões #27/#28 | COMPROVADO | 193 testes específicos e integração preexistente |

Os requisitos adicionais do pedido estão cobertos pelos mesmos testes: constraints/FKs,
CAS sem linhas, inicialização legada revertida, histórico autorizado/ordenado, todos
os cinco tipos, versões independentes, snapshot antigo intacto, restauração sem publicação,
falhas sem eventos órfãos e exatamente um evento para cada transição efetiva.

## F. Limites e pendências

- Gate exclusivo serializa decisões e suspende escritores bibliográficos durante
  validação; não há medição de escala ou alegação de prontidão de produção.
- Chamadas históricas de conteúdo sem expected_editorial_version não expressam uma
  expectativa sobre mudanças editoriais já concluídas; seguem política sob bloqueio.
  Novos consumidores podem enviar ambas as expectativas. Transições exigem ambas.
- Garantias transacionais dependem do protocolo dos serviços. SQL privilegiado ou
  stores usados fora da composição não recebem a garantia das referências até commit.
- Referências externas exigem classificação explícita; continuam pendentes de verificação
  remota, sem garantia sobre mudanças externas ou ciclos através dessas fontes.
- O contrato independente de substituição/descontinuação/fusão não ganhou armazenamento
  ou um segundo modelo; retirada/arquivamento preservam identidades e histórico.
- O downgrade elimina metadados editoriais; bloqueia novos tipos de eventos incompatíveis.
- Perfis, política institucional e papéis OIDC continuam sujeitos à homologação externa.
  APIs CRUD públicas, frontend e indexação permanecem fora do escopo.

## G. Git e encerramento

Branch inicial/final: main. Nenhuma branch criada/trocada, commit, staging, push, merge,
rebase, reset ou PR. Todas as alterações permanecem no working tree para revisão.
Não houve mutação remota GitHub. git status/diff final incluem arquivos novos não
rastreados; git diff --stat sozinho mostra somente os rastreados, não toda a entrega.


Verificação final executada: `git branch --show-current`, `git status --short`,
`git diff --stat`, `git diff --check`. Branch main preservada; diff sem erros.
23 arquivos locais: 15 rastreados modificados e oito novos não rastreados.
As quatro fixtures/doubles alteradas conservam suas assertions de regressão,
com a extensão explícita do contrato de taxonomia; nenhum teste foi desabilitado.
