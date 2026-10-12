# Identificadores e referências persistentes — M03.01.04 (#17)

Versão 1.0. Consolida ADRs 0009, 0011–0013, 0015, 0017–0019.
Política técnica implementável; homologação/publicação institucional pendentes.
Não define esquema bibliográfico definitivo nem identidade de usuário/OIDC.

## Diagnóstico inicial e escopo aplicado

Branch inicial: main, HEAD 2f2b61c43fc10c2f34452f7f43102de87d143116.
git status --short estava vazio. A comparação somente leitura com GitHub revelou
dois commits posteriores relacionados à #16. Não houve fetch Git, merge,
checkout, commit ou push. Arquivos da #16 foram consultados pelo conector GitHub.
Seus schemas, registro, aplicação, testes e fixtures foram incorporados ao checkout
como pré-requisito necessário para reutilizar ReferenceResolver e validar a
compatibilidade pedida, com documentação/ADR 0018. O relatório histórico de execução
da #16 não foi copiado nem apresentado como execução desta sessão.

| Situação inicial | Evidência / ação |
| --- | --- |
| Atendido: UUIDv4 e URI imutáveis | ResourceIdentity frozen; create preservado |
| Atendido: URI armazenada prevalece | RevisionStore.get/advance e BibliographicService.revise reutilizam URI |
| Atendido: revisões independentes, RDF nativo | ownership.py, Graph e perfis locais; ADRs 0009/0011/0015 |
| Atendido: UUID e URI únicos no protótipo | PK e UNIQUE em experimental_semantic_resources, migração 0001 |
| Parcial: validação de domínio | Aceitava UUID fora do tipo, host vazio, caracteres/escapes/portas inválidos; corrigido |
| Parcial: contratos #16 | Presentes no GitHub, ausentes no checkout; pré-requisito reaproveitado, sem formato paralelo |
| Ausente: política consolidada | Matriz, ciclo de vida, importação, HTTP, reconciliação e casos futuros documentados aqui |
| Inconsistência documental | bibliographic-model ainda registra UUID/URI como proposta histórica; ADR 0012 já decide a convenção |
| Futuro | Tombstones/aliases persistidos, APIs públicas, importação completa, domínio definitivo, #18 |

Arquivos novos próprios da #17: ADR 0019, esta especificação, relatório de
verificação, test_persistent_identifiers.py e fixtures identifiers.
models.py reforça invariantes; README e catalogographic-schemas apontam a política.
Pré-requisito #16 conserva os arquivos e formatos publicados, listados no relatório.
Serviços de revisão, ORM, migrações, perfis e frontend não exigem alteração.

## Vocabulário e convenção única

| Conceito | Exemplo ilustrativo | Regra |
| --- | --- | --- |
| UUID interno | 00000000-0000-4000-8000-000000000001 | Opaco, imutável, único, sem reutilização |
| URI canônica | https://example.org/resources/00000000-0000-4000-8000-000000000001 | Identifica entidade, atribuída uma vez |
| URL de API | https://example.org/api/v1/works/00000000-0000-4000-8000-000000000001 | Endereço de operação/DTO futuro |
| URL HTML | https://example.org/catalog/works/00000000-0000-4000-8000-000000000001 | Documento humano futuro |
| URL JSON-LD/Turtle | https://example.org/documents/00000000-0000-4000-8000-000000000001.jsonld | Documento semântico futuro, não entidade |
| Identificador bibliográfico | ISBN transcrito, DOI, ORCID | Atributo estruturado, nunca PK automática |
| Revisão | UUID:r2 | Token de escrita do domínio, não URI nem ETag universal |
| Registro de origem | fonte/conjunto/chave/componente | Identifica registro/descrição na origem, não entidade por si só |

Work, Instance, Item, Agent (incluindo Person/Organization) e Subject
(skos:Concept) usam a mesma construção sem classe no caminho. UUIDv4 não depende
de título, nome, ISBN, localização, idioma ou revisão. Identidade e descrição
possuem ciclos distintos. Instanciação com UUID válido previamente atribuído
permanece suportada sem exigir versão 4 ou calcular URI de leitura.

RESOURCE_BASE_URI é configuração de novas alocações. ResourceIdentity.create
valida a base e acrescenta /UUID; armazenamento persiste o resultado exato.
Mudança de configuração não é migração nem autorização para reconstruir URIs.
Base histórica pode continuar coexistindo com base nova. Não normalizar/regravar
identidades por caixa, escapes, barra final ou tentativa de resolver via HTTP.
URI local não admite query/fragmento, mesmo delimitadores vazios, credenciais,
espaços/controles, escapes percentuais inválidos ou porta fora do intervalo.
HTTP(S) exige host. Auxiliares privados podem usar blank nodes ou URI-raiz#fragmento;
isso não cria outra identidade principal.

A instituição deverá controlar domínio, DNS, TLS, serviço de resolução, backups
e sucessão/migração de infraestrutura. Preservar controle das bases publicadas,
mesmo quando mudarem servidores e rotas de documentos. Publicação precisa de
responsável e política de retenção; não presumir domínio definitivo. localhost,
ambientes temporários e example.org são desenvolvimento/exemplos, sem promessa
de persistência pública.

## Matriz de identificadores

| Entidade | Identificador | Formato | Origem | Escopo de unicidade | Persistência | Mutabilidade |
| --- | --- | --- | --- | --- | --- | --- |
| Work/Instance/Item/Agent/Subject | UUID | UUID; geração v4 | Libris | Todas as identidades locais, incluindo reservadas | Par armazenado PostgreSQL | Imutável |
| Work/Instance/Item/Agent/Subject | URI canônica | HTTP(S) base/UUID | Libris | Namespace local inteiro, incluindo aliases históricos | Coluna uri e snapshots | Imutável |
| Todas | Revisão | UUID + inteiro positivo | Serviço transacional | Entidade + número | Revisões imutáveis | Nova revisão, sem sobrescrever |
| Instance | ISBN | Valor transcrito; chave derivada opcional ISBN-10/13 | Publicação/importação | Não global; pode ser compartilhado | bf:Isbn/rdf:value, bf:source | Correções com proveniência |
| Work/Instance conforme fonte/perfil | ISSN | Valor transcrito; padrão ISSN quando conhecido | Fonte serial | Esquema/contexto, sem dedup automática | bf:Identifier no perfil atual | Correções com proveniência |
| Entidade adequada ao objeto registrado | DOI | Valor original + https://doi.org/... quando aplicável | Agência/origem | Namespace DOI; conflito local revisado | bf:Identifier + fonte; catálogo futuro | Valor original preservado; novas afirmações |
| Agent/Person | ORCID/ISNI | Valor original; URI externa quando disponível | Registro de autoridade | Namespace e entidade alegada, sem PK local automática | Identifier e seeAlso existentes | Verificação/reconciliação versionadas |
| Agent | VIAF | Chave de registro/cluster + URI | VIAF | Namespace e escopo da origem | seeAlso ou Identifier estruturado | Cluster pode mudar, sem mudar UUID |
| Agent/Subject conforme classe | Wikidata | Q + dígitos; URI do item | Wikidata | Namespace e item, classe verificada | seeAlso existente | Novas afirmações, sem fusão automática |
| Item | Identificador Local/barcode | Texto e fonte | Instituição | Escopo institucional a definir | bf:Local no snapshot | Correções; não muda URI |
| Todas importadas | Registro de origem | Fonte/conjunto/chave/componente | Adaptador | Tupla de origem, não ISBN | Mapeamento futuro e proveniência | Histórico e sucessores, não sobrescrever origem |
| Referência provisória | namespace + key | IRI de origem + texto | Importação | Origem e papel/componente | Rascunho futuro | Reconciliação explícita |

ISBN/ISSN em linha indicam contexto bibliográfico; um perfil futuro pode oferecer
subclasses próprias sem acrescentá-las unilateralmente ao DTO atual. Mais de um
identificador por entidade é permitido. Um objeto bf:Identifier pertence à revisão
do proprietário, sem UUID/revisão principal próprios.

## Catálogo conceitual e normalização

Cada afirmação de identificador terá entidade proprietária, esquema/tipo, valor
original, URI aplicável, fonte, proveniência (registro/processo/instante/ator quando
disponível), estado de verificação, escopo de unicidade e reconciliação pertinente.
Este é catálogo conceitual futuro, não novos campos de API. DTO Identifier atual
oferece kind Identifier/Local/Isbn, value e source; provenance da entidade representa
prov:wasDerivedFrom. Proveniência técnica das revisões permanece separada.

Verificação: não verificado, verificado, inválido ou conflitante; anotar evidência
e instante. Verificação sintática/checksum não comprova titularidade, disponibilidade
ou equivalência. Disponibilidade externa pode mudar e não invalida identidade local.
Sem consultas HTTP na validação Pydantic ou no domínio.

Normalização futura é derivada, por esquema e versão, preservando valor original:
ISBN/ISSN podem remover separadores numa chave de comparação, com checksum opcional;
DOI pode remover somente prefixos de apresentação reconhecidos e produzir URI
https://doi.org/..., preservando conteúdo/escapes; ORCID e ISNI podem oferecer forma
de comparação padronizada, sem afirmar titularidade; VIAF e Wikidata conservam chave
e namespace de origem. URI Wikidata de entidade não é URL wiki de representação.
Não concatenar namespace/external_id arbitrariamente como se o provedor garantisse
essa convenção. Não aplicar lowercase universal, transliteração, URL decoding
indiscriminado ou normalização HTTP a identidades persistidas.
Valores históricos incompletos permanecem transcritos com estado apropriado;
não impor checksum ou regex fechada aos DTOs atuais.

## Contratos e integridade referencial

Reutiliza os [contratos #16](relationships.md), com extra=forbid:

```json
{"kind":"local","entity_type":"Work","internal_id":"00000000-0000-4000-8000-000000000001","uri":"https://example.org/resources/00000000-0000-4000-8000-000000000001"}
```

Local aceita UUID, URI ou ambos. Estrutura não prova existência. ReferenceResolver
é protocolo de aplicação sem HTTP/ORM; retorna ResolvedEntity com ResourceIdentity
armazenada, classe e eventual subtipo Agent. validate_references verifica inexistência,
UUID/URI simultâneos e tipo real, além das regras do vínculo. URI-only legada
`{"uri":"..."}` continua ResourceReference nos DTOs; a aplicação deve classificá-la
explicitamente pela identidade conhecida antes de montar vínculos tipados. Nunca
determinar localidade pelo prefixo, nem fabricar URI a partir de base atual.

```json
{"kind":"external","entity_type":"Agent","uri":"https://viaf.org/viaf/123","namespace":"https://viaf.org/viaf/","external_id":"123"}
```

External exige URI absoluta, admite URN/outros esquemas nos contratos atuais,
e exige namespace se external_id for informado. Namespace não é obrigatório para
link URI-only externo. Pode haver múltiplos links externos, inclusive conflitantes;
validade sintática não prova o tipo ou confiança. Não atribui UUID local.

```json
{"kind":"unreconciled","entity_type":"Agent","label":"Nome transcrito","namespace":"urn:libris:test:source","key":"record-42:agent-1"}
```

Unreconciled exige tipo esperado, rótulo/chave não vazios e namespace.
Não possui URI/UUID público. Apenas política explícita de rascunho permite a
pendência na aplicação; SHACL final pode recusá-la. Não gerar URI fictícia nem
converter bf:agent/subject em texto para contornar a pendência.

## Reconciliação e equivalência semântica

Estado conceitual de reconciliação é independente de kind do DTO e de estado da
identidade: pendente → candidata → confirmada/próxima/rejeitada/conflitante.
Os DTOs atuais não têm campos para esse workflow; kind distingue representação,
não todas as decisões humanas. Guardar futuramente evidência, autor, instante,
origem e decisão. Candidata não altera vínculo público. Confirmada transforma a
referência numa local resolvida ou externa confirmada após verificar tipo/identidade.
Próxima permanece distinta; rejeitada/conflitante conserva a referência de origem
e suspende associação automática. Reabrir decisão por nova evidência cria histórico.
Origem indisponível retorna pendência, não rejeição automática.

| Relação com fonte externa | Significado / política RDF |
| --- | --- |
| Mesma entidade comprovada | owl:sameAs somente com evidência suficiente e revisão institucional; não criado automaticamente |
| Conceitos próximos | skos:closeMatch quando ambos forem conceitos e o perfil permitir; não identidade |
| Conceitos equivalentes no esquema | skos:exactMatch conforme SKOS, sem promover automaticamente a owl:sameAs |
| Associação bibliográfica | Predicado apropriado bf:relatedTo/dcterms:relation; não equivalência |
| Link informativo | rdfs:seeAlso conforme ADR 0013 |
| Registro/descrição de terceiro | Identifier + fonte ou seeAlso; registro não é automaticamente pessoa/obra |
| Derivação de fonte | prov:wasDerivedFrom; não afirma identidade |

ORCID pode identificar pessoa; VIAF pode identificar cluster/registro; DOI pode
identificar objeto diferente da entidade esperada. Distinguir entidade, autoridade,
conceito, descrição e registro antes de afirmar correspondência forte.

## Ciclo de vida e histórico de identidade

| Estado conceitual | Identidade / descrição | Referências antigas e resolução futura |
| --- | --- | --- |
| Ativa | Descrição revisável, identidade fixa | Mesmo recurso; 303 para documento |
| Substituída | Nova entidade sem equivalência, relação explícita | URI antiga preservada; página histórica ou 410/tombstone, nunca 308 de fusão |
| Fundida | Duplicação comprovada; sobrevivente definido | UUID/URI antigos reservados; 308 para sobrevivente e histórico de decisão |
| Descontinuada | Sem uso corrente; histórico retido | 410/tombstone quando retirada; representação histórica separada |
| Removida logicamente | Visibilidade reduzida, sem apagar reserva | 410 quando publicável; acesso ao histórico conforme política |
| Reservada/tombstone | Identidade não pode ser realocada; metadados mínimos | Reserva sem publicação não precisa ser resolvível; retirada publicada mantém 410 |

Renomear/corrigir metadados e mover Item não altera identidade. Alterar classificação
descritiva também não altera; mudar tipo principal RDF não é permitido pelo serviço
atual. Reclassificação que implique outra entidade exige revisão humana e operação
futura explícita, sem usar URI tipada para compensar a mudança.

Fusão: registrar ambos os pares, sobrevivente, evidência, revisão esperada e autoria;
reconciliar vínculos em transações dos proprietários, com novas revisões. Não
reescrever snapshots históricos. Resolver identidade antiga deve retornar histórico/
alias explícito antes de usar referência canônica; o resolvedor atual exige igualdade
exata com URI armazenada e NÃO aceita silenciosamente alias de fusão. API futura
precisará de contrato explícito de resolução de alias antes de validate_references.
Detectar ciclos, alias conflitante e cadeia com destino retirado; apontar sempre
ao sobrevivente final preservando os passos históricos. Não reutilizar perdedores.

Substituição: preservar origem e apontar sucessor por relação sem identidade
forte; não reatribuir todas as referências sem decisão. Desmembramento: criar novas
identidades para resultados, registrar derivação e revisar cada vínculo segundo
contexto; sem escolher automaticamente um sucessor único.
Descontinuação/exclusão lógica conservam par e história. Retenção/publicação de
conteúdo depende de política institucional; reserva técnica mínima permanece.
Histórico de identidade não se confunde com snapshots de descrição.

## PostgreSQL: garantias atuais e futuras

Hoje: PK UUID global em experimental_semantic_resources; UNIQUE uri; PK composta
resource_id/number nas revisões; FK da revisão ao recurso e FK composta diferida
da revisão corrente; trigger contra UPDATE/DELETE de revisões; CAS+snapshot no
mesmo commit. RevisionStore recupera URI persistida, sem derivação da configuração.
Nenhum índice Elasticsearch participa dessas garantias.

Não há CHECK de correspondência lexical UUID/sufixo URI nem trigger de
imutabilidade do par: a aplicação conserva o par e o serviço não expõe atualização
de identidade. Validar par UUID/URI significa consultar armazenamento, não extrair
UUID de URL. Não afirmar que PostgreSQL impede mutação direta por administradores.

Futuro: reservar UUID e URI mesmo após remoção; namespace de aliases sem colisões
com URIs principais; restrições que impeçam reassociação; resolver referências
locais dentro da transação de escrita com política para fusão/descontinuação e
concorrência; mapeamento de origem único; proteção de par contra DML indevido.
IDs embutidos em JSONB não possuem FK relacional automática. Verificação antes
do commit deve evitar corrida com mudança de ciclo de vida (lock/versão).
Identificadores externos têm índices de busca por esquema/valor/fonte e regras
escopadas; conflitos alimentam revisão, não UNIQUE global de ISBN/ISSN.
Essas regras exigem persistência futura, não uma migração definitiva nesta issue.

## Resolução HTTP futura

URI não informacional identifica entidade bibliográfica; URL de documento
identifica sua representação. Todas as rotas abaixo são especificação futura.
Resolução começa por correspondência exata no catálogo persistido de URIs/aliases,
incluindo bases históricas; não reconstruir nem consultar domínio externo arbitrário.

| Situação | URI de identidade | Documento |
| --- | --- | --- |
| Ativa, formato suportado | 303 See Other + Location da representação | 200 + Content-Type correspondente |
| Identidade desconhecida | 404 | 404 |
| Accept sem formato aceitável | 406; informar formatos disponíveis | 406 se negociado |
| Retirada publicada | 410 e corpo/link tombstone conforme negociação | Documento tombstone acessível em URL própria com 200 |
| Fusão confirmada | 308 para URI sobrevivente, conforme ADR 0012 | Histórico da fusão acessível em documento separado |
| Substituição sem equivalência | Documento histórico por 303 ou 410 conforme retirada | Relação explícita ao sucessor, sem redirecionamento de identidade |

Suportar GET/HEAD; HEAD replica status/cabeçalhos sem corpo.
Accept: text/html, application/ld+json, text/turtle, com q e curingas; q=0 exclui
formato. Sem Accept ou */*: default documentado text/html. Empate escolhe preferência
documentada; nunca ignorar um 406. Vary: Accept em respostas cujo destino/corpo
dependam da negociação, incluindo 303 e erros negociados. URLs com formato fixo
podem dispensar Vary se a resposta não variar por Accept.

303 não prova equivalência com documento. 308 preserva método e é permanente:
usar somente identidade lida por GET/HEAD, nunca como reapontamento de operações
de edição/POST. Não pressupor que clientes seguem redirects; retornar Location
e links úteis. Evitar cadeias e loops; não derivar owl:sameAs de status HTTP.

Cache deve ter política explícita: 404/410/308 podem ser reutilizados por caches;
controlar max-age, revalidação e invalidação antes de ativar mudança de estado.
No lançamento, TTL curto para estados sujeitos a revisão; cache longo de 308 só
após confirmação institucional da permanência. Tombstone expõe somente dados
permitidos. ETag de documento depende de bytes/formato/revisões compostas;
UUID:rN não é ETag forte universal. Histórico e alias preservam identidade,
enquanto URLs de documento podem mudar de infraestrutura.
ADR 0012 permanece; fusão reversível não é resolvida aqui silenciosamente:
exigirá ADR de evolução e plano para caches antes da publicação.
Referências: [HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html) e
[Cool URIs](https://www.w3.org/TR/cooluris/).

## Importação, migração e exportação futuras

Persistir tupla fonte/conjunto/chave de registro/componente → UUID/URI local,
com versão/hash do material de origem e proveniência. Um registro pode produzir
Work, Instance e autoridades distintas, portanto chave do registro sozinha não
garante idempotência das entidades. Fonte pode mudar chaves: adicionar mapeamento
sucessor com evidência, mantendo alias/histórico da origem.

Reimportação idêntica recupera os mesmos pares e evita revisão vazia; mudança
de metadados cria revisão só dos proprietários afetados, com CAS. Mudança de ISBN/
ORCID/VIAF não troca UUID/URI: atualizar afirmações e conservar origem/histórico.
Concorrência de duas importações deve ser arbitrada pela unicidade da tupla e
transação, não somente por busca seguida de criação.
Registros de fontes diferentes que compartilham ISBN geram candidatos, sem fusão
automática. Deduplicação exige evidência da mesma entidade/classe e decisão rastreável.

Após fusão, origem perdedora continua mapeada/reservada; reimportação resolve
alias/sobrevivente explicitamente, sem recriar entidade perdida. Referências
históricas continuam descrevendo suas revisões originais. Substituição/desmembramento
exigem contexto para escolher destino, sem heurística por um identificador.
Importação pendente conserva namespace/key/rótulo e evidência até reconciliação.
Sem integração VIAF/Wikidata/ORCID ou pipeline MARC completo nesta etapa.

Migração de aplicação/host conserva UUID/URI armazenados. Migração de domínio
público precisa manter controle da URI antiga e especificar aliases/resolução;
alterar RESOURCE_BASE_URI só afeta novas entidades. Exportação usa @id/URI
original e proveniência permitida. Nunca substituir tudo pela base corrente.

## BIBFRAME, JSON-LD e projeções

URI armazenada é sujeito RDF/@id da entidade e objeto RDF de referências
resolvidas. Instance → bf:instanceOf → Work; Item → bf:itemOf → Instance.
Work → bf:contribution → bf:Contribution → bf:agent → Agent, com bf:role
no auxiliar; Work → bf:subject → Subject/skos:Concept. Inversas são derivadas.
Identifier, Contribution, Title e Publication conservam estruturas privadas,
idiomas, datatypes e multivalores; não achatar em strings.

Fixtures identifiers/*-read.json são DTOs atuais executáveis das cinco entidades.
references.json demonstra três modalidades e compatibilidade URI-only.
entities.ttl e entities.jsonld são grafo ilustrativo equivalente, com JSON-LD
expandido sem contexto remoto, produzido pelo adaptador existente. Não são contrato
final da #18 nem snapshot proprietário único: compõem cinco entidades. Os testes
extraem snapshots proprietários e conferem os perfis locais e isomorfismo.
ORCID/VIAF/Wikidata são links sintéticos, sem alegar titularidade da pessoa fictícia.
lifecycle-proposal.json é proposta futura explícita, sem DTO/endpoint implementado.

#18 detalhará serialização da superfície de edição, contexto local versionado,
tratamento de pendências e preservação de RDF fora dos DTOs. Parsing sempre passa
pelo adaptador limitado, sem importar contextos/shapes remotos.
Outras ontologias mantêm namespaces inequívocos e não mudam identidade canônica.

Descoberta futura recebe UUID, URI persistida, revisão e estado público; URLs
de UI ficam derivadas na representação. Elasticsearch não atribui identidades.
Outbox e consumidor idempotente por entidade/revisão serão introduzidos no
primeiro caso real; reconstrução a partir de PostgreSQL conserva pares, aliases
e estados sem reviver entidades retiradas. Nenhum índice definitivo criado aqui.
