# ADR 0008 — Snapshots JSON-LD em JSONB e revisões experimentais

Status: aceito para o protótipo experimental; não é esquema bibliográfico definitivo

Data: 2026-10-09

## Contexto e evidência

ADRs 0003/0004 mantêm PostgreSQL autoritativo e adiam triplestore. O protótipo
RDFLib passou round-trip isomórfico JSON-LD/Turtle de um grafo sintético de 49 triplas,
com idiomas, repetição, URIs externas, datatype e blank nodes. A integração com
PostgreSQL 17 real comprovou o mesmo isomorfismo após JSONB, histórico e concorrência.

| Alternativa | Integridade e consultas | Versionamento e manutenção |
| --- | --- | --- |
| JSON-LD expandido em JSONB | Termos explícitos; JSONB suporta inspeção JSON, sem SPARQL. Ordem de arrays preservada; ordem de chaves irrelevante | Snapshot por revisão; biblioteca RDF já disponível; consulta semântica limitada |
| Turtle em TEXT | Grafo fiel, inspeção humana; toda consulta exige parsing ou projeção | Snapshot simples; menos capacidade de inspeção SQL; prefixos/ordem não são identidade |
| Tabela genérica de triplas | Exigiria modelar URIs, blank nodes, datatypes e idiomas e muitos joins | Versionamento e integridade mais complexos; sem necessidade comprovada |
| Colunas bibliográficas específicas | Boas restrições e consultas operacionais; esquema muda por propriedade | Risco de perda/extensão prematura; inadequado para este protótipo |
| Triplestore | Consultas SPARQL e travessias | Novo serviço e consistência distribuída, sem carga que justifique |

## Decisão

Dois objetos experimentais: `experimental_semantic_resources` (UUID, URI única,
revisão atual) e `experimental_semantic_revisions` (recurso+número, JSONB, UTC,
origem, processo, perfil versionado). Sem tabela genérica de triplas ou colunas
bibliográficas. Cada revisão representa um snapshot completo de um grafo agregado
com URI raiz Work, Instance ou Item. O exemplo agrega Work/Instance/Item, seus nós
auxiliares e um assunto SKOS; não são três agregados com controle independente.

JSON-LD expandido dispensa contextos de rede e torna explícitos `@id`, `@value`,
`@language` e `@type`. Não converter literais em números nativos JSON. Conferir
isomorfismo antes de persistir. U+0000 é rejeitado explicitamente, pois JSONB do
PostgreSQL não o suporta. Falhas interrompem e revertem a transação.

`BibliographicService` controla transações. Atualização condicional
`WHERE current_revision = expected_revision RETURNING uri` avança a versão e
insere snapshot na mesma transação. Gravação obsoleta/ausente gera
`StaleRevisionError`; falha de validação reverte o avanço. PK composta impede
números duplicados. FK composta diferida garante que revisão atual pertence ao
recurso e existe no commit. Um trigger impede UPDATE/DELETE de revisões por DML
normal. Isso não substitui permissões operacionais, backups ou segurança contra
administradores/superusuários capazes de remover triggers ou executar TRUNCATE.

Migração 0001_semantic é explícita e reversível. Nenhuma migração ou create_all
executa no startup. As tabelas são experimentais e não modelam inventário/circulação.
Proveniência registra origem e processo técnico explicitamente informados, sem
identidade fictícia de usuário; os campos podem futuramente alimentar PROV-O.

## Consequências e limites

Revisões são append-only; não há API de exclusão ou retenção. Downgrade descarta o
histórico experimental e deve ser usado somente quando essa perda for intencional.
Regras de fusão/redirecionamento, controle independente dos três recursos,
transações entre agregados, autorização, ETags HTTP, índices semânticos e seleção
dinâmica de perfis ficam para outras etapas.

O ensaio demonstra fidelidade dos casos testados, não desempenho corporativo,
compatibilidade com todos os recursos JSON-LD ou escala de milhões de registros.
Antes de estabilizar o esquema, testar perfis institucionais, tamanho dos grafos,
consultas reais, múltiplos agregados e custo do histórico. Não projetar Elasticsearch
nesta etapa. Grafos derivados de revisões são retornados isoladamente; snapshots
não são compartilhados como estruturas mutáveis em memória.
