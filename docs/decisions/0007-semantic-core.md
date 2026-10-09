# ADR 0007 — Núcleo RDF, perfil monográfico e identidade persistente

Status: aceito para a Etapa 2

Data: 2026-10-09

## Contexto

ADR 0002 exige BIBFRAME nativo. Dicionários de campos simples perdem datatypes,
idiomas, repetição e blank nodes. O perfil mínimo não pode impor regras universais
à ontologia nem impedir Dublin Core Terms e SKOS.

## Decisão

Usar RDFLib Graph diretamente para RDF 1.1 de um grafo, com serialização JSON-LD
expandida e Turtle. Toda exportação é interpretada novamente e comparada por
isomorfismo antes de ser aceita. Usar pySHACL com shapes locais versionadas, sem
inferência, imports, regras avançadas ou JavaScript. O relatório conserva o grafo
SHACL e fornece foco, caminho, severidade e mensagens estruturadas.

Separar `monograph-v1.json` (descrição de formulário) de `monograph-v1.ttl`
(regras semânticas). O perfil exige título de Work/Instance, uma relação
instanceOf/itemOf e suas inversas consistentes. Identificação de Item é recomendada,
com advertência; idioma, assunto e publicação não têm obrigatoriedade universal.
As cardinalidades unitárias são escolhas deste perfil experimental, não de BIBFRAME.
Outras propriedades são preservadas e não fechamos shapes com `sh:closed`.

UUID interno separado de URI HTTP(S). `RESOURCE_BASE_URI` provisória usa
`http://localhost:8000/resources`. A URI é materializada e armazenada na criação;
leituras e revisões reutilizam a URI armazenada, mesmo após mudança da configuração.
Título, idioma, ISBN e localização não participam da identidade. Não reescrever URIs
externas. Resolução HTTP, domínio público e migração de URIs exigem decisão futura.

## Consequências

O domínio contém identidade e proveniência e não depende de RDFLib ou FastAPI.
Os adaptadores usam bibliotecas existentes. Não existe editor nem endpoint novo.
Um formato de perfil está disponível, mas somente monograph-v1 possui validador
implementado; seleção dinâmica e carregamento de shapes arbitrárias ficam adiados.

Entrada limitada a 1 MiB por padrão (`RDF_MAX_DOCUMENT_BYTES`, máximo 10 MiB).
Contextos somente como objetos embutidos locais; URLs, listas de contextos,
`@import`, `@reverse`, `@graph` e aliases desses mecanismos são rejeitados antes
do parser. Inclusive wrappers `@graph` são rejeitados: utilizar array expandido.
Não aceitar datasets/named graphs sem modelar explicitamente sua identidade.
O parser recebe dados em memória e somente plugins Turtle/JSON-LD, nunca paths/URLs.
Isso evita resolução externa durante o processamento; não é uma garantia sobre
outros plugins ou chamadas diretas à biblioteca fora do adaptador.

RDFLib pode normalizar formas lexicais numéricas na entrada. Exportação de termos
que não sobrevivem ao round-trip exato de termos é rejeitada. Não preservamos texto,
ordem, comentários, prefixos nem nomes arbitrários de blank nodes da serialização.
Preservamos o grafo por isomorfismo. Ver limitações em `semantic-foundation.md`.

## Referências consultadas

- [Modelo oficial BIBFRAME](https://www.loc.gov/bibframe/docs/bibframe2-model.html).
- [Ontologia publicada pela Library of Congress](https://github.com/lcnetdev/bibframe-ontology/blob/master/bibframe.rdf):
  classes e propriedades utilizadas pelos exemplos e perfil. O acesso HTML a
  id.loc.gov retornou 403 nesta sessão; foi consultado o repositório oficial.
- [pySHACL: opções de validação](https://github.com/RDFLib/pySHACL).
