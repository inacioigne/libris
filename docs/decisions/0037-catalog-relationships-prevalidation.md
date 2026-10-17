# ADR 0037 — Relações HTTP e pré-validação sem escrita

Data: 2026-10-16. Status: implementado tecnicamente para M05.04 / #48.

## Contexto

As #16/#20/#21/#22 fornecem operações sobre vínculos, perfis fixados e diagnósticos.
A #47 fornece transação, gate PostgreSQL, CAS de conteúdo/estado e autoria confiável.
Reconstruir o snapshot por Read apagaria extensões; pré-validar por create/revise
criaria efeitos duráveis. As duas alternativas violariam os contratos existentes.

## Decisão

RelationshipService especializa CatalogService e usa `_revise` dentro de uma única
session.begin, com gate exclusivo antes dos locks. A consulta classifica localidade
por igualdade com identidades armazenadas, nunca por prefixo. URI externa continua
pendente de verificação; referência não reconciliada é recusada pela política atual.

As operações puras da #16 são aplicadas à coleção completa e resolvida. A alteração
RDF calcula diferenças entre vínculos antes/depois, preservando todas as demais
triplas. Publicações conservam lugar/data/anotações ao trocar somente agentes.
Remover uma contribuição anotada ou compartilhada é recusado em vez de apagar ou
realocar suas extensões. O fecho local das relações acíclicas é carregado sob o gate
existente e verificado pelo validate_cycles; não se alega fecho remoto.

Chaves de atividades baseadas em blank nodes são locais à representação: usa-se
canonicalização RDF para obter estabilidade entre leituras do mesmo snapshot.
Não são identificadores persistentes. ETag relacional usa namespace próprio,
projeção ordenada, ETag de conteúdo e geração editorial. Consulta com inversas é
explícita; seu ETag não substitui o validador da coleção própria no PATCH.

Pré-validação reutiliza a preparação DTO da #46 e validate_catalog. A preparação
comum não executa SHACL: create_to_graph continua exigindo a validação final.
Entradas RDF passam exclusivamente por parse_representation. Revisões existentes
usam BibliographicService.read autorizado. Nenhum caso chama create/revise/stores de
escrita. DTO usa SET TRANSACTION READ ONLY e resolvedor sem locks de escrita; testes
observam SQL e estado antes/depois no PostgreSQL real. Não há transação de escrita
simulada seguida de rollback como implementação de pré-validação.

Perfis usam metadata_revision.read do guard vigente; pré-validação usa capacidade
de criação do tipo e, para revisão existente, exige também leitura editorial.
Não se amplia enum de permissões nem se cria autenticador. Configured indica
presença no pacote; candidate/published/deprecated/draft vêm do registro. Não há
campo approved: o modelo não registra homologação institucional. A projeção legada
omite nomes de arquivos e publica referências de shapes por ID/release/contexto.

## Limites e consequências

A consulta opcional de inversas percorre snapshots correntes sob o gate shared;
não é índice de descoberta, nem promessa de escala. Perfis 2.0 podem ser
pré-validados e descobertos, mas continuam fora da escrita persistente histórica.
Limites de bytes/profundidade não constituem limite de CPU do pySHACL.

RDF não conserva namespace/external_id nem o tipo discriminado de alvos externos
com múltiplos tipos permitidos. O adaptador recusa esse caso com reference.unverified;
não inventa classe, identidade ou reconciliação. Uma extensão futura que conserve
esses metadados deverá ter contrato operacional próprio e transação versionada,
sem triplas fictícias no snapshot. Isso limita relações externas dcterms:relation
em Agent; alvos locais e predicados de destino único são suportados.

Sem dependências, migrações, alterações de releases históricos, frontend, indexação
ou administração de perfis. [Contrato HTTP](../architecture/catalogographic-http.md).
