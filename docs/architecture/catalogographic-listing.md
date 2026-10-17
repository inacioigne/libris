# Listagens e representações catalográficas — M05.06 / #50

Complementa o [contrato HTTP v1](catalogographic-http.md), sem alterar os DTOs
Create/Read/Update nem a especificação 1.0.0. Decisão: [ADR 0039](../decisions/0039-catalog-listing-representations.md).
[Evidências datadas](catalogographic-m0506-verification-2026-10-16.md).

## Rotas e visibilidade

`collection` abaixo significa uma das cinco rotas concretas `works`, `instances`,
`items`, `agents`, `subjects`. Prefixo `/api/v1/catalog`.

| Método e caminho | Conteúdo | Autorização |
| --- | --- | --- |
| GET `/{collection}` | Página tipada de Read da revisão corrente | bibliographic:read + metadata_revision:read para Work/Instance/Item; authority:read + metadata_revision:read para Agent/Subject |
| GET `/public/{collection}` | Página tipada de Read da revisão publicada exata | Anônimo; read_public M04, estado published obrigatório |
| GET `/{collection}/{id}` | Read corrente ou snapshot RDF corrente | Mesmas permissões editoriais da coleção |
| GET `/{collection}/{id}/public` | Read publicado ou snapshot RDF publicado | Anônimo; read_public M04 |

Draft/in_review/approved, legado sem estado, withdrawn e archived não aparecem na
coleção pública; leitura pública individual devolve o mesmo 404 para esses casos,
inexistência ou coleção errada. Publicado com candidata continua mostrando a revisão
publicada anterior em todos os formatos. Listas não expõem estado, revisão candidata,
autor, proveniência técnica, auditoria ou contadores privados. Referências são somente
URIs, sem expandir conteúdo ou existência dos alvos. Propriedades de proveniência
bibliográfica presentes no snapshot são mantidas; ator/processo da revisão não entram
no RDF. Histórico continua nas rotas protegidas M05.05.

Tokens ausentes/inválidos/expirados no editorial → 401 + WWW-Authenticate: Bearer;
identidade válida sem todas as permissões → 403, antes de consultar o catálogo.
`system:admin`, papéis em headers e `include_drafts=true` não concedem acesso. Rotas
públicas são explicitamente anônimas e não promovem Bearer a escopo editorial.

## Filtros e navegação

| Parâmetro | Escopo | Contrato |
| --- | --- | --- |
| limit | Ambos | Inteiro, default 20, mínimo 1, máximo 100 |
| cursor | Ambos | Continuação opaca devolvida em next_cursor; 1–4096 caracteres |
| internal_id | Ambos | Igualdade por UUID imutável |
| uri | Ambos | Igualdade exata de URI persistida HTTP(S), sem reconstrução/normalização |
| profile | Ambos | ID exato do perfil do snapshot selecionado, 1–200 caracteres; desconhecido retorna página vazia |
| editorial_state | Editorial | draft, in_review, approved, published, withdrawn, archived; estado do registro, não candidate_state |

O tipo é fixado pela rota. Todos os filtros combinam por AND. Não há filtros de
texto, relacionamento, ISBN, campos RDF arbitrários ou nomes de coluna. Campos
extras e estrutura inválida retornam 422 Problem Details. Cursor malformado ou
incompatível retorna 400; cursor não concede acesso. `editorial_state` na rota
pública é extra proibido (422). Parâmetro omitido não restringe; vazio não é null;
`internal_id=null`/`uri=null` são inválidos e `profile=null` busca literalmente esse
ID, sem significado especial. Legado sem estado não satisfaz editorial_state=draft.

Resposta `application/json`, com `items` validado como lista do Read específico:

```json
{"items":[],"next_cursor":null,"limit":20,"order":"internal_id:asc"}
```

Ordenação total UUID ascendente, sem depender de título, nome ou data. UUID resolve
qualquer empate de campos bibliográficos; não há ordenação alternativa. Reenviar
**os mesmos filtros e limit**, acrescentando next_cursor como cursor. null encerra a
travessia. Não há total, offset ou URL com token. Identificadores e URI permanecem
nos Read; perfil é filtro, sem novo campo no DTO histórico.

Em conjunto estático não há omissões/duplicatas. Keyset usa `id > último UUID`.
Atualizar conteúdo não muda sua posição. Inserção com UUID antes do cursor fica
fora da continuação, e depois pode aparecer. Retirada/publicação ou mudança de
filtros de um registro muda sua participação entre páginas. Cada página tem visão
coerente de um statement MVCC; não é snapshot global entre requisições. Recomece a
consulta para refletir um catálogo alterado. Não se promete ordenação cronológica
por UUIDv4 nem paginação estável diante de todas as mudanças de participação.

## Negociação dos GET individuais

| Accept | Content-Type | Corpo |
| --- | --- | --- |
| ausente, `*/*`, `application/json` | application/json | Read operacional v1 com internal_id e uri |
| application/ld+json | application/ld+json | Snapshot proprietário integral, contexto local bibframe-v1 |
| text/turtle | text/turtle; charset=utf-8 | Mesmo snapshot RDF |

UUID permanece no contrato operacional e na associação persistida com a URI; não
se inventa predicado RDF para o UUID técnico. A URI armazenada é sujeito/@id e não
é recalculada pela configuração atual. JSON-LD e Turtle conservam idiomas, datatypes,
multivalores, IRIs auxiliares, referências e extensões do snapshot. Não reconstruir
exportação por Read: esse caminho perderia propriedades fora da superfície v1.
Nenhum contexto remoto é consultado. Ver [serialização M03](semantic-serialization.md).

Negociação reutiliza q, especificidade, curingas e preferência JSON → JSON-LD →
Turtle. q=0 específico vence curinga positivo. Accept vazio/malformado ou sem
alternativa suportada gera 406 Problem Details e Vary: Accept. Parâmetros de mídia
não oferecidos (por exemplo profile) não correspondem. Empates e outros limites
seguem o negociador M03. Vary inclui Accept em sucesso, podendo incluir Origin pelo
CORS. Listagens são exclusivamente JSON e não anunciam exportação RDF de coleção.

JSON editorial mantém ETag `catalog-v1-...`, utilizável no PATCH/commands If-Match.
RDF e JSON público usam `catalog-export-v1-...`, hash do formato e bytes efetivos;
seu uso como precondição de edição resulta em 412. Blank nodes podem gerar bytes
diferentes em exportações semanticamente equivalentes: não prometer ETag estável
por isomorfismo. No-store/private aplica-se inclusive ao público, preservando a
política M04 e evitando cache público obsoleto após retirada. POST/PATCH continuam
com seus contratos de JSON e não negociam exportações.

## Exemplos reproduzíveis

Com a API e um registro efetivamente publicado, defina apenas os valores locais:

```bash
API=http://localhost:8000/api/v1/catalog
RESOURCE_ID='<uuid-de-um-work-publicado>'
curl "$API/public/works?limit=2"
# Reenviar os mesmos filtros/limit; CURSOR recebe next_cursor da resposta anterior.
curl -G "$API/public/works" --data-urlencode limit=2 --data-urlencode "cursor=$CURSOR"
curl -G "$API/public/works" --data-urlencode "internal_id=$RESOURCE_ID"
curl -H 'Accept: application/json' "$API/works/$RESOURCE_ID/public"
curl -H 'Accept: application/ld+json' "$API/works/$RESOURCE_ID/public"
curl -H 'Accept: text/turtle' "$API/works/$RESOURCE_ID/public"
curl -i -H 'Accept: text/html' "$API/works/$RESOURCE_ID/public" # 406
# ACCESS_TOKEN obtido pelo OIDC existente, sem registrar seu valor.
curl -H "Authorization: Bearer $ACCESS_TOKEN" "$API/works?limit=20&editorial_state=draft"
```

Exemplo mínimo do mesmo conteúdo nos três formatos (dados sintéticos; respostas
operacionais reais incluem também as listas opcionais vazias):

```json
{"internal_id":"00000000-0000-4000-8000-000000000001","uri":"https://example.org/resources/00000000-0000-4000-8000-000000000001","title":[{"kind":"Title","main_title":[{"value":"Ação","language":"pt"}],"subtitle":[]}]}
```

```json
[{"@id":"https://example.org/resources/00000000-0000-4000-8000-000000000001","@type":["http://id.loc.gov/ontologies/bibframe/Work"],"http://id.loc.gov/ontologies/bibframe/title":[{"@id":"_:title"}]},{"@id":"_:title","@type":["http://id.loc.gov/ontologies/bibframe/Title"],"http://id.loc.gov/ontologies/bibframe/mainTitle":[{"@value":"Ação","@language":"pt"}]}]
```

O exemplo JSON-LD usa a forma expandida aceita pelo parser; o servidor compacta
predicados conhecidos e inclui o contexto local versionado em cada nó.

```turtle
@prefix bf: <http://id.loc.gov/ontologies/bibframe/> .
<https://example.org/resources/00000000-0000-4000-8000-000000000001>
    a bf:Work; bf:title [ a bf:Title; bf:mainTitle "Ação"@pt ] .
```

Os [exemplos pareados existentes](../examples/serialization/) cobrem os cinco tipos.
A equivalência é por isomorfismo RDF, sem comparar strings ou rótulos de blank nodes.

## Consulta PostgreSQL e limites

Uma consulta por página junta recursos, estado opcional e revisão escolhida. O
público exige published e número published_revision; editorial usa current_revision.
Seleciona somente UUID, URI, número e document, LIMIT limit+1; apenas limit snapshots
são parseados/projetados. Não carrega coleções completas, histórico, atores ou perfis
por registro. O teste de custo conta exatamente um statement por página.

Filtro de tipo usa JSONB `@>` com jsonb_build_array/jsonb_build_object de @id e @type
no mesmo objeto. Todas as entradas são parâmetros SQLAlchemy. As PKs existentes
suportam seek/junções, UNIQUE uri suporta igualdade. EXPLAIN real e índices estão
nas evidências. A amostra pequena pode usar scans e sort; quantidade constante de
statements não significa quantidade constante de linhas examinadas. Não há benchmark
de escala institucional. Índices adicionais/materialização de tipo exigem medição
representativa; não foi demonstrada necessidade de migração nesta entrega.

M05 é consulta transacional estruturada. M09 permanece responsável por descoberta,
Elasticsearch, indexação assíncrona, facetas, full-text e relevância; a primeira
integração exigirá decidir consistência/outbox. Nenhum RDF Store adicional é necessário.
Homologação institucional de perfis, OIDC de produção e carga permanecem separadas.
