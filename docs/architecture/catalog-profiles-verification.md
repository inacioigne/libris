# Verificação da #20 — perfis declarativos

Data: 2026-10-12. Implementação técnica no workspace; issue permanece aberta para
revisão dos critérios e alterações. Não houve commit, push, publicação ou mudança
remota. Homologação institucional permanece pendente.

## Resumo e decisões

Formato JSON/Pydantic 2.0, descritores discriminados de valores RDF, metadados de
família/release, políticas catalográficas separadas da apresentação, herança simples
fixada por release, resolução/seleção determinísticas e registros semânticos/SHACL
locais. Entrada declarativa e resposta resolvida são distintas. Fingerprints
protegem conteúdo e bases transitivas das releases do pacote; publicação/depreciação
em memória são transições explícitas de disponibilidade. Não há persistência
administrativa, migração implícita ou motor SHACL paralelo. [ADR 0021](../decisions/0021-declarative-catalog-profiles.md).

Dez definições: núcleo, cinco entidades, monografia, seriada, digital e Work mínimo
independente. Exemplos incorporam Title/Contribution/Identifier/Publication, idioma,
referência a autoridade, relação entre obras, enum digital, datatype e condição de
formulário. A serial usa bf:frequency com vocabulário por IRI. Foram conferidos
**48 termos BIBFRAME** contra o
[RDF oficial arquivado 2.0.1](https://github.com/lcnetdev/bibframe-ontology/blob/main/archive/bibframe-2.0.1.rdf).
Nenhuma ontologia é consultada em runtime.

## Arquivos e finalidade

Caminhos Python abaixo são relativos a
`apps/api/src/libris/modules/bibliographic/`.

| Arquivo/conjunto | Estado e finalidade |
| --- | --- |
| domain/profiles.py | Modificado: publica novos contratos junto dos modelos/aliases legados; conserva schema histórico |
| domain/iris.py | Modificado: validador absoluto independente, removendo ciclo de imports; não normaliza IRIs |
| domain/profile_contract.py | Criado: metadados, variantes, policy/presentation, seções/grupos, condições, referências de validação e contexto |
| domain/profile_registry.py | Criado: registros confiáveis, resolver/seleção, erros, fingerprint, imutabilidade, disponibilidade e comparação de evolução |
| infrastructure/profiles.py | Criado: manifest do pacote, verificação de fingerprints/bases e adaptador v1 sem reescrever artefatos |
| infrastructure/validation.py | Modificado: extrai execução compartilhada; adaptador de shapes versionadas/contexto e correlação de erros |
| resources/profiles-v2/*.json | Criados: dez definições, manifest, release-lock, registro semântico 1.0, registro SHACL 1.0 e quatro schemas gerados |
| scripts/generate_profile_artifacts.py | Criado: gera/confere dez artefatos públicos; somente acrescenta fingerprints novos após validação |
| tests/api/test_declarative_profiles.py | Criado: 116 testes unitários/de contrato, inclusive regressão, OpenAPI isolado, SHACL e segurança de carregamento |
| tests/fixtures/bibliographic/profiles/ | Criado: cinco inválidos/manifest, hashes históricos e inventário BIBFRAME revisado |
| docs/examples/profiles/ | Criado: seis payloads gerados, incluindo exemplo completo independente e monografia resolvida |
| docs/architecture/catalog-profiles.md | Criado: referência, criação/composição, regras, versões, API candidata e integração futura |
| docs/decisions/0021-declarative-catalog-profiles.md | Criado: decisão estrutural, alternativas, compatibilidade e limites |
| README.md e docs/architecture/catalogographic-contract.md | Modificados: links à evolução, preservando o conteúdo histórico |
| Este relatório | Criado: evidências e revisão individual dos critérios |

Exemplo completo funcional:
[work-minimal-2.0.0.json](../examples/profiles/work-minimal-2.0.0.json).
Especialização funcional com campos herdados:
[monograph-2.0.0.json](../examples/profiles/monograph-2.0.0.json).
Resposta efetiva preparada para consumidor:
[monograph-2.0.0.resolved.json](../examples/profiles/monograph-2.0.0.resolved.json).
Os exemplos e respectivas referências são carregados pelos testes, não somente
ilustrados em documentação.

## Compatibilidade histórica

Preservados integralmente monograph-v1.json/ttl, monograph-v1.1.json/ttl,
monograph-v1.1-composed.ttl e authority-v1.json/ttl. O teste confere seus SHA-256
junto do catalog-profile.schema.json. IDs mantidos; não converter IDs antigos em
famílias do formato 2.0. O schema antigo continua idêntico ao gerado por
CatalogProfile. Não houve mudança de tabelas, DTOs de recursos, snapshots ou locks
de dependências.

v1 tem adaptação de **descritores de leitura**, sem alteração do arquivo ou
validação histórica. v1.1/authority carregam diretamente nos modelos originais.
As invariantes legadas requiredInForm/cardinalidade/repeatable/absent continuam
exigidas. validate_monograph/validate_profile e os relatórios públicos antigos
continuam compatíveis. A suíte anterior permanece intacta e passa.

## Comandos executados e resultados

Ambiente Python 3.13.15, pytest 9.1.1. Nenhum PostgreSQL/Elasticsearch é necessário
para a suíte API. Ferramentas do ambiente virtual já existente; sem instalar novas
dependências.

| Comando efetivamente executado | Resultado |
| --- | --- |
| cd apps/api; uv run pytest | Bloqueado pelo uv/Snap: snap-confine recusou execução no ambiente |
| bash scripts/check.sh | Tentado; parou na mesma limitação de uv/Snap |
| cd apps/api; .venv/bin/pytest | Execução final: **711 passaram**, 329 warnings, 46,58 s; inclui **116 novos** |
| cd apps/api; .venv/bin/pytest ../../tests/api/test_declarative_profiles.py -q | 116 passaram na execução isolada; verificação integral final cobre as alterações posteriores |
| cd apps/api; .venv/bin/ruff check . ../../tests ../../scripts/generate_profile_artifacts.py | Passou |
| cd apps/api; .venv/bin/mypy src | Passou, strict, **52 arquivos** |
| apps/api/.venv/bin/python scripts/generate_profile_artifacts.py | Dez artefatos gerados por Pydantic/configuração local |
| apps/api/.venv/bin/python scripts/generate_profile_artifacts.py --lock-new-releases | Passou; fingerprints existentes preservados |
| apps/api/.venv/bin/python scripts/generate_profile_artifacts.py --check | Dez artefatos conferidos, sem divergências |
| cd apps/web; PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH npm run build | Passou, Next.js 16.4.0, build webpack, páginas /pt e /en |
| Mesmo PATH; npm run typecheck | Passou |
| docker compose --env-file .env.example config --quiet | Passou |
| git diff --check | Passou |
| Verificação de inventário BIBFRAME contra arquivo oficial 2.0.1 obtido para /tmp | 48 termos presentes; sem termos inventados |

A primeira suíte completa confinada parou de avançar em TestClient e foi
interrompida; a execução final fora do sandbox passou. O build confinado falhou ao
ler TypeScript --showConfig; o build fora do sandbox passou. A primeira chamada de
npm sem PATH explícito não encontrou o binário; a versão local de Node resolveu.
Todas as partes disponíveis de check.sh foram executadas separadamente. Não se
atribui sucesso ao wrapper uv ou ao script completo, que permaneceram bloqueados
pelo Snap. As formas `uv run ruff`/`uv run mypy` não foram concluídas por esse caminho;
foram executados os equivalentes locais acima.

Warnings existentes: Starlette/httpx e RDFLib ConjunctiveGraph. Não houve mudança de
bibliotecas para suprimi-los. Não foram executados testes PostgreSQL de integração
ou migrações, pois não houve alteração de persistência. O teste de rede desabilita
socket.create_connection durante carregamento/validação e confere grafo intacto;
acesso a serviços externos não é necessário.

## Critérios de aceitação da issue #20

| Critério da issue | Estado | Evidência |
| --- | --- | --- |
| Contrato documentado, versionável e extensível | Atendido | Formato 2.0, quatro schemas, referência e ADR 0021 |
| Propriedades, obrigatoriedade, cardinalidade, tipos e apresentação configuráveis | Atendido | DeclarativeField/CatalogPolicy/Presentation; casos válidos/invalidade e separação required_in_form |
| BIBFRAME principal e extensões controladas | Atendido | SemanticRegistry, inventário 2.0.1; DCTerms/SKOS/Schema.org/PROV-O; testes de registro/extensão |
| Exemplos Work/Instance/Item/Agent/Subject | Atendido | Cinco especializações e núcleo, Person/Organization e Concept, todos resolvidos/serializados |
| Respeito ao canônico e contratos Pydantic existentes | Atendido no escopo de configuração | DEFAULT_REGISTRY, alvos/cardinalidades/derivação, estruturas privadas; suíte legada/DTOs permanece íntegra |
| Backend interpreta e frontend pode gerar formulários futuramente | Atendido como contrato | ProfileDefinition→ResolvedProfile, controles/seções/condições, payload público gerado; sem editor |
| Associação a SHACL da #21 | Atendido como integração contratual | ShapeReference/FieldConstraint, contexto, adaptador local e correlação resultPath; mesmo pySHACL |
| Identificação, versionamento e evolução documentados | Atendido | Famílias/releases/contratos/shapes separados, disponibilidade, fingerprints e compare_profiles |
| Novos perfis existentes não exigem código-fonte | Atendido | Herança/JSON; dez definições usando a mesma classe; exemplo mínimo e registro confiável extensível |
| Independência de persistência/indexação | Atendido | Domínio sem HTTP/ORM/infraestrutura; nenhuma tabela, dependência ou projeção adicionada |
| Testes válidos, inválidos e limites | Atendido | 116 novos; 711 totais; corpus inválido e geração/OpenAPI/regressão |
| Decisões, limitações e extensões documentadas | Atendido | ADR 0021, referência e integrações #21/#22/#24/#25/#27/#30/#31 |

## Critérios adicionais do pedido de implementação

| Critério | Estado e evidência |
| --- | --- |
| Contrato declarativo documentado/versionável/extensível | Atendido: referência + schemas/registro |
| Pydantic v2 implementado | Atendido: profile_contract/profile_registry |
| Schema reproduzível | Atendido: geração e --check executados |
| Cinco entidades | Atendido: exemplos/testes parametrizados |
| Propriedades e relações semânticas | Atendido: IRIs, variantes authority/relationship e estruturas auxiliares |
| Cardinalidade/obrigatoriedade/repetibilidade coerentes | Atendido: validadores, limites de domínio e testes negativos |
| Apresentação separada da semântica | Atendido: policy versus presentation; regressão do formato antigo |
| Configuração sem novas subclasses Python | Atendido: herança por release em JSON |
| Composição/especialização determinísticas | Atendido: merge explícito, ordenação e política de restrição |
| Referências inválidas/ciclos rejeitados | Atendido: bases, condições, auxiliares, sucessoras e registros |
| Contrato SHACL versionado | Atendido: referências/contexto/adaptador; validação completa de políticas adicionais pertence à #21 |
| Legado funcional | Atendido: carga dos três IDs, schema antigo e suíte anterior |
| Histórico não sobrescrito | Atendido: hashes legados, fingerprints novos e isolamento de registro |
| Sem ORM/React | Atendido: contratos puros, sem telas/endpoints |
| Fixtures/testes representativos | Atendido: válidos, cinco inválidos, corpus RDF reutilizado e 116 testes |
| Decisões/limitações documentadas | Atendido: ADR 0021/referência/este relatório |
| Sem antecipar issues posteriores | Atendido: somente contrato e adaptador; limites abaixo |

## Limites e recomendações posteriores

O adaptador executa as shapes declaradas, **não compila** políticas extras, enums ou
condições em SHACL. A #21 deve conferir sua correspondência e completar validação
semântica/diagnóstico. Não atribuir ao conjunto 1.1 regras mais estritas que o
arquivo efetivamente executa. Nenhum perfil v2 foi integrado ao fluxo persistente
de escrita do serviço nesta issue. Conformidade não prova existência de referências,
pertinência remota a vocabulário ou homologação.

#22 padronizará respostas; #24 avançará valores controlados/reconciliação; #25 terá
novos componentes/ontologias; #27 cuidará dos estados de **registros**; #30 ampliará
o corpus; #31 consolidará contratos/documentação. Extensões digitais não acrescentam
campos aos DTOs atuais; edição RDF genérica/API deverá preservar dados fora desses
DTOs. Sem React/CRUD/editor, serviços externos, tabelas, migrações automáticas,
MARC, Elasticsearch, circulação ou triplestore.

Recomenda-se revisar/homologar os perfis e começar #21 pelo inventário das diferenças
entre policy e shapes, mantendo as releases/identidades fixadas. A transição de
estado é somente um novo registro em memória, não administração persistida. Locks
são guardas de artefatos/revisão e carregamento, não controle contra um administrador
que altere simultaneamente arquivos e fingerprints. A licença do projeto não foi
escolhida nem alterada.
