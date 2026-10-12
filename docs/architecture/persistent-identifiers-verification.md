# Verificação de identificadores persistentes — issue #17

Data: 2026-10-11. Execução local na branch main, sem commit/push/PR.

## Resumo

Consolidação técnica da estratégia existente de UUIDv4 e URI persistida para
Work/Instance/Item/Agent/Subject. Validação do domínio reforçada, documentação de
ciclo de vida, identificadores externos, reconciliação, HTTP e importação,
exemplos JSON/JSON-LD/Turtle e testes executados. Não há novo esquema, dependência,
workflow administrativo, endpoint público ou serializador da #18.

## Diagnóstico inicial

HEAD 2f2b61c43fc10c2f34452f7f43102de87d143116, main; nenhuma alteração preexistente.
Executados pwd, git status --short, git branch --show-current e git log -5 --oneline.
A issue #17 foi lida no GitHub; comparação read-only mostrou main remota dois
commits à frente, relativos à #16. Nenhuma atualização de histórico foi feita.

Reaproveitado localmente: ResourceIdentity UUIDv4/frozen, RevisionStore,
BibliographicService, Graph, ownership, perfis e restrições SQL existentes.
Reaproveitado do pré-requisito #16: modalidades tipadas, ReferenceResolver,
ResolvedEntity, validate_references, registro/schemas de vínculos, cinco DTOs,
108 testes e 41 fixtures + manifest. O resolvedor depende dos contratos de vínculos;
seus componentes e testes foram preservados em conjunto, sem versão paralela.
Documentação e ADR 0018 da dependência também foram preservados. O relatório
histórico de execução remoto foi substituído por nota de verificação desta sessão.

Novo na #17: validate_identity_uri e UUID validado em runtime no domínio,
ADR 0019, especificação, nove arquivos de exemplo, 54 testes unitários/contratos,
dois casos PostgreSQL de unicidade e este relatório.
Lacunas futuras não foram simuladas: não reutilização após remoção, workflow,
importação idempotente persistida, reconciliação e aliases de fusão.

Inconsistência histórica: bibliographic-model chama URI/UUID de proposta, enquanto
ADR 0012 já os decide; esta especificação esclarece qual decisão prevalece.
O texto inicial dos schemas descreve URI-only; um aviso explicita o complemento
#16/#17, sem apagar o registro de evolução.

## Decisões arquiteturais

Preservados ADRs 0009/0012/0013/0015/0017/0018. UUIDv4 e URI sem tipo continuam
únicos; UUIDv7 é opção futura condicionada a benchmark e suporte Python 3.13.
URI armazenada prevalece; mudanças de base não reescrevem identidades.
Par inválido em tipo/formato falha no domínio; coerência referencial depende do
resolvedor com armazenamento confiável. Nenhuma normalização silenciosa nova.

Ciclo de vida e catálogo de identificadores são políticas conceituais versionadas.
308 para fusão comprovada foi preservado e analisado criticamente em relação a
método, cache e reversão. Não há equivalência OWL automática, URI definitiva de
pendência ou transformação de ISBN em PK. Domínio não importa HTTP/ORM/API.

## Contratos e exemplos

- LocalReference: tipo e UUID e/ou URI; ambos devem corresponder ao par persistido.
- ExternalReference: tipo e IRI, namespace obrigatório quando há external_id.
- UnreconciledReference: tipo, label, namespace e key; sem UUID/URI público.
- ResourceReference URI-only: compatibilidade explícita, sem inferir localidade.
- Identifier: kind/value/source existentes; verificação/proveniência estendidas são
  catálogo conceitual futuro, sem campos fictícios no DTO.

As cinco fixtures *-read.json validam os DTOs atuais e referências rasas.
entities.jsonld e entities.ttl descrevem Work/Instance/Item/Person/Concept,
bf:instanceOf, bf:itemOf, Contribution/agent/role e identificadores externos.
Isomorfismo e conformidade dos snapshots proprietários foram verificados.
JSON-LD é exemplo ilustrativo produzido pelo adaptador existente, sem contrato
final de serialização da #18. lifecycle-proposal.json é proposta futura explícita;
seus campos não são apresentados como API existente. Todos os dados são sintéticos.

## Testes e comandos executados

Em apps/api, ambiente virtual existente Python 3.13, sem instalação/dependências novas:

| Comando | Resultado final |
| --- | --- |
| .venv/bin/pytest test_persistent_identifiers.py + test_relationships.py + test_catalogographic_schemas.py + test_catalogographic_contract.py + test_bibliographic.py -q (caminhos ../../tests/api/) | 421 aprovados, 0 reprovados, 0 ignorados |
| timeout 90 .venv/bin/pytest -q | 477 aprovados, 0 reprovados, 0 ignorados; 274 avisos |
| .venv/bin/pytest -c pyproject.toml ../../tests/api/test_persistent_identifiers.py -q | 54 aprovados, 0 reprovados, 0 ignorados |
| .venv/bin/ruff check . ../../tests | Aprovado |
| .venv/bin/mypy src | Aprovado, 44 arquivos |
| .venv/bin/ruff format --check models.py e dois arquivos de teste novos | Aprovado |
| .venv/bin/alembic heads | 0002_revision_actor (head) |
| .venv/bin/alembic upgrade head --sql | Aprovado; SQL temporário /tmp, não aplicado ao banco de trabalho |
| .venv/bin/alembic upgrade head em PostgreSQL descartável | Aprovado; somente migrações existentes |
| .venv/bin/alembic check em PostgreSQL descartável | No new upgrade operations detected |
| TEST_DATABASE_URL=... .venv/bin/pytest -c pyproject.toml ../../tests/integration -m integration -q | 5 aprovados, 0 reprovados, 0 ignorados; 51 avisos RDFLib; incluindo dois novos casos de unicidade |

PostgreSQL 17 real foi iniciado com imagem local postgres:17-bookworm, sem volumes,
porta aleatória em loopback e banco exclusivo libris_issue17. Nunca usado SQLite.
Ao terminar, o container exclusivo foi encerrado com docker stop; --rm removeu
o banco descartável, sem tocar em volumes ou serviços de trabalho.
Os testes existentes comprovam URI estável após mudança de base, atualização e
revisões, snapshots/histórico imutáveis, concorrência/CAS, rollback e ator.
Os novos testes inserem UUID/URI conflitantes em savepoint e exigem IntegrityError;
a transação externa é revertida, sem recurso comprometido sem revisão.

Em apps/web, Node 24.16.0 e dependências existentes:
PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH npm run build e npm run typecheck
passaram, incluindo páginas /pt e /en. Nenhuma mudança de frontend/dependências.
Na raiz, docker compose --env-file .env.example config --quiet e git diff --check passaram.

Limitações e tentativas registradas:

- bash scripts/check.sh falhou no uv/Snap (snap-confine); suas partes foram executadas
  individualmente pelo ambiente virtual e Node existentes.
- Execução direcionada no sandbox ficou presa no TestClient e foi interrompida com
  código 130; a execução fora do sandbox terminou com 421 aprovados.
- Build no sandbox falhou ao interpretar TypeScript --showConfig; fora do sandbox passou.
- docker info no sandbox recebeu permission denied; fora dele o daemon e PostgreSQL
  foram acessíveis. Compose config também passou dentro do sandbox.
- Primeiro lint identificou uma linha longa no teste novo; formatada e reverificada.
- Depreciações preexistentes de Starlette/httpx e RDFLib não foram ocultadas.
- Primeira execução de integração usou descoberta de config fora de apps/api e gerou
  avisos de marker; a confirmação final usa -c pyproject.toml.
- Não foram iniciados Elasticsearch ou serviços da aplicação; não houve teste de
  indexação, disponibilidade pública, DNS ou chamadas a autoridades externas.
- Fusões, substituições, retenção, aliases persistidos e importações idempotentes
  ainda não possuem implementação; não existem testes executados dessas operações.

## Casos de teste futuros — especificação, não execução

Todos os casos de persistência usarão PostgreSQL dedicado e migrações revisadas.

| Caso | Preparação e resultado esperado | Dependência |
| --- | --- | --- |
| Não reutilização | Descontinuar/remover logicamente, tentar alocar UUID/URI antigos; rejeitar e preservar reserva | Persistência de ciclo de vida |
| URI/UUID imutáveis por DML | Tentar modificar par principal; negar via contrato/privilégios/restrição futura | Esquema e operação futuras |
| Alias duplicado | Criar alias já pertencente a identidade principal/alias de outra entidade; rejeitar | Catálogo persistido de aliases |
| Reimportação idêntica | Importar duas vezes a mesma tupla fonte/conjunto/chave/componente; mesmo par, sem revisão vazia | Pipeline e mapeamento de origem |
| Importação concorrente | Duas transações para mesma tupla; uma alocação, repetição resolve identidade existente | Unicidade do mapeamento |
| Metadados/ID externo mudam | Reimportar origem com ISBN/ORCID corrigido; nova revisão, mesmo UUID/URI e origem anterior retida | Importação |
| ISBN compartilhado | Fontes/entidades distintas com mesmo ISBN; não fundir automaticamente | Deduplicação |
| Fusão | Evidência confirmada, revisar vínculos atuais, alias antigo chega ao sobrevivente, histórico intacto | Workflow/aliases |
| Reimportação após fusão | Chave da origem perdedora resolve alias sem recriar entidade | Importação + fusão |
| Substituição | Sucessor distinto, relação explícita sem sameAs/308 de fusão; referências exigem contexto | Ciclo de vida |
| Desmembramento | Duas novas identidades, origem preservada, referência não escolhe sucessor arbitrário | Ciclo de vida |
| Descontinuação/remoção | Par reservado, 410 e tombstone conforme publicação; histórico acessível só pela política | API e retenção |
| Alias em cadeia/ciclo | Resolver destino final, preservar passos; recusar loops/conflitos | Resolução persistida |
| Corrida de referência/retirada | Mudança de ciclo de vida concorrente com vínculo; lock/versão evita referência incoerente | Serviço transacional |
| HTTP Accept | HTML/JSON-LD/Turtle, q=0, curingas, HEAD, 303/200/404/406/410, Vary e Location corretos | API Linked Data |
| Cache de fusão | 308 confirmado, invalidação e revalidação conforme TTL; não usar fusão provisória | Infraestrutura pública |
| Reconciliação | Candidata/próxima/rejeitada/conflitante não publicam equivalência forte; confirmada registra evidência | Autoridades |
| Exportação/projeção | @id/objetos e índice reutilizam URI histórica; reconstrução não revive tombstone | #18/descoberta |

## Critérios de aceitação

A classificação distingue contrato/política entregue de execução futura.

| Critério solicitado | Classificação | Evidência concreta |
| --- | --- | --- |
| Convenção única documentada | Atendido | ADR 0019 e especificação: base/UUID, cinco tipos |
| Identidade imutável, independente de metadados | Atendido | ResourceIdentity frozen, testes novos e revisão PostgreSQL |
| Separar UUID/URI/URLs/revisão/origem | Atendido | Tabela de conceitos e exemplos ilustrativos |
| Separar identificadores locais/externos | Atendido | Modalidades da #16, catálogo e matriz de esquemas |
| Não reutilização/persistência | Atendido como política; parcialmente atendido na execução | PK/UNIQUE testadas; reserva após retirada depende de persistência futura |
| Fusão/substituição/descontinuação | Atendido como política; pendente por dependência futura na execução | Tabela de ciclo, proposta explícita e casos futuros |
| Contratos coerentes com #16 | Atendido | Reutilização dos arquivos publicados, 108 testes de vínculos na suíte |
| Pydantic/FastAPI compatíveis | Atendido | 171 testes de schemas existentes + testes novos; OpenAPI isolado |
| Integridade e unicidade definidas | Atendido | Matriz SQL, protocolo de resolução, dois casos PostgreSQL novos |
| Exemplos das cinco entidades | Atendido | Cinco Read JSON, references, grafo JSON-LD/Turtle |
| Compatibilidade futura JSON-LD/RDF | Atendido como contrato; #18 pendente por dependência futura | Isomorfismo, SHACL, auxiliares preservados, sem novo serializador |
| Independência de Elasticsearch/frontend | Atendido | Domínio sem ORM/HTTP, nenhuma escrita/projeção nova |
| Testes do comportamento implementado | Atendido | 477 unitários/contratos e 5 integrações aprovados |
| Casos futuros identificados | Atendido | Tabela acima, sem teste fictício de operação ausente |
| ADR, alternativas e consequências | Atendido | ADR 0019: UUIDv4/v7, URI tipada, HTTP, riscos |
| Decisões institucionais identificadas | Atendido; publicação bloqueada por decisão institucional | Domínio/DNS/TLS, retenção, permissões e titularidade pendentes |
| Sem mudança destrutiva/incompatível | Atendido para identidades válidas e contratos existentes | Fixtures legadas e suíte passaram; validação agora rejeita entradas inválidas antes toleradas |

Os nove critérios oficiais da issue são cobertos pelas linhas acima: convenção,
estabilidade, distinções, ciclo de vida, contratos, integridade, exemplos,
independência e responsabilidades futuras. Nenhum endpoint público é alegado pronto.

## Pendências

- #18: serializar DTOs/vínculos preservando Graph, propriedades fora da superfície,
  contextos locais e auxiliares; não fabricar URI para unreconciled.
- Outras entregas: APIs transacionais, persistência de estados/aliases, importação,
  reconciliação de autoridades, projeção/outbox e testes de HTTP/cache; #20/#21
  aprofundam perfis e SHACL. Não requer nova tabela definitiva nesta issue.
- Institucionais: domínio público e custódia, retenção/publicabilidade do histórico,
  permissões de fusão/descontinuação, evidência de equivalência e vocabulários.
- Opcionais: medir UUIDv7 em carga real e propor ADR somente com necessidade;
  biblioteca 3.13 ou mudança da versão de referência exigem decisão explícita.

## Arquivos alterados — inventário completo

73 arquivos locais novos/alterados; nenhum arquivo excluído.

| Caminho | Finalidade |
| --- | --- |
| `README.md` | Integração documental #16/#17, compatibilidade e navegação |
| `apps/api/src/libris/modules/bibliographic/api/schemas/__init__.py` | Contrato/código/teste/documentação do pré-requisito #16 reutilizado |
| `apps/api/src/libris/modules/bibliographic/api/schemas/agent.py` | Contrato/código/teste/documentação do pré-requisito #16 reutilizado |
| `apps/api/src/libris/modules/bibliographic/api/schemas/common.py` | Contrato/código/teste/documentação do pré-requisito #16 reutilizado |
| `apps/api/src/libris/modules/bibliographic/api/schemas/instance.py` | Contrato/código/teste/documentação do pré-requisito #16 reutilizado |
| `apps/api/src/libris/modules/bibliographic/api/schemas/item.py` | Contrato/código/teste/documentação do pré-requisito #16 reutilizado |
| `apps/api/src/libris/modules/bibliographic/api/schemas/relationships.py` | Contrato/código/teste/documentação do pré-requisito #16 reutilizado |
| `apps/api/src/libris/modules/bibliographic/api/schemas/subject.py` | Contrato/código/teste/documentação do pré-requisito #16 reutilizado |
| `apps/api/src/libris/modules/bibliographic/api/schemas/work.py` | Contrato/código/teste/documentação do pré-requisito #16 reutilizado |
| `apps/api/src/libris/modules/bibliographic/application/relationships.py` | Contrato/código/teste/documentação do pré-requisito #16 reutilizado |
| `apps/api/src/libris/modules/bibliographic/domain/models.py` | Invariantes de UUID/URI reforçadas, geração UUIDv4 preservada |
| `apps/api/src/libris/modules/bibliographic/domain/relationships.py` | Contrato/código/teste/documentação do pré-requisito #16 reutilizado |
| `docs/architecture/catalogographic-schemas.md` | Integração documental #16/#17, compatibilidade e navegação |
| `docs/architecture/persistent-identifiers-verification.md` | Implementação/documentação/verificação própria #17 |
| `docs/architecture/persistent-identifiers.md` | Implementação/documentação/verificação própria #17 |
| `docs/architecture/relationships-verification.md` | Nota de verificação do pré-requisito, sem importar resultados históricos |
| `docs/architecture/relationships.md` | Contrato/código/teste/documentação do pré-requisito #16 reutilizado |
| `docs/decisions/0018-bibliographic-relationships.md` | Contrato/código/teste/documentação do pré-requisito #16 reutilizado |
| `docs/decisions/0019-persistent-identifiers.md` | Implementação/documentação/verificação própria #17 |
| `tests/api/test_persistent_identifiers.py` | Implementação/documentação/verificação própria #17 |
| `tests/api/test_relationships.py` | Contrato/código/teste/documentação do pré-requisito #16 reutilizado |
| `tests/fixtures/bibliographic/identifiers/agent-read.json` | Exemplo próprio #17; proposta futura explícita quando lifecycle-proposal |
| `tests/fixtures/bibliographic/identifiers/entities.jsonld` | Exemplo próprio #17; proposta futura explícita quando lifecycle-proposal |
| `tests/fixtures/bibliographic/identifiers/entities.ttl` | Exemplo próprio #17; proposta futura explícita quando lifecycle-proposal |
| `tests/fixtures/bibliographic/identifiers/instance-read.json` | Exemplo próprio #17; proposta futura explícita quando lifecycle-proposal |
| `tests/fixtures/bibliographic/identifiers/item-read.json` | Exemplo próprio #17; proposta futura explícita quando lifecycle-proposal |
| `tests/fixtures/bibliographic/identifiers/lifecycle-proposal.json` | Exemplo próprio #17; proposta futura explícita quando lifecycle-proposal |
| `tests/fixtures/bibliographic/identifiers/references.json` | Exemplo próprio #17; proposta futura explícita quando lifecycle-proposal |
| `tests/fixtures/bibliographic/identifiers/subject-read.json` | Exemplo próprio #17; proposta futura explícita quando lifecycle-proposal |
| `tests/fixtures/bibliographic/identifiers/work-read.json` | Exemplo próprio #17; proposta futura explícita quando lifecycle-proposal |
| `tests/fixtures/bibliographic/relationships/invalid/add-duplicate.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/bad-identifiers.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/bad-uri.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/derived-write.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/direct-role.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/duplicate.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/incompatible-identity.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/maximum.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/minimum.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/missing-identity.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/missing-role.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/nonexistent.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/null.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/remove-absent.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/self.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/unknown-predicate.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/wrong-origin.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/invalid/wrong-target.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/manifest.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/external-subject.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/instance-create.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/instance-items-read.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/item-create.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/patch-absent.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/patch-add.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/patch-clear.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/patch-empty.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/patch-remove.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/patch-replace.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/publication.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/resource-instance-create.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/resource-item-create.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/resource-work-create.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/resource-work-null.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/resource-work-read.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/resource-work-update.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/unreconciled-agent.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/work-agents.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/work-create.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/work-instance-read.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/work-related.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/fixtures/bibliographic/relationships/valid/work-replace.json` | Fixture/manifest do pré-requisito #16 preservado |
| `tests/integration/test_persistent_identifiers_postgres.py` | Dois testes PostgreSQL próprios #17: unicidade de UUID e URI |

## Estado do Git

Branch main; sem commit, push, PR ou alteração da issue.
O diff --stat padrão mostra apenas arquivos rastreados; o inventário acima inclui os novos.

```text
$ git status --short
 M README.md
 M apps/api/src/libris/modules/bibliographic/api/schemas/__init__.py
 M apps/api/src/libris/modules/bibliographic/api/schemas/agent.py
 M apps/api/src/libris/modules/bibliographic/api/schemas/common.py
 M apps/api/src/libris/modules/bibliographic/api/schemas/instance.py
 M apps/api/src/libris/modules/bibliographic/api/schemas/item.py
 M apps/api/src/libris/modules/bibliographic/api/schemas/subject.py
 M apps/api/src/libris/modules/bibliographic/api/schemas/work.py
 M apps/api/src/libris/modules/bibliographic/domain/models.py
 M docs/architecture/catalogographic-schemas.md
?? apps/api/src/libris/modules/bibliographic/api/schemas/relationships.py
?? apps/api/src/libris/modules/bibliographic/application/relationships.py
?? apps/api/src/libris/modules/bibliographic/domain/relationships.py
?? docs/architecture/persistent-identifiers-verification.md
?? docs/architecture/persistent-identifiers.md
?? docs/architecture/relationships-verification.md
?? docs/architecture/relationships.md
?? docs/decisions/0018-bibliographic-relationships.md
?? docs/decisions/0019-persistent-identifiers.md
?? tests/api/test_persistent_identifiers.py
?? tests/api/test_relationships.py
?? tests/fixtures/bibliographic/identifiers/
?? tests/fixtures/bibliographic/relationships/
?? tests/integration/test_persistent_identifiers_postgres.py
```

```text
$ git diff --stat
 README.md                                          |  8 ++
 .../modules/bibliographic/api/schemas/__init__.py  | 14 ++++
 .../modules/bibliographic/api/schemas/agent.py     |  5 +-
 .../modules/bibliographic/api/schemas/common.py    | 85 +++++++++++++++++++++-
 .../modules/bibliographic/api/schemas/instance.py  |  7 +-
 .../modules/bibliographic/api/schemas/item.py      | 10 ++-
 .../modules/bibliographic/api/schemas/subject.py   |  9 ++-
 .../modules/bibliographic/api/schemas/work.py      | 14 ++--
 .../libris/modules/bibliographic/domain/models.py  | 30 +++++---
 docs/architecture/catalogographic-schemas.md       | 12 +++
 10 files changed, 162 insertions(+), 32 deletions(-)
```

```text
$ git diff --check
(sem saída; código 0)
```

