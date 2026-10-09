# Relatório — Etapa 3, Incremento 1

Data: 2026-10-09. Diagnóstico apresentado antes da implementação; o solicitante
autorizou executar as diretrizes propostas. O incremento consolida tecnicamente
o contrato; a aprovação institucional dos perfis candidatos continua pendente.

## Alterações realizadas

- Release institucional candidata **monograph-v1.1**, com perfil complementar de
  autoridades e JSON Schema local para descritores. O perfil experimental original
  foi preservado, com validação e default de criação compatíveis.
- Campos declaram proprietário, nome, propriedade RDF, tipo, cardinalidade,
  obrigatoriedade, repetibilidade, idioma/datatype, ausência, destino e vocabulário.
  A matriz e as regras estão no [contrato](catalogographic-contract.md).
- Shapes validam estruturas de título, contribuição, publicação, identificadores,
  extensão, classificação, notas e autoridades. Título de Instance é opcional;
  Work exige título não variante e Item exige identificador `bf:Local`.
- Snapshots institucionais contêm uma entidade e auxiliares privados. O serviço
  existente aceita as novas releases explicitamente, preserva perfil/tipo nas
  revisões e rejeita descrições alheias ou inversas armazenadas.
- Composição deriva `hasInstance`/`hasItem`, renomeia blank nodes de grafos
  independentes e rejeita duas revisões da mesma raiz. Validação composta verifica
  consistência das inversas sem corrigir silenciosamente o grafo recebido.
- Token de domínio vincula UUID/revisão; o contrato distingue esse token de ETags
  de cache e precondições HTTP. Não foram criados endpoints.
- Corpus identificado por manifesto: **10 fixtures válidas e 14 inválidas**, todas
  sintéticas. Os testes conferem SHACL, metadados nos proprietários corretos,
  compartilhamento de autoridades e isomorfismo JSON-LD/Turtle após partição/composição.
- Dois testes antigos usavam edição na Work como alteração genérica; passaram a
  usar descrição DCTERMS, sem modificar a fixture legada.

## Arquivos criados

No módulo `apps/api/src/libris/modules/bibliographic/`:

- `domain/profiles.py`: descritores Pydantic tipados e invariantes do formulário.
- `infrastructure/ownership.py`: propriedade e composição de snapshots.
- `resources/monograph-v1.1.json`, `monograph-v1.1.ttl`,
  `monograph-v1.1-composed.ttl`: candidato monográfico e validação composta.
- `resources/authority-v1.json`, `authority-v1.ttl`: autoridades complementares.
- `resources/catalog-profile.schema.json`: schema local versionado.

Documentação:

- `docs/architecture/catalogographic-contract-diagnosis.md`: Momentos A/B,
  alternativas e decisões apresentadas para revisão.
- `docs/architecture/catalogographic-contract.md`: contrato, matriz de campos,
  política HTTP/URIs, persistência/versionamento e diagrama Mermaid.
- `docs/architecture/catalogographic-contract-verification.md`: este relatório.
- ADRs 0009–0015, detalhados abaixo.

Testes:

- `tests/api/test_catalogographic_contract.py`.
- `tests/integration/test_entity_revisions_postgres.py`.
- `tests/fixtures/bibliographic/institutional/manifest.json` e os 24 arquivos
  Turtle enumerados nesse manifesto, com indicação explícita de dados sintéticos.

## Arquivos modificados

- `README.md`, `docs/architecture/bibliographic-model.md` e
  `docs/architecture/semantic-foundation.md`: estado atualizado e links para o
  contrato; documentação legada preservada como histórico.
- `apps/api/src/libris/modules/bibliographic/__main__.py`: seleção local de release
  e modo composto no CLI de inspeção/exportação.
- `apps/api/src/libris/modules/bibliographic/application/service.py`: criação com
  perfil explícito, preservação de release/tipo e validação de propriedade.
- `apps/api/src/libris/modules/bibliographic/domain/models.py`: token de escrita.
- `apps/api/src/libris/modules/bibliographic/infrastructure/validation.py`:
  seleção restrita de shapes locais, reutilizando o relatório existente.
- `tests/api/test_bibliographic.py` e
  `tests/integration/test_semantic_postgres.py`: correção semântica do exemplo de
  alteração de Work.

Não foram alterados dependências, locks, migrações, tabelas, rotas FastAPI ou código
Next.js. Não houve transformação destrutiva de dados nem novo mecanismo gravável.
O esquema experimental suporta raízes e releases adicionais sem migração física.

## Decisões registradas

| ADR | Decisão |
| --- | --- |
| [0009](../decisions/0009-bibliographic-identity.md) | Identidade independente e propriedade de auxiliares |
| [0010](../decisions/0010-bibliographic-operational-persistence.md) | PostgreSQL/RDF canônicos e fronteira administrativa |
| [0011](../decisions/0011-independent-revisions-concurrency.md) | Revisão independente, histórico e concorrência |
| [0012](../decisions/0012-institutional-uris.md) | URIs estáveis, negociação futura, descontinuação e fusões |
| [0013](../decisions/0013-agents-subjects.md) | Autoridades, papéis, assuntos e identificação externa |
| [0014](../decisions/0014-profile-evolution.md) | Releases imutáveis e compatibilidade do legado |
| [0015](../decisions/0015-transactional-rdf-consistency.md) | Commit único, inversas derivadas e projeções futuras |

Status: aceitos para implementação técnica após autorização do solicitante;
homologação institucional pendente. Nenhum ADR prévio foi sobrescrito.

## Verificações executadas

| Verificação | Resultado |
| --- | --- |
| `scripts/check.sh` com uv nativo/Node locais e modo offline | Passou completo: 87 testes naquela execução, Ruff, mypy, build Next.js, TypeScript e configuração Compose |
| Verificação final da suíte padrão após mais invariantes do descritor | 93 passaram em 27,97 s; 273 avisos de depreciação conhecidos |
| Ruff / mypy após validações adicionais do descritor | Passaram; 20 arquivos Python, strict |
| Integração PostgreSQL, legado e novas entidades | 2 testes passaram na execução final, em 4,32 s; 45 avisos conhecidos |
| `alembic upgrade head` e `alembic check` no banco descartável | Passaram; nenhuma nova operação de migração detectada |
| CLI sobre `two-editions.ttl` e JSON-LD exportado | Ambos conformes, 25 triplas, sem issues |
| Termos BIBFRAME dos dois perfis contra a cópia local da ontologia oficial | 47 termos verificados; nenhum ausente após revisão |
| Consistência do manifesto | 24 arquivos únicos; 10 válidos, 14 inválidos |
| `git diff --check` e links locais da documentação | Passaram |

O script foi executado com ferramentas já instaladas em `/tmp`, sem downloads:

```bash
PATH=/tmp/libris-bootstrap/bin:/tmp/node-v24.21.0-linux-x64/bin:$PATH \
UV_CACHE_DIR=/tmp/libris-uv-cache UV_PYTHON_INSTALL_DIR=/tmp/libris-python \
UV_OFFLINE=1 bash scripts/check.sh
```

A tentativa inicial no Momento A usou `uv` via snap e foi bloqueada por
`snap-confine`. Tentativas de testes/build no sandbox encontraram restrições de
streams/subprocessos; as verificações completas foram executadas fora do sandbox
com escalonamento autorizado. Isso não requereu alteração do script do projeto.

## Evidência PostgreSQL e isolamento

Foi criado somente para este incremento o container
`libris-contract-stage3-20261009`, PostgreSQL 17, banco `libris_contract_test`,
porta aleatória de loopback 32768, senha descartável e sem volumes persistentes.
A migração existente foi aplicada apenas nele; nenhum banco de trabalho recebeu
migrações ou modificações. SQLite não foi usado como substituto.

Os testes reais comprovaram histórico imutável, round-trip JSONB, CAS concorrente,
rejeição obsoleta, rollback após grafo inválido, estabilidade da URI após mudança
de configuração e preservação do perfil/tipo. A nova integração comprova que
atualizar Authority, Instance ou Item preserva a revisão de Work; atualizar Item
também preserva Instance. Uma tentativa válida estruturalmente de mudar Instance
para Work é rejeitada com rollback. Composição após releitura preserva vínculos
e identidade única da autoridade. O teste legado mantém trigger e FK diferida.

O container exclusivo foi removido após a execução final, por seu ID registrado
na criação. Como não tinha volumes persistentes, nenhum volume de trabalho foi
removido. Exportações de inspeção ficaram somente em `/tmp/libris-stage3-export`.

## Limitações, decisões pendentes e Incremento 2

- Homologar o candidato com catalogadores, em especial a modelagem de tradução,
  títulos, obrigatoriedade do identificador de Item e vocabulários institucionais.
- Escolher domínio público e validar política institucional de fusão, descontinuação,
  equivalência e acesso ao histórico; estados/tombstones ainda não têm operações
  ou armazenamento implementados.
- Implementar API de catalogação/resolução e representação estável de edição,
  ETag/If-Match, 303/308/404/406/410 e negociação conforme contrato. As respostas
  HTTP foram especificadas, não testadas como endpoints inexistentes.
- Implementar integridade transacional de referências locais por contratos de
  serviço. SHACL verifica URI/tipo quando descrito; não prova existência em banco
  nem validade de vocabulário externo. Não dereferenciar referências durante parsing.
- Definir autenticação, autorização, ator de auditoria e política de visibilidade
  antes de expor escrita. Proveniência técnica atual não é auditoria humana completa.
- Planejar adoção explícita dos novos snapshots para agregados legados, preservando
  originais e rastreabilidade. Não há migração automática de registros existentes.
- Definir composição histórica por revisões/corte temporal e ETags de dependências.
  Não foi implementada consulta global temporal ou índice de relações reversas.
- ISBN é transcrito e estruturado; checksum, reconciliação externa e processamento
  de autoridades não foram implementados. Fixtures são representativas de testes,
  sem afirmar validação com registros de produção.
- Editor, busca Elasticsearch, outbox e circulação continuam fora do incremento.
  Não houve benchmark, teste de carga, auditoria de produção ou inspeção visual.
- RDFLib e Starlette continuam emitindo depreciações conhecidas; os avisos foram
  reportados e não suprimidos por mudanças de dependências fora do escopo.
