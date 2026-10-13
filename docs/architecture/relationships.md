# Contrato de relacionamentos — M03.01.03 (#16)

Estado atual consolidado na [especificação v1](catalogographic-contract.md).
Os trechos de diagnóstico/integração futura desta entrega registram seu momento:
#18 implementou serialização; #20–#25 implementaram perfis, SHACL e extensões;
#43 implementou integridade local na publicação editorial transacional. A escrita
pública de vínculos, CRUD e resolução HTTP continuam futuras.

Versão 1.0. Complementa os [DTOs catalográficos](catalogographic-schemas.md), o
[contrato canônico](catalogographic-contract.md) e o
[ADR 0018](../decisions/0018-bibliographic-relationships.md). Os perfis institucionais
continuam candidatos. O registro não redefine BIBFRAME nem substitui RDFLib Graph.

## Diagnóstico e plano executado

Antes das alterações foram examinados README, arquitetura, ADRs, modelos de
identidade, perfis JSON/SHACL, ownership RDF, serviços, schemas e suíte pytest.
Work/Instance/Item e Agent/Subject são classes RDF em Graph; não há cinco modelos
ORM canônicos. `ResourceIdentity` fornece UUID/URI; `api/schemas` fornece quinze
DTOs Create/Read/Update. Contribution e Publication já são estruturas privadas do
proprietário, e `ownership.py` deriva hasInstance/hasItem. Não havia modalidades de
referência, registro de relações ou operações explícitas de coleção.

A issue #16 foi lida integralmente pelo conector GitHub. #14/#15 estavam fechadas;
#14 não retornou descrição. #17/#18/#20/#21 estavam abertas e sem descrição
retornada: não se presumiu implementação adicional. Código local foi a fonte de
verdade. `gh` não está instalado. A página id.loc.gov retornou 403, então os nomes,
classes, caminhos e inversas BIBFRAME foram conferidos no
[RDF oficial da Library of Congress](https://github.com/lcnetdev/bibframe-ontology/blob/master/bibframe.rdf),
versão declarada 2.0.1. A
[convenção RDF oficial](https://www.loc.gov/bibframe/docs/bibframe2-rdf-conventions.html)
distingue semântica das decisões de armazenar ambas as direções.

Plano executado: ampliar `common.py` e os cinco DTOs de recursos; criar
`domain/relationships.py`, `api/schemas/relationships.py` e
`application/relationships.py`; publicar contratos; adicionar fixtures e testes de
conformidade; documentar matriz, decisões e evidências. Domínio não importa API;
schemas importam apenas tipos/metadados de domínio. Aplicação usa DTOs sem HTTP e
protocolo de resolução. Não há imports circulares ou dependência de ORM/Elasticsearch.

## Matriz versionável

Fonte executável: `INITIAL_RELATIONS` e `REGISTRY_VERSION` em
`apps/api/src/libris/modules/bibliographic/domain/relationships.py`.
`bf:` = `http://id.loc.gov/ontologies/bibframe/`, `skos:` =
`http://www.w3.org/2004/02/skos/core#`, `dcterms:` = `http://purl.org/dc/terms/`.
Subject é skos:Concept; Agent inclui bf:Person e bf:Organization.

Todas as linhas têm direção explícita origem → destino. Cardinalidade é por
predicado no proprietário. `0..*` é opcional/múltipla; `0..1` é opcional/unitária;
`1..1` é obrigatória/unitária. Mínimos e máximos são limites desta superfície de
contrato, não limites universais da ontologia. A coluna perfil separa os mínimos
adicionais do candidato atual. Origem/destino são subconjuntos suportados pelo Libris:
bf:subject e bf:relatedTo permitem alvos mais amplos no vocabulário; não os fechamos
como restrições ontológicas. Tradução é entre Works conforme ADR 0013, embora o
vocabulário também preveja Instances.

| Nome / identificador | Campo | Significado | Origem → destino | Predicado / caminho | Inversa formal ou simetria | Estrutura | Perfil atual | Integridade / observações |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| instance_of | instance_of | Materialização de uma obra | Instance → Work | bf:instanceOf | bf:hasInstance | 0..1 | 1..1 | Escrita na Instance; alvo existente/local ou externo pendente |
| has_instance | has_instance | Instâncias da obra | Work → Instance | bf:hasInstance | bf:instanceOf | 0..* | 0..* | Somente leitura derivada dos filhos; Work sem Instance permitido |
| item_of | item_of | Cópia bibliográfica de uma instância | Item → Instance | bf:itemOf | bf:hasItem | 0..1 | 1..1 | Escrita no Item; nenhum estado de circulação |
| has_item | has_item | Cópias bibliográficas da instância | Instance → Item | bf:hasItem | bf:itemOf | 0..* | 0..* | Somente leitura derivada dos filhos |
| contribution | contribution | Agente e função na obra | Work → Agent | bf:contribution / bf:agent | Não declarada | 0..* | 0..* | Nó bf:Contribution; um agente e 1..* papéis por vínculo |
| subject | subject | Assunto conceitual da obra | Work → Subject | bf:subject | Não declarada | 0..* | 0..* | Conceito reutilizável; não copiar descrição da autoridade |
| work_related_to | related_to | Associação bibliográfica entre obras | Work → Work | bf:relatedTo | Simétrica; sem owl:inverseOf | 0..* | 0..* | Sem autorreferência; ciclos associativos permitidos |
| translation_of | translation_of | Obra original da tradução | Work → Work | bf:translationOf | bf:translation | 0..* | 0..* | Sem autorreferência/ciclo; origem da tradução apontada pelo proprietário |
| instance_related_to | related_to | Associação entre materializações | Instance → Instance | bf:relatedTo | Simétrica; sem owl:inverseOf | 0..* | 0..* | Contrato de vínculos; DTO Instance do perfil ainda não possui esse campo |
| publication_agent | provision_activity.agent | Publicador de uma publicação | Instance → Agent | bf:provisionActivity / bf:agent | Não declarada | 0..* | 0..* | Nó bf:Publication; activity_key agrupa publicadores da mesma atividade |
| held_by | held_by | Detentor bibliográfico do Item | Item → Agent | bf:heldBy | Não declarada | 0..* | 0..* | Perfil exige Organization; disponibilidade não pertence ao vínculo |
| broader | broader | Conceito mais amplo | Subject → Subject | skos:broader | skos:narrower | 0..* | 0..* | Política local impede autorreferência/ciclo hierárquico |
| subject_related | related | Associação conceitual | Subject → Subject | skos:related | Simétrica; sem owl:inverseOf | 0..* | 0..* | Sem autorreferência; ciclos associativos permitidos |
| related_authority | related_authority | Autoridade relacionada | Agent → Agent/Subject | dcterms:relation | Não declarada | 0..* | 0..* | Não afirma equivalência; permite identidade compartilhada |

Todas as linhas permitem especialização futura por novos predicados declarados;
propriedades canônicas não podem ser sobrescritas pelo mecanismo `extend`.
Autorreferência é recusada no conjunto inicial como política de integridade do
contrato, sem alegar que toda ontologia a proíbe. Cada linha rejeita destinos fora
do conjunto declarado, predicados não autorizados e duplicações do mesmo vínculo.
Uma navegação reversa de contribution, subject, held_by ou publication não é
inversa formal BIBFRAME. Simetria não cria outra escrita, revisão ou campo automático.

Outras propriedades existentes foram avaliadas: title/main_title, rótulos, notas,
identificadores, shelf_mark e datas são literais ou auxiliares privados, não relações
entre as cinco entidades. language/content/carrier/scheme/place/source referenciam
vocabulários ou classes fora deste inventário. external_reference usa rdfs:seeAlso;
provenance usa prov:wasDerivedFrom. Continuam `ResourceReference` por URI, sem
inferir equivalência owl:sameAs ou criar classes canônicas adicionais.

## Referências e identidade

`EntityReference` é união discriminada por `kind`, com `extra=forbid` em cada ramo:

| Modalidade | Obrigatórios | Opcionais | Combinações rejeitadas |
| --- | --- | --- | --- |
| local | kind=local, entity_type; ao menos internal_id ou uri | UUID existente e/ou ResourceURI HTTP(S) armazenada | ambos ausentes; UUID inválido; URI própria com fragmento/query/credenciais; campos externos/provisórios |
| external | kind=external, entity_type, uri absoluta | namespace; external_id acompanhado de namespace | internal_id; rótulo provisório; identificador externo sem origem |
| unreconciled | kind=unreconciled, entity_type, label, namespace, key | nenhum | UUID/URI; rótulo/chave vazios ou apenas espaços |

`kind` é obrigatório no JSON da união; instanciação da classe concreta pode usar
seu default. `entity_type` admite Work, Instance, Item, Agent e Subject. `key` é
uma chave provisória no namespace de importação/origem: não gera identidade
bibliográfica. `kind` explicita estado de reconciliação, sem booleanos redundantes.
O identificador externo é uma chave na origem; URI externa identifica um recurso
sem reescrever sua grafia. UUID interno e URI persistente são identidades separadas
conforme ADRs 0009/0012. Não se deduz localidade por prefixo da URI base atual.

A URI persistente conhecida é sempre reutilizada, inclusive após mudança de
RESOURCE_BASE_URI. UUID-only exige resolução para obter URI antes de RDF. Se ambos
forem enviados, o resolvedor verifica que correspondem à mesma identidade armazenada.
Não existe resolução HTTP nova, novo formato público ou política de fusão (#17).

Os campos entre entidades de Work/Instance/Item/Agent/Subject aceitam as três
modalidades e também a forma legada `{"uri":"..."}`. Os aliases WorkReference,
InstanceReference, AgentReference, SubjectReference e AuthorityReference conferem
tipo quando informado; URI-only não prova tipo ou localidade. Antes de transformar
um DTO legado em vínculos, a aplicação deve classificar explicitamente essa URI
com seu serviço de identidade. Nunca presumir que um prefixo significa recurso local.
Auxiliares de vocabulários continuam URI-only. Payloads não incorporam descrições
recursivas, ORM, empréstimos ou outros campos operacionais.

## Vínculos, papéis e extensões

`DirectLink` informa source (local), target (EntityReference) e predicate (URI completa).
`ContributionLink` usa kind=contribution, predicado fixo bf:contribution e role (1..*
URIs únicas). O caminho RDF é proprietário → Contribution → Agent, com bf:role
no nó Contribution. Agente, papel e propriedade são conceitos distintos. Exemplos
usam relators/aut (autor), edt (editor) e trl (tradutor). Outros papéis são permitidos;
`allowed_roles` na aplicação aplica uma whitelist de perfil quando fornecida.
Papéis em vínculos diretos/publicação são extras inválidos.

`PublicationLink` usa kind=publication, predicado fixo bf:provisionActivity,
activity_type=Publication e activity_key obrigatória. O caminho passa por bf:Publication.
Publicadores da mesma atividade compartilham activity_key; grupos diferentes podem
ter o mesmo agente. A chave é privada do proprietário e não vira UUID de autoridade.
Datas/lugares continuam na estrutura Publication de InstanceCreate/Read/Update;
a coleção de vínculos descreve somente suas referências a agentes. Um adaptador
futuro deve conservar esses atributos ao editar vínculos, sem substituir toda a
atividade por uma referência. Contribution participa da revisão do proprietário.

O registro declara classes auxiliares, caminhos, papéis, tipos, direção, inversas,
simetria, cardinalidade, derivação e política de ciclos. `RelationRegistry.extend`
retorna outro registro, exige namespace absoluto próprio terminado em /, # ou :,
e não altera o original. Duplicatas de nome ou origem/predicado falham. BIBFRAME e
SKOS não podem ser redefinidos, inclusive com namespace pai. Apenas relações
novas diretas são admitidas por esse mecanismo; auxiliares exigem schemas próprios.
Os dados não registram novas relações. A configuração confiável fornece o registro
pelo contexto Pydantic `{"registry": registry}` e à aplicação.

## Criação, leitura, substituição e PATCH

RelationshipCreate representa todos os vínculos proprietários de uma entidade;
RelationshipRead também admite hasInstance/hasItem derivados; RelationshipReplace
é a substituição completa desses vínculos, preservando literais e outras propriedades
RDF fora dessa superfície. Identidade do proprietário não muda numa alteração:
a aplicação deve comparar source com o recurso endereçado, usando revisão esperada.
As rotas definitivas continuam fora desta issue.

RelationshipUpdate oferece uma lista ordenada `operations` discriminada por `op`:

| Entrada | Efeito |
| --- | --- |
| {} / campo operations ausente | Preservar vínculos |
| operations=[] | Nenhuma operação; não apaga a coleção |
| operations=null | Rejeitar |
| add com links não vazios | Acrescentar; duplicatas são rejeitadas |
| remove com links não vazios | Remover vínculos existentes; ausência é erro |
| replace com predicate e links | Substituir somente os vínculos desse predicado |
| replace com links=[] | Limpar a coleção opcional do predicado |
| RelationshipReplace com links=[] | Limpar todos os vínculos opcionais; falha se mínimos obrigatórios forem violados |

Cada operação exige origem correta e proíbe inversas derivadas, mesmo se uma
operação posterior tentasse ocultá-las. replace exige predicado autorizado e que
todos os seus vínculos usem esse predicado. O estado final é revalidado; substituir
referência obrigatória pode remover/adicionar dentro de uma operação atômica, mas
não deixar Instance sem Work ou Item sem Instance no perfil atual. Falha não altera
os objetos de entrada. A função não persiste nada e não executa commit.

Igualdade de vínculo usa proprietário, predicado, identidade de destino e conjunto
de papéis (ordem não altera função). Publicação também considera activity_key.
Rótulo provisório não define identidade: namespace/key a define durante a importação.
URI e UUID conhecidos detectam duplicatas; aliases complementares exigem resolução.
`apply_resolved_relationship_update` normaliza ambos para identidade armazenada antes
de adicionar/remover, revalida resultado e retorna pendências. Remover por URI um
alvo originalmente enviado por UUID é testado. Remoção não apaga entidade compartilhada.

Os DTOs `WorkUpdate` etc. permanecem compatíveis com ADR 0017: ausência preserva,
lista substitui integralmente, null remove propriedade opcional. O serviço futuro
escolherá uma dessas superfícies por operação e sempre validará estado completo.
Não combinar implicitamente PATCH de propriedade com operações de coleção.

## Camadas de validação e limites

Estrutural/Pydantic: modalidade, IRI/UUID, campos obrigatórios, ausência/null,
discriminadores, origem/destino declarado, predicado autorizado, auxiliares/papéis,
cardinalidade, duplicatas conhecidas e autorreferências conhecidas.

Aplicação: `ReferenceResolver.resolve` recebe referência local e devolve
ResolvedEntity com ResourceIdentity armazenada, tipo real e subclassificação opcional
de Agent. `validate_references` verifica existência, identidade coerente, tipo real,
Organization em held_by, duplicatas após resolução e whitelist de papéis. Uma
referência externa é devolvida como pendência, nunca acessada na rede; classe
informada continua uma afirmação a verificar semântica/institucionalmente.
Não reconciliadas exigem `allow_unreconciled=True` como política explícita de rascunho.
Isso não autoriza gravar um grafo inválido no serviço RDF existente.

Semântica: `validate_cycles` verifica translationOf/broader na closure de vínculos
fornecida; relatedTo/related permitem ciclos. A aplicação futura deve resolver aliases
e carregar a closure transitiva relevante dentro da transação. Um subconjunto não
comprova ausência global de ciclo. As shapes locais continuam verificando o grafo
final; Pydantic não substitui SHACL, existência PostgreSQL ou controle de revisão.

O mínimo padrão 1 de instanceOf/itemOf reproduz monograph-v1.1, mas o contexto
confiável `{"minimums": {}}` permite demonstrar que não é axioma ontológico. Limites
adicionais de perfil dependem de #20/#21. A estrutura da superfície atual tem máximo
1 nesses dois predicados, como os DTOs existentes. Outro perfil com limites diferentes
precisará de contrato/registro explicitamente configurado, não relaxamento implícito.

Antes de gravar: resolver referências locais; aplicar operação ao proprietário
vigente; validar resultado, closure e SHACL; conferir revisão esperada/CAS; criar
snapshot imutável e commit/rollback no serviço transacional. Não manter duas escritas
para inversas. Não apagar/fundir uma entidade referenciada sem política explícita
(#17). Autoridades compartilhadas são legítimas; atualizar seus metadados não copia
sua descrição nem revisa automaticamente todas as obras.

## Integração futura e domínio operacional

#17 consolidará resolução pública, redirects/tombstones e identificadores externos,
reutilizando UUID/URI armazenada. #18 mapeará predicados completos e caminhos auxiliares
para JSON-LD/RDF, preservando URIs, papéis, activity_key como agrupamento privado,
literais e dados fora da superfície. Referência não reconciliada não recebe URI
fictícia nem é convertida silenciosamente em literal bf:agent/subject. JSON-LD terá
contextos locais; parsing usa o adaptador limitado, sem imports/contextos remotos.
Conversões futuras exigem isomorfismo, não igualdade textual.

#20/#21 aprofundarão política de obrigatoriedade, vocabulários, subclasses, ciclos
institucionais e conformidade SHACL. Artefatos atuais não foram reescritos.
Não se implementou serializador novo, motor SHACL, editor ou endpoints.

Instance–Item representa cópia bibliográfica. Disponibilidade, reservas, multas,
empréstimos, leitores e políticas patrimoniais pertencem a módulos operacionais.
As URIs e metadados permitem navegação e projeções futuras, sem dependência de
Elasticsearch. O protocolo não acessa tabelas de outro módulo nem cria esquema físico.

## Exemplos e testes

Fixtures versionadas em `tests/fixtures/bibliographic/relationships/`, divididas
entre `valid/` e `invalid/`. O manifest identifica schema, camada de rejeição e estado
atual/contagem esperada nas operações. Todos os arquivos são carregados pela suíte;
nenhum JSON é somente ilustrativo. Identidades e dados são sintéticos.
Em uso real, todos os alvos locais dos exemplos devem existir com o tipo indicado;
a validade estrutural do arquivo não comprova essa pré-condição.

`resource-work-create`, `resource-instance-create` e `resource-item-create` mostram
criação sequencial com WorkCreate → InstanceCreate(instance_of) → ItemCreate(item_of).
A aplicação deve alocar/guardar a identidade de Work antes da referência da Instance
e a identidade da Instance antes da referência do Item; não são inversas graváveis.
`work-instance-read` e `instance-items-read` mostram navegação sem incorporação.
`work-agents`, `work-create`, `work-related`, `instance-create`, `external-subject`,
`unreconciled-agent` e `publication` cobrem multiplicidade, assuntos, obras/instâncias,
URIs externas, papéis e publicação. `work-replace` mostra substituição completa;
`patch-*` cobre ausência, lista vazia, adição, remoção, substituição e limpeza.
`resource-work-read/update/null` confere também a compatibilidade M03.01.02.

`invalid/nonexistent` é estruturalmente válido; requer que o resolvedor não encontre
o alvo 999. `incompatible-identity` depende do tipo real do alvo retornado.
Os testes usam MemoryResolver com identidades sintéticas 1–8, explicitamente um
double em memória. Não simula nem comprova existência em PostgreSQL. Exemplos de
tipo errado, cardinalidade, autorreferência, duplicação, URI, papel e null falham
estruturalmente; remoção inexistente/adição duplicada falham após aplicação ao estado.

Da raiz, executar as ferramentas configuradas:

```bash
cd apps/api
uv run pytest ../../tests/api/test_relationships.py
uv run pytest
uv run ruff check . ../../tests
uv run mypy src
```

Se uv/Snap estiver indisponível mas o ambiente já estiver sincronizado, usar
`.venv/bin/pytest`, `.venv/bin/ruff` e `.venv/bin/mypy`. O teste de JSON Schema cobre
discriminadores/nulidade; a suíte catalográfica existente continua cobrindo FastAPI/
OpenAPI real em aplicação isolada. O registro declara metadados suficientes para
futuros serializadores, mas não afirma round-trip RDF desta nova superfície JSON.

A revisão individual dos nove critérios e os resultados executados estão no
[relatório de verificação](relationships-verification.md).
