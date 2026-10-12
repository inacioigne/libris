# ADR 0021 — Perfis catalográficos declarativos e resolução por release

Status: aceito para implementação técnica da #20; homologação institucional pendente

Data: 2026-10-12

## Contexto

ProfileField/ProfileResource/CatalogProfile e seus artefatos locais já descrevem
campos RDF, cardinalidades e shapes. O formato antigo acopla requiredInForm,
repeatable e absent ao mínimo/máximo. Não possui composição, seleção ou separação
entre identidade de família, release e versão do formato. monograph-v1 é ainda
mais antigo e não satisfaz diretamente o CatalogProfile atual. Releases estão
referenciadas por revisões históricas e não podem mudar de significado.

## Decisão

Acrescentar formato JSON **libris.catalog-profile 2.0**, publicado por
`domain/profiles.py` junto dos contratos históricos. Pydantic v2 gera schemas;
validadores cruzados e registros de domínio verificam o que JSON Schema não
expressa. `profile_contract.py` descreve entrada e resposta resolvida;
`profile_registry.py` interpreta configuração confiável, sem HTTP, ORM, arquivos,
RDFLib/pySHACL ou serviços. Infraestrutura lê somente artefatos do pacote.

Graph RDFLib continua canônico. Uma definição descreve edição de propriedades do
grafo, não registros nem entidades persistentes. Literais textuais/com idioma,
tipados, referências e auxiliares são variantes discriminadas. Title, Contribution,
Identifier e Publication conservam nós, classes e predicados, não strings achatadas.

Três responsabilidades: registro semântico declara superfície suportada e limites
do contrato Libris; policy acrescenta regras catalográficas; presentation orienta
formulário. required_in_form e condições de required são preferências/políticas do
formulário, sem impor automaticamente mínimos RDF. Cardinalidades de policy são
políticas do perfil; a ontologia não recebe cardinalidades institucionais universais.
Shapes SHACL locais e versionadas continuam independentes e autoritativas para
validar o RDF concreto. A #21 deverá completar a aplicação semântica das políticas.

Herança simples por **base_release**, nunca nome de arquivo, família implícita ou
classe Python. Merge por classe RDF e nome de campo; adições são livres dentro do
registro confiável, sobrescritas exigem overrides e identidade semântica igual.
Uma política somente pode ser restringida se o campo base declarar specializable.
Seções/grupos podem ser reorganizados. Ciclos, duplicações, referências inexistentes,
conflitos, derivações graváveis e enfraquecimento dos limites são rejeitados.
Entrada declarativa e perfil resolvido têm discriminadores e schemas distintos.

Registro semântico JSON local para BIBFRAME, RDF/RDFS, XSD, SKOS, DCTerms,
Schema.org e PROV-O; URI absoluta identifica propriedade, prefixo é alias validado.
Origens/destinos são a superfície **suportada pelo Libris**, não uma transcrição dos
domínios/ranges completos das ontologias. Termos desconhecidos falham; extensões
precisam de registro confiável revisado. Termos deprecated/review_required não são
usados por novos perfis. Não baixar ontologias, vocabulários, contextos ou shapes.
Não se implementa plugin de ontologias nem reconciliação externa (#24/#25).

Família id, release_id, release, format_version, bibliographic_contract e release
SHACL são distintos. Releases candidatas/publicadas/usadas e bases fixadas são
imutáveis quanto ao conteúdo. O registro copia entradas/saídas; operações retornam
outro registro. Transição explícita de disponibilidade muda somente status/sucessora,
preservando campos, interpretação e shapes; o registro anterior permanece acessível.
Fingerprints SHA-256 fixam o conteúdo das releases do pacote e suas bases
transitivas; o carregador detecta divergência/remoção e o gerador não sobrescreve
locks existentes. Não é um workflow persistido nem modifica revisões. Depreciação não redireciona
seleção explícita. Mudança de conteúdo exige nova release e análise conservadora
por compare_profiles. Não há migração implícita nem reescrita de snapshots.

O adaptador SHACL acrescenta contexto de snapshot/composição e correlação por
classe do foco/resultPath, conservando erros fora do formulário. Executa o mesmo
pySHACL e somente mapeamentos locais permitidos; não traduz policy em shapes nem
implementa o contrato definitivo de erros da #22. APIs candidatas são documentadas,
com OpenAPI em aplicação de teste, sem registrar rotas na aplicação real.

## Alternativas consideradas

- Sobrescrever o formato antigo: quebra releases e obriga reinterpretação histórica.
- Uma união que relaxa invariantes legadas: arrisca aceitar descritores antigos incoerentes.
- YAML: acrescentaria parser/dependência sem necessidade; JSON já é adotado.
- Herança múltipla e subclasses Python: conflitos desnecessários e novos perfis exigiriam código.
- Gerar SHACL automaticamente ou consultar ontologias: duplica responsabilidades da #21/#25.
- CRUD/tabelas/React agora: antecipa infraestrutura sem caso autorizado.

## Compatibilidade e consequências

Modelos públicos antigos e aliases mantidos; schema antigo é preservado. O adaptador
v1 completa somente a visão de metadados ausentes, conservando id/arquivo original.
Não torna a candidata v1.1 a regra de validação de v1. Os sete JSON/TTL históricos
e o schema anterior são protegidos por hashes de teste. validate_profile,
validate_monograph, ValidationIssue e ValidationReport continuam compatíveis.

Novos perfis usam JSON e componentes já registrados. Novos auxiliares/datatype
não suportado exigem adaptação deliberada futura. Perfis externos aos DTOs atuais
podem orientar edição RDF futura, mas não acrescentam campos mágicos aos DTOs nem
mapeamentos de serialização. Rótulos/idiomas/IRIs/datatype/nós existentes permanecem
sem normalização. Sem novas dependências, tabelas, filas, downloads ou frontend.

A garantia de imutabilidade vale para operações sobre o registro em memória e
artefatos históricos protegidos por testes/revisão. Não promete impedir edição
manual de arquivos ou DML: publicação administrativa/persistência/auditoria são
trabalhos posteriores. Bases e conjuntos SHACL devem ficar disponíveis junto das
releases que os utilizam. Homologar exemplos antes de catalogação institucional.

Ver [referência do contrato](../architecture/catalog-profiles.md),
[evidências](../architecture/catalog-profiles-verification.md) e
[issue #20](https://github.com/inacioigne/libris/issues/20).
