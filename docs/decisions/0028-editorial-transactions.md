# ADR 0028 — Estado editorial e auditoria no mesmo commit PostgreSQL

Status: implementado tecnicamente para #43; homologação institucional pendente

Data: 2026-10-12

## Contexto

ADRs 0026/0027 fornecem máquina editorial, revisões imutáveis, CAS e eventos, mas
não conectam metadados editoriais duráveis à escrita de conteúdo. Uma validação
antes do UPDATE sem proteção das referências admite TOCTOU e aprovação obsoleta.
RETURN/ARCHIVE não têm representação fiel nos oito tipos históricos.

## Decisão

Acrescentar somente experimental_semantic_editorial_states, PK da identidade,
CHECKs da política e FKs compostas de revisão corrente/aprovada/publicada. Versão
editorial é independente; candidata usa current_revision mais candidate_state,
como no domínio vigente. Não duplicar identidade, snapshots, histórico ou estados RDF.

Uma session.begin por operação. BibliographicService compõe prepare_content_revision,
RevisionStore/CAS, EditorialStore/CAS e AuditStore/append, todos sem commit próprio.
PostgresEditorialTransactions implementa EditorialTransaction, grava estado e evento
na mesma sessão e só devolve controle ao chamador depois do commit. Aprovação seleciona
revisão corrente esperada; publicação seleciona aprovada exata. Conteúdo candidato
não substitui a revisão pública. Restauração de conteúdo cria snapshot novo;
republicação revalida o snapshot público anterior, sem novo conteúdo.

Combinar locks de identidade com UPDATE condicional de versão/revisão. Estabelecer
ordem gate PostgreSQL transacional → identidade → referências. Conteúdo usa gate
advisory shared; decisões editoriais usam exclusive. Nenhuma decisão disputa locks
cruzados de referências enquanto outra decisão valida, e conteúdo não modifica
cabeças consultadas entre validação e commit. Referências locais também recebem
FOR KEY SHARE. Fechos locais acíclicos usam os contratos de resolução/validate_cycles.
Gate é conservador e serializa decisões no banco, compatível com o núcleo experimental;
não se declara escalabilidade de produção. Serviços de escrita precisam aderir ao
protocolo. Não confundir advisory lock transacional com mutex de processo.

Preservar assinaturas anteriores de conteúdo com expected_editorial_version opcional.
Chamadas anteriores usam estado bloqueado e ambos os CAS; novas chamadas podem
expressar expectativa editorial também. Uma expectativa omitida não detecta mudança
editorial anterior ao início da chamada. Transições sempre exigem duas expectativas.

Migração 0004 incremental, sem backfill. Legado sem estado retorna None; primeira
escrita bem-sucedida inicializa draft na mesma transação. Não inferir publicação de
eventos preparados/históricos, nem fabricar created/approved. Preservar inclusive
envelopes repetidos que a #28 permitia. Exatamente uma vez é propriedade da composição
CAS/append/commit, não unicidade retrospectiva ou mecanismo de deduplicação.

Ampliar taxonomia com record.returned e record.archived, CHECKs e invariantes tipadas.
Não alterar os oito significados anteriores. Downgrade rejeita presença dos novos
eventos; sem eles, perde somente estado editorial novo, em execução descartável.

Contexto usa releases locais/SHACL existentes, classificação por identidade PostgreSQL
ou mapa externo explícito confiável. Ausência não implica exterioridade. Não resolver
rede nem alegar consistência de fontes externas. Histórico autorizado reutiliza
metadata_audit:read e metadata_revision:read, sob bloqueio coerente do recurso.

## Alternativas e consequências

- Estado dentro do JSON-LD exigiria modificar snapshots; rejeitado pela imutabilidade.
- Stores com commits separados permitem estado sem auditoria; rejeitado.
- Validação apenas em memória não protege duas sessões nem referências; rejeitada.
- Locks de dependências em ordem arbitrária criam deadlocks em publicações cruzadas.
- Descobrir fecho e ordenar todos os locks com retries é alternativa de maior
  paralelismo, mas adiciona complexidade antes de medir necessidade. Evolução futura
  pode substituir o gate conservador por essa estratégia sem mudar a máquina.
- Serialização de todas as escritas com gate exclusivo reduziria também o paralelismo
  entre edições independentes; shared para conteúdo mantém esse paralelismo.
- Filas/outbox, Elasticsearch e workflow genérico não resolvem a necessidade desta issue.

UUID/URI, perfis e migrações anteriores permanecem intactos. Ciclo da identidade
active/discontinued/replaced/merged continua independente e sem novo serviço persistente.
Nenhuma exclusão, fusão automática, circulação ou API pública foi introduzida.

[Contrato operacional e limites](../architecture/editorial-persistence.md).
