# ADR 0031 — Autorização por operação no boundary de aplicação

Data: 2026-10-13. Estado: aceito para implementação M04.05 / #38.

## Contexto

OIDC, permissões e guardas HTTP existem (ADR 0016); histórico/editorial já
verificam permissões. `create`, `revise` e `read` ainda confiam em qualquer chamador
interno, inclusive sem ator. `ExecutionActor` classifica auditoria, mas não concede
acesso. Acrescentar permissões ao enum amplia implicitamente `frozenset(P)` do admin.

## Decisão

Preservar as 17 permissões e os seis papéis, enumerando as concessões administrativas.
Registrar políticas imutáveis em identity por operação, tipo de recurso, permissões
conjuntas, modalidade pública e elegibilidade técnica. Operação desconhecida ou
incompleta é negada; `system:admin` nunca substitui uma permissão funcional.

Um `AuthorizationGuard` por instância de serviço, injetável, independente de HTTP,
verifica contextos humanos/técnicos e recursos fornecidos pelos serviços proprietários.
Não consulta tabelas. OIDC/dependência FastAPI cria `HumanContext`; composition roots
internos configuram `TechnicalContext` com identificador, origem, permissões e operações
explícitas. Nenhum tipo Python protege contra código privilegiado dentro do processo.
Não deserializar esses contextos, atores ou recursos de body/header/query.

Serviços M03 aceitam `actor=` autenticado como adaptador de compatibilidade para
`HumanContext`, mas ausência de contexto não autoriza escrita/leitura editorial.
`ExecutionActor` isolado não autoriza; contexto técnico registra identidade técnica
real na nova auditoria. Autoria histórica nula continua nula, sem backfill.

Leitura editorial genérica exige read e metadata_revision:read, pois não existe
contrato confiável de instituição/propriedade. Histórico mantém permissões próprias.
Público acessa somente a revisão selecionada por `read_public`, em published.
Transições humanas preservam a máquina/CAS/validação/auditoria M03. Pré-verificação
por destino ocorre antes da transação; publish/republish são alternativas explícitas,
resolvidas e verificadas novamente no estado bloqueado. Kind de conteúdo existente
é verificado pelo perfil persistido antes das mutações, nunca pelo grafo proposto.

## Consequências

Chamadores legítimos passam contexto explicitamente; fixtures legadas usam stores
para representar registros históricos, sem introduzir escrita anônima na aplicação.
Não há endpoint novo, credencial técnica, tabela, migração, policy engine ou singleton.
Futuros adaptadores M05 propagam o contexto autenticado e reutilizam os serviços.
Falhas tipadas são traduzidas para 403 pelo Problem Details v1 existente.

Autenticação M2M, governança/revogação (#39), segurança operacional/E2E (#40–#42)
e escopo institucional permanecem fora desta decisão. O provedor configurado para
humanos deve impedir atribuição de papéis humanos a clients técnicos; não converter
client_credentials em HumanContext por conveniência. Homologação produção não é inferida.

[Contrato vigente](../architecture/operation-authorization.md).
