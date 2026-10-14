# ADR 0035 — Emissão de eventos de segurança separada da auditoria M03

Data: 2026-10-14. Estado: implementado localmente para M04.08 / #41;
retenção institucional, coleta durável e homologação operacional pendentes.

## Contexto

#28/#43 mantêm revisões, snapshots e auditoria catalográfica na transação PostgreSQL.
#38 centraliza autorização por operação; #39 governa a identidade; #40 protege HTTP
e quotas. A #41 exige observação de autenticação, decisões de acesso e sessões,
sem transformar tentativas em alterações bibliográficas nem criar usuários locais.
Não há requisito de ledger durável ou endpoint de consulta na issue.

## Decisão

Criar módulo `security_audit` na API, com contrato Pydantic frozen/extra=forbid,
protocolo síncrono `SecuritySink` e adaptador de JSON por logging nativo. No BFF,
contrato server-only equivalente com validação em runtime, `SecurityAudit` injetável
e adaptador `console.info`. Envelope 1.0 com campos fechados; nenhum objeto arbitrário
ou mensagem externa é serializado. Perfis API/BFF e taxonomia em
[security-audit.md](../architecture/security-audit.md).

AuthorizationGuard aceita observador opcional mantendo os construtores existentes.
O guard continua sendo o único motor e só registra a decisão preliminar, nunca
commit de negócio. Recursos conhecidos acrescentam somente UUID ao ResourceContext;
as chamadas M03 propagam esse UUID sem alterar auditoria, revisão ou transação.
Pré-verificações e verificações contra estado carregado são decisões distintas.

Identidade só é associada após validação do boundary existente. Falhas de
autenticação têm ator null. BFF deriva o mesmo hash issuer/subject a partir de ID
token validado ou sessão armazenada pelo serviço confiável, nunca do cookie/payload.
Eventos de estado da sessão são emitidos após retorno do store/COMMIT; observações
preparadas dentro de withSession são locais à chamada e descartadas em rollback.
Refresh falho e revogação confirmada descrevem fatos distintos. Logout confirmado
significa revogação local, sem afirmar logout global no provedor.

Reutilizar ContextVar Python e adicionar AsyncLocalStorage Node para correlação.
Proxy web substitui o ID externo; API aceita UUID canônico apenas como metadado
informativo. O BFF encaminha o ID à API quando realiza /me. API envolve também CORS
e tratamento de 500. Nenhuma autenticação depende do request ID. Não criar tracing,
identificador derivado de credencial ou vínculo persistido de login/callback.

Falha do sink é **best effort**: sinal fixo `security_audit_sink_unavailable`, sem
exceção externa; decisões/exceções e transações seguem inalteradas. Negação continua
negada, autorização pode prosseguir sem log. Esse compromisso implica risco de perda,
exige monitoramento operacional e não substitui fail-closed do armazenamento M03.
Não há atomicidade entre log de segurança, provedor e banco, nem entrega garantida.

## Alternativas e consequências

Reutilizar AuditStore/M03 fabricaria eventos bibliográficos; rejeitado. Persistência
nova, outbox, fila ou coletor embutido acrescentaria transação/infraestrutura sem
requisito demonstrado. Falhar operações por falha do logger alteraria comportamento
de autorização/sessão e disponibilidade; a emissão desta issue permanece observacional.
Se a instituição exigir trilha durável obrigatória, será necessária nova decisão,
mecanismo concreto e testes de consistência antes de declarar essa garantia.

A implantação deve coletar stdout BFF e stderr do logger dedicado da API, restringir
acesso, configurar retenção/expurgo, lidar com backups e preservação para incidentes,
monitorar perda/volume e sincronizar relógios. Política proposta em security-audit.md;
não há expurgo automático implementado. Nenhuma migração, backfill, alteração RDF,
novo endpoint, dependência ou mudança das 17 permissões/seis papéis.
