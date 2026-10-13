# Verificação e entrega — M03.05.02 / issue #31

Data da execução: 2026-10-12 (America/Manaus).
Branch inicial: `main`; `git status --short` inicial vazio.
A [issue #31](https://github.com/inacioigne/libris/issues/31) foi lida pelo conector
GitHub em operação somente leitura; seus critérios correspondem à tarefa anexada.
Nenhuma escrita remota ou operação de branch/staging foi executada.

## Entrega e investigação

README/AGENTS, arquitetura, ADRs 0009–0015/0017–0028, relatórios correlatos,
modelos Pydantic, perfis/shapes, serializadores, serviços/persistência, exemplos
e asserções de testes foram confrontados. A #30 já oferece corpus/matriz/evidência
de integração real; não duplicar fixtures nem reimplementar CRUD para documentá-lo.

Concluído: [referência canônica v1](catalogographic-contract.md), ID inequívoco,
baseline documental 1.0.0, inventário gerado de 22 contratos raiz e 50 definições
alcançáveis, operações internas versus HTTP, quatro dimensões de versão,
política direcional de evolução, matriz com implementadores/ADRs/asserções,
exemplos existentes verificáveis e limites técnicos/institucionais.
Não há modificação de código de produção, dependências, locks, migrações,
contextos ou releases históricas. A política de governança do ADR 0029 está
**proposta**, sem aprovação institucional ou seleção pública de versão presumida.

## Arquivos

| Criados | Finalidade |
| --- | --- |
| `docs/architecture/catalogographic-contract-v1.schema.json` | Baseline de validação JSON Schema com 22 raízes/50 definições, ID documental |
| `docs/architecture/catalogographic-contract-field-inventory.md` | Tabelas geradas: campos, tipos, enums, presence/null/cardinalidades/defaults/auxiliares |
| `docs/architecture/catalogographic-contract-traceability.md` | Vínculo regra → documento → ADR → implementador → teste → asserção, com lacunas |
| `docs/architecture/catalogographic-contract-v1-verification.md` | Este relatório, resultados atuais e critérios de aceite |
| `docs/decisions/0029-catalogographic-contract-versioning.md` | Política proposta SemVer documental, coexistência/migração e compatibilidade direcional |
| `scripts/generate_catalogographic_contract.py` | Geração/check do schema e inventário; recusa baseline divergente |
| `tests/api/test_catalogographic_contract_specification.py` | Conformidade da baseline com modelos vivos, refs, imutabilidade, OpenAPI real e limites de compatibilidade/HTTP |

| Modificados | Alteração |
| --- | --- |
| `README.md` | Entradas para referência, schema, inventário, rastreabilidade e política |
| `docs/architecture/catalogographic-contract.md` | Referência atual v1; preserva perfil do Incremento 1 e corrige estado de auditoria/editorial |
| `docs/architecture/catalogographic-schemas.md` | Links para campos gerados; referências tipadas/exportação já existentes versus API futura |
| `docs/architecture/catalogographic-errors.md` | Completa códigos atuais; enum fechado, status fallback 422 e distinção resultado interno/HTTP |
| `docs/architecture/catalogographic-v1-conformance-matrix.md` | Link à nova rastreabilidade; evidência #30 preservada |
| `docs/architecture/relationships.md` | Delimita trechos históricos e aponta integrações implementadas |
| `docs/architecture/catalog-profiles.md` | Referências atuais para entregas já implementadas |
| `docs/architecture/shacl-validation.md` | Corrige o mapeamento de diagnóstico #22 já implementado |

## Divergências e resolução

| Encontrado | Resolução documental / limite |
| --- | --- |
| Contrato central sem versão pública inequívoca, identificado só pelo incremento/perfil | ID público e baseline documental 1.0.0; não modificar info.version/DTO/rotas |
| Trechos atuais ainda diziam ator/auditoria/referências/serialização futuros | Corrigidos para OIDC/auditoria/editorial/referências/exportação implementados; ADRs e relatórios históricos preservados |
| Orientação de aceitar códigos/campos desconhecidos versus Diagnostic.code enum fechado e extra=forbid | Distinguir recomendação de UI da aceitação real de Pydantic; testes demonstram rejeição; não relaxar contrato unilateralmente |
| Inventário de erros #22 omitia códigos de vocabulário/editorial/ciclo de identidade posteriores | Inventário completado conforme CatalogCode; sem inventar novos códigos |
| Nome de erro editorial sugere 403/409/428/412 mas CODE_STATUS não oferece tais mapeamentos | Documentar fallback atual 422; teste de classify; evolução de HTTP exige decisão futura |
| CatalogPublicationRejected tem result, mas handler só publica validation para CatalogValidationRejected | Registrar distinção sem modificar handler ou prometer relatório HTTP editorial |
| DTO exige um valor inclusive sem idioma; SHACL uniqueLang não limita strings sem idioma; core Item não lista toda alternativa SHACL histórica | Preservar diferenças já documentadas; não mudar shapes/perfis históricos |
| bf:Item versus exemplar administrativo | Distinção explícita; sem inventário/circulação implementados |

Não foi necessária mudança incompatível de contrato/persistência ou de semântica
histórica. Não foi escolhido domínio público, licença, mecanismo HTTP de versão ou
prazo de descontinuação. Não houve pedido de decisão bloqueante para esta entrega.

## Verificações executadas

Resultados finais são preenchidos após os processos concluírem. Logs de sessão
em `/tmp/libris-issue31-*.log` não são artefatos do contrato.

| Comando efetivamente executado | Resultado / limite |
| --- | --- |
| Raiz: `bash scripts/check.sh` no sandbox | Falhou antes dos testes: snap-confine recusou uv por confinamento |
| Raiz: `PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH bash scripts/check.sh` com execução escalonada autorizada | **Exit 0**: 1.234 testes passaram, 465 avisos; Ruff passou; mypy src passou (76 arquivos); build Next.js, typecheck e Compose config passaram. Log `/tmp/libris-issue31-check.log` |
| `apps/api/.venv/bin/pytest -q tests/api/test_catalogographic_contract_specification.py` a partir da raiz, primeira execução | 26 passaram antes da extensão dos testes de fallback/recusa de sobrescrita; não é a contagem final |
| Em apps/api: `.venv/bin/pytest -q ../../tests/api/test_catalogographic_contract_specification.py` intermediário | 39 passaram; a recusa de baseline divergente foi acrescentada depois |
| Em apps/api: `.venv/bin/pytest -q ../../tests/api/test_catalogographic_contract_specification.py ../../tests/api/test_catalogographic_conformance.py ../../tests/api/test_catalogographic_contract.py` final | **133 passaram**, 358 avisos; inclui os **40 casos novos** e os 93 de conformidade/contrato existentes. Log `/tmp/libris-issue31-contracts.log` |
| Em apps/api: `.venv/bin/ruff check . ../../tests ../../scripts/generate_catalogographic_contract.py` final | Passou, incluindo script novo; warnings de streams do ambiente não alteraram exit 0 |
| Em apps/api: `MYPYPATH=src .venv/bin/mypy ../../scripts/generate_catalogographic_contract.py` final | Passou: 1 arquivo; chamada inicial sem MYPYPATH tinha imports sem py.typed e identificou `required` como object; conferência de lista corrigida sem modificar schema |
| Raiz: `apps/api/.venv/bin/python scripts/generate_catalogographic_contract.py --check` | 2 artefatos verificados contra modelos atuais, sem escrita |
| Raiz: `apps/api/.venv/bin/python scripts/generate_profile_artifacts.py --check` | 10 artefatos históricos/atuais verificados, sem atualizar locks |
| Raiz: `apps/api/.venv/bin/python scripts/generate_controlled_value_artifacts.py --check` | 8 artefatos verificados; pares RDF por isomorfismo |
| Em apps/api: `.venv/bin/alembic heads` e `.venv/bin/alembic upgrade head --sql` | Head único `0004_semantic_editorial`; SQL offline em `/tmp/libris-issue31-migrations.sql`; nenhum banco alterado |
| Em apps/api: `env -u TEST_DATABASE_URL -u TEST_MIGRATION_DATABASE_URL -u TEST_EDITORIAL_MIGRATION_DATABASE_URL .venv/bin/pytest -c pyproject.toml ../../tests/integration -q` | **55 skipped** por ausência explícita dos bancos dedicados; não comprova atomicidade PostgreSQL nesta sessão |
| Checagem local de links/âncoras Markdown (README + docs) | 71 documentos; nenhum link local/âncora inválido |
| Checagem AST das referências arquivo::test_* da matriz | Todos os nomes apontam para funções existentes; inspeção de asserções é registrada na matriz |
| `git diff --check` e conferência de alterações em código de produção/migrações/locks/fixtures/examples | Sem erros; nenhum desses artefatos existentes modificado |

A suíte agregada coletou antes da inclusão do último caso de recusa de sobrescrita:
1.195 anteriores + 39 novos = 1.234. A seleção final inclui **40 novos**, todos
aprovados, junto dos 93 existentes; ela complementa a suíte agregada, não soma
133 casos inéditos à contagem. O caso adicional só cria arquivos temporários de
teste e comprova que baseline divergente não é sobrescrita. Não houve mudança de
comportamento de produção entre as execuções. A correção final de tipagem do gerador
foi verificada por mypy e `--check`; lint final também passou.

RDFLib/ConjunctiveGraph e Starlette/httpx emitiram depreciações preexistentes;
não foram suprimidas nem usadas para justificar atualização de dependências.
Build verifica páginas atuais /pt e /en, não um editor catalográfico inexistente.
OpenAPI de produção foi inspecionado diretamente sem abrir conexão com serviços.

A integração PostgreSQL real **não foi executada nesta sessão**. Os resultados
históricos (55 aprovados) da [#30](catalogographic-v1-testing.md) e
[#43](editorial-persistence-verification.md) continuam rastreáveis, mas não contam
como aprovação atual. As variáveis foram removidas apenas do processo de teste,
evitando qualquer banco de trabalho. Não há SQLite ou Elasticsearch substitutos,
novos containers, migrações aplicadas ou requisito de banco para os testes da API.

## Critérios de aceite e pendências

| Critério | Avaliação |
| --- | --- |
| Referência inequívoca v1 / campos/tipos/estruturas/required/null/cardinalidades | Concluído: documento + schema/inventário gerados |
| Create/Read/Update versus serviços/endpoints | Concluído: modelos públicos disponíveis em Python; somente health/me no produto |
| Identidade, propriedade, revisão e relacionamentos | Concluído no comportamento existente; recursos de identidade operacionais futuros delimitados |
| JSON, JSON-LD, Turtle e RDF | Concluído: mapeamento real, contexto limitado e isomorfismo; Graph → DTO completo não suportado |
| Perfis, SHACL, políticas e diagnósticos | Concluído: artefatos locais e códigos inventariados; sem equivalência artificial entre camadas |
| Quatro dimensões, compatibilidade e releases históricas | Concluído documentalmente; aprovação da governança futura do ADR 0029 pendente explícita |
| Rastreabilidade e exemplos | Concluído: corpus existente, asserções específicas e baseline verificável |
| Qualidade/testes | Ver resultados de execução e limites abaixo; não usar evidência histórica como execução desta sessão |
| Homologação institucional e limitações | Documentadas; não realizadas por testes de software |
| Escopo/Git | Concluído: alterações locais, sem funcionalidades de produção novas ou escrita Git/GitHub |

Pendências fora do escopo: homologar perfis/regras/vocabulários, aprovar governança
de evolução e disponibilidade, decidir domínio/retenção/visibilidade/fusão, integrar
CRUD/editor/PATCH/resolver HTTP e eventual seleção de versões. Os serviços internos
não fazem migração de perfis ou reconciliação remota. `consume.ts` permanece exemplo
sem execução/typecheck específico, não cliente implementado/homologado.

## Estado final do Git

Branch: **main**. O estado final contém **8 arquivos rastreados modificados** e
**7 arquivos novos não rastreados**, todos listados acima. `git diff --name-only
--cached` vazio: sem staging. Nenhuma branch, commit, push, merge/rebase, tag,
release, pull request ou escrita em issue/GitHub foi realizada. Todas as mudanças
permanecem locais para revisão e versionamento pelo usuário.

Avaliação: critérios documentais e de verificação da #31 atendidos, com limites
de integração física atual e decisões institucionais explicitamente registrados.
Disponibilidade local no repositório não significa publicação remota da especificação
ou fechamento de issue; ambas foram preservadas sob controle do usuário.
