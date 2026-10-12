# ADR 0018 — Referências tipadas e operações de vínculos bibliográficos

Status: aceito para implementação técnica da M03.01.03; homologação institucional pendente

Data: 2026-10-11

## Contexto

A M03.01.02 fornece DTOs de edição com referências somente por URI. Os ADRs
0009–0015 fixam identidades independentes, contribuições estruturadas, snapshots
proprietários e inversas derivadas. A issue #16 exige referências locais, externas
e não reconciliadas, integridade verificável e operações inequívocas. As issues
#17, #18, #20 e #21 continuam abertas, sem descrição retornada na consulta.

## Decisão

Acrescentar referências discriminadas por `kind` aos campos entre entidades dos
DTOs existentes, mantendo `ResourceReference` por URI para compatibilidade. Local
reutiliza UUID e URI armazenada existentes, sem gerar identidades ou estabelecer
resolução HTTP. Externa preserva URI, namespace e identificador externo opcional.
Não reconciliada tem rótulo e chave escopada à origem; não é URI persistente.

Definir metadados imutáveis em `domain/relationships.py`, sem importação de API,
HTTP, ORM ou infraestrutura. Os contratos Pydantic ficam em `api/schemas`, como
no ADR 0017. As funções de aplicação consomem esses DTOs independentes de HTTP e
um protocolo explícito de resolução; não há acesso a repositórios de outros módulos.
RDFLib Graph permanece o modelo semântico canônico.

Vínculos diretos, contribuições e agentes de Publication têm estruturas distintas.
O predicado contribution aponta para Contribution, não diretamente para Agent;
o registro informa o caminho contribution/agent e a classe auxiliar. Publication
preserva agrupamento por `activity_key`, chave privada do proprietário, sem nova
identidade persistente. As estruturas completas de publicação dos DTOs anteriores
continuam mantendo lugar e data. A coleção de vínculos não substitui o grafo completo.

Escrita é somente no proprietário: Instance instanceOf Work e Item itemOf Instance.
hasInstance/hasItem existem apenas na leitura composta. Propriedades simétricas
são sinalizadas como tais, sem inventar owl:inverseOf. A inversa de translationOf
é **translation**, conforme o RDF oficial consultado, não hasTranslation.

Create/Read/Replace representam estado completo dos vínculos de um proprietário.
Update recebe operações ordenadas add/remove/replace, aplicadas atomicamente em
memória, com revalidação do estado final. Campo omitido e operações vazias preservam;
null é rejeitado; replace de predicado com [] remove seus vínculos opcionais.
Os Update de recursos mantêm a política do ADR 0017: null limpa propriedade opcional.
São superfícies alternativas, sem aplicação simultânea implícita.

Limites unitários de instanceOf/itemOf seguem o contrato de edição atual. Mínimos
1 são política candidata monograph-v1.1, não axiomas BIBFRAME; o contexto confiável
de validação permite mínimos diferentes. Instâncias de RelationRegistry podem
representar outros limites de contrato/perfil. Ausência de Instance em Work é legítima.
Papéis são URIs, sem lista global fechada; perfis podem restringi-los explicitamente.

Extensões diretas exigem declaração confiável em namespace próprio, tipos e
cardinalidade; não aceitam redefinição de BIBFRAME/SKOS. Auxiliares de novas
ontologias exigirão um DTO próprio, não dicionário arbitrário. Requests não podem
registrar predicados ou enviar shapes/contextos remotos.

## Alternativas e consequências

Substituir todas as referências quebraria payloads existentes. Inferir localidade
por prefixo reclassificaria identidades após mudança de base. Um vínculo genérico
com papel opcional apagaria as estruturas de Contribution/Publication. Inversas
graváveis duplicariam a propriedade transacional. Adotamos contratos complementares,
compatibilidade explícita e metadados para futura serialização.

Validação Pydantic não prova existência. Resolução de aliases, classe real, ciclos
na closure completa e CAS devem ocorrer na aplicação dentro da transação de escrita.
O protocolo tem testes com double em memória, sem alegar consulta PostgreSQL.
Referências externas são pendentes e nunca baixadas; não reconciliadas só passam
pela integridade com política explícita de rascunho. Perfis/SHACL podem recusá-las.
Remover vínculo não remove a autoridade compartilhada. Exclusão/fusão de entidades
continua dependente da política de identidade da #17.

Não há endpoints, migrações, serializador novo, indexação, circulação ou dependências
adicionais. A #18 deverá preservar auxiliares e propriedades fora da superfície de
edição; #20/#21 definirão perfis e shapes locais versionados. Veja a
[especificação e matriz](../architecture/relationships.md).
