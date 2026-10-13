# ADR 0027 — Auditoria observada na transação das revisões semânticas

Status: implementado tecnicamente para #28; persistência editorial e homologação pendentes

Data: 2026-10-12

## Contexto

ADRs 0011/0015 oferecem revisões append-only, CAS e RDF no PostgreSQL; 0016 oferece
identidade OIDC opcional. ADR 0026 implementa política editorial e eventos preparados,
sem adaptador persistente. Provenance tem origem/processo; faltam envelope observado,
consulta autorizada e associação durável de operações que não criam conteúdo.

## Decisão

Preservar RevisionStore e acrescentar AuditEvent frozen, taxonomia fechada de oito
StrEnum, atores human/service/automated e restauração content/editorial explícita.
Provenance recebe reason opcional; demais metadados continuam agregados por Revision.
Resolver a release pelo identificador local imutável do perfil, sem coluna duplicada.

Migração 0003 acrescenta reason nullable e tabela experimental de eventos, com PK,
FKs de revisão/origem/sucessor, CHECKs, índices cronológicos e triggers contra
UPDATE/DELETE/TRUNCATE. UUID/URI e perfil são recuperados por joins ao recurso/revisão.
Sem backfill, sem alteração de 0001/0002 ou snapshots e sem autoria fictícia.
DML privilegiado que desabilite triggers/edite identidades não está coberto.

BibliographicService grava created/revised na mesma transação de recurso/CAS/snapshot.
Stores fazem flush, não commit. restore_content exige permissões de leitura/criação,
copia snapshot histórico como revisão nova pelo mesmo CAS e grava um único restored,
com origem histórica e proveniência atual. Não altera visibilidade editorial.

HistoryService exige metadata_revision:read; auditoria exige nova metadata_audit:read,
concedida explicitamente a reviewer/publisher/admin. BibliographicService.read continua
primitiva interna confiável. Nenhuma API pública de histórico. Actor desconhecido
permanece ausente; contexto técnico controlado não representa humano. Contexto humano
continua vindo da autenticação OIDC, sem JWT/claims/e-mail na persistência.

Comparar Graph com rdflib.compare (isomorfismo/canonicalização/graph_diff), retornando
termos/triplas estruturados. Mudança estrutural de blank node pode incluir seu
componente inteiro no delta; rótulos nunca são identidade persistente. Não compor
revisões atuais de terceiros ao comparar snapshots históricos nem resolver a rede.

Adaptar eventos preparados da #27 sem recriar sua matriz. O adaptador editorial
persistente futuro deve salvar estado e envelope na mesma transação CAS. RETURN e
ARCHIVE não têm correspondência fiel na taxonomia solicitada; rejeitar explicitamente
até extensão governada, evitando falso revised/withdrawn/superseded. Não simular
workflow durável nem integrar BibliographicService a metadados inexistentes.

## Alternativas e consequências

Embedding de auditoria em JSON-LD misturaria operação administrativa e afirmação RDF,
e forçaria snapshots novos para decisões editoriais. Outro histórico duplicaria CAS.
Logs, Elasticsearch, outbox, event bus ou triplestore não fornecem necessidade adicional
neste escopo. Backfill fabricaria observações não realizadas. Um dict genérico de
claims facilitaria vazamento e tipos arbitrários; usar campos explícitos e enums.

A migração deve preceder execução do serviço atualizado. Downgrade perde toda a
auditoria e justificativas, sendo verificado só em banco descartável separado.
Leituras legadas continuam válidas e podem indicar ausência de evento observado.
Homologação institucional, retenção/visibilidade, quotas de comparação e operações
editoriais/ciclo de identidade persistentes permanecem entregas posteriores.
Sem novas dependências, frontend, rotas ou mudanças em locks.

[Contrato e limites](../architecture/provenance-audit-versioning.md).
