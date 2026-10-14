# Critérios de saída de segurança — M04

A implementação vigente de autorização backend é a **M04.05 / #38**, descrita em
[autorização por operação](operation-authorization.md) e comprovada no
[relatório próprio](identity-m04-05-verification.md). As tabelas datadas abaixo
preservam o diagnóstico das entregas anteriores, sem representar enforcement atual.

Data: 2026-10-13. Checkout e inventário na [baseline](security-baseline.md);
resultados atuais na [verificação](security-m04-01-verification.md).
Esta lista diferencia aceitação documental da #34, conclusão da milestone M04 e
capacidades posteriores. “Documentado” não significa controle operacional aprovado.
Não declara homologação institucional, segurança E2E ou produção.

## Aceitação da M04.01 / #34

Cada linha deve ser verificável pelo mantenedor no working tree desta entrega.
Situação “atendido documentalmente” requer revisão humana, sem fechar a issue remota.

| ID | Requisito verificável | Evidência esperada / atual | Situação | Dependência / responsável | Condição de aprovação |
| --- | --- | --- | --- | --- | --- |
| A01 | Inventariar Entrega A com estados distintos e checkout datado | security-baseline: tabela, branch/HEAD, testes/símbolos e fontes | atendido documentalmente | código local, #34 | revisar que IT/IO/EP/ND não afirmam Keycloak/Next.js operacional |
| A02 | Preservar Resource Server, mapa centralizado e deny-by-default | ADR 0016 + matriz das 17 permissões/seis papéis | atendido documentalmente | #34, ADR 0016 | valores/concessões iguais ao enum/mapa; nenhum mecanismo paralelo |
| A03 | Modelar oito fronteiras e ameaças com evidência | security-threat-model: Mermaid, TH01–TH24, cenários/controles/tratamento | atendido documentalmente | #34 | cada ID possui todos os campos e identifica fluxo atual/futuro |
| A04 | Descrever fail closed e exceções de liveness | tabela de falhas com testes, cache válido, lacunas de cobertura | atendido documentalmente | #34 | 401/403 reais distinguidos de erros internos/futuros; /health público |
| A05 | Consolidar acesso por domínio e operação | security-access-matrix: bibliographic, authority, revision/audit, editorial e system | atendido documentalmente | #27/#28/#43, #34 | nenhuma rota inexistente apresentada como protegida; enforcement interno corretamente delimitado |
| A06 | Preservar pré-condições M03 e identidade histórica | submatriz editorial, CAS, transação, candidata/publicada, NULL histórico | atendido documentalmente | ADRs 0011/0015/0026/0027/0028 | não reimplementar auditoria nem fabricar ator/estado; contratos v1 intactos |
| A07 | Examinar necessidade de ADR e conter escopo | baseline: decisão de nenhum ADR novo | atendido | #34 | documentação consolida decisões existentes; ADRs históricos intactos |
| A08 | Mapear saída M04 e capacidades M05–M15 | critérios M/P abaixo e vínculos GitHub | atendido documentalmente | #34 | diferidos explícitos, sem inventar responsabilidades de milestones |
| A09 | Reproduzir verificações e limitações | security-m04-01-verification: comandos/resultados atuais | executado conforme relatório | ambiente local, #34 | falhas/skips/limites registrados; nenhuma aprovação baseada só em histórico |
| A10 | Integrar navegação e preservar trabalho/Git | links em overview/identity/README e estado final no relatório | atendido localmente | #34 | links válidos; branch original; sem commit/push/PR/alteração remota/dados sensíveis |

## Conclusão futura da milestone M04

Issues abaixo foram consultadas no GitHub em 2026-10-13 e estavam abertas,
associadas à milestone 4. A sequência decorre de seus escopos/dependências,
não da suposição de entregas concluídas. IT/IO/EP/ND seguem a baseline.

| ID / categoria | Requisito verificável | Evidência esperada | Situação atual | Dependência / issue responsável | Condição de aprovação |
| --- | --- | --- | --- | --- | --- |
| M01 Arquitetura/confiança | Baseline e política por fronteira mantidas durante implementações | quatro documentos #34 + revisão de cada fluxo ativado | esta consolidação documental | [#34](https://github.com/inacioigne/libris/issues/34), consumidor de cada fronteira | revisão aceita; novas decisões duradouras com ADR quando necessário |
| M02 Identidade OIDC | Validar assinatura/claims/discriminador/alg/kid e erros | testes offline + tokens reais, sem publicar tokens | IT offline, IO integração | [#35](https://github.com/inacioigne/libris/issues/35), [#42](https://github.com/inacioigne/libris/issues/42) | casos negativos e positivos efetivamente executados com provedor real |
| M03 Keycloak | Compose, issuer único browser/API, PKCE S256, audience API/typ/roles, rotação e indisponibilidade | roteiro reproduzível e execução datada isolada | IO: realm/Compose, sem homologação real | #35 depende #34 | token real → /me e negações; sem credenciais/usuários versionados; atualizar papéis reviewer/publisher conscientemente |
| M04 Sessão web | Login/callback/logout, renovação ou expiração, sessão servidor e cookies adequados | testes state/PKCE/nonce pertinente/callback/logout/expiração/provedor | ND no App Router | [#36](https://github.com/inacioigne/libris/issues/36), depende #35 | fluxos reais e negativos aprovados; tokens fora de JS/localStorage/URLs/logs/NEXT_PUBLIC |
| M05 Interface administrativa | Guardas no servidor e navegação baseada em permissões efetivas | testes sem sessão/negação/expiração/serviço indisponível, acessibilidade pt/en | ND | [#37](https://github.com/inacioigne/libris/issues/37), depende #36 | conteúdo protegido não renderizado sem sessão; esconder botão não substitui API |
| M06 Autorização backend | Política por operação/recurso, guard de aplicação e contexto técnico confiável | matriz RBAC parametrizada; payload/header/unknown role/mismatch recusados | IT dependências/histórico/editorial; EP guard geral | [#38](https://github.com/inacioigne/libris/issues/38), depende #34 | create/revise/read não expostos diretamente; deny-by-default; admin sem bypass; boundaries testados |
| M07 Governança de acesso | Ativação/desativação, concessão/revogação, serviços e menor privilégio | procedimento Keycloak, prazos de token/revogação, testes e auditoria administrativa | EP; ExecutionActor interno não é conta de serviço autenticada | [#39](https://github.com/inacioigne/libris/issues/39), depende #38/#35 | revogação não prometida instantânea; identidade técnica estável e privilégio restrito; sem cadastro/senhas locais |
| M08 HTTP/proteção de dados | CORS/CSRF, headers pertinentes, limites, HTTPS produção, redirects/caches seguros | testes CORS proibido, CSRF/state/open redirect/cache/headers e ausência de segredos | IT CORS/limites OIDC; EP demais | [#40](https://github.com/inacioigne/libris/issues/40), depende #36 | política adequada a browser/SSR/cookies; exceções HTTP de dev explícitas; falhas sem vazamento |
| M09 Proveniência/auditoria | Integrar segurança sem duplicar M03; ator/ação/resultado/correlação UTC; retenção/restrição | eventos de sessão/autorização/admin e testes de logs sem tokens/PII | IT auditoria bibliográfica interna; EP segurança | [#41](https://github.com/inacioigne/libris/issues/41), depende #28/#38 | eventos de falha sem humano fictício; cadeia editorial/NULL/snapshots preservados |
| M10 Testes/E2E | Consolidar suíte offline e integração real opcional, gate/roteiro de homologação | artefatos/versões/comandos e matriz negativa JWT/RBAC/sessão | IT offline; E2E ND | #42 depende #35–#41 | execuções reproduzidas, riscos aceitos explicitamente, nenhum skip tratado como prova |
| M11 Persistência | Confirmar regressão de CAS, revisão/estado/auditoria atômicos e visibilidade | PostgreSQL real descartável, sessões concorrentes e rollback em sessão nova | código/testes presentes; resultado atual discriminado | #27/#28/#43 e regressão #42 | nenhum banco de trabalho usado; sem backfill; publicada exata/candidata isolada |
| M12 Operação/infraestrutura | Distinguir dev/prod, segredos/rede/TLS e indisponibilidade/readiness | revisão da implantação específica e limites de disponibilidade | Compose IO dev; produção ND | #35/#40/#42; produção detalhada conforme escopo aprovado | /health continua liveness público; ambiente seguro não inferido do Compose ou de build aprovado |

Concluir M04 exige evidência dos requisitos operacionais no escopo aprovado das
#35–#42, revisão dos riscos residuais e aprovação do mantenedor. #34 não implementa
essas issues. Segurança institucional e produção exigem decisões específicas;
M12 não atribui automaticamente toda a operação de produção à M04.

## Capacidades posteriores M05–M15

O pedido e #34 diferem explicitamente capacidades para **M05–M15**. As fontes locais
e issues consultadas não oferecem distribuição completa e aprovada entre todos
esses milestones; esta tabela não inventa número de issue ou milestone específico.
M05 é citado para APIs catalográficas pelo contexto M04; os demais vínculos abaixo
exigem confirmação de planejamento antes de implementação.

| ID | Capacidade / requisito verificável futuro | Evidência esperada | Situação | Dependência / responsável | Condição antes de disponibilizar |
| --- | --- | --- | --- | --- | --- |
| P01 | CRUD/PATCH catalográfico, ETag/If-Match e seleção pública/editorial | endpoints registrados, guards, Problem Details v1, testes 401/403/CAS/visibilidade | EP: contratos e serviços internos, sem API | M05, após M04; ADRs 0011/0016/0017/0028 | nenhuma escrita anônima, ator confiável, permissões por operação/recurso; contratos v1 compatíveis |
| P02 | Autoridades/identificadores/reconciliação e ciclo persistente de identidade | APIs/serviços com CAS/sucessor/justificativa e preservação UUID/URI | contratos IT; reconciliação/fusão operacional ND | M05–M15 conforme planejamento; autoridade distinta de usuário | authority:manage não concede publicação/histórico automaticamente; sem reutilização de identidade |
| P03 | Editor/formulários/perfis e workflow UI | testes de acessibilidade/i18n/sessão/XSS e estados editoriais | perfis/SHACL internos IT; editor ND | M05–M15; #37 menciona editor M07 como fora do shell, não autoriza implementá-lo aqui | UI usa permissões do servidor e preserva candidata/publicada |
| P04 | Descoberta Elasticsearch/projeções/exportações | ADR de consistência/outbox antes da primeira integração, reconstrução e testes de retirada/visibilidade | ND; container dev não é integração | M05–M15 conforme escopo; ADR 0015 | minimizar campos; nunca rascunhos/PII; PostgreSQL fonte de verdade |
| P05 | Inventário/circulação/reservas/usuários/políticas | modelo operacional próprio, autorização por recurso e proteção de dados pessoais | ND | M05–M15 conforme [domínios](domains.md) | separar Work/Instance/Item de disponibilidade/empréstimo; catálogo não autoriza PII de leitores |
| P06 | Aquisições/periódicos/relatórios/interoperabilidade | contratos de módulos, quotas, privilégio de integração e exportação mínima | ND | M05–M15 conforme escopo documentado | sem acesso direto a tabelas alheias nem serviços administrativos com privilégio universal |
| P07 | Contextos institucionais/multiunidade/serviços | política por instituição/unidade, isolamento e teste entre contextos | EP | #39 menciona extensão M10/M11; implementação futura requer requisitos confirmados | sem multi-tenant prematuro; não deduzir escopo de roles ou campos do cliente |
| P08 | Produção, retenção/backup/recuperação/observabilidade/carga | plano aprovado e execuções datadas específicas de implantação | ND operacionalmente | etapa de operação M05–M15 conforme planejamento; sem milestone arbitrário | configuração própria, privilégio mínimo, recuperação e riscos testados; Compose local não é aceite |

Cada nova operação deve reabrir a avaliação de fronteiras/ameaças e testar negações,
autoridade do ator e visibilidade. Não criar permissões presumidas para esses domínios:
granularidade futura requer contrato/revisão antes de ampliar o enum e libris-admin.

## Atualização M04.03 — 2026-10-13

A baseline/tabelas acima representam o diagnóstico M04.01 datado; não foram
reescritas como evidência de testes posteriores. O App Router agora contém
[BFF OIDC e sessões compartilhadas](identity-web.md), decisão
[ADR 0030](../decisions/0030-web-oidc-sessions.md), com
[resultados próprios](identity-web-verification.md).

| Fronteira/ameaça | Controle implementado M04.03 | Limite restante |
| --- | --- | --- |
| F1/F3/F4, TH13 | Tokens somente server-only, PostgreSQL cifrado, cookie ID opaco, no-store/referrer | Logs do proxy, host/secret manager e backups exigem configuração operacional |
| TH15 | Code/S256, state/binding por tentativa, nonce/assinatura/aud/issuer, uso único, novo ID; POST Origin/Host + CSRF no logout | XSS pode executar ações no contexto da vítima; revisão CSP/pentest #40/#42 |
| TH16 | Redirect URI fixa, retorno /pt ou /en canônico, endpoints discovery restritos à origem do issuer | Confiança no provedor/configuração; homologação navegador real pendente |
| TH07/TH22 | Timeout/limite de resposta, locks PG e backoff por sessão, fail closed | Quotas globais, avaliação de carga/pool/locks e disponibilidade pendentes |
| TH21/TH23 | HTTPS obrigatório em production, cookies Secure/__Host-, logout local commit antes de RP logout | Compose é local; JWT previamente emitido não tem revogação global instantânea |
| M04 sessão web | Código e testes negativos; persistência real isolada e ensaio HTTP próprio | Keycloak web real, leitores de tela e produção não homologados |

/health permanece público; /identity/me continua Bearer da API. Páginas públicas
não dependem de login; identidade renderizada provém somente da API. Nenhuma
permissão de CRUD/shell M05/#37 foi introduzida. Auditoria de segurança #41,
autorização contextual #38/#39 e homologação abrangente #42 continuam separadas.

## Atualização M04.05 — 2026-10-13

As 17 permissões/seis papéis são preservados, com admin enumerado explicitamente.
Política fechada por operação/recurso, guard de aplicação e contextos humano/técnico
estão implementados. create/revise/read não têm fallback sem ator/contexto; histórico
conserva permissões próprias e conjunção explícita na leitura editorial de auditoria.
Reader só com read não acessa rascunhos. read_public seleciona a publicação exata.
Serviços técnicos exigem permissões e allowlist, sem decisões editoriais humanas.
SYSTEM_ADMIN não é bypass. Payload/header/query não criam contextos confiáveis.

O item M06 da tabela histórica é implementado tecnicamente nesta entrega, com
[evidências atuais](identity-m04-05-verification.md). M07/M09/M10, M2M, escopo
institucional e APIs CRUD M05 continuam escopos futuros. Nenhuma homologação de
produção/Keycloak/navegador é declarada por esta regressão. Relatórios anteriores
não foram sobrescritos; nenhum estado/issue remoto foi modificado.
