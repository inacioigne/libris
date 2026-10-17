# ADR 0039 — Consultas catalográficas e representações autorizadas

Data: 2026-10-16. Status: implementado tecnicamente para M05.06 / #50.

## Contexto

M05.03 e M05.05 já fixam caminhos, identidade, CAS e seleção pública. O tipo não
possui coluna própria: está no nó raiz do JSONB expandido imutável. DTO Read é uma
projeção parcial; reconstruir RDF pelo DTO perderia extensões históricas.

## Decisão

GET das cinco coleções é editorial; GET `/public/{collection}` é anônimo. As
políticas M04 existentes autorizam leitura editorial antes do SQL. Público restringe
estado published e junta exatamente published_revision, conferindo também a política
read_public com a identidade e revisão selecionadas antes da projeção. Não há fallback
entre escopos nem expansão de referências. A consulta é um único statement MVCC:
identidade + ponteiro + snapshot pertencem à mesma visão PostgreSQL do statement.

Keyset por UUID ascendente imutável fornece ordem total, sem títulos/datas mutáveis.
`limit` 20, 1–100; seek `id > :after`, LIMIT limit+1. Cursor base64url canônico contém
versão, último UUID e digest de coleção, escopo, ordem, limite e filtros. É opaco para
o consumidor, sem assinatura ou concessão de acesso: pode ser reconstruído por um
cliente, mas toda consulta revalida autorização e filtros. Não contém conteúdo privado.
Nenhuma sessão/snapshot de banco é mantida entre requisições. Em conjunto estático a
travessia não duplica nem omite; inserções anteriores ao cursor não aparecem, posteriores
podem aparecer. Atualizações não movem UUID; mudança de visibilidade/filtro altera a
participação. Não há garantia de snapshot global ou de total constante entre páginas.

Filtros são igualdades explícitas por UUID, URI e perfil do snapshot selecionado,
com estado editorial adicional somente no escopo editorial. Tipo vem da rota fechada.
Estado ausente no legado não equivale a draft. Parâmetros desconhecidos são rejeitados;
null textual não funciona como sentinela. Sem busca textual ou filtros por predicados
arbitrários. SQLAlchemy parametriza os valores; a condição JSONB combina @id e @type
no mesmo objeto raiz, incluindo os três subtipos de Agent. Somente limit+1 snapshots
chegam à aplicação e somente limit são projetados. Não há leitura de perfil/revisão
por linha, contagem global ou parsing de todo o catálogo na aplicação.

Os GET individuais editorial/público usam negotiate_format e serialize_graph M03,
sobre o snapshot selecionado pelo serviço existente. JSON continua sendo Read v1;
JSON-LD/Turtle exportam integralmente o snapshot proprietário, sem proveniência
administrativa, histórico ou descrição de alvos. Vary inclui Accept, 406 preserva
Problem Details. JSON editorial conserva seu ETag; exportações e JSON público têm
ETag próprio de formato + bytes. If-Match de escrita continua aceitando exclusivamente
o ETag JSON editorial. Cache no-store/private M04 permanece aplicável à retirada.

## Índices e alternativas

Reutilizar PK recursos(id), UNIQUE recursos(uri), PK revisões(resource_id,number)
e PK estado(resource_id). Não criar migração sem ganho demonstrado: joins usam essas
chaves e seek usa UUID; o tipo depende do snapshot selecionado e do @id correlacionado.
GIN genérico do histórico pode aumentar custo de escrita sem resolver esse join.
O EXPLAIN real está nas evidências M05.06, incluindo scans/sort da amostra pequena.
Não se afirma custo constante em registros examinados nem escala institucional:
filtrar tipos/perfis/estados seletivos pode examinar muitas cabeças. Medir em volume
representativo antes de materializar tipo ou criar índices adicionais; eventual
materialização requer migração incremental e contrato para legado.

Offset foi descartado por deslocamento sob inserções. Snapshot global/cursor assinado
adicionariam estado/gestão de chaves sem requisito demonstrado. Elasticsearch, outbox,
facetas, full-text, relevância e RDF Store adicional continuam fora desta entrega;
M09 decidirá projeções e consistência antes da primeira integração real.

## Consequências

Sem mudanças de DTOs históricos, perfis, SHACL, snapshots, autenticação ou migrações.
As garantias de publicação/CAS continuam nos serviços M03/M05. Homologação OIDC real,
produção, perfis institucionais e carga não são inferidas dos testes desta entrega.
