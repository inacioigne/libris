# ADR 0019 — Identificadores e referências persistentes

Status: aceito para o contrato técnico da M03.01.04 (#17); publicação institucional pendente

Data: 2026-10-11

## Contexto e problema

ADRs 0007–0015 já estabelecem UUID, URI persistida, PostgreSQL autoritativo,
Graph RDFLib e revisões independentes. ADRs 0017/0018 definem DTOs e referências.
Falta consolidar ciclo de vida, identificadores externos, importação e resolução.
O checkout inicial 2f2b61c ainda não contém a #16, publicada dois commits depois.
Seus contratos e testes foram reaproveitados como pré-requisito local, sem merge,
troca de branch ou alteração do histórico. Não se criou uma segunda estratégia.

## Decisão

Manter UUIDv4 gerado por ResourceIdentity.create e URI
`{RESOURCE_BASE_URI}/{uuid}` para Work, Instance, Item, Agent e Subject.
Atribuir e persistir o par uma única vez. Metadados, classificação, localização,
revisão ou configuração posterior não o alteram. UUID aceito em leitura não é
restrito à versão 4: não invalidar identidades previamente atribuídas.

URI local é HTTP(S), absoluta, sem query, fragmento, credenciais ou caracteres
inválidos. Validação não normaliza strings nem exige reconstruir a URI pelo UUID:
o par armazenado é autoritativo, inclusive em bases históricas. Separar URI da
entidade, URLs de documentos/API/UI, revisão e chave na origem.

Reutilizar LocalReference/ExternalReference/UnreconciledReference e o protocolo
ReferenceResolver da #16. UUID e URI simultâneos devem corresponder ao mesmo par
armazenado; classe declarada deve corresponder ao tipo real. Nunca inferir
localidade por prefixo. Forma legada URI-only continua aceita nos campos atuais.
Referências externas não são consultadas na validação e não tornam uma entidade
local. bf:Identifier continua estrutura RDF privada, distinta da identidade técnica.

Documentar estados ativa, substituída, fundida, descontinuada, removida logicamente
e reservada/tombstone. Preservar UUID, URI, histórico e aliases sem reutilização.
Fusão exige evidência de mesma entidade e sobrevivente; substituição sem
equivalência não redireciona como fusão. Desmembramento atribui novas identidades
às entidades resultantes e conserva a origem/histórico. Não criar workflow ou tabelas.

Preservar ADR 0012: URI não informacional ativa usa 303 para documento negociado;
documentos usam 200; fusão comprovada usa 308 para a identidade sobrevivente.
308 é permanente, pode ser armazenado em cache e preserva método: exige decisão
confirmada e serviço de identidade somente leitura. Não o usar para candidato,
correspondência aproximada, erro catalográfico ou substituição. Uma política
reversível exigiria novo ADR antes de publicar redirecionamentos permanentes.
Tombstones e aliases conservam a identidade antiga, sem criar equivalência OWL.

Idempotência de importação será escopada por fonte, conjunto, chave de registro
e componente/entidade do registro. Persistir futuramente esse mapeamento e
proveniência na mesma transação. ISBN/ISSN e outros valores compartilhados não
autorizam deduplicação automática nem unicidade global.

## Alternativas avaliadas

| Alternativa | Avaliação |
| --- | --- |
| UUIDv4 atual | Biblioteca padrão em Python 3.13, dados e testes compatíveis; aleatório, sem ordem temporal, menor localidade no índice |
| UUIDv7 futuro | Ordenação temporal favorece localidade; inclui instante, exige avaliar relógio, concorrência, exposição temporal e ganho real |
| URI tipada /works/UUID | Acopla identidade à classificação, contraria ADR 0012; rejeitada |
| ISBN/ORCID como chave primária | Identificadores descrevem escopos distintos, podem mudar/conflitar; rejeitada |
| HTTP 200 direto na identidade | Alternativa Linked Data possível, já preterida pelo ADR 0012 |
| owl:sameAs automático | Evidência insuficiente e confusão entidade/registro; rejeitada |
| Tabelas definitivas de identidade | Anteciparia persistência fora da etapa; rejeitada |

UUIDv7 está na biblioteca padrão a partir de Python 3.14; a referência 3.13
precisaria biblioteca adicional. Nenhuma dependência nova é justificada agora.
Adoção futura somente para novas alocações, com benchmark PostgreSQL, compatibilidade
3.13/3.14 explicitada e ADR. UUIDv4 existente nunca é convertido; versão do UUID não
é token de revisão, data autoritativa, segredo ou regra de autorização.
Ver [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562.html) e
[Python uuid](https://docs.python.org/3.14/library/uuid.html).

## Consequências, riscos e limites

Validação de domínio foi reforçada sem HTTP/ORM. Contratos existentes são
preservados; entradas antes toleradas mas inválidas passam a falhar explicitamente.
Não há migração física, alteração de locks, endpoints públicos ou serializador novo.
Restrição SQL existente garante UUID/URI únicos enquanto registros são retidos;
não garante sozinha não reutilização após remoção administrativa ou restauração.
Persistência futura deve reservar também aliases e tombstones e impedir mutação
da identidade por DML autorizado. Integridade referencial precisa da transação real.

Domínio/DNS/TLS, sucessão institucional, retenção histórica, publicabilidade e
permissões de fusão/descontinuação permanecem decisões institucionais. Perda de
domínio, caches de 308 e backups incompatíveis ameaçam persistência pública.
localhost e domínios de exemplo não oferecem garantia pública.

#18 implementará adaptação dos DTOs e representação JSON-LD/RDF, preservando
auxiliares, propriedades fora da superfície e isomorfismo. API/ciclo de vida,
importações, reconciliação, persistência definitiva e descoberta são entregas
posteriores. Elasticsearch será reconstruível e receberá UUID/URI persistidos,
com outbox no primeiro caso real conforme ADR 0015.

A [especificação](../architecture/persistent-identifiers.md) detalha regras e a
[verificação](../architecture/persistent-identifiers-verification.md) separa
comportamento executado de casos futuros.
